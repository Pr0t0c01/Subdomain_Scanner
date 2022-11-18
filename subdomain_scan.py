import sys
import re
import socket
import random
import argparse
import requests as req
from datetime import date
from threading import Thread
from bs4 import BeautifulSoup

from setup_vpn_proxy import rotate_user_agent

G = '\033[92m'  # green
Y = '\033[93m'  # yellow
B = '\033[94m'  # blue
R = '\033[91m'  # red
W = '\033[0m'   # white

subdomain_list = []

headers = rotate_user_agent()

#############################################################################
# SSLCertificate Scan 
class SSLCertificate:
    def __init__(self, domain):
        self.domain = domain

    def SSL_scan(self, domain):
        base_url = f"https://crt.sh/?q=%25.{self.domain}"
        get_response = req.get(base_url, headers = headers, timeout=20)
        subdomains = get_response.text

        regx_subdo = re.compile('<TD>(.*?)</TD>')
        total_subdomains = regx_subdo.findall(subdomains)
        for subdomain in total_subdomains:
            subdomain = subdomain.strip()

            if '<A style="white-space:normal' in subdomain:
                pass
            else:
                if '<BR>' in subdomain:
                    split_subdomain = subdomain.split("<BR>")
                    for each_subdomain in split_subdomain:
                        subdomain_list.append(each_subdomain)
                else:
                    subdomain_list.append(subdomain)
        return subdomain_list

#############################################################################
# PassiveDNS Scan
class PassiveDNS:
    def __init__(self, domain):
        self.domain = domain

    def PassiveDNS_scan(self, domain):
        base_url = f"https://api.sublist3r.com/search.php?domain={self.domain}"
        get_response = req.get(base_url, headers = headers, timeout=10)
        subdomains = get_response.text
        subdomains = subdomains.strip()

        remove_chars = '[]"'
        for char in remove_chars:
            subdomains = subdomains.translate({ord(char):""})
        total_subdomains = subdomains.split(",")
        
        for subdomain in total_subdomains:
            subdomain_list.append(subdomain)
        return subdomain_list

#############################################################################
# Parse the arguments
def args_parse():
    parser = argparse.ArgumentParser()
    parser.title = "OPTIONS"
    parser.add_argument('-d', dest='domain', required=True)
    return parser.parse_args()

# Check target host is live or not
def check_host(domain):
    print(f"{Y}[{G}-{Y}] Checking status of target domain... {W}", end='\r')

    domain_check = req.get(f"http://{domain}", headers=headers, timeout=10)
    if domain_check.ok:
        print(f"{Y}[{G}-{Y}] Checking status of target domain... {G}{domain_check.status_code} OK!{W}")
    else:
        sys.exit()

# Enumerate subdomain from all resource
def enumeration_subdomain(domain):
    scanning_resource = {
                         'ssl': SSLCertificate(domain).SSL_scan(domain),
                         'passivedns': PassiveDNS(domain).PassiveDNS_scan(domain)}
#'threatcrowd': Threatcrowd(domain).Threatcrowd_scan(domain),                         
    for resource in scanning_resource:
        resource = Thread(target = scanning_resource[resource])
        resource.daemon = True
        resource.start()
        try:
            resource.join()
        except Exception:
            pass

# Sorting Results
def sorting_result(hostname):
    schema = hostname.split('.')[::-1]
    if schema[-1] == 'www':
        return schema[:-1], 1
    return schema, 0

#############################################################################
# Main Function
if __name__ == "__main__":
    args = args_parse()
    domain = args.domain
    check_host(domain)
    enumeration_subdomain(domain)

    print("Removing duplicate data & sorting order...")
    subdomain_list = set(subdomain_list)
    subdomain_list = sorted(subdomain_list, key=sorting_result)

    for count, final_subdomain in enumerate(subdomain_list):
        print(f"{G}[{Y}{count+1}{G}]{Y} - {G}{final_subdomain}{W}")
    print(f"Total Subdomains : {count+1}")