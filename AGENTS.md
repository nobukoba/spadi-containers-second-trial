# Instructions for AI and Developers

This repository provides unified SPADI container images. Keep the implementation practical, reproducible, and easy for humans to understand and maintain.

## Mandatory English for GitHub communication

All GitHub-facing communication authored by AI agents or developers MUST be written in English. This is a mandatory repository rule, not a preference. It applies to pull request titles and descriptions, issue titles and descriptions, conversation comments, review comments and replies, commit messages, and release notes. Do not write these in Japanese, even when the user requests the work in Japanese or the change concerns Japanese documentation. Check the language before creating or updating any GitHub content.

Japanese documentation pages and Japanese replies to the user in chat remain supported. Preserve literal filenames, identifiers, and necessary quotations from Japanese documentation when explaining them in English. Only an explicit user instruction overriding this rule permits an exception.

## Working method and knowledge capture

Treat `AGENTS.md` as the persistent engineering knowledge base for this repository, not only as a static style guide.

Before making a design decision or answering a question about repository policy, inspect the current repository state and this `AGENTS.md` rather than relying on memory or assumptions when the answer can be verified directly.

Whenever a build, CI, Docker, Apptainer, dependency, runtime, or hardware-related error is investigated and the investigation reveals a reusable rule, constraint, compatibility issue, failure mode, or non-obvious fix, update `AGENTS.md` in the same development cycle. Record the reason for the rule, not only the final workaround, so that future AI sessions and developers do not repeat the same failure.

In particular, after fixing an error:

1. identify what was actually wrong from the relevant source, configuration, or logs;
2. make the smallest maintainable implementation fix;
3. add the reusable lesson to `AGENTS.md` when it can prevent recurrence;
4. keep validation or smoke tests that detect the failure automatically when practical;
5. verify the repository state after the change instead of assuming that the intended edit or CI result exists.

Do not add transient one-off log details to `AGENTS.md`; capture the general engineering knowledge learned from them.

When investigating GitHub Actions failures, do not fetch, read, or process the complete workflow log by default. Large ROOT/ARTEMIS/FULL build logs can be very large, and reading the whole log can make an AI/tool session slow, stall, or fail before the useful error is reached. First inspect the workflow/job/step status, identify the most recent failed step, and retrieve only the latest relevant error output or a small tail/context around that failure. Expand to earlier or larger log sections only when the latest error does not contain enough information to diagnose the cause. Do not repeatedly re-read successful build output. For long-running jobs with no failure yet, inspect status, timestamps, and the latest available activity rather than downloading the full log.

When transferring dependency build recipes from a reference repository, verify exact upstream repository URLs, tags, and versions against the working reference instead of retyping them from memory. A one-character owner/repository typo can waste an entire long container build before the dependency-clone step is reached. In particular, redis-plus-plus is hosted at `https://github.com/sewenew/redis-plus-plus.git`.

Explicit new corrections from Nobuyuki Kobayashi should also be incorporated into `AGENTS.md` when they establish a reusable repository rule.

## Two developer audiences

Keep these two audiences distinct in documentation and terminology:

1. **Container users developing SPADI software** use an already-built `spadi-devel-*` Docker/SIF image, edit source under `$SPADI_LOCAL`, and self-build software into `$SPADI_LOCAL`. This workflow belongs in the four image-specific spadi-devel-* guides and their Japanese counterparts; docs/developer-guide.md is a navigation index. Link all eight image guides and both languages from the main READMEs.
2. **Container maintainers** modify Dockerfiles, CI, image composition, SIF generation, publishing, and releases. Their documentation belongs in `docs/container-maintainer-guide.md`, not in the main README's normal development workflow.

Do not instruct normal container users to build Docker or SIF images.

## Version and revision policy

Second-trial builds must be reproducible. The repository-level source of truth for upstream versions and revisions is `versions/versions.env`.

Prefer an upstream project's official stable release tag when it exists and is suitable for the tested stack. NestDAQ core remains on its official `v1.0.0` release. When current debugging requires newer `nestdaq-user-impl` fixes, pin the exact tested upstream commit rather than an unpinned `main` checkout; as of 2026-10-03 the tested pin is `47897e9bdc4dac2f429909b3fa8bf05ab93115d0`. Keep NestDAQ-facing dependencies aligned with the actual source API, not blindly with stale dependency prose. NestDAQ v1.0.0 still documents redis-plus-plus `1.2.1 (recipes branch)`, but its released source includes `<sw/redis++/patterns/redlock.h>`. Upstream redis-plus-plus renamed `recipes` to `patterns` in commit `8fbe9523` on 2022-10-19; the `1.2.1` tag predates Redlock integration, and even `1.3.5` predates the `patterns` path. The first official redis-plus-plus release containing `patterns/redlock.h` is `1.3.6`, but the tested container baseline is now `1.3.15` because older redis-plus-plus builds have triggered LockCatcher `SIGABRT` failures. Keep hiredis at `v1.0.0`, install both libraries only in the common `/opt/spadi` prefix, and verify runtime linkage so an older system or copied library cannot be selected accidentally. NestDAQ documents FairMQ `1.4.26 or later`, so the repository may pin a newer tested FairMQ release such as `v1.4.55`. For repositories without an appropriate release tag, pin an exact commit SHA.

