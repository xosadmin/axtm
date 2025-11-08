import subprocess
from utils.domain_monitor import checkDomain, checkResolve
from utils.ipaddr import testip

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