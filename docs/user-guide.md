# SPADI container user guide

**Language: English | [日本語](user-guide.ja.md)**

Use `spadi-user-*` to run installed software. AMANEQ acquisition below requires **spadi-user-daq** or **spadi-user-full** for both FEE control and NestDAQ. For source editing and builds, read the [developer guide](developer-guide.md).

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
        │   ├── run-attach.sh
        │   └── run-cleanup.sh
        └── raris-ac-lgad/             # replay helpers and rawdata-download.sh

/workspace/spadi/                     # SPADI_LOCAL; host workspace/spadi
├── scripts/                          # editable copies of runtime recipes
│   ├── fee/amaneq-lrtdc-1ch/
│   └── nestdaq/{common,amaneq-lrtdc-1ch,raris-ac-lgad}/
└── rawdata/
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

## What SPADI_LOCAL means

`SPADI_LOCAL` is an environment variable containing the path to the user's workspace for editable settings and acquired data. Container startup sets it automatically; its default is `/workspace/spadi`. This guide uses that default.

| Variable | Purpose | Default |
|---|---|---|
| `$SPADI_ROOT` | Installation provided by the image | `/opt/spadi` |
| `$SPADI_LOCAL` | User workspace for editing and saving | `/workspace/spadi` |

The `$` tells the shell to substitute the variable's value. These commands therefore refer to the same directory:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cd /workspace/spadi/scripts/nestdaq/amaneq-lrtdc-1ch
```

Inside the container, use `echo "$SPADI_LOCAL"` to check its value. Environment setup alone creates no directories; the helpers below create the required directories and files.

The startup command's `workspace:/workspace` mount maps container `/workspace/spadi/` to the host's `workspace/spadi/` under the directory where you ran the startup command. Settings and acquired data remain on the host after the container exits.

You do not need to create the whole tree manually. Run the helpers inside the container; directories and files appear at these stages.

| Operation | What is created |
|---|---|
| `spadi-prepare-runtime.sh` | Copies installed helpers and configurations under `/workspace/spadi/scripts/`, and creates `/workspace/spadi/rawdata/` |
| AMANEQ `./run-start.sh` | Creates the output directory `rawdata/amaneq-lrtdc-1ch/00/`; acquisition has not started |
| FileSink **Run** in the browser | Creates the selected run's data file, for example `00/run000001.dat` |

Preparation never overwrites existing files, including edited `config.sh` files. `/opt/spadi/` is provided by the image. With the default paths, files created under `/workspace/spadi/` persist in the host's `workspace/spadi/`. If you change `SPADI_LOCAL` or `RAWDATA_DIR`, the configured paths are used instead.



Repository recipes live under `scripts/fee` and `scripts/nestdaq`; the prepare helper is in `scripts/runtime/spadi-prepare-runtime.sh`. See the [official hardware guide](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/firmware/strlrtdc/strlrtdc/) and [pinned revisions](../versions/versions.env).

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

When updating an existing workspace, stop its sessions, rename the old `scripts/nestdaq/common` directory, then run the helper again to obtain the new common scripts. Compare and reapply any local changes. Update an old FEE `amaneq-lrtdc-1ch/setup.sh` to the version accepting an optional IP argument too. Refresh the AMANEQ recipe run helpers too, including run-cleanup.sh; otherwise an older run-start.sh may still start acquisition automatically. Keep your edited recipe `config.sh` files.

## AMANEQ: channel 102 with NestDAQ

Use 1-Gbps Str-LRTDC firmware at **192.168.10.16**, DIP1 = 0 (default IP), DIP3 = 1 (standalone), and connect a signal to **zero-based channel 102** on the lower DCRv2 mezzanine. Set the host Ethernet interface to an address such as `192.168.10.1/24`. Allow UDP 4660 for RBCP control and TCP 24 for SiTCP data. In WSL2, verify Windows interface settings and Linux routing. Stop any other reader using this board.

```text
AMANEQ ch102 -> AmQStrTdcSampler-0 -> STFBuilder-0
            -> TimeFrameBuilder-0 -> FileSink-0 -> 00/run000001.dat
