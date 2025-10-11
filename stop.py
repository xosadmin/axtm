import os,sys
import configparser
import subprocess

def list_sections(conffile):
    output = {}
    if not os.path.exists(conffile):
        print("Cannot find specified config file. Exiting...")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(conffile)

    for item in config.sections():
        name = item[:6].lower()
        tunnType = config.get(section=item,option="type",fallback=None)
        if not tunnType:
            print(f"{item} contains unsupported protocol, or is none.")
            continue
        output[name] = tunnType.lower()

    return output

def detectTunnel(type,tunnel):
    try:
        result = subprocess.check_output(f"ip link | grep {type}-{tunnel}", shell=True, text=True)
        if result.strip():
            name = result.split(":")[1].strip()
            if "@" in name:
                name = name.split("@")[0]
            return name
        else:
            return False
    except subprocess.CalledProcessError:
        return False

def runCommand(command):
    print(f"+ Executing command: {command}")
    subprocess.run(command, shell=True, check=True)

confFile = ""
tmpFlag = False
if os.path.exists("/tmp/axtm.conf"):
    confFile = "/tmp/axtm.conf"
    tmpFlag = True
else:
    confFile = os.path.join(os.getcwd(), "conf.ini")
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