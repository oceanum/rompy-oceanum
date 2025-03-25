
FROM ubuntu:20.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV SWAN_VERSION=4141
ENV INSTALL_DIR=/usr/local

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    wget \
    make \
    cmake \
    unzip \
    libnetcdf-dev \
    libnetcdff-dev \
    libopenmpi-dev \
    git \
    patch \
    ninja-build \
    autoconf \
    automake \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

RUN git clone --depth 1 https://gitlab.tudelft.nl/citg/wavemodels/swan.git  && \
    cd swan && \
    mkdir build && \
    cd build && \
    cmake .. -GNinja -DNETCDF=ON -DMPI=ON -DCMAKE_Fortran_COMPILER=mpif90 && \
    cmake --build . && \
    cmake --install . --prefix $INSTALL_DIR && \
    cd ../../ && \
    rm -rf $BUILD_DIR/swan

# Command to run when container starts (can be overridden)
CMD ["swan.exe"]
