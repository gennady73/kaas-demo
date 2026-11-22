#!/usr/bin/env python3
"""Prepare exact boundary records for review; never connects to Kafka."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def value_chunks(seed, topic, sequence, size):
    """ASCII SHA-256 hex blocks; deterministic and byte-exact, no compression."""
    left, block = size, 0
    while left:
        body = hashlib.sha256(f'{seed}:{topic}:{sequence}:{block}'.encode('ascii')).hexdigest().encode('ascii')
        chunk = body[:min(left, len(body))]
        yield chunk
        left -= len(chunk)
        block += 1


def prepare(profile, run_id, seed):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', run_id):
        raise ValueError('run ID must be 1..64 ASCII alphanumeric, dash or underscore characters')
    if type(seed) is not int or seed < 1:
        raise ValueError('positive integer seed required')
    confirmed, proposed = profile['user_confirmed'], profile['proposed']
    topics = proposed['topics']
    if len(topics) != confirmed['topic_count'] or len(topics) != 4:
        raise ValueError('exactly four topics required')
    if len({t['name'] for t in topics}) != 4:
        raise ValueError('duplicate topics')
    records = []
    for topic in topics:
        if not re.fullmatch(r'[a-zA-Z0-9._-]{1,249}', topic['name']) or topic['name'] in ('.', '..'):
            raise ValueError('invalid topic')
        for seq, size in enumerate(topic['payload_sizes_bytes']):
            if type(size) is not int or not 1 <= size <= confirmed['maximum_value_payload_bytes']:
                raise ValueError('payload outside selected bounds')
            digest = hashlib.sha256()
            for chunk in value_chunks(seed, topic['name'], seq, size):
                digest.update(chunk)
            records.append({'id': f'{run_id}:{topic["name"]}:{seq}', 'topic': topic['name'],
                            'sequence': seq, 'value_bytes': size, 'sha256': digest.hexdigest(),
                            'consumer_group': f'{topic["consumer_group_prefix"]}-{run_id}'})
    total = sum(r['value_bytes'] for r in records)
    if len(records) != 16 or total != proposed['total_original_value_payload_bytes']:
        raise ValueError('record count or byte budget mismatch')
    return {'case_contract_version': '0.1', 'status': 'offline_expected_cases_not_execution_evidence',
            'algorithm': 'sha256-hex-ascii-v1', 'run_id': run_id, 'seed': seed,
            'client_wall_clock_limit_seconds': confirmed['maximum_test_runtime_seconds'],
            'total_original_value_bytes': total, 'records': records,
            'execution_ready': False,
            'runtime_mapping_needed': 'Map exact cases to selected xk6 build; verify deadlines, retries, acks, security and durable evidence. This is not a C2 planner input.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        cases = prepare(json.loads(args.profile.read_text()), args.run_id, args.seed)
        with args.output.open('x') as output:
            output.write(json.dumps(cases, indent=2) + '\n')
    except (ValueError, KeyError, OSError) as err:
        parser.exit(2, f'case preparation rejected: {err}\n')
    print(json.dumps({'output': str(args.output), 'records': len(cases['records']),
                      'original_value_bytes': cases['total_original_value_bytes'], 'execution_ready': False}))


if __name__ == '__main__':
    main()