```

There is one physical AMANEQ board. Sampler, STFBuilder, TimeFrameBuilder, and FileSink are four software processes inside the container.

The recipe shares Valkey, parameter, topology, plugin, and tmux helpers with RARiS. Live acquisition uses a hardware sampler and STF builder and saves TF/STF records with FileSink.

### Prepare services in the terminal

Inside the container:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cat config.sh
ping -c 3 192.168.10.16
./run-start.sh
```

`run-start.sh` applies and verifies the FEE masks, prepares Valkey, parameters, topology, and four processes, and waits for all processes to become **Idle**. Acquisition has not started. Initialize, Run, Stop, and change run numbers in the browser.

### Initialize in the browser

Open **http://localhost:8081/daq-webctl.html** in the host browser (the Windows browser for WSL2).

1. In **State Summary**, check that `AmQStrTdcSampler`, `STFBuilder`, `TimeFrameBuilder`, and `FileSink` each have one instance, all **Idle**. **Show details** displays individual states.
2. Uncheck **Wait Device Ready** and **Wait Ready**. Follow the explicit transitions below and check states after each click.
3. Uncheck **Auto increment at RUN-Stop**. Otherwise each individual Stop click increments the run number.
4. Enter `1` in **RUN number → New value**, click **Send**, and check **Next : 1**. Choose an unused number.
5. Under **Select command target**, select **all** for both services and instances.
6. Click **Init Device and Connection**; wait until all four processes are **Device-Ready**.
7. Click **Init Task**; wait until all four processes are **Ready**.

After reloading the browser, uncheck these three options again.

### Start acquisition in the browser

Deselect service **all** and select only the service in the table. Keep instances set to **all**. Start downstream first: click **Run**, wait for that device to become **Running**, then proceed.

| Order | Service to select | Action |
|---|---|---|
| 1 | `FileSink` | **Run** → **Running** |
| 2 | `TimeFrameBuilder` | **Run** → **Running** |
| 3 | `STFBuilder` | **Run** → **Running** |
| 4 | `AmQStrTdcSampler` | **Run** → **Running** |

Sampler Run opens the TCP connection to AMANEQ and starts acquisition. Check all four processes are **Running** with **Error = 0**. Run 1 is saved to the host's `workspace/spadi/rawdata/amaneq-lrtdc-1ch/00/run000001.dat`.

### Stop and start the next run in the browser

Select one service at a time in upstream order: `AmQStrTdcSampler` → `STFBuilder` → `TimeFrameBuilder` → `FileSink`. Click **Stop**, wait for **Ready**, and allow about one second before stopping the next service. FileSink **Ready** means its trailer has been written and the file closed.

For the next run, enter an unused **New value** (for example `2`) and click **Send**. Select **all** services and instances, click **Reset Task**, wait for all **Device-Ready**, then **Reset Device**, and wait for all **Idle**. Repeat initialization and startup. Do not change the run number during acquisition.

When finished, Stop all processes in the browser, select **all** services and instances, and click **End**. Check that processes are **Exiting** or have disappeared, then run `./run-cleanup.sh` in the tmux `control` window to close this session. Cleanup refuses while any process is still active. Closing the browser does not stop acquisition.

### Configuration and saved data

The FEE masks for Main-U, Main-D, MZN-U, MZN-D are `ffffffff ffffffff ffffffff ffffffbf`. Channel 102 is MZN-D bit 6; 1 masks and 0 unmasks. All other inputs 0–127 are masked. To apply masks separately while stopped, run `./fee-setup.sh`.

Edit NestDAQ `config.sh` for `AMANEQ_IP`, initial `RUN_NUMBER`, `RAWDATA_DIR`, and ports. Its IP is passed to the FEE helper; masks remain in `scripts/fee/amaneq-lrtdc-1ch/config.sh`. Choose later run numbers in the browser. Preparation refuses an existing initial output; FileSink uses `openmode=create` to prevent overwrites during browser Run too. If a duplicate number makes FileSink fail, do not continue acquisition; inspect its logs. Keep configuration unchanged while its session runs.

Defaults: Valkey `127.0.0.1:6380` (DB0 registry, DB1 metrics, DB2 parameters), web status `http://localhost:8081/daq-webctl.html`, and data ports 5599–5601, and optional DQM PUB port 5602. FileSink needs this DQM channel even without a monitor subscriber. These differ from RARiS defaults. This recipe owns its Valkey DBs; do not share them with another running setup. Valkey remains after stopping for reuse.

