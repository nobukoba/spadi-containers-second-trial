# NestDAQ runtime recipes

- `amaneq-lrtdc-1ch/`: live LR-TDC readout of 192.168.10.16, channel 102 only, through AmQStrTdcSampler -> STFBuilder -> TimeFrameBuilder -> FileSink.
- `raris-ac-lgad/`: the existing three-source STF file replay.
- `common/`: shared Valkey, parameters, topology, device/plugin startup, tmux, and state-control helpers.

Run `spadi-prepare-runtime.sh` in user images to obtain editable copies under `$SPADI_LOCAL/scripts/nestdaq`. It keeps existing files. Development images can also use `spadi-prepare-local.sh`.

See the [user guide](../../docs/user-guide.md) / [日本語](../../docs/user-guide.ja.md) for commands and directory structure.
