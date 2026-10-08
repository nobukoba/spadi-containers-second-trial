# spadi-user-full guide

**Language: English | [日本語](spadi-user-full-guide.ja.md)**

This image provides Acquisition and analysis using FEE, NestDAQ, ROOT, and ARTEMIS.

## Directory structure

```text
/opt/spadi/                         # SPADI_ROOT
├── bin/
│   ├── StrLRTDC/set_tdcmask
│   └── StrHRTDC/
├── lib/
├── lib64/
├── include/
├── share/
├── versions/
├── scripts/
│   ├── spadi-prepare-local.sh
│   ├── fee/
│   ├── nestdaq/
│   └── artemis/
└── scripts/exp-config/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   ├── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
│   ├── nestdaq/
│   │   ├── common/
│   │   ├── amaneq-lrtdc-1ch/
│   │   └── raris-ac-lgad/
│   └── artemis/
├── analysis/example/{macro,output}/
└── rawdata/
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates scripts and rawdata. User images do not provide /opt/spadi/src. AMANEQ run-start.sh creates the output subdirectory; browser FileSink Run creates the data file. rawdata-download.sh downloads RARiS input files. The mkdir command below creates analysis directories.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download and start the image

Run the following commands in the host terminal. Choose either Apptainer or Docker.

### Apptainer (Linux / Windows WSL2)

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-full.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-full.sif
```

### Docker (macOS / Linux)

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-full:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-full:latest
```

Apptainer normally shares the host network regardless of the image type. Docker shares the host network when started with `--network host`, regardless of the image type. Verify device connectivity in your environment.

Files under `workspace` persist on the host. Download or pull again when updating the image.

## Prepare the workspace

Copy the runtime scripts available in this image. Existing configuration and source files are preserved. See the [README](../README.md) for common preparation and update procedures.

```bash
spadi-prepare-local.sh
```

## AMANEQ: channel 102 with NestDAQ

Use 1-Gbps Str-LRTDC firmware at **192.168.10.16**, DIP1 = 0 (default IP), DIP3 = 1 (standalone), and connect a signal to **zero-based channel 102** on the lower DCRv2 mezzanine. Set the host Ethernet interface to an address such as `192.168.10.1/24`. Allow UDP 4660 for RBCP control and TCP 24 for SiTCP data. In WSL2, verify Windows interface settings and Linux routing. Stop any other reader using this board.

```text
AMANEQ ch102 -> AmQStrTdcSampler-0 -> STFBuilder-0
            -> TimeFrameBuilder-0 -> FileSink-0 -> 00/run000001.dat
```

There is one physical AMANEQ board. Sampler, STFBuilder, TimeFrameBuilder, and FileSink are four software processes inside the container.

The recipe shares Valkey, parameter, topology, plugin, and tmux helpers with RARiS. Live acquisition uses a hardware sampler and STF builder and saves TF/STF records with FileSink.

### MZN-D readback limitation

A board reporting FW ID `0x60c4`, version `2.10` (hexadecimal `2.A`), acknowledged the MZN-D write but returned `0xffffffff` on readback. The [official HDL](https://github.com/AMANEQ-official/strtdc-src/blob/71c188a74c93a7d06cb9e803d50360b05495e730/lrtdc-impl/strLrTdc.vhd#L685) incorrectly tests MZN-U in the MZN-D Read branch. This does not establish a failed write or independently verify the internal mask. The helper stops with `Mask verification failed at 10300000`. Do not treat that as success; confirm the setting with corrected firmware or independent hardware-data validation. NestDAQ acquisition from this hardware remains unverified.

### Prepare services in the terminal

Inside the container:

`cat config.sh` displays the current settings. Edit them with a text editor such as `vim config.sh` before preparing services.

Move to the configuration directory, review settings, and check connectivity.

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
cat config.sh
ping -c 3 192.168.10.16
```

First configure and read back the FEE input masks.

```bash
./fee-setup.sh
```

**Continue only if this command succeeds.** Stop on any error and check the MZN-D readback limitation above.

Then initialize DAQ services.

```bash
./initialize.sh
```

This prepares Valkey, parameters, topology, the initial run number, the Web Controller, and four processes, then waits for all processes to become **Idle**. It does not change FEE registers or masks. Acquisition has not started. Initialize, Run, Stop, and change run numbers in the browser.

