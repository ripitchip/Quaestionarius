# 1. Base Image
FROM mcr.microsoft.com/devcontainers/base:debian-12

# 2. Set Environment Variables
ENV SHELL=/bin/zsh
ENV XDG_RUNTIME_DIR=/run/user/1000
ENV GDK_BACKEND=x11

# 3. Install System Dependencies (Added python3-pip)
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        libglib2.0-dev \
        libgtk-3-dev \
        libwebkit2gtk-4.1-dev \
        libayatana-appindicator3-dev \
        librsvg2-dev \
        libssl-dev \
        curl \
        wget \
        build-essential \
        python3-full \
        python3-dev \
        python3-pip \
        libpython3.11-dev \
        x11-apps \
        mesa-utils \
        sudo \
        xdg-utils \
        libfuse2 \
        file \
        appstream \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Install Node.js (v20)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm

# 5. Setup Python Tools (Now pip will be found)
RUN python3 -m pip install --upgrade pip --break-system-packages \
    && python3 -m pip install pyinstaller google-api-python-client google-auth-oauthlib --break-system-packages

# 6. Install Rust (for user vscode)
USER vscode
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/vscode/.cargo/bin:${PATH}"

# 7. Setup Zsh Plugins
RUN git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting \
    && git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions \
    && sed -i 's/plugins=(git)/plugins=(git zsh-syntax-highlighting zsh-autosuggestions)/' ~/.zshrc

# 8. Create Build Helper Script & Prepare Directories
USER root
RUN mkdir -p /run/user/1000 && chown -R vscode:vscode /run/user/1000 && chmod 700 /run/user/1000

RUN echo '#!/bin/bash\n\
/usr/bin/python3 -m PyInstaller --onefile --noconsole --clean src-python/main.py\n\
TRIPLE=$(rustc -Vv | grep host | cut -d " " -f 2)\n\
if [ -f "dist/main" ]; then\n\
    mkdir -p src-tauri/binaries\n\
    mv dist/main "src-tauri/binaries/backend-$TRIPLE"\n\
    echo "Done: backend-$TRIPLE created."\n\
else\n\
    echo "Error: dist/main not found."\n\
fi' > /usr/local/bin/build-backend && chmod +x /usr/local/bin/build-backend

USER vscode