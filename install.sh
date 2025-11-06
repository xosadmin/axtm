#!/usr/bin/env bash

user=$(whoami)

if [[ "$user" != "root" ]]; then
    echo "ax.wiki Tunnel Manager can only installed or executed under root user." >&2
    exit 1
fi

echo "Thanks for using ax.wiki Tunnel Manager (AXTM). Starting installation..."

echo "Installing bridge utilities and iproute2..."
apt install bridge-utils iproute2 gcc build-essential -y

if [[ $(dpkg -l | grep -c "python3-*") -gt "0" ]]; then
  echo "Removing conflict python libraries installed by apt-get..."
  apt remove python3-* -y
fi

if [[ $(dpkg -l | grep -c python3-pip) -eq "0" ]]; then
  echo "Python 3 is not installed. Installing..."
  apt update -y --fix-missing && apt install python3 python3-pip -y
fi

if [[ -d "/etc/systemd/system" ]]; then
  cp -r systemd/*.service /etc/systemd/system
  chmod a+x /etc/systemd/system/axtm*.service
  systemctl daemon-reload && systemctl enable axtm && systemctl disable axtm-api
  echo "axtm service is installed and enabled."
  echo "axtm-api is not enabled by default. Use systemctl enable axtm-api to enable it."
else
  echo "Your system is not supported to run axtm as service. Skipping service installation..."
fi

if [[ ! -d "/opt/axtm" ]]; then
  if ! mkdir -p /opt/axtm; then
      echo "Error: cannot create directory /opt/axtm. Exiting..." >&2
      exit 1
  fi
fi

cp -r utils /opt/axtm && cp -r *.py /opt/axtm && cp -r uwsgi.ini /opt/axtm

if [[ ! -f "/opt/axtm/config.yml" ]]; then
  cat>>/opt/axtm/config.yml<<EOF
global:
    countdown: 3
api:
    enable: False

EOF
else
  echo "Warning: /opt/axtm/config.yml is exist. Adopting existing configures."
fi

if [[ $(grep -c "axtm" /etc/passwd) -eq "0" ]]; then
  useradd axtm && usermod -s /usr/sbin/nologin axtm
  echo "axtm ALL=NOPASSWD: /bin/systemctl restart axtm" >> /etc/sudoers
  systemctl restart ssh
  echo "User axtm is created and disabled SSH access."
fi

chown -R axtm:axtm /opt/axtm/config.yml

if [[ ! -f requirements.txt ]]; then
  echo "Error: requirements.txt is not exist. Exiting..." >&2
  exit 1
fi

pip3 install -r requirements.txt --break-system-packages

echo "Install Complete. The program is located at /opt/axtm. You can edit config.yml to add tunnel configuration."
