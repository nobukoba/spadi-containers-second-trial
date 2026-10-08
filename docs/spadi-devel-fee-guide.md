# spadi-devel-fee guide

**Language: English | [日本語](spadi-devel-fee-guide.ja.md)**

This image provides FEE board control, SiTCP network configuration, and FPGA programming. This guide also covers source editing and rebuilding.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
│   ├── get_version / read_register / write_register
│   ├── openFPGALoader
│   ├── sitcp-sitcpxg-ip-{reader,writer}
│   ├── mpc-mpcx-ip-{reader,writer,command}
│   ├── StrLRTDC/set_tdcmask
│   └── StrHRTDC/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   ├── spadi-env.sh
│   ├── *-build.sh / *-clone-latest.sh
│   └── fee/
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

## Download and start the image

Run the following commands in the host terminal. Choose either Apptainer or Docker.

### Apptainer (Linux / Windows WSL2)

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-devel-fee.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-devel-fee.sif
```

### Docker (macOS / Linux)

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-devel-fee:latest
```

Files under `workspace` persist on the host. Download or pull again when updating the image.

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
ls -l "$SPADI_LOCAL/bin/StrLRTDC/set_tdcmask"
```

Local bin and lib paths precede the image installation. To test a rebuilt LR command separately, use $SPADI_LOCAL/bin/StrLRTDC/set_tdcmask explicitly. The version reporter describes the image, not your local modifications; record source commits and build logs too.

For Dockerfile, CI, SIF creation, and publication changes, see the [container maintainer guide](container-maintainer-guide.md).

## Configure SiTCP / SiTCP-XG networking

Run these commands inside the container. They contact the board at its current IP using RBCP (UDP 4660). Configure the host Ethernet interface and route to the board first, and stop DAQ before changing settings. Ordinary Apptainer startup shares the host network. On Linux, add `--network host` to the Docker startup command to use the same host routes. See the [README](../README.md) for platform-specific networking conditions.

### Read the current settings

```bash
sitcp-sitcpxg-ip-reader 192.168.10.16
mpc-mpcx-ip-reader 192.168.10.16
```

The first command displays SiTCP / SiTCP-XG MAC and IP information; the second reads MPC / MPCX EEPROM settings. Select the command matching the board implementation.

### Change the EEPROM IP

This example contacts the current address `192.168.10.16` and stores `192.168.10.17`.

```bash
sitcp-sitcpxg-ip-writer 192.168.10.16 192.168.10.17
```

The default operation updates EEPROM. Changing the live IP and selecting the EEPROM IP after reset depend on the board implementation and DIP settings. Follow the board's reset and verification procedure rather than assuming the new address becomes active immediately.

### Write an MPC / MPCX license file and change the EEPROM IP

Place the file obtained for this board in the host `workspace` directory. Here `board.mpcx` is an example filename supplied by the user.

```bash
mpc-mpcx-ip-writer 192.168.10.16 /workspace/board.mpcx \
  --set-eeprom-ip 192.168.10.17
