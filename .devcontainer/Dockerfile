FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libgl1 \
    libegl1 \
    libgles2 \
    libglx0 \
    libgl1-mesa-dri \
    libx11-6 \
    libxkbcommon0 \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    gstreamer1.0-plugins-good \
    libmpv-dev \
    libxcb1 \
    libxdmcp6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep container alive for exec / debugging
CMD ["tail", "-f", "/dev/null"]
