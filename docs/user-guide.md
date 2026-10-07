# SPADI container user guide

**Language: English | [日本語](user-guide.ja.md)**

Use `spadi-user-*` to run installed software. AMANEQ acquisition below requires **spadi-user-daq** or **spadi-user-full** for both FEE control and NestDAQ. For source editing and builds, read the [developer guide](developer-guide.md).

## Start the container

### Apptainer (64 bit Linux / Windows WSL2)

Install Apptainer on 64 bit Linux (x86_64). In WSL2, run these commands in the Linux terminal. On the host:

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

### Docker (Linux hardware acquisition)

On a Linux host with Docker running:

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
mkdir -p "$PWD/workspace"
docker run --rm -it --platform linux/amd64 --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

Host networking exposes the board network and web controller. On Windows, use Apptainer in WSL2 above. For general Docker usage on macOS, see the [README](../README.md).

Both methods load SPADI settings and enter `/workspace` automatically. Files there persist in the host's `workspace` directory. Run `exit` to leave and repeat the host command to reopen. The following recipes need an image containing the new helpers.

## Prepare runtime recipes

Inside the container:

```bash
spadi-prepare-runtime.sh
```

This copies available runtime recipes to `$SPADI_LOCAL/scripts` without overwriting existing files, and creates `$SPADI_LOCAL/rawdata`. No source checkout, compilation, or `spadi-prepare-local.sh` is required.

When updating an existing workspace, stop its sessions, rename the old `scripts/nestdaq/common` directory, then run the helper again to obtain the new common scripts. Compare and reapply any local changes. Update an old FEE `amaneq-lrtdc-1ch/setup.sh` to the version accepting an optional IP argument too. Keep your edited recipe `config.sh` files.

## AMANEQ: channel 102 with NestDAQ

Use 1-Gbps Str-LRTDC firmware at **192.168.10.16**, DIP1 = 0 (default IP), DIP3 = 1 (standalone), and connect a signal to **zero-based channel 102** on the lower DCRv2 mezzanine. Set the host Ethernet interface to an address such as `192.168.10.1/24`. Allow UDP 4660 for RBCP control and TCP 24 for SiTCP data. In WSL2, verify Windows interface settings and Linux routing. Stop any other reader using this board.

```text
AMANEQ ch102 -> AmQStrTdcSampler-0 -> STFBuilder-0
            -> TimeFrameBuilder-0 -> FileSink-0 -> 00/run000001.dat
```

The recipe shares Valkey, parameter, topology, plugin, and tmux helpers with RARiS. Live acquisition uses a hardware sampler and STF builder and saves TF/STF records with FileSink.

### Prepare services in the terminal

