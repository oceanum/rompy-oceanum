FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    build-essential \
    libnetcdf-dev \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir appdirs oceanum rompy

# # Copy the local rompy-oceanum source code
# COPY . /app/rompy-oceanum
#
# # Install rompy-oceanum from the local source code
# WORKDIR /app/rompy-oceanum
# RUN pip install -e .
RUN pip install rompy-oceanum==0.1.11


WORKDIR /app

