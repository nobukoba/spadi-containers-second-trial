# AMANEQ LR-TDC: channel 102 only

Use `spadi-user-fee`, `spadi-user-daq`, or `spadi-user-full`. This recipe uses the installed FEE tools; it does not require source code or development helpers.

This is a short standalone readout test with the 1-Gbps Str-LRTDC firmware, board IP `192.168.10.16`, and zero-based channel 102. Connect that input on the lower DCRv2 mezzanine. Select standalone operation with DIP3 = 1 and the default IP with DIP1 = 0. The host needs an address such as `192.168.10.1/24` on the board's Ethernet network. Allow UDP 4660 (RBCP) and TCP 24 (SiTCP). In Windows WSL2, confirm that the Linux environment can reach the board through the Windows network interface.

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

`config.sh` contains the board IP and four channel masks. `setup.sh` writes and reads back each mask, stopping if it detects a communication error or a mismatched value. Stop acquisition before changing masks, and apply them again after a board reset.

| Bank | Channels | Register | Mask |
|---|---|---|---|
| Main-U | 0–31 | `0x10000000` | `0xffffffff` |
| Main-D | 32–63 | `0x10100000` | `0xffffffff` |
| MZN-U | 64–95 | `0x10200000` | `0xffffffff` |
| MZN-D | 96–127 | `0x10300000` | `0xffffffbf` |

A set bit masks a channel. Channel 102 is MZN-D bit `102 - 96 = 6`, so `0xffffffff & ~(1 << 6) = 0xffffffbf`. All other TDC inputs are masked. Heartbeat delimiters still appear, and scaler counting is unaffected. This recipe targets the current 128-input firmware; it does not write the deprecated extension-input register.

After successful verification, run the installed standalone streaming reader:

```bash
mkdir -p "$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch/data"
cd "$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch"
# Use a new run number each time; strdaq overwrites an existing run file.
test ! -e data/run1.dat && strdaq 192.168.10.16 1
# Stop with Ctrl-C, wait for "End of DAQ", then inspect the saved file.
ls -lh data/run1.dat
```

Standalone firmware starts sending on TCP connection; `set_hbfstate` is not needed in this mode. The pinned `strdaq` buffers data in memory and writes `data/run1.dat` when acquisition stops. Use it for a short test; sustained acquisition should use NestDAQ. File size alone does not establish that channel 102 produced hits, because delimiters are present even without input pulses. This is a raw SiTCP stream, not a NestDAQ STF/TF file.

For Docker, use `--network host` on a Linux host for this hardware test, in addition to the workspace and UID/GID options in the main README.

References: [official Str-LRTDC guide](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/firmware/strlrtdc/strlrtdc/), [pinned channel register map](https://github.com/spadi-alliance/amaneq-soft/blob/86fef97ccc4e6488739e2d8b549a1c5bddd3542e/StrLRTDC/RegisterMap.hh), and [pinned standalone reader](https://github.com/spadi-alliance/hul-common-lib/blob/65476509aa401aad10148ec7c2d2a50ba7d2db3e/HulCore/DaqFuncs.cc).
