# RARiS ARTEMIS offline and replay analysis

Use a newly built `spadi-user-full` image containing this tutorial. It needs
ARTEMIS, ROOT and NestDAQ. The processor is compiled when the image is built; runs do not compile it. No detector
hardware is needed. The raw data are public RARiS run 20, three FileSink v1
STF files. Histograms use uncalibrated channel, raw TDC and raw TOT values;
they are not calibrated charge or time.

Inside the container, prepare the writable workspace and download data.
Preparation preserves existing user configuration: if the recipe was copied
from an older image, compare its `config.sh` with the new image before using
the pinned manifest.

```bash
spadi-prepare-local.sh
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./rawdata-download.sh
mkdir -p "$SPADI_LOCAL/raris-results"
/opt/spadi/scripts/artemis/raris-ac-lgad/run.sh offline \
  "$SPADI_LOCAL/raris-results/offline.root"
```

Offline reads aligned STF IDs from all three files and stops at the first
source trailer. Thus it analyzes the 2,815 common STFs; source 01 has 25
additional STFs. Errors and an empty run fail the command. The output contains
`channel`, `tdc`, `tot`, and TF/HBF/hit counters.

For online, keep this same container running and use two shells in it (or a
second shell entering the same container). Start the existing replay first:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./run-start.sh
./run-status.sh
```

In the other shell, start the receiver **before** starting the DAQ run:

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/run.sh online \
  "$SPADI_LOCAL/raris-results/online.root"
```

Open `http://127.0.0.1:8080` in the host browser (publish port 8080 if using
Docker). Leave both Control Targets selectors set to `all`, then click INIT DEVICE,
INIT TASK, and RUN after each state transition completes. INIT DEVICE sends
the CONNECT command. Start RUN within 30 seconds of starting the online receiver; set
`RARIS_TIMEOUT_MS=120000` before the online command to allow more time. The
receiver stops after 30 seconds without a TF, writes the ROOT file, and fails if
no TF arrived. A timeout also marks the end of a successful replay, so compare
counts and bins to detect early termination. With the sample data the comparison
should report 2,815 TF, 33,780 source HBF and 68,956 hit words, with zero
histogram bin differences:

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/compare.sh \
  "$SPADI_LOCAL/raris-results/offline.root" \
  "$SPADI_LOCAL/raris-results/online.root"
root -l "$SPADI_LOCAL/raris-results/online.root"
```

The recipe uses `TFB_DECIMATION_FACTOR=1000`, but the pinned builder applies
this to its separate `decimator` channel. The configured port 5501 is `out`,
which is not decimated. The 25 unmatched source 01 STFs are not emitted with
incomplete TF output disabled. Actual output depends on replay timing; a count
or bin mismatch is a failed comparison, not evidence of equal results.

In the first shell, stop replay after the analysis and clean up:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/raris-ac-lgad"
./run-stop.sh
```

The recipe may leave its Redis/Valkey server running; stop it only if this run
started it and no other work uses it. Remove result files explicitly when no
longer needed. If the receiver times out, verify the DAQ states, port 5501,
input paths and that the receiver was started before RUN. The actual-data HBF
ordering evidence and replay limitations are in
[the inspection report](../experiments/raris-ordering/README.md).

```bash
/opt/spadi/scripts/artemis/raris-ac-lgad/test-actual.sh \
  "$SPADI_LOCAL/rawdata/raris_ac_lgad_202603" \
  "$SPADI_LOCAL/raris-results/online.root"
```

Data manifest: `container-interfacing-nestdaq-eicrecon` revision `ccf94e725389b5d32b2cd167312deb88c6461eba`; SHA-256 hashes are recorded in `config.sh`.