Stop acquisition in the browser as described above. Use `run-stop.sh` to stop and exit when the browser is unavailable. After normal browser End, use `run-cleanup.sh`. The emergency stop helper stops the source first, allows downstream processing, waits for FileSink's PostRun/trailer/close, then exits devices and tmux. On errors/timeouts tmux is retained for inspection. The pinned upstream may discard a final incomplete frame and queued FileSink PostRun input; this procedure does not guarantee a lossless run boundary. Review logs and delimiter flags. Heartbeat delimiters appear without hits, so file growth alone does not establish channel 102 activity. The output contains FileSink header/trailer and TF/STF records, rather than the previous `strdaq` stream.

## Terminal and log operations in tmux

After preparing AMANEQ services, run `./run-attach.sh` inside the container. RARiS provides the same helper in its recipe directory.

| Window | Purpose |
|---|---|
| `control` | Shell for configuration, `./run-status.sh`, and `./run-cleanup.sh` after End |
| `webctl` | Web Controller log |
| `sampler` | AMANEQ sampler log |
| `STF0` | STFBuilder log |
| `TFB0` | TimeFrameBuilder log |
| `sink0` | FileSink log |

Press and release **Ctrl-b**, then press:

| Key | Action |
|---|---|
| `w` | Choose a window from the list |
| `n` / `p` | Next / previous window |
| `0` | Open `control` |
| `[` | Scroll log history (arrows / PageUp; `q` returns) |
| `d` | Detach; acquisition and Web Controller continue |

During initialization and acquisition, check one instance per service in **State Summary / Show details**, and inspect each tmux log for errors. Windows remain after a process exits, so window count alone is not proof of healthy acquisition; inspect exit status and logs. If the browser is unavailable, run `./run-stop.sh` from `control`.

Valkey is a managed background service. From `control`, inspect its default log with `tail -n 50 /tmp/spadi-valkey-6380.log` (the filename follows the configured port). Terminal operations need no xterm, `DISPLAY`, or X11 forwarding. Valkey remains available after stopping for reuse.

## RARiS AC-LGAD replay

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d detaches.
```

This launches three STFBFilePlayer processes and one TimeFrameBuilder. Open `http://localhost:8080/daq-webctl.html`, select the services, set a run number, then use **Init Device and Connection → Init Task → Run**, checking states. The default replay topology has no FileSink: connect the desired consumer to TFB output `tcp://127.0.0.1:5501`. Use browser Stop → Reset Task → Reset Device, select all targets and End, then `./run-stop.sh` to close the tmux session. Normal changes belong in its `config.sh`.

## Appendix: Relation to the SPADI-A DAQ manual

This guide follows the official [DAQ execution](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの実行方法), [NestDAQ script editing](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの設定/NestDAQスクリプトの編集), and [FEE script editing](https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20マニュアル/ソフトウェア/DAQの設定/FEEスクリプトの編集) procedures: prepare services and FEE, check process counts and logs, then browser Init → Run → Stop → Reset → End. One tmux session manages terminals.

| Role in the official manual | Container equivalent |
|---|---|
| `init.sh`: Redis and Web Controller | `common/start-valkey.sh` and the `webctl` window in `common/tmux-start.sh` |
| `fee_scripts/config_modules.sh`: FEE settings | AMANEQ `fee-setup.sh` and FEE `setup.sh` (input masks for this standalone LR example) |
| `mq-param.sh`, `topology.sh` | `common/apply-parameters.sh`, `common/apply-topology.sh` |
| `tf.sh`, `run-stf-tf.sh`, `start_device.sh` | AMANEQ `run-start.sh`, `common/tmux-start.sh`, `common/start-device.sh` |
| Per-xterm log inspection | `run-attach.sh` and named windows in one tmux session |
| Cleanup after browser **End** | AMANEQ `run-cleanup.sh`, affecting this session only |

`run-start.sh` coordinates preparation; the common helpers need not be run separately. Historical HR mezzanine initialization, MIKUMARI-primary operations, and deprecated extension masks are not copied into this standalone LR recipe. The pinned sampler uses `TdcType=1` for LR.
