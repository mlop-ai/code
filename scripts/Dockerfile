# code-server/blob/main/ci/release-image/Dockerfile

ARG BASE=debian:stable-slim
FROM scratch AS packages
COPY code-server*.deb /tmp/

FROM $BASE
# RUN sed -i -e 's/^Components: main$/Components: main contrib non-free non-free-firmware/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update \
  && apt-get install -y \
    curl dumb-init git git-lfs locales lsb-release man-db nano procps build-essential \
  && git lfs install \
  && rm -rf /var/lib/apt/lists/*
# RUN apt-get install -y sudo nvidia-smi nvidia-driver nvidia-cuda-toolkit openssh-client openssh-server 

RUN sed -i "s/# en_US.UTF-8/en_US.UTF-8/" /etc/locale.gen \
  && locale-gen
ENV LANG=en_US.UTF-8

RUN if grep -q 1000 /etc/passwd; then userdel -r "$(id -un 1000)"; fi \
  && adduser --gecos '' --disabled-password mlop
# && echo "mlop ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nopasswd

COPY entrypoint.sh /usr/bin/
RUN --mount=from=packages,src=/tmp,dst=/tmp/packages dpkg -i /tmp/packages/code-server*$(dpkg --print-architecture).deb

COPY settings.json /home/mlop/.local/share/code-server/User/settings.json
RUN mkdir -p /home.bak /home/linuxbrew/.linuxbrew \
  && chown -R mlop:mlop /home.bak/ /home/

ENV ENTRYPOINTD=${HOME}/entrypoint.d
EXPOSE 8080
USER 1000
ENV USER=mlop
WORKDIR /home/mlop

RUN NONINTERACTIVE=1 bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
  && echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/mlop/.bashrc
# RUN for EXTENSION in "ms-python.python" "ms-toolsai.jupyter" "ms-vscode.makefile-tools" "ms-vscode.vscode-typescript-next" "charliermarsh.ruff" "redhat.vscode-yaml" "rust-lang.rust-analyzer"; do \
#     code-server --install-extension $EXTENSION ; \
#   done

RUN mv /home/* /home.bak/ 
ENTRYPOINT ["/usr/bin/entrypoint.sh", "--bind-addr", "0.0.0.0:8080", "."]
