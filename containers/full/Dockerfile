# syntax=docker/dockerfile:1

ARG DAQ_DEVEL_IMAGE=ghcr.io/nobukoba/spadi-containers-first-trial/spadi-devel-daq:latest
ARG DAQ_USER_IMAGE=ghcr.io/nobukoba/spadi-containers-first-trial/spadi-user-daq:latest
ARG ARTEMIS_DEVEL_IMAGE=ghcr.io/nobukoba/spadi-containers-first-trial/spadi-devel-artemis:latest

FROM ${ARTEMIS_DEVEL_IMAGE} AS artemis-devel-files
FROM ${DAQ_DEVEL_IMAGE} AS devel-full

ARG NPROC=4

ENV SPADI_ROOT=/opt/spadi
ENV ROOTSYS=/opt/spadi
ENV ARTEMIS_ROOT=/opt/spadi
ENV TARTSYS=/opt/spadi
ENV SPADI_IMAGE_KIND=devel
ENV SPADI_PROMPT_NAME=devel-full
ENV EXP_CONFIG_ROOT=/opt/spadi/scripts/exp-config
ENV PATH=/opt/spadi/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/spadi/lib:/opt/spadi/lib64
ENV CMAKE_PREFIX_PATH=/opt/spadi
ENV PKG_CONFIG_PATH=/opt/spadi/lib/pkgconfig:/opt/spadi/lib64/pkgconfig
ENV CFLAGS="-O2 -march=x86-64 -mtune=generic -mno-avx -mno-avx2"
ENV CXXFLAGS="-O2 -march=x86-64 -mtune=generic -mno-avx -mno-avx2"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Merge the ARTEMIS/ROOT installation and source trees into the already
# validated DAQ development image. Both stacks intentionally share /opt/spadi.
COPY --from=artemis-devel-files /opt/spadi/ /opt/spadi/

# ARTEMIS/ROOT development dependencies such as giflib-devel are provided by
# AlmaLinux 9 CRB. Enable the same repository used by the canonical ARTEMIS
# build before installing the FULL development dependencies.
RUN dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf -y install \
      libX11-devel libXext-devel libXft-devel libXpm-devel libXrender-devel \
      libjpeg-turbo-devel libpng-devel freetype-devel giflib-devel \
      mesa-libGL-devel mesa-libGLU-devel openmpi openmpi-devel && \
    dnf clean all && rm -rf /var/cache/dnf

# DAQ-only disables the ROOT-dependent TriggerView target. FULL restores the
# upstream CMakeLists and reapplies only the generic-CPU and target-order fixes,
# then rebuilds nestdaq-user-impl against ROOT in the unified prefix.
RUN cd /opt/spadi/src/nestdaq-user-impl && \
    git checkout -- CMakeLists.txt && \
    python3 - <<'PY'
from pathlib import Path
p = Path('/opt/spadi/src/nestdaq-user-impl/CMakeLists.txt')
s = p.read_text()
s = s.replace('set(CMAKE_CXX_FLAGS_RELEASE "-Ofast -DNDEBUG -march=native")',
              'set(CMAKE_CXX_FLAGS_RELEASE "-Ofast -DNDEBUG -march=x86-64 -mtune=generic -mno-avx -mno-avx2 -fpermissive")')
s = s.replace('  target_include_directories(${EXEC} PUBLIC \n',
              '  target_include_directories(${EXEC} PUBLIC \n    ${CMAKE_INSTALL_PREFIX}/include;\n', 1)
for subdir in ('utility', 'emulator', 'sqlite'):
    s = s.replace(f'add_subdirectory({subdir})\n', '')
marker = '#==============================================================================\n# Sampler(for Emulator), Sink, FileSink, STFBuilder, TimeFrameBuilder\n'
if marker not in s:
    raise RuntimeError('nestdaq-user-impl executable marker not found')
s = s.replace(marker,
              '#==============================================================================\n'
              '# Internal libraries must exist before executables link to them.\n'
              'add_subdirectory(utility)\n'
              'add_subdirectory(emulator)\n'
              'add_subdirectory(sqlite)\n\n'
              + marker,
              1)
