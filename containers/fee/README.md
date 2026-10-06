# FEE container build

`Dockerfile` provides two build targets:

- `user-fee` — runtime image without source/build tools
- `devel-fee` — development image with source/build tools

Both install SPADI software under `/opt/spadi` and use the shared `scripts/tests/smoke-test-fee.sh` validation.
