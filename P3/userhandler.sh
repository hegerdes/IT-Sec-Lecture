#!/bin/bash

if [ $1 = "add" ]; then
    sudo useradd -m tmp
    sudo echo "tmp:tmp" | sudo chpasswd
    sudo usermod -s /bin/bash tmp
    dir=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
    sudo cp trusted_log_server.py /home/tmp/
    sudo chown tmp /home/tmp/trusted_log_server.py
    cd /home/tmp
    mkdir .gnupg
    sudo chown tmp .gnupg
    sudo mkdir tmp_home
    sudo chown tmp tmp_home
    # su - tmp
    #gpg-connect-agent /bye
    tmp="cd ${dir}"
    #sudo echo "${tmp}" >> /home/tmp/.bashrc
fi

if [ $1 = "del" ]; then
    sudo killall -u tmp
    sudo userdel -r -f tmp
fi