ARTEMIS is developed upstream on the moving `develop` branch. Treat that as an upstream development model, not as a reason for container builds to move: select a known-good commit from `develop`, record its exact SHA as `ARTEMIS_REF` in `versions/versions.env`, and build published images from that SHA. Updating ARTEMIS is an explicit pin-update operation followed by validation.

Do not silently replace a pinned ref with `main`, `master`, or another moving branch. When updating a pin, make it a deliberate change, record why when non-obvious, and rebuild/test every image family affected by that component.

User and development images of the same family must use the same pinned upstream revisions. Dockerfiles and CI should consume the centralized revision set rather than maintaining independent copies that can drift.

A change to documentation or a host-only helper must not trigger expensive ROOT/ARTEMIS/FULL rebuilds. When image-resident scripts change, structure Docker layers so the expensive compiled dependency layers remain cacheable and only the lightweight final layers rebuild where practical.

## Container version metadata

Every published image must be self-describing. Keep the pinned component manifest at `/opt/spadi/versions/versions.env`, build metadata at `/opt/spadi/versions/container.env`, and the user-facing reporter at `/opt/spadi/scripts/spadi-version.sh`. The reporter must show the SPADI container version, source Git commit, image target, and pinned component versions. Docker and SIF smoke tests must verify these files and the reporter so an old standalone SIF remains identifiable without external metadata.

## User development overlay

Do not overwrite the validated base installation when a user rebuilds software interactively. The immutable/container-provided installation remains under `/opt/spadi` and is named by `SPADI_ROOT`. The writable user installation prefix is `/workspace/spadi` and is named by `SPADI_LOCAL`.

Keep the two prefixes structurally parallel where practical:

- `$SPADI_ROOT/bin`, `lib`, `include`, `share`, `src`: validated container-provided stack.
- `$SPADI_LOCAL/bin`, `lib`, `include`, `share`, `src`: user-built stack and user source checkouts.

The local prefix takes precedence over the validated base in `PATH`, `LD_LIBRARY_PATH`, `CMAKE_PREFIX_PATH`, and `PKG_CONFIG_PATH`. The canonical environment entry point is `/opt/spadi/spadi-setup.sh`; interactive shell startup may source it, but scripts and CI must also be able to source it explicitly. Keep setup side-effect free: it sets environment variables but does not create directories. `spadi-prepare-local.sh` creates the writable local prefix and copies only missing source trees/helper scripts; it must never overwrite or delete existing user files. `spadi-env.sh` displays the effective search paths. Shell helper scripts use an explicit `.sh` suffix.

SPADI's own build recipes should install libraries under `$PREFIX/lib`, not split SPADI libraries between `lib` and `lib64`. Keep `$SPADI_ROOT/lib64` and `$SPADI_LOCAL/lib64` in runtime search paths defensively for compatibility with dependencies and older builds; remove those references only after every component's actual install layout has been verified. OS libraries under `/usr/lib64` are unrelated to this SPADI prefix policy.

NestDAQ runtime recipes use a single human-editable `config.sh` per recipe. Keep Redis/Valkey topology and parameter-application logic in shared helpers under `scripts/nestdaq/common` so recipe files do not duplicate host, port, process-count, or parameter boilerplate. Operation scripts use explicit names such as `run-start.sh`, `run-stop.sh`, `run-status.sh`, `run-attach.sh`, and `rawdata-download.sh`. Raw-data download helpers must show transfer progress and support resumable public downloads where practical. Runtime recipes copied into `SPADI_LOCAL` are user-owned configuration and must never be overwritten by prepare/update helpers.

Provide developer helper scripts that can rebuild the source shipped in the devel image into `SPADI_LOCAL`. Build helpers use short natural names such as `<component>-build.sh`; do not call them `self-build`, `user-build`, or `local-build`. Put editable copies in `$SPADI_LOCAL/scripts` and put that directory on `PATH` so helpers can run from any working directory. Prefer one small script per operation/component instead of one argument-driven dispatcher. Also provide an explicit opt-in workflow for cloning latest upstream source into `$SPADI_LOCAL/src/<project>` and building it against the validated `SPADI_ROOT` base. The normal container build remains pinned and reproducible; a developer asking for `latest` is intentionally leaving that pinned baseline. Never make the image build itself silently clone latest/main.

## Runtime user identity

