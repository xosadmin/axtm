import os,sys
import time
import yaml
import argparse
from utils.confpreprocess import checkmandatory, nameGen, checkvalue
from utils.ipaddr import testip, sit_ip_check
from utils.tunnelcommands import detectSth, runCommand, prepostup, createTunnel, creategretap, createLink

def readConf(file):
    if not os.path.exists(file):
        return None
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

def createConfBak():
    if os.path.exists("/tmp/axtm.conf"):
        os.remove("/tmp/axtm.conf")
    os.system("cp -r config.yml /tmp/axtm.conf")

def main():
    if not detectSth("user"):
        print("You are not running on user root. Exiting...")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Specify user-defined config path")
    parser.add_argument('--config', type=str, default="/opt/axtm/config.yml", help='Config path')
    args = parser.parse_args()
    # Detect User-defined Config Path

    confFile = args.config
    if not os.path.exists(confFile):
        print("Error: Cannot find specified config file. Exiting...")
        sys.exit(1)
    sections = readConf(confFile)
    ifAPIEnable = sections.get("api",{}).get("enable", False)

    if isinstance(ifAPIEnable, bool) and ifAPIEnable:
        print(f"API Detected Enabled. Starting API Interface...")
        runCommand(["systemctl","restart","axtm-api"], False)

    countdown = sections.get("global",{}).get("countdown", 3)
    try:
        countdown = float(countdown)
    except ValueError:
        print("Warning: Invalid countdown value. Using default (3) seconds.")
        countdown = 3

    createConfBak()
    print(f"Welcome. AXTM will start provision tunnel(s) after {countdown} seconds....")
    time.sleep(countdown)

    checkedArgs = checkmandatory(sections.get("configs",{}))

    if len(checkedArgs) == 0:
        print("There is no valid tunnel configuration in conf.ini. Exiting...")
        sys.exit(1)

    for name, conf in checkedArgs.items():
        name = name.lower()
        types = checkedArgs[name]["type"]
        tunnelName = nameGen(name)

        if detectSth("tunnel",f"{types}-{tunnelName}"):
            print(f"The tunnel {name} already up. Skipped.")
            continue

        try:
            if "preup" in conf.get("pre_post_scripts", {}):
                prepostup("preup", conf.get("pre_post_scripts", {}).get("preup", []))
            else:
                print(f"Note: Tunnel {name} does not define pre-up script, or script file is not exist.")
        except Exception as e:
            print(f"Error executing preup command for tunnel {name}: {e}")
            continue

        if conf["type"] == "vxlan":
            vni = ""
            if "vni" in conf and conf.get("vni"):
                vni = conf.get("vni")
            elif "id" in conf and conf.get("id"):
                vni = conf.get("id")
            else:
                print(f"Unknown vxlan ID for tunnel {name}. Skipping...")
                continue

            dstport = conf.get("dstport", False)

            if not dstport or not checkvalue("dstport", dstport):
                print(f"Incomplete configuration for vxlan {name}. Skipped.")
                continue

            if "bridge" in conf and conf["bridge"]:
                if detectSth("bridge",conf["bridge"]):
                    createLink(tunnelName, conf["src"], conf["dst"], conf["dstport"],
                               conf["ttl"], vni, conf["mtu"], conf["bridge"])
                else:
                    print(f"Bridge {conf['bridge']} does not exist. Skipping...")
                    continue
            else:
                if testip(conf["address"]):
                    createLink(tunnelName, conf["src"], conf["dst"], conf["dstport"],
                               conf["ttl"], vni, conf["mtu"], conf["address"])
                else:
                    print(f"Incorrect endpoint address. Skipping config {name}...")
                    continue
        elif conf["type"] == "gretap":
            if testip(conf["address"]):
                creategretap(tunnelName,conf["src"],conf["dst"],conf["ttl"],conf["mtu"],conf["address"])
            else:
                print(f"Incorrect endpoint address. Skipping config {name}...")
                continue
        else:
            # Non-vxlan tunnel
            if conf["type"] == "sit":
                if not sit_ip_check(conf.get("src",None),conf.get("dst",None)):
                    print(f"Error: sit tunnel {name} is not allowed to use IPv6 as src/dst.")
                    continue

            if testip(conf["address"]):
                createTunnel(tunnelName, conf["type"], conf["src"], conf["dst"],
                             conf["ttl"], conf["mtu"], conf["address"])
            else:
                print(f"Incorrect endpoint address. Skipping config {name}...")
                continue

        try:
            if "postup" in conf.get("pre_post_scripts", {}):
                prepostup("postup", conf.get("pre_post_scripts", {}).get("postup", []))
            else:
                print(f"Note: Tunnel {name} does not define post-up script, or script file is not exist.")
        except Exception as e:
            print(f"Error executing postup command for tunnel {name}: {e}")
            continue

    print(f"Process completed.")

if __name__ == "__main__":
    main()
