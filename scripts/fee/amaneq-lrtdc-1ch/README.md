# AMANEQ LR-TDC: channel 102 only

Use `spadi-user-fee`, `spadi-user-daq`, or `spadi-user-full`. This recipe uses the installed FEE tools; it does not require source code or development helpers.

This is the FEE mask-configuration step for standalone NestDAQ acquisition with the 1-Gbps Str-LRTDC firmware, board IP `192.168.10.16`, and zero-based channel 102. Connect that input on the lower DCRv2 mezzanine. Select standalone operation with DIP3 = 1 and the default IP with DIP1 = 0. The host needs an address such as `192.168.10.1/24` on the board's Ethernet network. Allow UDP 4660 (RBCP) and TCP 24 (SiTCP). In Windows WSL2, confirm that the Linux environment can reach the board through the Windows network interface.

Inside the container, copy the recipe once into the persistent workspace. User images do not provide `spadi-prepare-local.sh`:

```bash
mkdir -p "$SPADI_LOCAL/scripts/fee"
if [ ! -e "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch" ]; then
  cp -a /opt/spadi/scripts/fee/amaneq-lrtdc-1ch "$SPADI_LOCAL/scripts/fee/"
fi
cd "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch"
ping -c 3 192.168.10.16
bash setup.sh
```

`config.sh` contains the board IP and four channel masks. `setup.sh` uses `/opt/spadi/StrLRTDC/bin/set_tdcmask` to write all four masks, then reads back each mask, stopping if it detects a communication error or a mismatched value. Stop acquisition before changing masks, and apply them again after a board reset.

| Bank | Channels | Register | Mask |
|---|---|---|---|
| Main-U | 0–31 | `0x10000000` | `0xffffffff` |
| Main-D | 32–63 | `0x10100000` | `0xffffffff` |
| MZN-U | 64–95 | `0x10200000` | `0xffffffff` |
| MZN-D | 96–127 | `0x10300000` | `0xffffffbf` |

A set bit masks a channel. Channel 102 is MZN-D bit `102 - 96 = 6`, so `0xffffffff & ~(1 << 6) = 0xffffffbf`. All other TDC inputs are masked. Heartbeat delimiters still appear, and scaler counting is unaffected. This recipe targets the current 128-input firmware; it does not write the deprecated extension-input register.

After successful verification, use the NestDAQ recipe in `scripts/nestdaq/amaneq-lrtdc-1ch` for acquisition. It requires `spadi-user-daq` or `spadi-user-full` and connects AmQStrTdcSampler -> STFBuilder -> TimeFrameBuilder -> FileSink. The FEE-only image performs register control but does not contain NestDAQ.

See the [FEE guide](../../../docs/spadi-user-fee-guide.md) / [日本語](../../../docs/spadi-user-fee-guide.ja.md) for startup, run helpers, storage, and directory structure. `setup.sh [AMANEQ-IP]` accepts an optional IP argument; the NestDAQ wrapper passes its config IP so control and acquisition use the same board.

References: [official Str-LRTDC guide](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/firmware/strlrtdc/strlrtdc/), [pinned channel map](https://github.com/spadi-alliance/amaneq-soft/blob/86fef97ccc4e6488739e2d8b549a1c5bddd3542e/StrLRTDC/RegisterMap.hh).
