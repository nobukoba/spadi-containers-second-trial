#!/usr/bin/env python3
"""Experimental one-source STF-to-TF wrapper for ARTEMIS compatibility tests.

This preserves each STF and its HBF bytes. It does not synchronize sources or
simulate a NestDAQ replay and is not the Issue #7 offline implementation.
"""
import argparse
import struct
from pathlib import Path

TF = struct.Struct('<QIHHII')
TF_MAGIC = 0x004d5246454d4954

def wrap(source: Path, destination: Path):
    with source.open('rb') as src, destination.open('xb') as dst:
        header = src.read(304)
        if len(header) != 304 or header[:8] != b'FILESNK\0' or struct.unpack_from('<H', header, 12)[0] != 304:
            raise ValueError('expected a 304-byte FileSink header')
        dst.write(header)
        frames = 0
        while True:
            head = src.read(48)
            if head[:8] == b'FILETRL\0':
                rest = src.read()
                trailer = head + rest
                if len(trailer) != 304 or struct.unpack_from('<IH', trailer, 8) != (304, 304):
                    raise ValueError('invalid FileSink trailer')
                dst.write(trailer)
                return frames
            if len(head) != 48 or head[:8] != b'SUBTIME\0':
                raise ValueError('missing or truncated STF header')
            length, hlen = struct.unpack_from('<IH', head, 8)
            if hlen != 48 or length < hlen or length > 16 * 1024 * 1024:
                raise ValueError('invalid STF length')
            body = src.read(length - hlen)
            if len(body) != length - hlen:
                raise ValueError('truncated STF body')
            frame_id = struct.unpack_from('<I', head, 16)[0]
            dst.write(TF.pack(TF_MAGIC, TF.size + length, TF.size, 0, frame_id, 1))
            dst.write(head)
            dst.write(body)
            frames += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(f'wrapped {wrap(args.source, args.destination)} STF records')
