import copy
import json
import tempfile
import unittest
from pathlib import Path

import render


class C5PreparationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = json.loads((render.ROOT / "inputs.json").read_text())
        self.stages, self.missing = render.load(self.inputs)

    def candidate_inputs(self):
        # Deliberately synthetic. These values are never promotion evidence.
        result = copy.deepcopy(self.inputs)
        result["values"].update(SOURCE_REVISION="a" * 40)
        result["promotion_evidence"] = {k: "SYNTHETIC_TEST_ONLY" for k in result["promotion_evidence"]}
        return result

    def test_preview_and_explicit_gaps(self):
        self.assertEqual(sum(map(len, self.stages.values())), 25)
        self.assertEqual(self.missing, ["SOURCE_REVISION"])
        for policy in self.stages["registry"]:
            if policy["kind"] == "NetworkPolicy":
                self.assertEqual(policy["spec"]["ingress"][0]["from"][0]["namespaceSelector"]["matchLabels"],
                                 {"policy-group.network.openshift.io/ingress": ""})

    def test_real_candidate_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "candidate"
            with self.assertRaisesRegex(ValueError, "missing values"):
                render.render(self.inputs, out, "candidate")
            self.assertFalse(out.exists())

    def test_other_release_csv_or_images_rejected(self):
        for key, value in (("STARTING_CSV", "apicurio-registry-3.v3.3.4-r2"),
                           ("APP_IMAGE", "example.invalid/app@sha256:" + "a" * 64),
                           ("UI_IMAGE", "example.invalid/ui@sha256:" + "b" * 64)):
            inputs = copy.deepcopy(self.inputs)
            inputs["values"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "release lock"):
                render.load(inputs)

    def test_complete_synthetic_candidate_schema_validation(self):
        stages, missing = render.load(self.candidate_inputs(), "candidate")
        self.assertFalse(missing)
        self.assertEqual(len(stages["realm"]), 1)

    def test_mutation_flags_rejected(self):
        for field in ("deployment_authorized", "registration_authorized", "tests_authorized"):
            for value in (True, 0, "false", None):
                with self.subTest(field=field, value=value):
                    inputs = copy.deepcopy(self.inputs)
                    inputs[field] = value
                    with self.assertRaises(ValueError):
                        render.load(inputs)

    def test_existing_realm_and_parent_are_protected(self):
        for name in ("master", "sso"):
            stages = copy.deepcopy(self.stages)
            stages["realm"][0]["spec"]["realm"]["realm"] = name
            with self.assertRaisesRegex(ValueError, "existing SSO"):
                render.validate(stages)

    def test_existing_keycloak_resource_cannot_be_added(self):
        self.stages["realm"].append({"apiVersion": "k8s.keycloak.org/v2alpha1", "kind": "Keycloak",
                                     "metadata": {"name": "keycloak", "namespace": "keycloak"}})
        with self.assertRaisesRegex(ValueError, "disallowed"):
            render.validate(self.stages)

    def test_auto_sync_and_cascade_delete_rejected(self):
        app = next(d for d in self.stages["bootstrap"] if d["kind"] == "Application")
        app["spec"]["syncPolicy"]["automated"] = {}
        with self.assertRaisesRegex(ValueError, "automatic"):
            render.validate(self.stages)

    def test_wrong_namespace_and_unknown_cr_field_rejected(self):
        stages = copy.deepcopy(self.stages)
        stages["postgres"][0]["metadata"]["namespace"] = "kaas-kafka"
        with self.assertRaisesRegex(ValueError, "outside isolated"):
            render.validate(stages)
        self.stages["registry"][0]["spec"]["app"]["auth"]["notAnAuthField"] = True
        with self.assertRaisesRegex(ValueError, "unknown CR field"):
            render.validate(self.stages)

    def test_grant_and_audience_mismatch_rejected(self):
        clients = self.stages["realm"][0]["spec"]["realm"]["clients"]
        clients[1]["protocolMappers"][0]["config"]["included.client.audience"] = "other-api"
        with self.assertRaisesRegex(ValueError, "audience"):
            render.validate(self.stages)

    def test_tls_bypass_rejected(self):
        self.stages["registry"][0]["spec"]["app"]["auth"]["tls"]["tlsVerificationType"] = "none"
        with self.assertRaisesRegex(ValueError, "TLS validation"):
            render.validate(self.stages)

    def test_secret_values_remain_external(self):
        ri = self.stages["realm"][0]
        self.assertEqual(len(ri["spec"]["placeholders"]), 5)
        for user in ri["spec"]["realm"]["users"]:
            for credential in user.get("credentials", []):
                self.assertRegex(credential["value"], r"^\$\{C5_[A-Z_]+\}$")
        self.assertFalse(any(d["kind"] == "Secret" for docs in self.stages.values() for d in docs))

    def test_retained_storage_and_no_secret_rbac(self):
        pvc = next(d for d in self.stages["postgres"] if d["kind"] == "PersistentVolumeClaim")
        del pvc["metadata"]["annotations"]
        with self.assertRaisesRegex(ValueError, "retained"):
            render.validate(self.stages)
        stages, _ = render.load(self.inputs)
        role = next(d for d in stages["bootstrap"] if d["kind"] == "Role")
        role["rules"][0]["resources"].append("secrets")
        with self.assertRaisesRegex(ValueError, "Secret"):
            render.validate(stages)

    def test_moving_tags_and_missing_evidence_rejected(self):
        inputs = self.candidate_inputs()
        inputs["values"]["POSTGRES_IMAGE"] = "example.invalid/postgres:latest"
        with self.assertRaisesRegex(ValueError, "immutable"):
            render.load(inputs, "candidate")
        inputs = self.candidate_inputs()
        inputs["promotion_evidence"]["exact_redhat_bundle_and_crds"] = None
        with self.assertRaisesRegex(ValueError, "evidence"):
            render.load(inputs, "candidate")

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "exists"):
                render.render(self.inputs, Path(d), "preview")


if __name__ == "__main__":
    unittest.main()
