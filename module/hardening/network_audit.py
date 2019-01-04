import psutil, struct, socket, os, re
from utils.harden_mgr import Kharden
from utils import common, lib, file_op

#http://tcpipguide.com/free/t_TCPOperationalOverviewandtheTCPFiniteStateMachineF-2.htm
STATUS = {
    "LISTEN" : 0,
    "SYN_SENT" : 1,
    "SYN_RECV" : 2,
    "ESTABLISHED" : 3,
    "CLOSE_WAIT" : 4,
    "LAST_ACK" : 5,
    "FIN_WAIT1" : 6,
    "FIN_WAIT2" : 7,
    "CLOSING" : 8,
    "TIME_WAIT" : 9,
    "CLOSE" : 10,
    "NONE" : 11
}

def sort_by_status(p):
    status = p[3]

    if status in STATUS:
        return STATUS[status]

    raise
    return 12        

def get_connections(response, kind):
    connections = psutil.net_connections(kind = kind)
    values = []

    for conn in connections:
        fd, family, _type, laddr, raddr, status, pid = conn
        
        if _type == 1:
            _type = "TCP"
        elif _type == 2:
            _type = "UDP"
        
        local = "{}:{}".format(laddr[0], laddr[1])

        if len(raddr) == 0:
            remote = ""
        else:
            remote = "{}:{}".format(raddr[0], raddr[1])
        
        try:
            if pid:
                p = psutil.Process(pid = pid)
                pid = "{}/{}".format(pid, p.name())
        except Exception as e:
            pass

        values.append([_type, local, remote, status, pid])
        
    values = sorted(values, key = sort_by_status)
    values.insert(0, ["PROTO", "LOCAL ADDRESS", "FOREIGN ADDRESS", "STATE", "PID/PROCESS"])
    
    response["network"].append({
        "name" : "Connections",
        "value" : len(values) - 1,
        "values" : values
    })

def network_connections(response):
    get_connections(response, "inet")
    #get_connections(response, "tcp")
    #get_connections(response, "udp")
    #get_connections(response, "unix")
    
def arp_force(ip):
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        
        ip = socket.inet_ntoa(struct.pack(">I", ip))
        
        for i in range(5):
            sock.sendto(str(id(sock) & 0xFF + i ** 8), (ip, id(ip) & 0xFFFF + i * 1000))
            
        sock.close()
    except:
        pass

def get_arp_caches(response):
    values = []
    interfaces = psutil.net_if_addrs()

    for name, addrs in interfaces.items():
        for addr in addrs:
            if addr[0] == 2 and addr[1] != '127.0.0.1':

                #cidr = sum([bin(int(x)).count("1") for x in addr[2].split(".")])
                #netmask = (2 ** cidr - 1) << (32 - cidr)
                netmask = struct.unpack(">I", socket.inet_aton(addr[2]))[0]
                num = 0xFFFFFFFF - netmask

                ip = struct.unpack(">I", socket.inet_aton(addr[1]))[0]
                start_ip = ip & netmask 
                
                for i in range(num):
                    target = start_ip + i
                    
                    if target == ip:
                        continue
                        
                    arp_force(target)
                    
    if common.is_linux():
        with open('/proc/net/arp') as arpt:
            for line in arpt.readlines():
                if "IP address" in line or "Flags" in line:
                    continue
                    
                (ip, hw, flags, mac, mask, dev) = line.split()
                
                if flags == hex(2):
                    values.append([ip, hw, flags, mac, mask, dev])
                    
    values = sorted(values, key = lambda t : struct.unpack(">I", socket.inet_aton(t[0]))[0])
    values.insert(0, ["IP address", "HW type", "Flags", "HW address", "Mask", "Device"])
    
    response["network"].append({
        "name" : "ARP Table",
        "value" : len(values) - 1,
        "values" : values
    })
    
def get_gateway(response):
    nic, ipv4, ipv6, gateway = lib.get_ip_gateway()
    
    if gateway:
        response["network"].append({
            "name" : "Gateway IPv4 Address",
            "value" : gateway
        })
        
def check_ipv4_configuration(response):
    ipv4_ipforward = "/proc/sys/net/ipv4/ip_forward"
    
    if os.path.exists(ipv4_ipforward):
        data_ipv4_ipforward = file_op.cat(ipv4_ipforward, "r")
        
        response["network"].append({
            "name" : "IPv4 Packet Forwarding Support",
            "value" : "Disable" if data_ipv4_ipforward == "0" else "Enabled"
        })
        
    ipv4_icmp_redirect = "/proc/sys/net/ipv4/conf/all/accept_redirects"
    
    if os.path.exists(ipv4_icmp_redirect):
        data_redirect = file_op.cat(ipv4_icmp_redirect, "r")
        
        response["network"].append({
            "name" : "IPv4 ICMP Redirect Support",
            "value" : "Disable" if data_redirect == "0" else "Enabled"
        })