Docker containers run interactive commands as the non-root user `spadi`. The Docker entrypoint reads `LOCAL_UID` and `LOCAL_GID` and remaps the numeric UID/GID of `spadi` at startup before dropping privileges. User-facing Docker commands should pass `LOCAL_UID="$(id -u)"` and `LOCAL_GID="$(id -g)"` on both macOS and Linux. The container username remains `spadi`; only its numeric identity follows the host user. This keeps bind-mounted `/workspace` files owned by the invoking host user without requiring separate macOS and Linux command variants.

Do not replace this with Docker `--user` alone: the named `spadi` account and its HOME must remain valid for interactive development tools.

`setpriv` preserves the environment by default. Its `--reset-env` option is a flag with no argument; `--reset-env=false` aborts startup before the requested command can run. Omit the flag when retaining SPADI paths while dropping privileges. Run `bash scripts/tests/test-entrypoint.sh` to verify the real AlmaLinux 9 command, user/group remapping, environment preservation, workspace ownership, argument forwarding, and exit status before expensive SPADI builds. The workflow runs this host-side regression check before compilation for each independent target.

## Paths

All SPADI-related software uses the single installation prefix `/opt/spadi`.

- Source trees: `/opt/spadi/src/<project>`
- Installed executables: `/opt/spadi/bin`
- Installed libraries: `/opt/spadi/lib` and `/opt/spadi/lib64`
- Installed headers: `/opt/spadi/include`
- Scripts: `/opt/spadi/scripts`
- Component script trees: `/opt/spadi/scripts/nestdaq`, `/opt/spadi/scripts/fee`, and `/opt/spadi/scripts/artemis`
- NestDAQ shared runtime helpers: `/opt/spadi/scripts/nestdaq/common`
- NestDAQ experiment/replay recipes: `/opt/spadi/scripts/nestdaq/<recipe>`
- Experiment configuration: `/opt/spadi/scripts/exp-config`
- Container-provided scripts: `/opt/spadi/scripts`
- User working directory: `/workspace`
- User source checkouts: `$SPADI_LOCAL/src/<project>` (normally `/workspace/spadi/src/<project>`)
- User-built installation prefix: `$SPADI_LOCAL` (normally `/workspace/spadi`)
- User-editable runtime recipes: `$SPADI_LOCAL/scripts/<component>/...`
- Raw data: `$SPADI_LOCAL/rawdata` (normally `/workspace/spadi/rawdata`)

Do not use `/work`.

ROOT and ARTEMIS sources also belong below `/opt/spadi/src`. Prefer installing ROOT, ARTEMIS, NestDAQ, FEE software, and their dependencies directly into the common `/opt/spadi` prefix when the software supports it.

For ROOT, use `gnuinstall=OFF`. `/opt/spadi` is a self-contained SPADI software prefix rather than a system `/usr`-style installation. ROOT should therefore use its native prefix layout so that its `bin`, `lib`, and `include` directories integrate directly with the common `/opt/spadi` environment. Do not change ROOT to `gnuinstall=ON` unless the overall SPADI installation layout is intentionally redesigned.

User images should not normally contain `/opt/spadi/src`. Development images retain source trees.

ROOT/Cling is an exception to the general preference to omit compiler-related runtime content. When ROOT is built against the system GCC toolchain, Cling invokes a `c++` compiler driver to discover the standard-library include paths and also requires installed ROOT headers such as `/opt/spadi/include/ROOT.modulemap` at runtime. ARTEMIS and FULL user images that include this ROOT build must therefore retain `/opt/spadi/include` and provide `gcc-c++` (or an equivalent `c++` driver plus matching standard C++ headers). They should still omit `/opt/spadi/src`, CMake, Git, and unrelated development tools unless another runtime component genuinely requires them. On AlmaLinux 9, installing `gcc-c++` may also install `make` as a package dependency; do not treat the mere presence of `make` as a runtime-image failure when it is pulled in this way. Smoke tests must launch ROOT and verify both `c++` and `ROOT.modulemap` so this failure is caught before SIF publication.

## AlmaLinux 9 runtime baseline

AlmaLinux 9 is the runtime baseline for second-trial images. Prefer AlmaLinux 9-supported runtime packages over recreating historical distribution/package combinations from upstream documentation. For NestDAQ, retain the exact compatible build-library pins where they matter (for example hiredis and redis-plus-plus), but use AlmaLinux 9 `valkey` as the Redis-compatible runtime service. RedisTimeSeries is built as a separately pinned module because NestDAQ metrics uses `TS.*` commands. Document this distinction rather than claiming the image exactly reproduces NestDAQ's historical Redis server package baseline.

## Environment isolation

Do not make the container runtime depend on software environment variables inherited from the host.

Define the SPADI runtime environment explicitly. Do not initialize `PATH`, `LD_LIBRARY_PATH`, `CMAKE_PREFIX_PATH`, `PKG_CONFIG_PATH`, ROOT, ARTEMIS, or NestDAQ environments by blindly appending host values.

