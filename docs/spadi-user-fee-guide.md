# spadi-user-fee guide

**Language: English | [日本語](spadi-user-fee-guide.ja.md)**

This image provides FEE board control and mask configuration.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   └── fee/
├── StrLRTDC/bin/set_tdcmask
└── StrHRTDC/bin/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
└── rawdata/
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates scripts and rawdata. User images do not provide /opt/spadi/src.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download and start the image

Run the following commands in the host terminal. Choose either Apptainer or Docker.

### Apptainer (Linux / Windows WSL2)

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-fee.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-fee.sif
```

### Docker (macOS / Linux)

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-fee:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-fee:latest
```

Files under `workspace` persist on the host. Download or pull again when updating the image.

## Prepare the workspace

Copy the runtime scripts available in this image. Existing configuration and source files are preserved. See the [README](../README.md) for common preparation and update procedures.

```bash
spadi-prepare-local.sh
```

## Configure AMANEQ LR-TDC channel 102

Connect one 1-Gbps Str-LRTDC AMANEQ at `192.168.10.16`. Set DIP1 = 0 (default IP) and DIP3 = 1 (standalone). Use zero-based channel 102 on the lower DCRv2 mezzanine. Give the host Ethernet interface an address such as `192.168.10.1/24` and verify UDP 4660 access, including Linux routing in WSL2. Stop any acquisition program before changing the masks.

```bash
cd "$SPADI_LOCAL/scripts/fee/amaneq-lrtdc-1ch"
cat config.sh
get_version 192.168.10.16
./setup.sh
```

`cat config.sh` only displays the settings; edit them with a text editor such as `vim config.sh`. The helper calls the LR-specific set_tdcmask once for all four banks, then verifies them with read_register. The direct commands are:

```bash
/opt/spadi/StrLRTDC/bin/set_tdcmask \
  192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
read_register 192.168.10.16 10300000 4
```

| Bank | Channels | Mask |
|---|---|---|
| Main-U | 0–31 | `ffffffff` |
| Main-D | 32–63 | `ffffffff` |
| MZN-U | 64–95 | `ffffffff` |
| MZN-D | 96–127 | `ffffffbf` |

A set bit masks a channel. Channel 102 is MZN-D bit 6, the only cleared bit. Correct readback would be `0xffffffbf`. Change AMANEQ_IP in config.sh for another board address, and reapply the settings after a reset.

### MZN-D readback limitation

A board reporting FW ID `0x60c4`, version `2.10` (hexadecimal `2.A`), acknowledged the MZN-D write but returned `0xffffffff` on readback. The [official HDL](https://github.com/AMANEQ-official/strtdc-src/blob/71c188a74c93a7d06cb9e803d50360b05495e730/lrtdc-impl/strLrTdc.vhd#L685) incorrectly tests MZN-U in the MZN-D Read branch. This does not establish a failed write or independently verify the internal mask. The helper stops with `Mask verification failed at 10300000`. Do not treat that as success; confirm the setting with corrected firmware or independent hardware-data validation. NestDAQ acquisition from this hardware remains unverified.

## FEE tools and the acquisition image

get_version, read_register, and write_register control the board; openFPGALoader programs FPGAs; the SiTCP IP utilities configure networking. LR and HR mask commands share the same basename, so use the explicit LR path above.

```bash
openFPGALoader --version
command -v mpc-mpcx-ip-reader
command -v sitcp-sitcpxg-ip-reader
```

FPGA programming requires the correct bitstream and a JTAG connection. This recipe does not flash firmware or change the board IP automatically. FEE images do not contain NestDAQ or its Web Controller. For browser-controlled acquisition, use the [spadi-user-daq guide](spadi-user-daq-guide.md) or [spadi-user-full guide](spadi-user-full-guide.md). Mask configuration itself creates no acquired-data file.
