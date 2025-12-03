import subprocess
from utils.domain_monitor import checkDomain, checkResolve
from utils.ipaddr import testip

def runCommand(command, verbose):
    if verbose:
        print(f"+ Executing command: {command}")
    subprocess.run(command, check=True)

def resolvedstaddr(inputvalue):
    if checkDomain(inputvalue):
        ipresolve = checkResolve(inputvalue)
        if ipresolve is None:
            print(f"{inputvalue} resolve failed. Skipped.")
            return False
    else:
        ipresolve = inputvalue
    return ipresolve

def ipcommands(ipstream,tunnelName):
    if not isinstance(ipstream, list):
        ipstream = [ipstream]
    output = []
    for ip in ipstream:
        if testip(ip):
            output.append(["ip","addr","add",ip,"dev",f"{tunnelName}"])
    return output

def createTunnel(name,type,localaddr,dstaddr,ttl,mtu,ipaddress):
    ipresolve = resolvedstaddr(dstaddr)
    if not ipresolve:
        print(f"Setting up {type}-{name} failed.")
        return False
    cmd = [["ip", "tunnel", "add", f"{type}-{name}", "mode", type, "local", localaddr, "remote", ipresolve, "ttl", str(ttl)],
           ["ip", "link", "set", f"{type}-{name}", "mtu", str(mtu), "up"],
          ]
    cmd = cmd + ipcommands(ipaddress,f"{type}-{name}")
    print(f"Creating {type} tunnel {name}...")
    for item in cmd:
        runCommand(item, verbose=False)

def creategretap(name,localaddr,dstaddr,ttl,mtu,ipaddress):
    ipresolve = resolvedstaddr(dstaddr)
    if not ipresolve:
        print(f"Setting up {type}-{name} failed.")
        return False
    cmd = [["ip", "link", "add", f"gretap-{name}", "type", "gretap", "local", localaddr, "remote", ipresolve, "ttl", str(ttl)],
           ["ip", "link", "set", f"gretap-{name}", "mtu", str(mtu), "up"],
           ]
    cmd = cmd + ipcommands(ipaddress, f"gretap-{name}")
    print(f"Creating GRETAP tunnel {name}...")
    for item in cmd:
        runCommand(item, verbose=False)

def createLink(name,localaddr,dstaddr,dstport,ttl,vni,mtu,iporbridge):
    ipresolve = resolvedstaddr(dstaddr)
    if not ipresolve:
        print(f"Setting up {type}-{name} failed.")
        return False
    cmd = [["ip","link","add",f"vxlan-{name}","type","vxlan","local",localaddr,"remote",ipresolve,"dstport",str(dstport),"id",str(vni),"ttl",str(ttl)],
           ["ip","link","set",f"vxlan-{name}","mtu",str(mtu),"up"]]
    print(f"Creating vxlan tunnel {name}...")
    if isinstance(iporbridge, list):
        cmd = cmd + ipcommands(iporbridge, f"vxlan-{name}")
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