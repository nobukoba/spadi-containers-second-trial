# AMANEQ LR-TDC one-channel NestDAQ recipe

`config.sh` sets the board IP (192.168.10.16), LR type (1), run number, storage, Valkey, and data/web ports. One sampler and STFBuilder feed one TimeFrameBuilder and FileSink. `fee-setup.sh` applies the channel-102-only masks from the FEE recipe.

After `spadi-prepare-runtime.sh` in a DAQ/FULL image:

```bash
cd "$SPADI_LOCAL/scripts/nestdaq/amaneq-lrtdc-1ch"
./run-start.sh
./run-status.sh
./run-attach.sh
# Ctrl-b d detaches.
./run-stop.sh
```

The start helper initializes devices and starts acquisition automatically. Stop with the stop helper so FileSink closes normally before the session is removed. Change `RUN_NUMBER` for the next run. Output is `$SPADI_LOCAL/rawdata/amaneq-lrtdc-1ch/00/run000001.dat` for run 1.

Full instructions and directory structure: [user guide](../../../docs/user-guide.md) / [日本語](../../../docs/user-guide.ja.md).
