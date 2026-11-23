FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    llvm \
    gdb \
    strace \
    ltrace \
    binutils \
    file \
    patchelf \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    ca-certificates \
    pkg-config \
    libssl-dev \
    afl++ \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /workspace
CMD ["/bin/bash"]
