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
RUN pip install --no-cache-dir appdirs oceanum "rompy>=v0.2.4"

# Copy the local rompy-oceanum source code
COPY . /app/rompy-oceanum

# Install rompy-oceanum from the local source code
WORKDIR /app/rompy-oceanum
RUN pip install -e .
WORKDIR /app