Apptainer runtime tests must use a clean environment (`--cleanenv`) and verify that the resulting container environment is sufficient by itself. Do not assume Docker `ENV` values will always appear unchanged in an Apptainer `--cleanenv` invocation. For CI smoke tests, set host sentinel variables to detect leakage, then explicitly pass the intended SPADI runtime variables with Apptainer `--env`. This tests both host isolation and the actual required runtime environment instead of failing before the software itself is exercised.

## CPU compatibility

Target `linux/amd64` and generic x86-64 compatibility, including older x86-64 machines.

Never use `-march=native` for NestDAQ, nestdaq-user-impl, or other SPADI software. Do not require `x86-64-v2`, AVX, or AVX2 unless explicitly requested.

Prefer `-march=x86-64 -mtune=generic`; use explicit non-AVX flags where necessary. NestDAQ and nestdaq-user-impl currently contain upstream Release flags using `-march=native`; these must be neutralized and the resulting binaries checked for unintended AVX instructions.

Published Docker images intentionally provide `linux/amd64` rather than a native `linux/arm64` variant. On Apple Silicon Macs, Docker commands in user-facing documentation must therefore explicitly use `--platform linux/amd64` (or clearly document `DOCKER_DEFAULT_PLATFORM=linux/amd64`). Without this, Docker reports `no matching manifest for linux/arm64/v8`. Do not respond to this client-side architecture mismatch by changing the repository's generic x86-64 image policy or by adding an ARM64 build unless that policy is explicitly reconsidered.

Current `nestdaq-user-impl` may fail against the pinned FairMQ build because `TimeFrameBuilder.cxx` passes a `const fair::mq::Parts` through an API whose `operator[]` is not const-qualified, producing `passing 'const fair::mq::Parts' as 'this' argument discards qualifiers`. For the container build, intentionally add `-fpermissive` to the patched `nestdaq-user-impl` Release flags rather than carrying a local source-level const-signature modification. Keep this workaround scoped to `nestdaq-user-impl`; do not add `-fpermissive` globally to unrelated SPADI dependencies. Re-evaluate and remove it when upstream `nestdaq-user-impl` or FairMQ resolves the const mismatch. FULL restores the upstream `nestdaq-user-impl/CMakeLists.txt` before rebuilding with ROOT, so the FULL build must explicitly reapply this same scoped `-fpermissive` workaround after the checkout; otherwise the known const-qualification failure is reintroduced even when DAQ itself builds successfully.

## Images

The supported image names are:

- `spadi-user-fee`
- `spadi-devel-fee`
- `spadi-user-daq`
- `spadi-devel-daq`
- `spadi-user-artemis`
- `spadi-devel-artemis`
- `spadi-user-full`
- `spadi-devel-full`

`DAQ = FEE + NestDAQ` and `FULL = DAQ + ARTEMIS`.

User images are runtime images. Do not add compilers, CMake, development headers, source trees, or unrelated development tools unless required at runtime. Development helper scripts belong only in devel images; runtime smoke tests and the side-effect-free `spadi-setup.sh` may remain in user images. Before finalizing a devel image, remove in-tree `build` directories from retained source trees so `spadi-prepare-local.sh` copies clean source rather than stale container build artifacts.

Development images provide the corresponding runtime environment plus source and build tools.

## Dockerfiles and scripts

Write Dockerfiles, helper scripts, and workflows for human readability.

- Prefer clear code over clever or overly compact code.
- Keep FEE, DAQ, ARTEMIS, and FULL responsibilities visible.
- Avoid copying the same installation procedure into eight independent Dockerfiles.
- Share common logic where useful, but do not hide important behavior behind excessive abstraction.
- Use descriptive multi-stage build names.
- Put long shell procedures in readable scripts rather than embedding large shell programs in workflow YAML.
- Comment non-obvious compatibility patches and explain why they exist.

Canonical component Dockerfiles are the shared build definitions. FULL and DAQ CI must reuse `containers/fee/Dockerfile`, `containers/daq/Dockerfile`, and `containers/artemis/Dockerfile` rather than duplicating their installation recipes in workflow YAML or a second FULL-only implementation.

On AlmaLinux 9, the FULL development stage must enable the CRB repository before installing ARTEMIS/ROOT development packages that live there, such as `giflib-devel`. The canonical ARTEMIS build already enables CRB; when FULL reconstructs the development environment on top of the DAQ development image, do not assume the repository enablement state was inherited. Enable CRB explicitly before installing those development dependencies.

## Validation

A successful Docker build is not sufficient validation.

The normal pipeline is:

```text
Build image
    ↓
Test Docker image
    ↓
Create Apptainer SIF
    ↓
Test SIF with --cleanenv
    ↓
Publish
```

Use shared smoke-test scripts for Docker and SIF where practical.

Tests should verify at least:

- expected executables exist and start;
- runtime shared libraries resolve;
- `/workspace` exists and is usable;
- environment variables do not contain unintended host software paths;
- user images do not contain source/build environments unnecessarily;
- devel images contain the expected source/build environment;
- NestDAQ binaries do not accidentally contain AVX instructions introduced by `-march=native`.

