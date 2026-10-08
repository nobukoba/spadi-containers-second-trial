# spadi-user-fee guide

**Language: English | [日本語](spadi-user-fee-guide.ja.md)**

This image provides FEE board control, SiTCP network configuration, and FPGA programming.

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
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   └── fee/

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
/opt/spadi/bin/StrLRTDC/set_tdcmask \
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

user provides runtime software without source trees or local-development build helpers.
