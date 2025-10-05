import os,sys
import configparser
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

def checkvalue(type,value):
    try:
        rawinput = int(value)
    except ValueError: # If value is not a digit/contains non-digit value
        return False
    if type == "ttl":
        if rawinput >= 1 and rawinput <= 255:
            return True
    elif type == "mtu":
        if rawinput >= 68 and rawinput <= 9000:
            return True
    elif type == "dstport":
        if rawinput >= 1 and rawinput <= 65535:
            return True
    return False

def checkmandatory(dicts):
    modifydicts = dicts.copy()  # Make a copy of the dictionary to avoid modifying the original
    mandatory = ["src", "dst", "address", "type", "mtu", "ttl"]
    # Iterate over each key in the dictionary
    keys_to_remove = []  # List to store keys to remove
    for key, values in modifydicts.items():
        missing_keys = []
        tunnelType = modifydicts[key]["type"]
        for item in mandatory:
            if tunnelType == "vxlan" and item == "address":
                continue
            if item not in values:
                missing_keys.append(item)
        # If mandatory fields are missing, add this config to remove list
        src = modifydicts[key].get("src")
        dst = modifydicts[key].get("dst")
        ttl = modifydicts[key].get("ttl")
        mtu = modifydicts[key].get("mtu")
        if not testip(src) or not testip(dst):
            print(f"Error: config {key} will not be provisioned because of incorrect src/dst address.")
            keys_to_remove.append(key)
        if not checkvalue("ttl",ttl) or not checkvalue("mtu",mtu):
            print(f"Error: config {key} will not be provisioned because of incorrect ttl and/or mtu.")
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
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(conffile)

    return config.sections()

def isIPv6(addr):
    ip_for_check = ipaddress.ip_address(addr)
    if isinstance(ip_for_check, ipaddress.IPv6Address):
        return True
    else:
        return False

def runCommand(command):
    print(f"+ Executing command: {command}")
    subprocess.run(command, check=True)

def createTunnel(name,type,localaddr,dstaddr,ttl,mtu,ipaddress):
    cmd = [["ip", "tunnel", "add", f"{type}-{name}", "mode", type, "local", localaddr, "remote", dstaddr, "ttl", ttl],
           ["ip", "link", "set", f"{type}-{name}", "mtu", mtu, "up"],
           ["ip", "addr", "add", ipaddress, "dev", f"{type}-{name}"]]
    for item in cmd:
        runCommand(item)

def creategretap(name,localaddr,dstaddr,ttl,mtu,ipaddress):
    cmd = [["ip", "link", "add", f"gretap-{name}", "type", "gretap", "local", localaddr, "remote", dstaddr, "ttl", ttl],
           ["ip", "link", "set", f"gretap-{name}", "mtu", mtu, "up"],
           ["ip", "addr", "add", ipaddress, "dev", f"gretap-{name}"]]
    for item in cmd:
        runCommand(item)

def createLink(name,localaddr,dstaddr,dstport,ttl,vni,mtu,iporbridge):
    cmd = [["ip","link","add",f"vxlan-{name}","type","vxlan","local",localaddr,"remote",dstaddr,"dstport",dstport,"id",vni,"ttl",ttl],
           ["ip","link","set",f"vxlan-{name}","mtu",mtu,"up"]]
    if testip(iporbridge):
        cmd.append(["ip","addr","add",iporbridge,"dev",f"vxlan-{name}"])
    else:
        cmd.append(["brctl","addif",iporbridge,f"vxlan-{name}"])
    for item in cmd:
        runCommand(item)

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
    runCommand(splitedCommand)

if not detectSth("user"):
    print("You are not running on user root. Exiting...")
    sys.exit(1)

confFile = os.path.join(os.getcwd(), "conf.ini")
sections = list_sections(confFile)

if not os.path.exists(confFile):
    print("Error: Cannot find specified config file. Exiting...")
    sys.exit(1)

config = configparser.ConfigParser()
config.read(confFile)
arguments = {}

countdown = config.get(section="global", option="countdown", fallback="3")
try:
    countdown = float(countdown)
except ValueError:
    print("Warning: Invalid countdown value. Using default (3) seconds.")
    countdown = 3

print(f"Welcome. AXTM will start provision tunnel(s) after {countdown} seconds....")
time.sleep(countdown)