When asserting that a command must be absent, do not rely on a bare `! command -v ...` under `set -e`; commands used in an inverted conditional context are exempt from normal `errexit` behavior and can make an intended policy check ineffective. Use an explicit helper or `if command -v ...; then exit 1; fi` so the failure is unambiguous.

Hardware-dependent tests (JTAG, Digilent HS3, SiTCP hardware, real DAQ networks) are separate from container-only smoke tests.


## Commit batching and CI economy

When one logical change touches multiple repository files, batch those edits into one Git commit and update `main` once. Do not use one Contents API commit per file when Git Data API blob/tree/commit/ref operations are available. Each push to an image-affecting path can launch the expensive eight-target workflow, including multi-hour ROOT/ARTEMIS builds, so per-file commits waste runner time and create obsolete queued runs.

Treat one coherent implementation plus its tests and documentation as one commit where practical. Documentation-only changes should not trigger container builds. CI should also cancel superseded runs on the same branch as a safety net, but batching changes before push is the primary defense because cancellation can still discard hours of useful build work.

## GitHub Actions

Keep workflows readable from top to bottom. Build, Docker test, SIF creation, SIF test, and publishing should be visibly separate operations.

The automatic push build has a single source of truth: `.github/workflows/build-all.yml`. It must launch all eight supported image targets (`user` and `devel` for FEE, DAQ, ARTEMIS, and FULL) from one matrix with `max-parallel: 8`, so the eight top-level target jobs can start concurrently. Do not reintroduce separate push-triggered `build-fee.yml`, `build-daq.yml`, `build-artemis.yml`, or `build-full.yml` workflows, and do not add cross-target `needs:` relationships that serialize these eight jobs. Individual targets may still perform their own intrinsic prerequisite work inside their own runner.

FEE, DAQ, ARTEMIS, and FULL builds must be independently startable and must not require a sibling target or workflow to finish first. In particular, do not use a mutable sibling `:latest` image as the source of truth for a DAQ or FULL build. When DAQ or FULL needs prerequisite layers, build commit-local prerequisite images from the canonical component Dockerfiles and pass those immutable commit-specific tags as Docker build arguments. This deliberately trades additional CI compute for shorter wall-clock time, deterministic source consistency, and true top-level parallelism.

Inside FULL, the independent ROOT/ARTEMIS build should start in parallel with the FEE-to-DAQ chain. Only the intrinsic composition step waits for its own commit-local prerequisites; the standalone FEE, DAQ, ARTEMIS, and FULL targets themselves should all be able to run concurrently.

ARTEMIS images are expected to take substantially longer to build than FEE or DAQ images because the Docker build compiles ROOT and ARTEMIS from source. Do not classify an ARTEMIS Docker build as hung merely because it has remained in the `Build and push Docker image` step for a few hours. In the reference repository `nobukoba/container-artemis-first-trial`, a known successful GitHub Actions build (run `33737118485`, 2026-09-02) took about 2 hours 50 minutes for the job. Use this as a practical baseline: investigate a suspected hang using job timestamps, runner activity, logs, or an actual timeout/failure rather than elapsed time alone.

Support individual manual targets as well as `all`:

```text
all
user-fee
devel-fee
user-daq
devel-daq
user-artemis
devel-artemis
user-full
devel-full
```

Use `latest` and UTC timestamp tags in `YYYYMMDD-HHMMutc` format, following the existing Kobayashi container repositories. Commit-local prerequisite tags used only inside CI are allowed and should be clearly prefixed (for example `ci-...`) so they cannot be confused with published user-facing releases.

## README

Maintain separate image-specific user and devel guides, with matching .ja.md pages and links from the bilingual main READMEs. The legacy user-guide and developer-guide pages are navigation indexes. Runtime procedures belong in the relevant image guides.
Apptainer quick-start headings should say `Linux / Windows WSL2`;
state `64 bit Linux (x86_64)` in the installation sentence and run commands
inside the WSL2 Linux terminal.

The AMANEQ single-channel runtime recipe uses zero-based LR-TDC channel 102
at `192.168.10.16`. The four 32-bit masks are `ffffffff`, `ffffffff`,
`ffffffff`, `ffffffbf`: channel 102 is MZN-D bit 6. Current Str-LRTDC
has 128 inputs; the old extension input was deprecated in firmware v2.6,
so do not write its obsolete register for this recipe. Verify register values
by reading back: pinned hul-common-lib tools can report RBCP errors and still
exit zero. Use NestDAQ AmQStrTdcSampler -> STFBuilder -> TimeFrameBuilder -> FileSink for the one-channel workflow, sharing RARiS common helpers. A FEE-only image is insufficient for acquisition.

Before creating or revising `README.md`, read and follow `nobukoba/nobuyuki-kobayashi-instructions-for-ai`, especially `styles/nobuyuki-kobayashi-github-readme.md`.

