FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    build-essential \
    libnetcdf-dev \
    libexpat1 \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    proj-bin \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV GDAL_VERSION=$(gdal-config --version) \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Install Python dependencies in one layer to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir appdirs numpy wheel setuptools && \
    pip install --no-cache-dir GDAL==${GDAL_VERSION} && \
    pip install --no-cache-dir rasterio && \
    pip install --no-cache-dir oceanum rompy

# Copy the local rompy-oceanum source code
COPY . /app/rompy-oceanum

# # install required rompy branch from git
# WORKDIR /app
# RUN git clone https://github.com/rom-py/rompy.git && \
#     cd rompy && git checkout 162-run-and-postprocess-plugin-framework && pip install -e .

# Install rompy-oceanum from the local source code
WORKDIR /app/rompy-oceanum
RUN pip install -e .
WORKDIR /app
