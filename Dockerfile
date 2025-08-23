# ------------------------------------------------------------------------------
#                        __   _____                  __ 
#      ____  ___  ____ _/ /__/ ___/_________  __  __/ /_
#     / __ \/ _ \/ __ `/ //_/\__ \/ ___/ __ \/ / / / __/
#    / /_/ /  __/ /_/ / ,<  ___/ / /__/ /_/ / /_/ / /_  
#   / .___/\___/\__,_/_/|_|/____/\___/\____/\__,_/\__/  
#  /_/                                                  
#
# Copyrigh 2025 GNU AFFERO GENERAL PUBLIC LICENSE
# Alexander L. Lin, Lana A. Cartailler, Jean-Philippe Cartailler
# https://github.com/vandydata/peakScout
# 
# ------------------------------------------------------------------------------

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ .

# Make peakScout executable
RUN chmod +x peakScout

# Add peakScout to PATH
ENV PATH="/app:${PATH}"

# Create directories for data
RUN mkdir -p /data/input /data/output /data/reference

# Set volumes for data persistence
VOLUME ["/data"]

# Default command
CMD ["peakScout", "--help"]