def check_ipv6_configuration(response):
    ipv6_forward = "/proc/sys/net/ipv6/conf/all/forwarding "
    ipv6_all_disable = "/proc/sys/net/ipv6/conf/all/disable_ipv6"
    ipv6_default_disable = "/proc/sys/net/ipv6/conf/default/disable_ipv6"
    ipv6_disable = False

    if os.path.exists(ipv6_forward):
        data_ipv6_ipforward = file_op.cat(ipv6_forward, "r")

        response["network"].append({
            "name" : "IPv6 Packet Forwarding Support",
            "value" : "Disable" if data_ipv6_ipforward == "0" else "Enabled"
        })

    if os.path.exists(ipv6_all_disable) and os.path.exists(ipv6_default_disable):
        data_all = file_op.cat(ipv6_all_disable, "r")
        data_default = file_op.cat(ipv6_default_disable, "r")

        if data_all == "1" and data_default == "1":
            ipv6_disable = True

    response["network"].append({
        "name" : "IPv6 Support",
        "value" : "Disable" if ipv6_disable else "Enabled"
    })

    if not ipv6_disable:
        ipv6_icmp_redirect = "/proc/sys/net/ipv6/conf/all/accept_redirects"

        if os.path.exists(ipv6_icmp_redirect):
            data_redirect = file_op.cat(ipv6_icmp_redirect, "r")

            response["network"].append({
                "name" : "IPv6 ICMP Redirect Support",
                "value" : "Disable" if data_redirect == "0" else "Enabled"
            })

def check_dns_server(response):
    resolv_conf = "/etc/resolv.conf"

    if os.path.exists(resolv_conf):
        data = file_op.cat(resolv_conf, "r")

        if data:
            results = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", data)

            if results:
                values = [["IP Address", "Latency"]]
                
                for ip in results:
                    values.append([ip, common.measuring_latency(ip)])
                    
                response["network"].append({
                    "name" : "DNS Configuration",
                    "value" : len(results),
                    "values" : values
                })

def check_ssh_configuration(response):
    if common.is_program_running("sshd"):
        response["network"].append({
            "name" : "Checking running SSH daemon",
            "value" : "Found"
        })

        sshd_config = "/etc/ssh/sshd_config"
        data = file_op.cat(sshd_config, "r")

        if data:
            values = [["Key", "Value"]]
            lines = data.split("\n")
            keys = ["PasswordAuthentication", "PermitEmptyPasswords", "PermitRootLogin", "Port"]
            patterns = [re.compile(r"^(#|)PasswordAuthentication\s(yes|no)"),
                        re.compile(r"^(#|)PermitEmptyPasswords\s(yes|no)"),
                        re.compile(r"^(#|)PermitRootLogin\s(yes|no)"),
                        re.compile(r"^(#|)Port\s(\d+)")]
            uncomment = {}
            comment = {}

            for line in lines:
                for i in range(len(patterns)):
                    match = patterns[i].match(line)

                    if match:
                        groups = match.groups()
                        
                        if len(groups) == 2:
                            if groups[0] == "#":
                                comment[keys[i]] = groups[1]
                            else:
                                uncomment[keys[i]] = groups[1]

            for i in range(len(keys)):
                key = keys[i]

                if key in uncomment:
                    values.append([key, uncomment[key]])
                    continue

                if key in comment:
                    values.append([key, comment[key]])
                    continue

            if len(values) > 1:
                response["network"].append({
                    "name" : "SSH Configuration",
                    "value" : len(values) - 1,
                    "values" : values
                })

def check_arp_monitor_tool(response):
    arpwatch = False

    if common.is_program_running("arpwatch"):
        arpwatch = True

    if arpwatch:
        response["network"].append({
            "name" : "Checking for ARP monitoring software",
            "value" : "Found"
        })
    else:
        response["network"].append({
            "name" : "Checking for ARP monitoring software",
            "value" : "Not Found"
        })

def run(payload, socket):
    
    session_id = payload["args"]["session_id"]

    response = {
        "cmd_id" : payload["cmd_id"],
        "session_id" : session_id,
        "network" : [],
        "error" : ""
    }
    
    get_gateway(response)
    network_connections(response)
    get_arp_caches(response)
    check_arp_monitor_tool(response)
    check_ipv4_configuration(response)
    check_ipv6_configuration(response)
    check_dns_server(response)
    check_ssh_configuration(response)

    Kharden().sync_process(socket, session_id, Kharden().NETWORK, 2, 
        [0, 0.4, 0.6, 0.8, 1], 
        ["netstat -anp", 
        "ifconfig -a", 
        "cat /proc/net/arp", 
        "cat /etc/ssh/sshd_config",
        "Finished"])

    socket.response(response)
