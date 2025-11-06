import os,sys
import argparse
import subprocess
import yaml
from utils.confpreprocess import nameGen

def readConf(file):
    if not os.path.exists(file):
        return None
    f = open(file,"r",encoding="utf-8")
    data = yaml.safe_load(f)
    f.close()
    return data

def list_sections(conffile):
    output = {}
    if not os.path.exists(conffile):
        print("Cannot find specified config file. Exiting...")
        sys.exit(1)

    dicts = readConf(conffile).get("configs", None)
    if dicts is None:
        return output

    for item in dicts.keys():
        name = nameGen(item)
        tunnType = dicts.get(item, {}).get("type", None)
        if not tunnType:
            print(f"{item} contains unsupported protocol, or is missing a 'type'. Skipping...")
            continue
        output[name] = tunnType.lower()

    return output

def detectTunnel(type,tunnel):
    try:
        result = subprocess.check_output(f"ip link | grep {type}-{tunnel}", shell=True, text=True)
        if result.strip():
            name = result.split(":")[1].strip()
            if "@" in name:
                return f"{type}-{tunnel}"
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def runCommand(command):
    print(f"+ Executing command: {command}")
    subprocess.run(command, shell=True, check=True)

parser = argparse.ArgumentParser(description="Specify user-defined config path")
parser.add_argument('--config', type=str, default="/opt/axtm/config.yml", help='Config path')
args = parser.parse_args()
# Detect User-defined Config Path

confFile = args.config
tmpFlag = False
if os.path.exists("/tmp/axtm.conf"):
    confFile = "/tmp/axtm.conf"
    tmpFlag = True
sections = list_sections(confFile)

print("Start AXTM termination process...")

for key,value in sections.items():
    tunnelName = detectTunnel(value, key)
    if not tunnelName:
        continue
    cmd = f"ip link del {tunnelName}"
    runCommand(cmd)

if tmpFlag:
    os.remove("/tmp/axtm.conf")

print("Termination process completed.")