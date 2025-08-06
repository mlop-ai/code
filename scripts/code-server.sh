#!/bin/bash
WORKDIR="$(realpath $(dirname $0))/.ci"
mkdir -p $WORKDIR; cd $WORKDIR

export VERSION=$(curl -s https://api.github.com/repos/coder/code-server/releases/latest | grep -Po '"tag_name": "v\K[^"]*')
wget "https://github.com/coder/code-server/releases/download/v${VERSION}/code-server_${VERSION}_$(dpkg --print-architecture).deb"
fakeroot sh -c '
mkdir .work
dpkg-deb -R code-server_*.deb .work
rm -rf .work/DEBIAN/conffiles
wget https://github.com/mlop-ai/mlop/raw/refs/heads/main/design/favicon.ico -O .work/usr/lib/code-server/src/browser/media/favicon.ico
wget https://github.com/mlop-ai/mlop/raw/refs/heads/main/design/favicon.svg -O .work/usr/lib/code-server/src/browser/media/favicon.svg
wget https://github.com/microsoft/vscode/raw/refs/heads/main/resources/server/code-192.png -O .work/usr/lib/code-server/src/browser/media/pwa-icon-192.png
wget https://github.com/microsoft/vscode/raw/refs/heads/main/resources/server/code-512.png -O .work/usr/lib/code-server/src/browser/media/pwa-icon-512.png
sed -i 's/{{app}}/mlop/g' .work/usr/lib/code-server/out/node/i18n/locales/en.json
dpkg-deb -b .work code-server_${VERSION}_$(dpkg --print-architecture).deb
'

cp ../settings.json ../entrypoint.sh .
sudo DOCKER_BUILDKIT=1 docker build -t mlop-code-server:latest -f ../Dockerfile .
# sudo docker container prune -f; sudo docker builder prune -a
sudo docker run \
  --read-only --rm --cap-drop=all \
  --security-opt=no-new-privileges \
  --network=traefik -e AUTHORIZED_KEYS="nope" \
  --tmpfs /home/mlop:rw,exec,mode=0775,uid=1000,gid=1000 \
  --tmpfs /home/linuxbrew:rw,exec,mode=0775,uid=1000,gid=1000 \
  --tmpfs /tmp:rw,exec,mode=0775,uid=1000,gid=1000 \
  --entrypoint /bin/sh \
  mlop-code-server:latest \
  -c 'mkdir -p /home/mlop/ && curl -o /home/mlop/README.md https://raw.githubusercontent.com/microsoft/vscode/refs/heads/main/SECURITY.md && exec /usr/bin/entrypoint.sh --bind-addr 0.0.0.0:8080 . --disable-telemetry --auth none'
