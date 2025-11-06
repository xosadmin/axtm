#!/usr/bin/env bash

if [[ $(whoami) != "root" ]]; then
  echo "Error: you are not running this script under root user. privilege elevation required." >&2
  exit 1
fi

echo "Downloading latest source code..."
if [[ -d ".git" ]]; then
  echo "Pulling from Git Repository. This may overwrite modifications in this directory. Press Ctrl+C in 3 seconds to cancel."
  sleep 3
  git reset --hard
  git pull -f origin main
else
  echo "Downloading..."
  wget https://codeload.github.com/xosadmin/axtm/zip/refs/heads/main.zip
  unzip -o master.zip -d ./ && rm -rf master.zip
fi

if [[ ! -d "/opt/axtm" ]]; then
  echo "Error: AXTM is not installed. Installing..."
  bash install.sh
  exit 0
fi

echo "Updating files..."
cp -r utils /opt/axtm && cp -r *.py /opt/axtm && cp -r uwsgi.ini /opt/axtm
cp -r systemd/*.service /etc/systemd/system
chmod a+x /etc/systemd/system/axtm*.service
systemctl daemon-reload && systemctl enable axtm && systemctl disable axtm-api
pip3 install -r requirements.txt --break-system-packages

echo "Update completed. Restarting AXTM..."
systemctl restart axtm