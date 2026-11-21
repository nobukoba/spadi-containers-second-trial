import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

inspect_raris = load('inspect_raris')
wrap_stf = load('wrap_stf')

class InspectionTest(unittest.TestCase):
    def sample(self, bad=False):
        fs = bytearray(304); fs[:8] = b'FILESNK\0'; struct.pack_into('<H',fs,12,304)
        trailer = bytearray(304); trailer[:8] = b'FILETRL\0'; struct.pack_into('<IH',trailer,8,304,304)
        words=struct.pack('<QQ', (28<<58)|42, (29 if bad else 30)<<58)
        hb=struct.pack('<QIHH',0x0054414542545248,32,16,0)+words
        stf=struct.pack('<QIHHIIIIQQ',0x00454d4954425553,48+len(hb),48,0,42,5,100,1,0,0)+hb
        return bytes(fs)+stf+bytes(trailer)
    def test_real_format_and_wrapper_preserves_stf(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'in.dat'; dst=Path(d)/'out.dat'; src.write_bytes(self.sample())
            result=inspect_raris.inspect(src); self.assertEqual(result['first_hbf_ids'],[42]);self.assertEqual(result['non_unit_steps'],[])
            self.assertEqual(wrap_stf.wrap(src,dst),1)
            output=dst.read_bytes(); self.assertEqual(output[328:-304],src.read_bytes()[304:-304])
    def test_invalid_pair_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.dat';p.write_bytes(self.sample(True))
            with self.assertRaises(ValueError):inspect_raris.inspect(p)

if __name__=='__main__':unittest.main()
