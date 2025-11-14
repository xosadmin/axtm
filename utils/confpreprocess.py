import re
from utils.ipaddr import testip
from utils.domain_monitor import checkDomain

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

def checkmandatory(dicts,defaultSrc):
    if len(dicts) == 0:
        print("The config is empty!")
        return {}

    modifydicts = dicts.copy()  # Make a copy of the dictionary to avoid modifying the original
    mandatory = ["src", "dst", "address", "type", "mtu", "ttl"]
    # Iterate over each key in the dictionary
    keys_to_remove = []  # List to store keys to remove
    for key, values in modifydicts.items():
        missing_keys = []
        tunnelType = modifydicts.get(key,{}).get("type", "")
        if tunnelType == "":
            keys_to_remove.append(key)
            continue
        else:
            tunnelType = tunnelType.lower()
        src = modifydicts[key].get("src", defaultSrc)
        dst = modifydicts[key].get("dst", False)
        ttl = modifydicts[key].get("ttl", 255)
        mtu = modifydicts[key].get("mtu", 1450)
        for item in mandatory:
            if tunnelType == "vxlan" and item == "address":
                continue
            if item not in values:
                if "src" not in values and not src:
                    missing_keys.append(item)
            modifydicts[key]["src"] = src
            modifydicts[key]["ttl"] = ttl
            modifydicts[key]["mtu"] = mtu
            # If mandatory fields are missing, add this config to remove list
        if (not testip(src) and not src) or not testip(dst):
            if not checkDomain(dst):
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

def nameGen(rawName):
    inputName = re.sub(r'[^A-Za-z0-9]',"",rawName)
    output = inputName[:6]
    return output