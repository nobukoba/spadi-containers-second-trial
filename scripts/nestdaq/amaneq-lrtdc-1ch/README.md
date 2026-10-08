# AMANEQ LR-TDC one-channel NestDAQ recipe

`config.sh` sets the board IP (192.168.10.16), LR type (1), run number, storage, Valkey, and data/web ports. One sampler and STFBuilder feed one TimeFrameBuilder and FileSink. `fee-setup.sh` applies the channel-102-only masks from the FEE recipe.

After `spadi-prepare-local.sh` in a DAQ/FULL image:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d detaches.
# After browser Stop and End:
./run-cleanup.sh
```

`run-start.sh` invokes `fee-setup.sh` and then `initialize.sh`. The latter can be run independently to prepare DAQ without reconfiguring the FEE. The start helper prepares the session and waits for Idle; it does not start acquisition. Open http://localhost:8081/daq-webctl.html, initialize the four devices, then Run and Stop selected services in the order documented in the user guide. Choose subsequent run numbers in the browser. After browser Stop and End, run-cleanup.sh removes only this recipe's tmux session. run-stop.sh stops and exits acquisition if the browser is unavailable. Use tmux windows for logs; xterm and X11 are unnecessary. Output for run 1 is `$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch/00/run000001.dat`.

Full instructions and directory structure: [user guide](../../../docs/user-guide.md) / [日本語](../../../docs/user-guide.ja.md).
