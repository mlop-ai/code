#!/bin/sh
set -eu
if [ -d "${ENTRYPOINTD}" ]; then
  find "${ENTRYPOINTD}" -type f -executable -print -exec {} \;
fi

# sshd
ssh_dir=/home/mlop/.ssh; mkdir -p ${ssh_dir}
ssh-keygen -t ed25519 -f ${ssh_dir}/ssh_host_ed25519_key -N ""
# sed -i "1s|^|HostKey ${ssh_dir}/ssh_host_ed25519_key\n|" ${ssh_dir}/sshd_config
echo $AUTHORIZED_KEYS > ${ssh_dir}/authorized_keys
chmod 600 ${ssh_dir}/authorized_keys; chmod 700 ${ssh_dir}
$(which sshd) -4Def /dev/null -h ${ssh_dir}/ssh_host_ed25519_key -o"PidFile ${ssh_dir}/sshd.pid" \
  -o'ListenAddress 0.0.0.0:2222' -o'PermitRootLogin no' -o'LoginGraceTime 60' \
  -o'PasswordAuthentication no' -o'PubkeyAuthentication yes' -o'KbdInteractiveAuthentication no' \
  -o'Subsystem sftp /usr/lib/ssh/sftp-server' -o'PrintLastLog no' &

. /usr/bin/utils.sh; transfer "cp -a" "/home/linuxbrew/.*" "/home/mlop/"
exec dumb-init /usr/bin/code-server "$@"