Inside the container:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cat config.sh
ping -c 3 192.168.10.16
./run-start.sh
```

`run-start.sh` applies and verifies the FEE masks, prepares Valkey, parameters, topology, and four processes, and waits for all devices to become **Idle**. Acquisition has not started. Initialize, Run, Stop, and change run numbers in the browser.

### Initialize in the browser

Open **http://localhost:8081/daq-webctl.html** in the host browser (the Windows browser for WSL2).

1. In **State Summary**, check that `AmQStrTdcSampler`, `STFBuilder`, `TimeFrameBuilder`, and `FileSink` each have one instance, all **Idle**. **Show details** displays individual states.
2. Uncheck **Wait Device Ready** and **Wait Ready**. Follow the explicit transitions below and check states after each click.
3. Uncheck **Auto increment at RUN-Stop**. Otherwise each individual Stop click increments the run number.
4. Enter `1` in **RUN number → New value**, click **Send**, and check **Next : 1**. Choose an unused number.
5. Under **Select command target**, select **all** for both services and instances.
6. Click **Init Device and Connection**; wait until all four devices are **Device-Ready**.
7. Click **Init Task**; wait until all four are **Ready**.

After reloading the browser, uncheck these three options again.

### Start acquisition in the browser

Deselect service **all** and select only the service in the table. Keep instances set to **all**. Start downstream first: click **Run**, wait for that device to become **Running**, then proceed.

| Order | Service to select | Action |
|---|---|---|
| 1 | `FileSink` | **Run** → **Running** |
| 2 | `TimeFrameBuilder` | **Run** → **Running** |
| 3 | `STFBuilder` | **Run** → **Running** |
| 4 | `AmQStrTdcSampler` | **Run** → **Running** |

Sampler Run opens the TCP connection to AMANEQ and starts acquisition. Check all four are **Running** with **Error = 0**. Run 1 is saved to the host's `workspace/spadi/rawdata/amaneq-lrtdc-1ch/00/run000001.dat`.

### Stop and start the next run in the browser

Select one service at a time in upstream order: `AmQStrTdcSampler` → `STFBuilder` → `TimeFrameBuilder` → `FileSink`. Click **Stop**, wait for **Ready**, and allow about one second before stopping the next service. FileSink **Ready** means its trailer has been written and the file closed.

For the next run, enter an unused **New value** (for example `2`) and click **Send**. Select **all** services and instances, click **Reset Task**, wait for all **Device-Ready**, then **Reset Device**, and wait for all **Idle**. Repeat initialization and startup. Do not change the run number during acquisition.

When finished, Stop all devices in the browser, then run `./run-stop.sh` in the container terminal to exit processes and remove tmux. Use `./run-status.sh` and `./run-attach.sh` for diagnostics; **Ctrl-b d** detaches tmux. Closing the browser does not stop acquisition.

### Configuration and saved data

The FEE masks for Main-U, Main-D, MZN-U, MZN-D are `ffffffff ffffffff ffffffff ffffffbf`. Channel 102 is MZN-D bit 6; 1 masks and 0 unmasks. All other inputs 0–127 are masked. To apply masks separately while stopped, run `./fee-setup.sh`.

Edit NestDAQ `config.sh` for `AMANEQ_IP`, initial `RUN_NUMBER`, `RAWDATA_DIR`, and ports. Its IP is passed to the FEE helper; masks remain in `scripts/fee/amaneq-lrtdc-1ch/config.sh`. Choose later run numbers in the browser. Preparation refuses an existing initial output; FileSink uses `openmode=create` to prevent overwrites during browser Run too. If a duplicate number makes FileSink fail, do not continue acquisition; inspect its logs. Keep configuration unchanged while its session runs.

Defaults: Valkey `127.0.0.1:6380` (DB0 registry, DB1 metrics, DB2 parameters), web status `http://localhost:8081/daq-webctl.html`, and data ports 5599–5601, and optional DQM PUB port 5602. FileSink needs this DQM channel even without a monitor subscriber. These differ from RARiS defaults. This recipe owns its Valkey DBs; do not share them with another running setup. Valkey remains after stopping for reuse.

Stop acquisition in the browser as described above. Use `run-stop.sh` for final cleanup or when the browser is unavailable. It stops the source first, allows downstream processing, waits for FileSink's PostRun/trailer/close, then exits devices and tmux. On errors/timeouts tmux is retained for inspection. The pinned upstream may discard a final incomplete frame and queued FileSink PostRun input; this procedure does not guarantee a lossless run boundary. Review logs and delimiter flags. Heartbeat delimiters appear without hits, so file growth alone does not establish channel 102 activity. The output contains FileSink header/trailer and TF/STF records, rather than the previous `strdaq` stream.

## RARiS AC-LGAD replay

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d detaches.
```

This launches three STFBFilePlayer processes and one TimeFrameBuilder. Open `http://localhost:8080/daq-webctl.html`, select the services, set a run number, then use **Init Device and Connection → Init Task → Run**, checking states. The default replay topology has no FileSink: connect the desired consumer to TFB output `tcp://127.0.0.1:5501`. Stop/reset via web control before `./run-stop.sh` closes the session. Normal changes belong in its `config.sh`.

## Directory structure

```text
/opt/spadi/                           # image-provided; read-only in SIF
├── bin/                              # devices and FEE register tools
├── lib/                              # libraries, plugins, RedisTimeSeries
└── scripts/
    ├── spadi-prepare-runtime.sh
    ├── fee/amaneq-lrtdc-1ch/          # config.sh and setup.sh: masks
    └── nestdaq/
        ├── common/                   # shared service, parameter, topology, control helpers
        ├── amaneq-lrtdc-1ch/
        │   ├── config.sh
        │   ├── fee-setup.sh
        │   ├── run-start.sh
        │   ├── run-stop.sh
        │   ├── run-status.sh
        │   └── run-attach.sh
        └── raris-ac-lgad/             # replay helpers and rawdata-download.sh

/workspace/spadi/                     # SPADI_LOCAL; host workspace/spadi
├── scripts/                          # editable copies of runtime recipes
│   ├── fee/amaneq-lrtdc-1ch/
│   └── nestdaq/{common,amaneq-lrtdc-1ch,raris-ac-lgad}/
└── rawdata/
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

Repository recipes live under `scripts/fee` and `scripts/nestdaq`; the prepare helper is in `scripts/runtime/spadi-prepare-runtime.sh`. See the [official hardware guide](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/firmware/strlrtdc/strlrtdc/) and [pinned revisions](../versions/versions.env).
