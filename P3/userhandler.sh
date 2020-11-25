#!/bin/bash

if [ $1 = "add" ]; then
    sudo useradd -m tmp
    sudo echo "tmp:tmp" | sudo chpasswd
    sudo usermod -s /bin/bash tmp
    dir=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
    tmp="cd ${dir}"
    sudo echo "${tmp}" >> /home/tmp/.bashrc
fi

if [ $1 = "del" ]; then
    sudo userdel -r tmp
fi
