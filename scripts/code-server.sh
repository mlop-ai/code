#!/bin/bash

cd $(dirname $0)
WORKDIR="$(realpath .)/.ci"
mkdir -p $WORKDIR
cd $WORKDIR

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

cp ../settings.json ../entrypoint.sh ../utils.sh .
DOCKER_BUILDKIT=1 docker build -t mlop-code-server:latest -f ../Dockerfile .
# docker container prune -f; docker builder prune -a