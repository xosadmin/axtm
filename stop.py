import os,sys
import configparser
import subprocess

def list_sections(conffile):
    if not os.path.exists(conffile):
        print("Cannot find specified config file. Exiting...")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(conffile)

    return config.sections()

def detectTunnel(tunnel):
    try:
        result = subprocess.check_output(f"ip link | grep {tunnel}", shell=True, text=True)
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

confFile = os.path.join(os.getcwd(), "conf.ini")
sections = list_sections(confFile)

print("Start AXTM termination process...")

for item in sections:
    item = item.lower()
    if len(item) > 6:
        item = item[:6]
    if not detectTunnel(item):
        continue
    tunnelName = detectTunnel(item)
    cmd = f"ip link del {tunnelName}"
    runCommand(cmd)

print("Termination process completed.")