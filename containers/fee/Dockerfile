# syntax=docker/dockerfile:1

FROM almalinux:9 AS fee-build

ARG NPROC=4
ARG HUL_COMMON_LIB_REF=65476509aa401aad10148ec7c2d2a50ba7d2db3e
ARG AMANEQ_SOFT_REF=86fef97ccc4e6488739e2d8b549a1c5bddd3542e
ARG OPENFPGALOADER_REF=24e46d13bb8f2bc9371e9ca8443ece2fafc4b20d
ARG SITCP_IP_UTILITY_REF=75353888d15381bb03ce5bfea410851a832ef9a7

ENV SPADI_ROOT=/opt/spadi
ENV PATH=/opt/spadi/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/spadi/lib:/opt/spadi/lib64
ENV CMAKE_PREFIX_PATH=/opt/spadi
ENV PKG_CONFIG_PATH=/opt/spadi/lib/pkgconfig:/opt/spadi/lib64/pkgconfig
ENV CFLAGS="-O2 -march=x86-64 -mtune=generic"
ENV CXXFLAGS="-O2 -march=x86-64 -mtune=generic"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN dnf -y update && \
    dnf -y install epel-release && \
    dnf -y install \
      gcc gcc-c++ make cmake git pkgconf-pkg-config \
      libftdi-devel libusbx-devel hidapi-devel libgpiod-devel systemd-devel zlib-devel \
      iproute iputils net-tools bind-utils traceroute tcpdump nmap-ncat \
      curl-minimal wget procps-ng psmisc lsof which less vim-minimal findutils tar gzip \
      binutils file && \
    dnf clean all && rm -rf /var/cache/dnf

RUN mkdir -p \
      /opt/spadi/bin \
      /opt/spadi/lib \
      /opt/spadi/lib64 \
      /opt/spadi/include \
      /opt/spadi/share \
      /opt/spadi/etc \
      /opt/spadi/src \
      /opt/spadi/scripts/local \
      /workspace && \
    chmod 1777 /workspace

WORKDIR /opt/spadi/src

RUN git clone https://github.com/spadi-alliance/hul-common-lib.git hul-common-lib && \
    cd hul-common-lib && \
    git checkout "${HUL_COMMON_LIB_REF}" && \
    cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/spadi \
      -DCMAKE_C_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" \
      -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" && \
    cmake --build build -j"${NPROC}" && \
    cmake --install build

RUN git clone https://github.com/spadi-alliance/amaneq-soft.git amaneq-soft && \
    cd amaneq-soft && \
    git checkout "${AMANEQ_SOFT_REF}" && \
    cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/spadi \
      -DCMAKE_PREFIX_PATH=/opt/spadi \
      -DCMAKE_C_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" \
      -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" && \
    cmake --build build -j"${NPROC}" && \
    cmake --install build

RUN git clone https://github.com/trabucayre/openFPGALoader.git openFPGALoader && \
    cd openFPGALoader && \
    git checkout "${OPENFPGALOADER_REF}" && \
    cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/spadi \
      -DCMAKE_C_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" \
      -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG -march=x86-64 -mtune=generic" && \
    cmake --build build -j"${NPROC}" && \
    cmake --install build

# The pinned SiTCP utility revision declares a C++11 baseline in its Makefile,
# but currently uses language/library behavior that requires C++17. Keep the
# dependency build reproducible here while retaining generic x86-64 CPU flags.
RUN git clone https://github.com/nobukoba/sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial.git \
      sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial && \
    cd sitcp-sitcpxg-mpc-mpcx-ip-utility-first-trial && \
    git checkout "${SITCP_IP_UTILITY_REF}" && \
    make -j"${NPROC}" CXXFLAGS="-O2 -std=c++17 -Wall -Wextra -Wpedantic -march=x86-64 -mtune=generic" && \
    make PREFIX=/opt/spadi install

RUN printf '%s\n' '/opt/spadi/lib' '/opt/spadi/lib64' > /etc/ld.so.conf.d/spadi.conf && ldconfig

COPY scripts/spadi-setup.sh /opt/spadi/spadi-setup.sh
COPY scripts/smoke-test-fee.sh /opt/spadi/scripts/smoke-test-fee.sh
RUN chmod 0755 /opt/spadi/spadi-setup.sh /opt/spadi/scripts/smoke-test-fee.sh

WORKDIR /workspace

FROM fee-build AS devel-fee
RUN find /opt/spadi/src -type d -name build -prune -exec rm -rf '{}' + && rm -rf /opt/spadi/src/root-build
COPY scripts/spadi-prepare-local.sh scripts/spadi-env.sh /opt/spadi/scripts/
COPY scripts/hul-common-lib-build.sh scripts/amaneq-build.sh /opt/spadi/scripts/
COPY scripts/openfpgaloader-build.sh scripts/sitcp-utility-build.sh /opt/spadi/scripts/
COPY scripts/hul-common-lib-clone-latest.sh scripts/amaneq-clone-latest.sh /opt/spadi/scripts/
COPY scripts/openfpgaloader-clone-latest.sh scripts/sitcp-utility-clone-latest.sh /opt/spadi/scripts/
RUN chmod 0755 /opt/spadi/scripts/*.sh

ENV SPADI_IMAGE_KIND=devel
CMD ["/bin/bash"]

FROM fee-build AS fee-runtime-files

RUN rm -rf /opt/spadi/src && \
    rm -rf /opt/spadi/include && \
    find /opt/spadi -type d -name CMakeFiles -prune -exec rm -rf '{}' + || true

FROM almalinux:9 AS user-fee

ENV SPADI_ROOT=/opt/spadi
ENV SPADI_IMAGE_KIND=user
ENV PATH=/opt/spadi/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LD_LIBRARY_PATH=/opt/spadi/lib:/opt/spadi/lib64
ENV CMAKE_PREFIX_PATH=/opt/spadi
ENV PKG_CONFIG_PATH=/opt/spadi/lib/pkgconfig:/opt/spadi/lib64/pkgconfig

RUN dnf -y update && \
    dnf -y install epel-release && \
    dnf -y install \
      iproute iputils net-tools bind-utils traceroute tcpdump nmap-ncat \
      curl-minimal wget procps-ng psmisc lsof which less vim-minimal findutils tar gzip \
      libftdi libusbx hidapi libgpiod systemd-libs zlib && \
    dnf clean all && rm -rf /var/cache/dnf

COPY --from=fee-runtime-files /opt/spadi /opt/spadi

RUN mkdir -p /workspace && chmod 1777 /workspace && \
    printf '%s\n' '/opt/spadi/lib' '/opt/spadi/lib64' > /etc/ld.so.conf.d/spadi.conf && \
    ldconfig

WORKDIR /workspace
CMD ["/bin/bash"]