for item in sections:
    name = item.lower()
    if len(name) > 6:
        name = name[0:6]
    if not name.isalpha():
        name = name[0:6] + "a"
    if name not in arguments:
        arguments[name] = {}
    for key, value in config[item].items():
        key = key.lower()
        arguments[name][key] = value

checkedArgs = checkmandatory(arguments)

if not checkedArgs:
    print("There is no valid tunnel configuration in conf.ini. Exiting...")
    sys.exit(1)

for name, conf in checkedArgs.items():
    name = name.lower()

    if name == "global":
        continue
    # Skip global configuration

    if detectSth("tunnel",name):
        print(f"The tunnel {name} already up. Skipped.")
        continue

    if conf["type"] == "vxlan":
        vni = conf.get("vni")
        dstport = conf.get("dstport")

        if not vni or not dstport:
            print(f"Incomplete configuration for vxlan {name}. Skipped.")
            continue

        if not checkvalue("dstport", dstport):
            print(f"The config {name} contains invalid dstport. Skipping...")
            continue

        if "bridge" in conf and conf["bridge"]:
            if detectSth("bridge",conf["bridge"]):
                try:
                    if "preup" in conf:
                        prepostup("preup",conf["preup"])
                except Exception as e:
                    print(f"Error executing preup command for tunnel {name}: {e}")
                    continue
                createLink(name, conf["src"], conf["dst"], conf["dstport"],
                           conf["ttl"], conf["vni"], conf["mtu"], conf["bridge"])
                try:
                    if "postup" in conf:
                        prepostup("postup",conf["postup"])
                except Exception as e:
                    print(f"Error executing postup command for tunnel {name}: {e}")
                    continue
            else:
                print(f"Bridge {conf['bridge']} does not exist. Skipping...")
                continue
        else:
            if testip(conf["address"]):
                try:
                    if "preup" in conf:
                        prepostup("preup",conf["preup"])
                except Exception as e:
                    print(f"Error executing preup command for tunnel {name}: {e}")
                    continue
                createLink(name, conf["src"], conf["dst"], conf["dstport"],
                           conf["ttl"], conf["vni"], conf["mtu"], conf["address"])
                try:
                    if "postup" in conf:
                        prepostup("postup",conf["postup"])
                except Exception as e:
                    print(f"Error executing postup command for tunnel {name}: {e}")
                    continue
            else:
                print(f"Incorrect endpoint address. Skipping config {name}...")
                continue
    elif conf["type"] == "gretap":
        if testip(conf["address"]):
            try:
                if "preup" in conf:
                    prepostup("preup",conf["preup"])
            except Exception as e:
                print(f"Error executing preup command for tunnel {name}: {e}")
                continue
            creategretap(name,conf["src"],conf["dst"],conf["ttl"],conf["mtu"],conf["address"])
            try:
                if "postup" in conf:
                    prepostup("postup",conf["postup"])
            except Exception as e:
                print(f"Error executing postup command for tunnel {name}: {e}")
                continue
        else:
            print(f"Incorrect endpoint address. Skipping config {name}...")
            continue
    else:
        # Non-vxlan tunnel
        if conf["type"] == "sit":
            try:
                src_ip = ipaddress.ip_address(conf["src"].split("/")[0])
                dst_ip = ipaddress.ip_address(conf["dst"].split("/")[0])
                if isinstance(src_ip, ipaddress.IPv6Address) or isinstance(dst_ip, ipaddress.IPv6Address):
                    print(f"Error: sit tunnel {name} is not allowed to use IPv6 as src/dst.")
                    continue
            except ValueError:
                print(f"Invalid IP format in config {name}. Skipping...")
                continue

        if testip(conf["address"]):
            try:
                if "preup" in conf:
                    prepostup("preup",conf["preup"])
            except Exception as e:
                print(f"Error executing preup command for tunnel {name}: {e}")
                continue
            createTunnel(name, conf["type"], conf["src"], conf["dst"],
                         conf["ttl"], conf["mtu"], conf["address"])
            try:
                if "postup" in conf:
                    prepostup("postup",conf["postup"])
            except Exception as e:
                print(f"Error executing postup command for tunnel {name}: {e}")
                continue
        else:
            print(f"Incorrect endpoint address. Skipping config {name}...")
            continue

print(f"Process completed.")