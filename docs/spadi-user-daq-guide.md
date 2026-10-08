# spadi-user-daq guide

**Language: English | [日本語](spadi-user-daq-guide.ja.md)**

This image provides FEE and NestDAQ acquisition and replay with browser control.

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
│   ├── fee/
│   └── nestdaq/
├── StrLRTDC/bin/set_tdcmask
└── StrHRTDC/bin/

/workspace/spadi/                   # SPADI_LOCAL → host workspace/spadi
├── scripts/
│   ├── fee/
│   │   └── amaneq-lrtdc-1ch/{config.sh,setup.sh}
│   └── nestdaq/
│   │   ├── common/
│   │   ├── amaneq-lrtdc-1ch/
│   │   └── raris-ac-lgad/
└── rawdata/
    ├── amaneq-lrtdc-1ch/00/run000001.dat
    └── raris_ac_lgad_202603/{00,01,02}/run000020.dat
```

/opt/spadi is supplied by the image; /workspace/spadi is the persistent host workspace. spadi-prepare-local.sh creates scripts and rawdata. User images do not provide /opt/spadi/src. AMANEQ run-start.sh creates the output subdirectory; browser FileSink Run creates the data file. rawdata-download.sh downloads RARiS input files.

The SPADI_LOCAL environment variable defaults to `/workspace/spadi`; SPADI_ROOT defaults to `/opt/spadi`. Startup sets both variables but does not create directories. The local area maps to the host directory `workspace/spadi`. See the [common README procedures](../README.md) for the full explanation.

## Download and start the image

Run the following commands in the host terminal. Choose either Apptainer or Docker.

### Apptainer (Linux / Windows WSL2)

```bash
curl -fL -O \
  https://github.com/nobukoba/spadi-containers-second-trial/releases/download/latest/spadi-user-daq.sif
mkdir -p "$PWD/workspace"
apptainer shell --cleanenv --bind "$PWD/workspace:/workspace" \
  --shell /opt/spadi/spadi-shell.sh spadi-user-daq.sif
```

### Docker (macOS / Linux)

```bash
docker pull --platform linux/amd64 \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
mkdir -p "$PWD/workspace"
docker run --rm -it \
  --platform linux/amd64 \
  --network host \
  -e LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
  -v "$PWD/workspace:/workspace" \
  ghcr.io/nobukoba/spadi-containers-second-trial/spadi-user-daq:latest
```

DAQ / FULL uses `--network host` to share the host network. Verify device connectivity in your environment.

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

Keep both service and instance targets set to **all**, then click **Run** once. Verify that `AmQStrTdcSampler`, `STFBuilder`, `TimeFrameBuilder`, and `FileSink` all reach **Running** with **Error = 0**. The sampler opens the TCP connection to AMANEQ and begins acquisition. Run 1 is saved under `workspace/spadi/rawdata/amaneq-lrtdc-1ch/00/run000001.dat` on the host.

### Stop and start the next run in the browser

With both targets set to **all**, click **Stop** once and wait for every process to reach **Ready**. Check the FileSink logs to confirm the output file closed successfully. A simultaneous stop may not allow downstream buffers to drain, so lossless run boundaries are not guaranteed. If shutdown or data integrity problems occur, use individual service stops for troubleshooting, in upstream order: `AmQStrTdcSampler` → `STFBuilder` → `TimeFrameBuilder` → `FileSink`, waiting for **Ready** after each.

For the next run, enter an unused **New value** (for example `2`) and click **Send**. With both targets set to **all**, click **Reset Task** and wait for **Device-Ready**, then **Reset Device** and wait for **Idle**. Repeat initialization and startup. Never change the run number during acquisition.

When finished, select **all** and click **Stop**, verify all processes are **Ready**, then click **End**. Wait for processes to exit, then run `./run-cleanup.sh` in the tmux `control` window. Closing the browser alone does not stop acquisition.

### Configuration and saved data

The FEE masks for Main-U, Main-D, MZN-U, MZN-D are `ffffffff ffffffff ffffffff ffffffbf`. Channel 102 is MZN-D bit 6; 1 masks and 0 unmasks. All other inputs 0–127 are masked. To apply masks separately while stopped, run `./fee-setup.sh`.

Edit NestDAQ `config.sh` for `AMANEQ_IP`, initial `RUN_NUMBER`, `RAWDATA_DIR`, and ports. Its IP is passed to the FEE helper; masks remain in `scripts/fee/amaneq-lrtdc-1ch/config.sh`. Choose later run numbers in the browser. Preparation refuses an existing initial output; FileSink uses `openmode=create` to prevent overwrites during browser Run too. If a duplicate number makes FileSink fail, do not continue acquisition; inspect its logs. Keep configuration unchanged while its session runs.

Defaults: Valkey `127.0.0.1:6380` (DB0 registry, DB1 metrics, DB2 parameters), web status `http://localhost:8081/daq-webctl.html`, and data ports 5599–5601, and optional DQM PUB port 5602. FileSink needs this DQM channel even without a monitor subscriber. These differ from RARiS defaults. This recipe owns its Valkey DBs; do not share them with another running setup. Valkey remains after stopping for reuse.

Stop acquisition in the browser as described above. Use `run-stop.sh` to stop and exit when the browser is unavailable. After normal browser End, use `run-cleanup.sh`. The emergency stop helper stops the source first, allows downstream processing, waits for FileSink's PostRun/trailer/close, then exits devices and tmux. On errors/timeouts tmux is retained for inspection. The pinned upstream may discard a final incomplete frame and queued FileSink PostRun input; this procedure does not guarantee a lossless run boundary. Review logs and delimiter flags. Heartbeat delimiters appear without hits, so file growth alone does not establish channel 102 activity. The output contains FileSink header/trailer and TF/STF records, rather than the previous `strdaq` stream.

Use the LR-TDC `set_tdcmask` command to set all four banks while acquisition is stopped. `fee-setup.sh` uses this command and verifies the masks with `read_register`.

```bash
/opt/spadi/StrLRTDC/bin/set_tdcmask 192.168.10.16 ffffffff ffffffff ffffffff ffffffbf
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