Organize the README around what a user actually needs to do. Keep download and run commands copy-pasteable, include concrete URLs and paths, document the container directory structure, and keep documentation consistent with the actual implementation.

When adapting a reference README or reorganizing it, preserve each supported runtime's complete download/pull, startup, workspace-mount, and environment-setup commands. Compare the previous and revised instructions explicitly: an Apptainer section with prose but no executable commands is incomplete. Update repository URLs and paths to the current implementation instead of deleting the examples. Keep both Docker and Apptainer workflows usable independently.

Explicit new corrections from Nobuyuki Kobayashi take precedence over this file and should be incorporated here when they establish a reusable repository rule.

## Reference repositories

Use these existing implementations as references rather than guessing their behavior:

- `nobukoba/container-hul-common-lib-amaneq-soft-first-trial`
- `nobukoba/container-interfacing-nestdaq-eicrecon`
- `nobukoba/container-artemis-first-trial`


## CI lessons from 2026-09-19

- NestDAQ v1.0.0's README has stale redis-plus-plus guidance: it says `1.2.1 (recipes branch)`, while the released NestDAQ source includes `sw/redis++/patterns/redlock.h`. redis-plus-plus renamed `recipes` to `patterns` in October 2022, after the 1.3.5 release; 1.3.6 is the first official release containing and installing the required `patterns/redlock.h`. Do not try to copy that header out of the 1.2.1 tag because it does not exist there. Current containers pin 1.3.15 because the older client setup was associated with LockCatcher `SIGABRT`; smoke tests should verify that DAQ executables resolve redis++ and hiredis from `/opt/spadi/lib`, not from an older system copy.
- An exact ARTEMIS commit SHA is not a branch name. Clone the repository and then `git checkout "$ARTEMIS_REF"`; do not pass an arbitrary SHA to `git clone --branch`.
- The same rule applies to `NESTDAQ_USER_IMPL_REF` when it is pinned to an exact commit: `git clone --branch <sha>` fails with exit 128 because a commit SHA is not a branch/tag. Initialize the checkout, fetch the exact SHA with depth 1, and detach at `FETCH_HEAD`.
- Shared-library smoke tests must only run `ldd` on ELF executables. Executable scripts or other non-ELF files can make `ldd` return nonzero even when no dependency is missing, especially under `set -o pipefail`.

## Startup and repository script layout

Place a short executable Quick start immediately after Image types (イメージの種類).
Include both Apptainer and Docker examples. Keep `--cleanenv` in the Apptainer
Quick start command; explain it in the later Apptainer details section. Interactive startup must load SPADI setup
and enter `/workspace` automatically. Apptainer's default bash uses `--norc`, so
use `--shell /opt/spadi/spadi-shell.sh` rather than relying on a user's bashrc.
The shared wrapper must not perform Docker UID/GID remapping; Apptainer runs as
the host identity. Keep setup itself side-effect free.

Repository shell scripts belong under `scripts/runtime`, `scripts/development`,
`scripts/tests`, or the component directories, not directly under `scripts`.
Keep existing installed helper paths stable through explicit Docker COPY paths.

Keep component build and clone helpers in their respective repository directories
(`scripts/fee`, `scripts/nestdaq`, `scripts/artemis`). Reserve `development/` for
shared workspace helpers. Copy only runtime recipes into user images; component
build/clone helpers are explicitly installed by devel stages.

## NestDAQ live recipe lessons

Do not equate MZN-D mask readback failure with failed unmasking. The official StrLrTdc firmware's pinned strtdc-src revision 71c188a74c93a7d06cb9e803d50360b05495e730 has a duplicated kTdcMaskMznU condition in the local-bus Read branch where kTdcMaskMznD is required; the Write branch correctly handles MZN-D. Hardware identifying as 0x60c4020a acknowledges a channel-102 byte write but reads back 0xff. This is consistent with the firmware readback defect, but does not independently prove the internal mask value. Keep the fail-closed helper check until a corrected firmware or independent acquisition verification establishes the setting. HUL 32-bit registers use four byte transactions at offsets i << 16, not consecutive byte addresses; decode firmware version with that layout.

Runtime preparation must be usable in user images without source/build helpers.
Use spadi-prepare-local.sh in both user and devel images for non-overwriting copies of component recipes; devel images additionally prepare source and build directories.
The live recipe uses a dedicated Valkey port/DB set, refuses to clear an active
registry, and uses SOURCE_MODE=live; replay remains the default for RARiS.
The pinned AmQStrTdcSampler reads case-sensitive msiTcpIp and TdcType parameters
(type 1 for LR). It opens TCP in PreRun and closes it in PostRun. Use common
state control to wait for initialization and start downstream before the source.
Stop source-to-sink and wait for FileSink PostRun before terminating tmux.
Pinned FileSink PostRun discards queued input, and builders may discard incomplete
final frames: graceful shutdown is not proof of a lossless run boundary.

