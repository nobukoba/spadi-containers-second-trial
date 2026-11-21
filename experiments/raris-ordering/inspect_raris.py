#!/usr/bin/env python3
"""Inspect FileSink v1/STF v1 and AMANEQ v1 heartbeat pairs in file order."""
import hashlib
import json
import struct
import sys
from pathlib import Path

STF = struct.Struct('<QIHHIIIIQQ')

def inspect(path):
    data = path.read_bytes()
    if data[:8] != b'FILESNK\0':
        raise ValueError(f'{path}: invalid FileSink magic')
    offset = struct.unpack_from('<H', data, 12)[0]
    frames, heartbeats, positions, types, ids = 0, [], [], set(), []
    while data[offset:offset + 8] == b'SUBTIME\0':
        magic, size, header_size, kind, frame_id, fem_type, fem_id, messages, sec, usec = STF.unpack_from(data, offset)
        if header_size != STF.size or size < header_size or (size - header_size) % 8 or offset + size > len(data):
            raise ValueError(f'{path}: invalid STF at {offset}')
        frames += 1
        ids.append(frame_id)
        types.add((fem_type, fem_id))
        pos = offset + header_size
        while pos < offset + size:
            if pos + 16 > offset + size:
                raise ValueError(f'{path}: truncated HBF header at {pos}')
            magic_hb, hb_size, hb_header_size, hb_type = struct.unpack_from('<QIHH', data, pos)
            if magic_hb != 0x0054414542545248 or hb_header_size != 16 or hb_size < 32 or hb_size % 8 or pos + hb_size > offset + size:
                raise ValueError(f'{path}: invalid HBF header at {pos}')
            first, second = struct.unpack_from('<QQ', data, pos + hb_size - 16)
            if first >> 58 != 0x1c or second >> 58 != 0x1e:
                raise ValueError(f'{path}: invalid heartbeat pair at {pos + hb_size - 16}')
            heartbeats.append(first & 0xffffff)
            positions.append(pos + hb_size - 16)
            pos += hb_size
        offset += size
    if data[offset:offset + 8] != b'FILETRL\0' or len(data) - offset != 304:
        raise ValueError(f'{path}: invalid FileSink trailer at {offset}')
    jumps = [(i, a, b) for i, (a, b) in enumerate(zip(heartbeats, heartbeats[1:])) if (b - a) % (1 << 24) != 1]
    return dict(file=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), stfs=frames,
                source_types=sorted(types), first_stf_ids=ids[:8], hbf_count=len(heartbeats),
                first_hbf_ids=heartbeats[:20], first_hbf_offsets=positions[:8],
                last_hbf_ids=heartbeats[-4:], non_unit_steps=jumps, trailer_offset=offset)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: inspect.py 00/run000020.dat 01/run000020.dat 02/run000020.dat')
    print(json.dumps([inspect(Path(p)) for p in sys.argv[1:]], indent=2))
