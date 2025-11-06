import os,sys
import subprocess
import time
import yaml
import argparse
from utils.domain_monitor import checkDomain, checkResolve
from utils.confpreprocess import checkmandatory, nameGen, checkvalue
from utils.ipaddr import testip, sit_ip_check

def readConf(file):
    if not os.path.exists(file):
        return None
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

def runCommand(command, verbose):
    if verbose:
        print(f"+ Executing command: {command}")
    subprocess.run(command, check=True)

def createTunnel(name,type,localaddr,dstaddr,ttl,mtu,ipaddress):
    if checkDomain(dstaddr):
        ipresolve = checkResolve(dstaddr)
        if ipresolve is None:
            print(f"{dstaddr} resolve failed. Skipped.")
            return False
    else:
        ipresolve = dstaddr
    cmd = [["ip", "tunnel", "add", f"{type}-{name}", "mode", type, "local", localaddr, "remote", ipresolve, "ttl", str(ttl)],
           ["ip", "link", "set", f"{type}-{name}", "mtu", str(mtu), "up"],
           ["ip", "addr", "add", ipaddress, "dev", f"{type}-{name}"]]
    print(f"Creating {type} tunnel {name}...")
    for item in cmd:
        runCommand(item, verbose=False)

def creategretap(name,localaddr,dstaddr,ttl,mtu,ipaddress):
    if checkDomain(dstaddr):
        ipresolve = checkResolve(dstaddr)
        if ipresolve is None:
            print(f"{dstaddr} resolve failed. Skipped.")
            return False
    else:
        ipresolve = dstaddr
    cmd = [["ip", "link", "add", f"gretap-{name}", "type", "gretap", "local", localaddr, "remote", ipresolve, "ttl", str(ttl)],
           ["ip", "link", "set", f"gretap-{name}", "mtu", str(mtu), "up"],
           ["ip", "addr", "add", ipaddress, "dev", f"gretap-{name}"]]
    print(f"Creating GRETAP tunnel {name}...")
    for item in cmd:
        runCommand(item, verbose=False)

def createLink(name,localaddr,dstaddr,dstport,ttl,vni,mtu,iporbridge):
    if checkDomain(dstaddr):
        ipresolve = checkResolve(dstaddr)
        if ipresolve is None:
            print(f"{dstaddr} resolve failed. Skipped.")
            return False
    else:
        ipresolve = dstaddr
    cmd = [["ip","link","add",f"vxlan-{name}","type","vxlan","local",localaddr,"remote",ipresolve,"dstport",str(dstport),"id",str(vni),"ttl",str(ttl)],
           ["ip","link","set",f"vxlan-{name}","mtu",str(mtu),"up"]]
    print(f"Creating vxlan tunnel {name}...")
    if testip(iporbridge):
        cmd.append(["ip","addr","add",iporbridge,"dev",f"vxlan-{name}"])
    else:
        cmd.append(["brctl","addif",iporbridge,f"vxlan-{name}"])
    for item in cmd:
        runCommand(item, verbose=False)

def detectSth(type, value=None):
    cmd = []
    expectValue = None

    if type == "tunnel":
        cmd = f"ip link | grep {value}"
    elif type == "user":
        cmd = ["whoami"]
        expectValue = "root"
    elif type == "bridge":
        cmd = f"brctl show | grep {value}"

    try:
        result = subprocess.check_output(cmd, shell=True, text=True).strip()
        if result:
            if expectValue:
                return result == expectValue
            return True  # If it's a tunnel or bridge, just return True if result exists
        return False
    except subprocess.CalledProcessError:
        return False

def prepostup(type,command):
    print(f"Executing {type} command: {command}")
    splitedCommand = command.split(" ")
    runCommand(splitedCommand, verbose=True)

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
