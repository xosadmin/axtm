import socket
import os,sys
import yaml, copy, subprocess
import validators, ipaddress
from domaintmp import domains_resolves

def checkDomain(input):
    return validators.domain(input)

def checkResolve(domain):
    try:
        ipaddr = socket.gethostbyname(domain)
        return ipaddr
    except Exception as e:
        print(f"Error while checking resolve for {domain}: {e}")
        return None

def detectipaddr(ipaddr):
    try:
        ipaddress.ip_address(ipaddr)
        return True
    except ValueError:
        return False

def restartaxtm():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'axtm'], check=True)
        return True
    except Exception as e:
        print(f"Error when restarting axtm: {e}")
        return False

def readConf(file):
    if not os.path.exists(file):
        return None
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

if os.path.exists(os.path.join("config.yml")):
    data = readConf(os.path.join("config.yml"))
else:
    print("Cannot find config.yml")
    sys.exit(1)

def main():
    configs = copy.deepcopy(data.get("configs", {}))

    if len(configs) == 0:
        print("Error: No valid config.")
        sys.exit(1)

    for key, value in configs.items():
        dst = value.get("dst", None)
        if detectipaddr(dst):
            continue
        else:
            if dst and checkDomain(dst):
                latestResolve = checkResolve(dst)
                currentResolve = domains_resolves.get(dst, None)
                if currentResolve is None or currentResolve != latestResolve:
                    if currentResolve:
                        domains_resolves.pop(dst)
                    domains_resolves[dst] = currentResolve
                    print(f"Domain {dst} has been updated with dst address {latestResolve}")
            else:
                print(f"Cannot find dst for {dst}, or dst of {dst} resolve failed.")
    restartaxtm()
    print("Complete")

if __name__ == '__main__':
    main()