mpc-mpcx-ip-reader 192.168.10.16
```

License files are not included in the image. This command connects to the current IP `192.168.10.16`, writes the license, and stores `192.168.10.17` in EEPROM. It does not change the live IP, so the immediate readback uses the original address. For an MPC file, substitute its actual path, such as `/workspace/board.mpc`. IP selection after reset follows the board's DIP settings and implementation. For additional options, MPC files, and live-IP changes, use `mpc-mpcx-ip-command --help` and the [README at the included utility revision](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/blob/4bc47b6f5ac791acfbd88c73dd987b7625074273/README.md).

## Program an FPGA with openFPGALoader

Prepare a bitstream matching the target FPGA and a supported JTAG cable. These examples use a Digilent HS3. Select the actual cable or board name from the supported lists for other hardware.

### Make the USB cable accessible

Connect the cable and configure USB access permissions on the Linux host. Ordinary Apptainer startup exposes host `/dev`. Docker requires explicitly passing the USB device: identify Bus / Device numbers with host `lsusb`, then add, for example, `--device=/dev/bus/usb/001/002` to the Docker startup command. Numbers can change after reconnection. See the [official installation instructions](https://trabucayre.github.io/openFPGALoader/guide/install.html) for host permissions. WSL2 requires attaching USB to Linux first. The macOS Docker startup example alone does not expose a host USB JTAG cable.

### Identify the cable and FPGA

```bash
openFPGALoader --version
openFPGALoader --list-cables
openFPGALoader --list-boards
openFPGALoader -c digilent_hs3 --detect
```

### Load a bitstream into SRAM

Place the target board's file at host `workspace/firmware.bit`, then run inside the container:

```bash
openFPGALoader -c digilent_hs3 /workspace/firmware.bit
```

SRAM loading is volatile and is lost at power-off. Flash programming is a separate operation using `-f`. Check the supported board name (`-b`), FPGA part, and flash configuration before using it; required arguments vary by board. Do not unconditionally append `-f` to the SRAM example. See the [official basic operations](https://trabucayre.github.io/openFPGALoader/guide/first-steps.html) for details.

## Board control with hul-common-lib and amaneq-soft

### hul-common-lib: firmware information and register access

[hul-common-lib](https://github.com/spadi-alliance/hul-common-lib) provides the common RBCP board-control library and utilities. Use `get_version` to inspect firmware information, `read_register` to read registers, and `write_register` to write them.

Start by checking the board IP and network route, then read its firmware information inside the container. Replace this example IP with your board's address.

```bash
get_version 192.168.10.16
```

For register operations, consult the target firmware's register map for addresses, sizes, and values, and verify writes by reading back. See the [upstream README](https://github.com/spadi-alliance/hul-common-lib#readme) for command arguments and library usage.

### amaneq-soft: firmware-specific configuration tools

[amaneq-soft](https://github.com/spadi-alliance/amaneq-soft) provides AMANEQ control and configuration tools for its firmware variants. Included LR-TDC tools are under `$SPADI_ROOT/bin/StrLRTDC/`; HR-TDC tools are under `$SPADI_ROOT/bin/StrHRTDC/`.

For example, `set_tdcmask` configures TDC channel masks. LR and HR commands share this basename, so select the full path matching the firmware. The LR command is `$SPADI_ROOT/bin/StrLRTDC/set_tdcmask` and accepts the IP and four bank-mask values. Consult the [upstream README and source](https://github.com/spadi-alliance/amaneq-soft#readme) for settings and procedures. Stop DAQ before changing configuration.

For acquisition using a specific channel, follow the [DAQ guide](spadi-user-daq-guide.md) or [FULL guide](spadi-user-full-guide.md).

## Proceed to data acquisition

FEE images do not include NestDAQ or its Web Controller. For browser-controlled acquisition, follow the [spadi-user-daq guide](spadi-user-daq-guide.md) or [spadi-user-full guide](spadi-user-full-guide.md). Board configuration alone does not create acquired-data files.

## Appendix: Included software

These are the main included software components. Pins are defined in [versions.env](../versions/versions.env). Inspect `/opt/spadi/scripts/spadi-version.sh` and `/opt/spadi/versions/versions.env` inside your image for its actual build metadata. Locally rebuilt software may differ from this baseline.

| Software | Purpose | Pinned version / revision |
|---|---|---|
| [hul-common-lib](https://github.com/spadi-alliance/hul-common-lib) | RBCP board control: get_version, read_register, write_register | [`65476509aa40`](https://github.com/spadi-alliance/hul-common-lib/tree/65476509aa401aad10148ec7c2d2a50ba7d2db3e) |
| [amaneq-soft](https://github.com/spadi-alliance/amaneq-soft) | AMANEQ LR/HR utilities in bin/StrLRTDC and bin/StrHRTDC | [`86fef97ccc4e`](https://github.com/spadi-alliance/amaneq-soft/tree/86fef97ccc4e6488739e2d8b549a1c5bddd3542e) |
| [openFPGALoader](https://github.com/trabucayre/openFPGALoader) | FPGA SRAM/flash programming over supported interfaces | [`24e46d13bb8f`](https://github.com/trabucayre/openFPGALoader/tree/24e46d13bb8f2bc9371e9ca8443ece2fafc4b20d) |
| [SiTCP IP / MPC utilities](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial) | SiTCP/SiTCP-XG IP and MPC/MPCX license configuration | [`4bc47b6f5ac7`](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/tree/4bc47b6f5ac791acfbd88c73dd987b7625074273) |

The OS is AlmaLinux 9. Network tools (iproute, iputils, net-tools, bind-utils, traceroute, tcpdump, nmap-ncat), curl / wget, and vim / emacs are also included. OS packages use AlmaLinux package versions rather than the source pins above.

devel adds source trees, development headers, compilers, Make / CMake, Git, and component build/clone helpers. Edit/build under `$SPADI_LOCAL/src` and `$SPADI_LOCAL/build`, and install into `$SPADI_LOCAL`.
