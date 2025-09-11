import os,configparser
import subprocess
import ipaddress
import time

def testip(inputvalue):
    if "/" in inputvalue:
        value = inputvalue.split("/")[0]
    else:
        value = inputvalue
    try:
        ipaddress.ip_address(value)
        return True
    except:
        return False


def checkmandatory(dicts):
    modifydicts = dicts.copy()  # Make a copy of the dictionary to avoid modifying the original
    mandatory = ["src", "dst", "address", "type", "mtu", "ttl"]
    # Iterate over each key in the dictionary
    keys_to_remove = []  # List to store keys to remove
    for key, values in modifydicts.items():
        missing_keys = []
        for item in mandatory:
            if item not in values:
                missing_keys.append(item)
        # If mandatory fields are missing, add this config to remove list
        src = modifydicts[key].get("src")
        dst = modifydicts[key].get("dst")
        if not testip(src) or not testip(dst):
            print(f"Warning: config {key} will not be provisioned because of incorrect src/dst address.")
            keys_to_remove.append(key)
        if missing_keys:
            keys_to_remove.append(key)
            print(
                f"Warning: config {key} will not be provisioned because of missing mandatory setting(s): {', '.join(missing_keys)}.")
    # Remove the keys after the loop has completed
    for key in keys_to_remove:
        modifydicts.pop(key)
    return modifydicts

def list_sections(conffile):
    if not os.path.exists(conffile):
        print("Cannot find specified config file. Exiting...")
        exit(1)

    config = configparser.ConfigParser()
    config.read(conffile)

    return config.sections()

def readconf(conffile,section,settings):
    if not os.path.exists(conffile):
        print("Cannot find specified config file. Exiting...")
        exit(1)

    config = configparser.ConfigParser()
    config.read(conffile)

    if settings not in config[section]:
        return ""

    return config[section][settings]

def runCommand(command):
    print(f"+ Executing command: {command}")
    subprocess.run(command, shell=True, check=True)

def createTunnel(name,type,localaddr,dstaddr,ttl,mtu,ipaddress):
    cmd = [f"ip tunnel add {type}-{name} type {type} local {localaddr} remote {dstaddr} ttl {ttl}",
           f"ip link set {type}-{name} mtu {mtu} up",
           f"ip addr add {ipaddress} dev {type}-{name}"]
    for item in cmd:
        runCommand(item)

def createLink(name,localaddr,dstaddr,dstport,ttl,vni,mtu,iporbridge):
    cmd = [f"ip link add vxlan-{name} type vxlan local {localaddr} remote {dstaddr} dstport {dstport} id {vni} ttl {ttl}",
           f"ip link set vxlan-{name} mtu {mtu} up"]
    if testip(iporbridge):
        cmd.append(f"ip addr add {iporbridge} dev vxlan-{name}")
    else:
        cmd.append(f"brctl addif {iporbridge} vxlan-{name}")
    for item in cmd:
        runCommand(item)

def detectTunnel(tunnel):
    try:
        result = subprocess.check_output(f"ip link | grep {tunnel}", shell=True, text=True)
        if result.strip():
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def detectUser():
    try:
        result = subprocess.check_output("whoami", shell=True, text=True)
        user = result.strip()
        if user == "root":
            return True
        else:
            return False
    except:
        return False

def prepostup(type,command):
    print(f"Executing {type} command: {command}")
    runCommand(command)

if not detectUser():
    print("You are not running on user root. Exiting...")
    exit(1)

print("Welcome. AXTunnelmanamger will start provision tunnel(s) after 3 seconds....")
time.sleep(3)

confFile = os.path.join("conf.ini")
sections = list_sections(confFile)

if not os.path.exists(confFile):
    print("Cannot find specified config file. Exiting...")
    exit(1)

config = configparser.ConfigParser()
config.read(confFile)
arguments = {}

for item in sections:
    name = item.lower()
    if len(name) > 6:
        name = name[0:6]
    if name not in arguments:
        arguments[name] = {}
    for key, value in config[item].items():
        key = key.lower()
        arguments[name][key] = value

checkedArgs = checkmandatory(arguments)

for key in checkedArgs:
    for key2 in checkedArgs[key]:
        if detectTunnel(key2):
            print(f"The tunnel {key2} already up. Skipped.")
            continue
        if checkedArgs[key2]["type"] == "vxlan":
            vni = checkedArgs[key2].get("vni")
            dstport = checkedArgs[key2].get("dstport")
            if not vni or not dstport:
                print(f"Incomplete configuration for vxlan {key2}. Skipped.")
                continue
            else:
                if checkedArgs[key2]["bridge"]:
                    createLink(key2,checkedArgs[key2]["src"],checkedArgs[key2]["dst"],checkedArgs[key2]["dstport"],
                               checkedArgs[key2]["ttl"],checkedArgs[key2]["vni"],checkedArgs[key2]["mtu"],
                               checkedArgs[key2]["bridge"])
                else:
                    if testip(checkedArgs[key2]["address"]):
                        createLink(key2, checkedArgs[key2]["src"], checkedArgs[key2]["dst"], checkedArgs[key2]["dstport"],
                                   checkedArgs[key2]["ttl"],checkedArgs[key2]["vni"], checkedArgs[key2]["mtu"],
                                   checkedArgs[key2]["address"])
                    else:
                        print(f"Incorrect endpoint address. Skipping config {key2}...")
                        continue
        else:
            if testip(checkedArgs[key2]["address"]):
                createTunnel(key2,checkedArgs[key2]["type"],checkedArgs[key2]["src"],checkedArgs[key2]["dst"],
                             checkedArgs[key2]["ttl"],checkedArgs[key2]["mtu"],checkedArgs[key2]["address"])
            else:
                print(f"Incorrect endpoint address. Skipping config {key2}...")
                continue

print(f"Process completed.")