Do not pass an explicit --id to the pinned NestDAQ v1.0.0 DaqServicePlugin:
SetId only initializes fPresence->key inside its automatic service-index branch.
Explicit IDs skip that initialization, undermining peer discovery. Let the plugin
allocate IDs after clearing an inactive dedicated registry, then verify states.

Keep shell scripts LF-terminated with .gitattributes: Windows CRLF or mixed endings break Bash control blocks in WSL2 and Linux containers.

Set enable-uds=false in the live sampler, STFBuilder, TimeFrameBuilder, and
FileSink parameter records. An endpoint hash field alone does not change the
plugin-wide UDS switch. The pinned plugin otherwise concatenates an IPC address
onto an explicit TCP address (for example tcp://127.0.0.1:5599ipc:...), and
Sampler binding fails while downstream initialization waits indefinitely.
FairMQ 1.4.55 publishes the registry state DEVICE READY with a space; normalize
state names before comparing them in shell helpers.

Pinned FileSink HandleMultipartData unconditionally looks up its dqm channel.
For the live multipart recipe, define a PUB bind endpoint with
waitForPeerConnection=false, even without monitor subscribers; otherwise the
first TF throws and only the file header is saved. Check all devices again
after the sampler starts, and fail stopping when a device has disappeared.

Runtime user guides must assume browser-based DAQ operation. AMANEQ run-start.sh
prepares FEE/Valkey/topology and waits for IDLE only; it must not issue Run.
Document browser target selection, run-number Send, and downstream-first Run /
upstream-first Stop. Disable Auto increment at RUN-Stop when stopping services
individually: the pinned page increments the run number on every Stop click.
Turn off Wait Device Ready / Wait Ready for explicit step-by-step transitions.
Normal shutdown uses browser Stop and End followed by run-cleanup.sh.
run-stop.sh is the fallback when browser control is unavailable.

## SPADI-A DAQ manual and tmux operation

Before changing DAQ user procedures, read this file and the official manual:
https://www.rcnp.osaka-u.ac.jp/~spadi/wiki/?SPADI-A%20DAQ%20%E3%83%9E%E3%83%8B%E3%83%A5%E3%82%A2%E3%83%AB
Read Software / DAQ execution, NestDAQ script editing, FEE script editing,
and the replayer tutorial. Follow service/FEE preparation, parameter and
topology registration, process-count/log checks, then browser Init Device
and Connection -> Init Task -> Run, Stop -> Reset Task -> Reset Device,
and End. Use the pinned controller's actual state labels (Device Ready,
Ready, Running), correcting outdated labels in prose rather than copying them.
Keep init.sh, mq-param.sh, topology.sh, start_device.sh, and tf.sh responsibilities
recognizable through a documented mapping to shared container helpers.

Replace xterm wrappers with one named tmux session per recipe, a webctl window,
a control shell, and one named window per DAQ process. No xterm, X11, or DISPLAY
is required. Document attach, window navigation, scrollback, detach, log and
process-count checks, and final browser End / recipe-only cleanup. Do not change
global tmux key bindings or use killall/pkill to stop other experiments.
Valkey is the managed background service; its log can be inspected from control.

Manual examples are historical: LR TdcType=6 is dated June 2024, while the pinned
AmQStrTdcSampler accepts LR=1. Check exact upstream code before copying values.
The deprecated LR extension-mask register must not be restored from old samples.
Document only the FEE initialization required by the selected standalone LR mode;
do not copy HR mezzanine initialization or MIKUMARI-primary operations blindly.
Use "four software processes" for the single-board pipeline, never "four boards".
Capture reusable corrections and runtime findings here in the same change.

Document directory creation stages: spadi-prepare-local.sh creates scripts/rawdata in user images and additionally source/build directories in devel images
and preserves existing configs; live run-start.sh creates the FileSink output
subdirectory; browser FileSink Run creates the data file. These are distinct
stages, and the host bind-mounted workspace retains their results.

Start user guides with the directory tree, then define SPADI_LOCAL/SPADI_ROOT
before using variable-based commands. Explain the default /workspace/spadi,
shell dollar expansion, automatic startup assignment versus directory creation,
and the bind mount mapping to the persistent host workspace/spadi.

Place the mapping to the official SPADI-A DAQ manual at the end of user guides
as "Appendix: SPADI-A DAQ マニュアルとの対応" and its English counterpart,
keeping directory layout and user operation instructions first.

Use the LR-TDC-specific `${SPADI_ROOT}/bin/StrLRTDC/set_tdcmask` for AMANEQ LR mask settings, with IP and four mask arguments. Do not replace it with four generic write_register calls. HR installs a command with the same basename; select the LR path explicitly. Retain read_register verification and fail-closed handling of firmware readback defects.

## Per-image bilingual documentation