`run-start.sh` is an alternative that runs these two commands in order. Do not run it again after executing them separately.

### Attach to the tmux session

After `initialize.sh` finishes successfully, run this inside the container from the same configuration directory.

```bash
./run-attach.sh
```

If you have moved to another directory, return before attaching:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
./run-attach.sh
```

The helper reads `TMUX_SOCKET` and `TMUX_SESSION` from `config.sh` and attaches to the session started by `initialize.sh`. Press `Ctrl-b`, release it, then press `w` to select the `control` window or a process log. Press `Ctrl-b`, release it, then press `d` to detach. DAQ processes and the Web Controller keep running while detached. Run `./run-attach.sh` again to reattach; do not rerun `initialize.sh`.

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

Use the LR-TDC `set_tdcmask` command to set all four banks while acquisition is stopped. `fee-setup.sh` uses this command and verifies the masks with `read_register`.

```bash
/opt/spadi/bin/StrLRTDC/set_tdcmask 192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
```

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

## Start ROOT and ARTEMIS

Container startup loads the ROOT and ARTEMIS environment. Check the version and executables:

```bash
root-config --version
command -v root
command -v artemis
mkdir -p "$SPADI_LOCAL/analysis/example/macro" "$SPADI_LOCAL/analysis/example/output"
cd "$SPADI_LOCAL/analysis/example"
```

The mkdir command creates the analysis directories. spadi-prepare-local.sh prepares the available ARTEMIS scripts and rawdata directory; experiment steering files, calibration parameters, and input data must be supplied separately.

Check ROOT and save a ROOT file without a graphical display:

```bash
root -b -q -e 'TFile f("output/example.root", "RECREATE"); TH1D h("example", "Example", 100, 0, 100); h.Fill(42); h.Write(); f.Close();'
ls -lh output/example.root
```

The result persists at host workspace/spadi/analysis/example/output/example.root. This example creates a synthetic histogram; it does not decode experiment data.

Start interactive ROOT or ARTEMIS with the following commands. Enter .q at each application prompt to exit.

```bash
root -l
# Enter .q before running the next command.
artemis
```

Graphical histogram windows require a display connection; the batch example above uses no xterm or X11. Browser-controlled acquisition is provided by the DAQ/FULL Web Controller. ARTEMIS itself is operated from the terminal or analysis macros.

## Analyze experiment data

Place the experiment steering files, processors, calibration files, and macros under a working directory in $SPADI_LOCAL/analysis and start ARTEMIS there. Keep inputs under $SPADI_LOCAL/rawdata and output ROOT files in the analysis output directory so they persist on the host. Follow the experiment procedures for loading its libraries and running its analysis.

NestDAQ FileSink .dat files contain TF/STF records. They require a compatible input processor, decoder, and steering configuration; they cannot simply be opened as ROOT files. This repository does not ship a complete ARTEMIS steering configuration for the single-channel AMANEQ example. See the [official ARTEMIS README](https://github.com/artemis-dev/artemis/tree/develop).

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

## Appendix: Included software

These are the main included software components. Pins are defined in [versions.env](../versions/versions.env). Inspect `/opt/spadi/scripts/spadi-version.sh` and `/opt/spadi/versions/versions.env` inside your image for its actual build metadata. Locally rebuilt software may differ from this baseline.

| Software | Purpose | Pinned version / revision |
|---|---|---|
| [hul-common-lib](https://github.com/spadi-alliance/hul-common-lib) | RBCP board control: get_version, read_register, write_register | [`65476509aa40`](https://github.com/spadi-alliance/hul-common-lib/tree/65476509aa401aad10148ec7c2d2a50ba7d2db3e) |
| [amaneq-soft](https://github.com/spadi-alliance/amaneq-soft) | AMANEQ LR/HR utilities in bin/StrLRTDC and bin/StrHRTDC | [`86fef97ccc4e`](https://github.com/spadi-alliance/amaneq-soft/tree/86fef97ccc4e6488739e2d8b549a1c5bddd3542e) |
| [openFPGALoader](https://github.com/trabucayre/openFPGALoader) | FPGA SRAM/flash programming over supported interfaces | [`24e46d13bb8f`](https://github.com/trabucayre/openFPGALoader/tree/24e46d13bb8f2bc9371e9ca8443ece2fafc4b20d) |
| [SiTCP IP / MPC utilities](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial) | SiTCP/SiTCP-XG IP and MPC/MPCX license configuration | [`4bc47b6f5ac7`](https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial/tree/4bc47b6f5ac791acfbd88c73dd987b7625074273) |
| [NestDAQ](https://github.com/spadi-alliance/nestdaq) | DAQ framework and Web Controller | [`v1.0.0`](https://github.com/spadi-alliance/nestdaq/tree/v1.0.0) |
| [nestdaq-user-impl](https://github.com/spadi-alliance/nestdaq-user-impl) | Samplers, builders and FileSink | [`47897e9bdc4d`](https://github.com/spadi-alliance/nestdaq-user-impl/tree/47897e9bdc4dac2f429909b3fa8bf05ab93115d0) |
| [UHBook](https://github.com/spadi-alliance/uhbook) | DAQ histogram support | [`e979eb28fb64`](https://github.com/spadi-alliance/uhbook/tree/e979eb28fb64de2eb216ebec31f73a6696d257ec) |
| [exp-config](https://github.com/spadi-alliance/exp-config) | Experiment configuration and scripts | [`0ac32181304f`](https://github.com/spadi-alliance/exp-config/tree/0ac32181304f92e608d4bdd1bb0aa087300e82f7) |
| [FairLogger](https://github.com/FairRootGroup/FairLogger) | Logging library | [`5aee7970fbfc`](https://github.com/FairRootGroup/FairLogger/tree/5aee7970fbfc66c2f0f1668ea15671b43166df68) |
| [FairMQ](https://github.com/FairRootGroup/FairMQ) | Message-based DAQ devices | [`v1.4.55`](https://github.com/FairRootGroup/FairMQ/tree/v1.4.55) |
| [fmt](https://github.com/fmtlib/fmt) | Text formatting library | [`10.2.1`](https://github.com/fmtlib/fmt/tree/10.2.1) |
| [RedisTimeSeries](https://github.com/RedisTimeSeries/RedisTimeSeries) | Time-series database module | [`v1.10.24`](https://github.com/RedisTimeSeries/RedisTimeSeries/tree/v1.10.24) |
| [ROOT](https://github.com/root-project/root) | Analysis, histograms, TTree and Cling | [`v6-32-06`](https://github.com/root-project/root/tree/v6-32-06) |
| [ARTEMIS](https://github.com/artemis-dev/artemis) | Nuclear-physics analysis framework | [`c74e24adf90a`](https://github.com/artemis-dev/artemis/tree/c74e24adf90a83227fa3e5c38dc255ddc4aeb785) |
| [yaml-cpp](https://github.com/jbeder/yaml-cpp) | YAML configuration parser | [`0.8.0`](https://github.com/jbeder/yaml-cpp/tree/0.8.0) |
| [ZeroMQ](https://github.com/zeromq/libzmq) | Messaging library | [`v4.3.5`](https://github.com/zeromq/libzmq/tree/v4.3.5) |
| [hiredis](https://github.com/redis/hiredis) | Redis/Valkey C client | [`v1.0.0`](https://github.com/redis/hiredis/tree/v1.0.0) |
| [redis-plus-plus](https://github.com/sewenew/redis-plus-plus) | Redis/Valkey C++ client | [`1.3.15`](https://github.com/sewenew/redis-plus-plus/tree/1.3.15) |

The OS is AlmaLinux 9. Network tools (iproute, iputils, net-tools, bind-utils, traceroute, tcpdump, nmap-ncat), curl / wget, and vim / emacs are also included. OS packages use AlmaLinux package versions rather than the source pins above.

Valkey and tmux are included for DAQ services. ROOT-dependent TriggerView is disabled in DAQ and enabled in FULL.

ROOT enables TMVA, X11 / OpenGL, SQLite, and SSL; PyROOT, RooFit, and Web GUI are disabled. ARTEMIS disables GET and enables ZeroMQ / Redis support. OpenMPI and compression libraries are also included.

`spadi-user-*` images provide runtime software without source trees or local-development build helpers. A C++ compiler and headers are retained for ROOT / Cling runtime use.
