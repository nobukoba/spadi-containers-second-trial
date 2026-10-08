# spadi-devel-fee guide

**Language: English | [日本語](spadi-devel-fee-guide.ja.md)**

This image provides FEE board control and mask configuration. This guide also covers source editing and rebuilding.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-runtime.sh
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── fee/
├── StrLRTDC/bin/set_tdcmask
├── StrHRTDC/bin/
└── src/
    ├── hul-common-lib/
    ├── amaneq-soft/
    ├── openFPGALoader/
    └── sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   └── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
├── bin/
├── lib/
├── lib64/
├── include/
├── share/
├── src/
├── build/
└── rawdata/
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates the local scripts, src, build, bin, lib, lib64, include, share, and rawdata directories. Source lists show the main editable projects.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download the image

Run these commands in a host terminal, outside the container. Choose either Apptainer or Docker for your environment.

### Apptainer

Install Apptainer on 64 bit Linux (x86_64) or a Windows WSL2 Linux distribution, then download this image's SIF from the Linux terminal.

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-fee.sif
```

### Docker

Start Docker on macOS or Linux, then download this image from the host terminal. Keep `--platform linux/amd64` on Apple Silicon as well.

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
```

`latest` can change. For repeatable environments, retain a timestamped SIF from [GitHub Releases](https://github.com/nobukoba/spadi-containers-second-trial/releases/tag/latest) or record the Docker image digest. See the [README Quick start](../README.md#quick-start) for startup and persistence settings.

## Start this image

Use **`spadi-devel-fee`** as the image name in the [README Quick start](../README.md#quick-start). Its SIF filename is `spadi-devel-fee.sif`; its Docker image is `ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest`. Run the remaining commands inside the container.

```bash
/opt/spadi/scripts/spadi-version.sh
```

## Prepare the workspace

Prepare a workspace including source and build directories. Existing configuration and source files are preserved. See the [README](../README.md) for common preparation and update procedures.

```bash
spadi-prepare-local.sh
```

## Edit and build software

Edit the source copied by spadi-prepare-local.sh under $SPADI_LOCAL/src. Build helpers compile that source and install the result into $SPADI_LOCAL. Stop DAQ or analysis processes using the local installation before rebuilding. You do not need to rebuild the container image.

| Source directory | Build helper |
|---|---|
| `$SPADI_LOCAL/src/hul-common-lib` | `hul-common-lib-build.sh` |
| `$SPADI_LOCAL/src/amaneq-soft` | `amaneq-build.sh` |
| `$SPADI_LOCAL/src/openFPGALoader` | `openfpgaloader-build.sh` |
| `$SPADI_LOCAL/src/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial` | `sitcp-utility-build.sh` |

```bash
hul-common-lib-build.sh
amaneq-build.sh
openfpgaloader-build.sh
sitcp-utility-build.sh
```

The list is in dependency order. Rebuild the changed component and its dependents as needed. Helpers default to NPROC=4; set a smaller value, for example NPROC=2 amaneq-build.sh. The SiTCP utility builds with make in its source tree; the other listed helpers use $SPADI_LOCAL/build/<project>.

## Try latest upstream source

Cloning and building are separate operations. Clone helpers refuse existing source directories. Preserve your current source and confirm the destination is absent before deliberately switching to latest upstream source.

```bash
amaneq-clone-latest.sh
amaneq-build.sh
```

Normal preparation copies the sources pinned in the image. Latest upstream source is outside that validated baseline.

## Check the rebuilt installation

```bash
spadi-env.sh
ls -l "$SPADI_LOCAL/StrLRTDC/bin/set_tdcmask"
```

Local bin and lib paths precede the image installation. The mask helper explicitly selects the image LR executable to avoid confusing LR and HR. To test a rebuilt LR command separately, use $SPADI_LOCAL/StrLRTDC/bin/set_tdcmask explicitly. The version reporter describes the image, not your local modifications; record source commits and build logs too.

For Dockerfile, CI, SIF creation, and publication changes, see the [container maintainer guide](container-maintainer-guide.md).

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
