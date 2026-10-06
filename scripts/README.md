# Scripts

| Directory | Purpose |
|---|---|
| `runtime/` | Container startup, environment setup, and version reporting |
| `development/` | Shared workspace preparation and environment inspection |
| `tests/` | Host regression checks and Docker/SIF smoke tests |
| `fee/`, `nestdaq/`, `artemis/` | Component build/clone helpers and operation recipes |

Dockerfiles explicitly install helpers at their existing container paths, including
`/opt/spadi/spadi-setup.sh` and `/opt/spadi/scripts/*.sh`. Repository organization
therefore does not change user commands or existing workspace copies.
