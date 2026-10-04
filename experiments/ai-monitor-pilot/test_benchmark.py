"""Protocol separation, injection semantics, scoring and API safety regressions."""
import copy
import json
import os
import struct
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
import benchmark as b


def chunks():
    return [b.HEADER.pack(b.STF_MAGIC, 56, 48, 0, 100+4*i, 5, 123, 4, 1000, i)+struct.pack('<Q',i) for i in range(32)]


REF=dict(id_step=4,fem_type=5,fem_id=123,messages=4,type=0,volume_threshold=168)


class BenchmarkTests(unittest.TestCase):
    def test_injection_and_location(self):
        for kind in b.KINDS:
            for variant in range(4):
                with self.subTest(kind=kind,variant=variant):
                    observed,label=b.inject(chunks(),kind,12,variant)
                    blind=b.make_input(observed,REF)
                    pred=b.rules(blind)
                    self.assertTrue(any(a['kind']==kind and set(a['indexes']) & set(label['observed_target_indexes']) for a in pred['alarms']))
                    self.assertEqual({a['kind'] for a in pred['alarms']},{kind})
                    self.assertEqual(b.rules(blind,True)['alarms'],[])
                    self.assertNotIn('original',json.dumps(blind))
                    self.assertNotIn('intervention',json.dumps(blind))
                    self.assertEqual(set(blind),{'reference','records'})

    def test_untouched_and_natural_candidate(self):
        self.assertEqual(b.rules(b.make_input(chunks(),REF))['alarms'],[])
        c=chunks();c.pop(10)
        self.assertEqual(b.rules(b.make_input(c,REF))['alarms'][0]['kind'],'missing')

    def test_wrong_location_no_detection_credit(self):
        labels={'x':dict(kind='missing',intervention=dict(observed_target_indexes=[12]))}
        inputs={'x':dict(phase='evaluation')}
        bad={'x':dict(alarms=[dict(kind='missing',indexes=[1],evidence='wrong')],elapsed_seconds=1)}
        metric=b.score(bad,labels,inputs)
        self.assertEqual(metric['by_kind']['missing']['detected'],0)
        bad['x']['alarms'][0].update(kind='reorder',indexes=[12])
        metric=b.score(bad,labels,inputs)
        self.assertEqual(metric['by_kind']['missing']['detected'],1)
        self.assertEqual(metric['by_kind']['missing']['correct_type'],0)

    def test_missing_api_cases_are_not_zero_rate(self):
        m=b.score({}, {'x':dict(kind='missing')}, {'x':dict(phase='evaluation')})
        self.assertIsNone(m['by_kind']['missing']['detection_rate'])

    def test_api_payload_allowlist_and_safety(self):
        protocol=dict(model=b.MODEL,prompt=b.PROMPT,max_output_tokens=1000,response_schema=b.ALARM_SCHEMA,
                      api=dict(endpoint='https://api.openai.com/v1/responses',timeout_seconds=1))
        blind=b.make_input(chunks(),REF)
        body=b.request_body(blind,protocol)
        self.assertEqual(json.loads(body['input']),blind)
        self.assertFalse(body['store'])
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-secret-never-log'}):
            with patch('urllib.request.urlopen',side_effect=urllib.error.HTTPError('url',401,'secret-in-body',{},None)):
                outcome=b.api_prediction(blind,protocol)
            self.assertEqual(outcome['http_status'],401)
            self.assertNotIn('secret',json.dumps(outcome))
            self.assertNotIn('test-secret-never-log',json.dumps(body))

    def test_freeze_rejects_artifact_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            (p/'protocol.json').write_text('{}')
            b.write(p/'freeze.json',dict(files={'protocol.json':b.hashlib.sha256(b'{}').hexdigest()},
                implementation_sha256=b.hashlib.sha256(Path(b.__file__).read_bytes()).hexdigest()))
            b.verify(p)
            (p/'protocol.json').write_text('{"modified":true}')
            with self.assertRaises(ValueError): b.verify(p)

    def test_header_input_is_actually_mutated(self):
        original=chunks()
        observed,label=b.inject(original,'header_corruption',12,0)
        self.assertNotEqual(original[12][:48],observed[12][:48])
        self.assertEqual(original[12][48:],observed[12][48:])
        self.assertEqual(b.make_input(observed,REF)['records'][12]['magic'],'0x00454d4954425500')

    def test_usage_cost_with_caching(self):
        self.assertAlmostEqual(b.cost(dict(input_tokens=1000,output_tokens=100,input_tokens_details=dict(cached_tokens=500))),.00041)


if __name__=='__main__': unittest.main()
