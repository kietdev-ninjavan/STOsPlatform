# Use an official Python runtime as a parent image
FROM python:3.11.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Set environment variables
# Project
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV TIME_ZONE=Asia/Ho_Chi_Minh
ENV USE_TZ=False

# Logging
ENV LOGGING_LEVEL=DEBUG

# Allowed hosts
ENV ALLOWED_HOSTS=*

# Copy the current directory contents into the container
COPY . /app/


