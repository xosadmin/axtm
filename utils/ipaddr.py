import ipaddress

def isIPv6(addr):
    ip_for_check = ipaddress.ip_address(addr)
    if isinstance(ip_for_check, ipaddress.IPv6Address):
        return True
    else:
        return False

def testip(inputvalue):
    if not inputvalue:
        return False
    if "/" in inputvalue:
        value = inputvalue.split("/")[0]
    else:
        value = inputvalue
    try:
        ipaddress.ip_address(value)
        return True
    except:
        return False

def testIPinList(listvalue):
    if not isinstance(listvalue, list) or len(listvalue) == 0:
        return False
    for item in listvalue:
        if not testip(item):
            return False
    return True

def sit_ip_check(srcip,dstip):
    try:
        src_ip = ipaddress.ip_address(srcip.split("/")[0])
        dst_ip = ipaddress.ip_address(dstip.split("/")[0])
        if isinstance(src_ip, ipaddress.IPv6Address) or isinstance(dst_ip, ipaddress.IPv6Address):
            return False
        else:
            return True
    except Exception as e:
        print(f"Error when check SIT ip address: {e}")
        return False