#!/usr/bin/env bash

user=$(whoami)

if [[ "$user" != "root" ]]; then
    echo "ax.wiki Tunnel Manager can only installed or executed under root user." >&2
    exit 1
fi

echo "Thanks for using ax.wiki Tunnel Manager (AXTM). Starting installation..."

deppy=$(dpkg -l | grep -c python3-pip)

echo "Installing bridge utilities and iproute2..."
apt install bridge-utils iproute2 -y

if [[ "$deppy" -eq "0" ]]; then
  echo "Python 3 is not installed. Installing..."
  apt update -y --fix-missing && apt install python3 python3-pip -y
fi

if [[ -d "/etc/systemd/system" ]]; then
  cp -r axtm.service /etc/systemd/system
  chmod a+x /etc/systemd/system/axtm.service
  systemctl daemon-reload && systemctl enable axtm
  echo "axtm service is installed and enabled."
else
  echo "Your system is not supported to run axtm as service. Skipping service installation..."
fi

if [[ ! -d "/opt/axtm" ]]; then
  mkdir -p /opt/axtm || echo "Error: cannot create directory." && exit 1
fi

touch /opt/axtm/conf.ini || echo "Error: cannot write default config to folder" && exit 1
cp -r main.py /opt/axtm || echo "Error: cannot write program to folder" && exit 1

if [[ ! -f requirements.txt ]]; then
  echo "Error: requirements.txt is not exist. Exiting..." >&2
  exit 1
fi

pip3 install -r requirements.txt --break-system-packages

echo "Install Complete. The program is located at /opt/axtm. You can edit conf.ini to add tunnel configuration."
echo "Supported Tunnel: vxlan, gre, gretap, sit"
