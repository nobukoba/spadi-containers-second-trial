#!/usr/bin/env python3
"""Compare a length/more-prefixed multipart TF capture with RARiS STF files."""
import argparse
import json
import struct
from pathlib import Path

STF = struct.Struct('<QIHHIIIIQQ')

def ids(data):
    at, result = 0, []
    while at < len(data):
        if at + 16 > len(data): raise ValueError('truncated HBF header')
        magic, length, hlen, _ = struct.unpack_from('<QIHH', data, at)
        if magic != 0x0054414542545248 or hlen != 16 or length < 32 or length % 8 or at + length > len(data): raise ValueError('invalid HBF')
        a, b = struct.unpack_from('<QQ', data, at + length - 16)
        if a >> 58 != 28 or b >> 58 != 30: raise ValueError('invalid heartbeat pair')
        result.append(a & 0xffffff); at += length
    return result

def source(path):
    data = path.read_bytes(); at = struct.unpack_from('<H', data, 12)[0]; result = {}
    while data[at:at+8] == b'SUBTIME\0':
        h = STF.unpack_from(data, at); end = at + h[1]
        if h[2] != 48 or end > len(data): raise ValueError('invalid STF')
        key = (h[4], h[6])
        if key in result: raise ValueError('duplicate STF key')
        result[key] = ids(data[at+48:end]); at = end
    if data[at:at+8] != b'FILETRL\0': raise ValueError('missing trailer')
    return result

def compare(paths, capture):
    expected = {}
    for path in paths:
        for k, v in source(path).items():
            if k in expected: raise ValueError('duplicate source key')
            expected[k] = v
    data = capture.read_bytes(); pos = 0; group = []; matched = 0; tf_count = 0; examples = []
    while pos < len(data):
        if pos + 8 > len(data): raise ValueError('truncated capture header')
        size, more = struct.unpack_from('<II', data, pos); pos += 8
        if more not in (0, 1) or pos + size > len(data): raise ValueError('invalid capture part')
        group.append(data[pos:pos+size]); pos += size
        if more: continue
        if len(group[0]) != 24 or group[0][:8] != b'TIMEFRM\0': raise ValueError('invalid TF header')
        tid, count = struct.unpack_from('<II', group[0], 16); tf_count += 1
        seen = []; current = None
        for part in group[1:]:
            if part[:8] == b'SUBTIME\0':
                if current is not None: seen.append((fem, current))
                if len(part) != 48: raise ValueError('invalid STF part')
                h = STF.unpack(part); fem = h[6]; current = []
                if h[4] != tid: raise ValueError('TF/STF id mismatch')
            else:
                if current is None: raise ValueError('HBF before STF')
                hbf = ids(part)
                if len(hbf) != 1: raise ValueError('not exactly one HBF per part')
                current.extend(hbf)
        if current is not None: seen.append((fem, current))
        if len(seen) != count or len({f for f, _ in seen}) != count: raise ValueError('source count mismatch')
        for fem, got in seen:
            if expected.get((tid, fem)) != got: raise ValueError(f'HBF mismatch for TF {tid}, FEM {fem}')
            matched += 1
        if len(examples) < 3: examples.append({'tf_id':tid, 'sources':seen})
        group = []
    if group: raise ValueError('truncated multipart TF')
    return {'tf_count':tf_count, 'matched_stfs':matched, 'examples':examples}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path); parser.add_argument('files', type=Path, nargs=3)
    a = parser.parse_args(); print(json.dumps(compare(a.files,a.capture), indent=2))