Maintain eight image-specific guides under docs/spadi-{user,devel}-{fee,daq,artemis,full}-guide.md and matching .ja.md files. Each guide must contain substantive procedures for its actual components, start with the relevant directory tree, and explain when those directories are created. Centralize shared startup, environment variables, workspace preparation, persistence, updates, networking, and image metadata in the bilingual main READMEs. Keep the relevant directory tree in every guide even when it repeats the common layout. User/developer landing pages are indexes; container-maintainer documentation remains separate. Preserve the complete browser/tmux DAQ procedures and put the SPADI-A DAQ manual mapping appendix last. Do not invent ARTEMIS steering or claim FileSink data is directly readable by ROOT.

Guide-navigation tables must link only to the page language: English pages list English guides, and Japanese pages list Japanese guides. Do not duplicate English/Japanese guide columns; retain a single language-switch link at the page top. Place shared Docker network options within Docker startup/details, and keep browser workflow, URLs, and board-specific networking in the relevant DAQ/FULL guides rather than a disconnected README browser/network section.

## ROOT compression smoke-test compatibility

For pinned ROOT v6-32-06, include `Compression.h`: `ROOT/RCompressionSetting.hxx` does not exist. `ROOT::RCompressionSetting::EAlgorithm` is a struct containing the `EValues` enum, so compression algorithm arrays must store `EAlgorithm::EValues`. Keep ARTEMIS and FULL smoke macros consistent and validate compressed TTree write/read with ZLIB, LZMA, LZ4, and ZSTD in the actual runtime image. A smoke-test compilation failure after a successful image build is not a reason to change pinned dependency versions.

Keep each image guide self-contained for downloads: include its exact SIF release URL and Docker pull command (with `--platform linux/amd64`) in both languages, even though the README repeats them. Place the SPADI_LOCAL/SPADI_ROOT environment explanation inside the directory-structure section, rather than under a separate top-level heading. Download commands run on the host; image-specific runtime commands run inside the container.

## Unified local preparation and startup documentation

All eight image variants expose `spadi-prepare-local.sh` as the single user-facing workspace preparation command. User images copy only runtime recipes and rawdata directories; devel images additionally copy source trees, build helpers, and local build/install directories. Never overwrite existing user files. Keep the download and startup commands together under separate Apptainer and Docker subsections in each image guide, in English and Japanese. DAQ and FULL Docker examples must retain `--network host`; do not replace it with bridge networking or suggest `-p` for host networking. Version metadata and CI checks remain required, but do not instruct users to run version checks immediately after entering the container.

## TDC utility layout and DAQ initialization separation

Install LR-TDC executables under `/opt/spadi/bin/StrLRTDC/` and HR-TDC executables under `/opt/spadi/bin/StrHRTDC/`, keeping identically named commands separate. Do not create compatibility symbolic links or legacy executable directories. Apply the same bin/<firmware> layout to local AMANEQ rebuilds and verify it in Docker and SIF smoke tests. The AMANEQ live NestDAQ recipe separates `fee-setup.sh` (FEE configuration) from `initialize.sh` (Valkey, parameters, topology, process initialization); `run-start.sh` calls them in order. DAQ initialization alone must not change FEE registers or masks. Keep smoke tests and both language guides aligned with this layout.

## Shared interactive Bash prompt

Docker and Apptainer use `/opt/spadi/spadi-shell.sh` with `--noprofile`
and the container-owned `/opt/spadi/spadi-bashrc.sh` as the only interactive
rc file. Never source the host bashrc or profile. Keep the prompt format
`spadi@user-daq:/workspace$` (and corresponding image labels): username/image
in bold green, working directory in bold blue, and `$` in the default color,
without Git branch information. Use `ls --color=auto`. Set `SPADI_PROMPT_NAME`
explicitly in each final image stage, including FULL, rather than deriving it
from the host identity or prerequisite image metadata. Apptainer retains the
host UID/GID even though the display name is `spadi`. Noninteractive commands
must keep argument forwarding and exit status and must not load interactive aliases.

Apptainer shell CI pipes commands without a TTY. Bash does not infer interactive
mode from the `shell` operation: without `-i`, the dedicated rc file is skipped
and PS1 is unset. The shared wrapper must explicitly select `-i` when invoked
without arguments, while preserving explicit arguments such as `-c` unchanged.
Keep a piped-stdin/no-argument regression test and assert the Bash interactive
flag before checking the prompt; a terminal-only test misses this failure.

Prefix the prompt with `[Apptainer]` or `[Docker]` in the default terminal
color, retaining the green username/image, blue working directory, default
colon and dollar sign, and no Git branch. Detect Apptainer from its runtime-set
`APPTAINER_CONTAINER` (available with `--cleanenv`), not `/.dockerenv`: a SIF
converted from Docker can retain Docker filesystem markers. The default for
these Docker/SIF images is Docker. CI must assert the expected runtime label
independently in both the real Docker and clean-environment Apptainer routes.
