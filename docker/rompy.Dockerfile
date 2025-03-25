FROM python:3.10-slim

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
# RUN pip install --no-cache-dir appdirs oceanum "rompy>=v0.2.3"
RUN pip install --no-cache-dir appdirs oceanum git+https://github.com/rom-py/rompy.git@time_perid_fix

