"""Byte-boundary, false-magic, truncation and blind recovery regression tests."""
import io
import struct
import unittest
import recovery as r

REF=dict(id_step=4,fem_type=5,fem_id=123,messages=4,type=0,
         volume_threshold=240,maximum_frame_bytes=4096)

def records():
    return [r.HEADER.pack(r.STF_MAGIC,80,48,0,100+4*i,5,123,4,1000,i)+bytes([i])*32 for i in range(64)]

class RecoveryTests(unittest.TestCase):
    def test_magic_split_across_tiny_reads(self):
        data=b''.join(records())
        for size in (1,7,31,512,65536):
            pred=r.classify(data,REF,size,True)
            self.assertEqual(pred['recovered_sha256'],[r.sha(c) for c in records()])
            self.assertEqual(pred['alarms'],[])

    def test_false_magic_noise_cannot_become_a_record(self):
        source=records();noise=b'abcd'+r.MAGIC+b'\xff'*64
        data=b''.join(source[:20])+noise+b''.join(source[20:])
        for size in (7,512,65536):
            pred=r.classify(data,REF,size,True)
            self.assertEqual(pred['recovered_sha256'],[r.sha(c) for c in source])
            self.assertEqual(pred['alarms'][0]['kind'],'framing_corruption')
            self.assertEqual(pred['alarms'][0]['start'],20*80)
            self.assertEqual(pred['alarms'][0]['end'],20*80+len(noise))

    def test_corrupt_length_has_bounded_recovery(self):
        data,label=r.mutate(records(),'header_length',20)
        strict=r.classify(data,REF,512,False)
        recovered=r.classify(data,REF,512,True)
        self.assertEqual(strict['recovered_frames'],20)
        self.assertEqual(r.score(recovered,label)['intact_recovered'],63)
        self.assertEqual(r.score(recovered,label)['extra_recovered_records'],0)
        self.assertEqual(r.score(recovered,label)['detected_events'],1)

    def test_sequence_mutations_are_localized(self):
        for pattern in ('missing','duplicate','reorder','mixed'):
            with self.subTest(pattern=pattern):
                data,label=r.mutate(records(),pattern,20)
                pred=r.classify(data,REF,512,True)
                self.assertEqual(r.score(pred,label)['detected_events'],len(label['interventions']))
                self.assertEqual(r.score(pred,label)['intact_recovered'],len(label['intact_sha256']))

    def test_incomplete_last_record_never_emitted(self):
        data=b''.join(records())[:-20]
        pred=r.classify(data,REF,7,True)
        self.assertEqual(pred['recovered_frames'],63)
        self.assertEqual(pred['alarms'][-1]['kind'],'framing_corruption')

    def test_parser_receives_no_labels(self):
        data,_=r.mutate(records(),'garbage',20)
        flags=[]
        result=list(r.stream_frames(io.BytesIO(data),REF,31,True,flags))
        self.assertEqual(len(result),64)
        self.assertEqual({type(record) for _,record in result},{bytes})

if __name__=='__main__':unittest.main()