p.write_text(s)

# Upstream TriggerView installs into ${CMAKE_SOURCE_DIR}/bin, which leaves the
# executable under the source tree and drops it from the runtime image. Install
# it into the configured prefix like the other DAQ executables.
trigger = Path('/opt/spadi/src/nestdaq-user-impl/TriggerView/CMakeLists.txt')
t = trigger.read_text()
old_bindir = 'set(INSTALL_BINDIR ${CMAKE_SOURCE_DIR}/bin)'
if old_bindir not in t:
    raise RuntimeError('TriggerView install bindir marker not found')
trigger.write_text(t.replace(old_bindir,
                             'set(INSTALL_BINDIR ${CMAKE_INSTALL_BINDIR})',
                             1))
PY

RUN rm -rf /opt/spadi/src/nestdaq-user-impl/build && \
    ! grep -R --line-number -- '-march=native' /opt/spadi/src/nestdaq-user-impl/CMakeLists.txt && \
    cmake -S /opt/spadi/src/nestdaq-user-impl \
      -B /opt/spadi/src/nestdaq-user-impl/build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/spadi \
      -DCMAKE_INSTALL_LIBDIR=lib \
      -DCMAKE_PREFIX_PATH="/opt/spadi;/opt/spadi/src/uhbook" \
      -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
      -DCMAKE_CXX_STANDARD=17 && \
    cmake --build /opt/spadi/src/nestdaq-user-impl/build -j${NPROC} --verbose && \
    cmake --install /opt/spadi/src/nestdaq-user-impl/build

RUN printf '%s\n' '/opt/spadi/lib' '/opt/spadi/lib64' > /etc/ld.so.conf.d/spadi.conf && ldconfig

# Keep retained development sources clean. Interactive rebuilds use
# /workspace/spadi/build rather than container-build directories in source.
RUN find /opt/spadi/src -type d -name build -prune -exec rm -rf '{}' + && \
    rm -rf /opt/spadi/src/root-build

COPY scripts/tests/smoke-test-full.sh /opt/spadi/scripts/smoke-test-full.sh
RUN chmod 0755 /opt/spadi/scripts/smoke-test-full.sh

WORKDIR /workspace
CMD ["/opt/spadi/spadi-shell.sh"]

FROM devel-full AS full-runtime-files
# ROOT/Cling needs the installed headers, including ROOT.modulemap, at runtime.
# Remove source trees from the user image, but keep /opt/spadi/include.
RUN rm -rf /opt/spadi/src

FROM ${DAQ_USER_IMAGE} AS user-full

ENV SPADI_ROOT=/opt/spadi
ENV ROOTSYS=/opt/spadi
ENV ARTEMIS_ROOT=/opt/spadi
ENV TARTSYS=/opt/spadi
ENV SPADI_IMAGE_KIND=user
ENV SPADI_PROMPT_NAME=user-full
ENV EXP_CONFIG_ROOT=/opt/spadi/scripts/exp-config
ENV PATH=/opt/spadi/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/spadi/lib:/opt/spadi/lib64
ENV CMAKE_PREFIX_PATH=/opt/spadi
ENV PKG_CONFIG_PATH=/opt/spadi/lib/pkgconfig:/opt/spadi/lib64/pkgconfig

RUN dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf -y install \
      gcc-c++ \
      libX11 libXext libXft libXpm libXrender \
      libjpeg-turbo libpng freetype giflib \
      mesa-libGL mesa-libGLU openmpi && \
    dnf clean all && rm -rf /var/cache/dnf

# Copy the fully merged/rebuilt prefix from the development stage. This keeps
# user-full functionally identical while excluding source and unrelated build files.
COPY --from=full-runtime-files /opt/spadi/ /opt/spadi/

RUN mkdir -p /workspace && chmod 1777 /workspace && \
    printf '%s\n' '/opt/spadi/lib' '/opt/spadi/lib64' > /etc/ld.so.conf.d/spadi.conf && \
    ldconfig

WORKDIR /workspace
CMD ["/opt/spadi/spadi-shell.sh"]
