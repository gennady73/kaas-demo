"""Offline fake API checks only: no real credentials, TLS connection or Kafka clients."""
import base64, copy, json, unittest
from unittest.mock import patch
import delivery as d

CANARY = 'OFFLINE_PRIVATE_CANARY_NOT_A_REAL_PASSWORD'
class FakeAPI:
    def __init__(self):
        self.created=[];self.reads=[];self.collision=False;self.bad_owner=False
        self.invalid_password=False;self.rotate=False;self.fail_after=None;self.bad_ca=False
    def destination_metadata(self,kind,name):return {'kind':'PartialObjectMetadata'} if self.collision else None
    def user(self,name):
        return {'metadata':{'name':name,'uid':'user-'+name,'generation':1},'spec':{'authentication':{'type':'scram-sha-512'}},'status':{'secret':name,'observedGeneration':1,'conditions':[{'type':'Ready','status':'True'}]}}
    def source_secret(self,name):
        self.reads.append(name)
        metadata={'name':name,'namespace':d.SOURCE_NS,'uid':'secret-'+name,'resourceVersion':'1','labels':{'strimzi.io/cluster':'kaas-dev'},'ownerReferences':[{'kind':'KafkaUser','name':name,'uid':'wrong' if self.bad_owner else 'user-'+name}],'annotations':{'never-copy':CANARY}}
        data={'password':None if self.invalid_password else base64.b64encode(CANARY.encode()).decode(),'unwanted':CANARY}
        if name==d.CA_SOURCE:data={'ca.crt':base64.b64encode(('bad' if self.bad_ca else 'PUBLIC_CA_STUB').encode()).decode()}
        return {'metadata':metadata,'data':data}
    def source_metadata(self,name):
        return {'name':name,'namespace':d.SOURCE_NS,'uid':'secret-'+name,'resourceVersion':'2' if self.rotate else '1'}
    def create(self,kind,obj):
        if self.fail_after is not None and len(self.created)>=self.fail_after:raise d.DeliveryError('HTTP_403')
        self.created.append((kind,copy.deepcopy(obj)))
        return {'metadata':{'name':obj['metadata']['name'],'namespace':d.DEST_NS,'uid':'new-'+obj['metadata']['name'],'resourceVersion':'9'}}

class FakeTLS:
    def load_verify_locations(self,*,cadata):
        if cadata!='PUBLIC_CA_STUB':raise ValueError('invalid stub')

class DeliveryTests(unittest.TestCase):
    def run_delivery(self,api,record=None):
        record={} if record is None else record
        with patch.object(d.ssl,'create_default_context',return_value=FakeTLS()):return d.deliver(api,record)
    def test_exact_four_password_secrets_and_public_ca(self):
        api=FakeAPI();record=self.run_delivery(api)
        self.assertEqual(len(api.created),5);self.assertEqual(record['status'],'DELIVERED_NOT_CLIENT_TESTED')
        self.assertEqual({x[1]['metadata']['name'] for x in api.created if x[0]=='secrets'},set(d.USERS))
        for kind,obj in api.created:
            self.assertEqual(obj['metadata']['namespace'],d.DEST_NS)
            self.assertNotIn('annotations',obj['metadata'])
            self.assertEqual(set(obj['data']),{'password'} if kind=='secrets' else {'ca.crt'})
        self.assertNotIn(CANARY,json.dumps(record));self.assertNotIn(base64.b64encode(CANARY.encode()).decode(),json.dumps(record))
    def test_collision_precedes_source_reads_and_all_writes(self):
        api=FakeAPI();api.collision=True
        with self.assertRaises(d.DeliveryError):self.run_delivery(api)
        self.assertEqual(api.reads,[]);self.assertEqual(api.created,[])
    def test_wrong_owner_blocks_all_writes(self):
        api=FakeAPI();api.bad_owner=True
        with self.assertRaises(d.DeliveryError):self.run_delivery(api)
        self.assertEqual(api.created,[])
    def test_missing_password_blocks_all_writes(self):
        api=FakeAPI();api.invalid_password=True
        with self.assertRaises(d.DeliveryError):self.run_delivery(api)
        self.assertEqual(api.created,[])
    def test_rotation_during_staging_blocks_all_writes(self):
        api=FakeAPI();api.rotate=True
        with self.assertRaises(d.DeliveryError):self.run_delivery(api)
        self.assertEqual(api.created,[])
    def test_invalid_ca_blocks_all_writes(self):
        api=FakeAPI();api.bad_ca=True
        with self.assertRaises(d.DeliveryError):self.run_delivery(api)
        self.assertEqual(api.created,[])
    def test_partial_failure_keeps_receipt_and_does_not_delete(self):
        api=FakeAPI();api.fail_after=2;record={}
        with self.assertRaises(d.DeliveryError):self.run_delivery(api,record)
        self.assertEqual(len(record['created']),2);self.assertEqual(len(api.created),2)
        self.assertNotIn(CANARY,json.dumps(record))
    def test_untrusted_error_text_is_not_exported(self):
        self.assertEqual(d.safe_reason(d.DeliveryError(CANARY)),'UNCLASSIFIED_DELIVERY_ERROR')
        self.assertEqual(d.safe_reason(d.DeliveryError('HTTP_403')),'HTTP_403')
    def test_default_command_has_no_live_api_access(self):
        with patch.object(d,'LiveAPI',side_effect=AssertionError('must not connect')):
            self.assertEqual(d.main([]),0)

if __name__=='__main__':unittest.main()
