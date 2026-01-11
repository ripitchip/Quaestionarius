FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

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
    dbus \
    dbus-x11 \
    git \
    curl \
    wget \
    unzip \
    xz-utils \
    clang \
    cmake \
    ninja-build \
    pkg-config \
    libgtk-3-dev \
    git \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash vscode && \
    chown -R vscode:vscode /app && \
    mkdir -p /run/user/1000 && \
    chown vscode:vscode /run/user/1000 && \
    chmod 700 /run/user/1000

USER vscode

# Add user's local bin to PATH and set XDG_RUNTIME_DIR
ENV PATH="/home/vscode/.local/bin:${PATH}"
ENV XDG_RUNTIME_DIR="/run/user/1000"
ENV DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"


# Keep container alive for exec / debugging
CMD ["tail", "-f", "/dev/null"]
