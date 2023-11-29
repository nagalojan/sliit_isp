# write by IT20077792
# search for subdomains and save in to a file
# Coded for sliit-ISP project
# import modules
import time
# Import internal modules
from modules import certspotter
from modules import crt
from modules import hackertarget
from modules import threatcrowd
from modules import alienvault
from modules import threatminer
from modules import omnisint
from modules import sublist3r
from utils.colors import G, Y, B, R, W
################################################################################
# Run all Modules...
def queries(target):
    print(G + "Enumerating subdomains for " + target + " ...\n" + W)
    time.sleep(1)
    print(R + "[-] Searching " + target + " in CertsPotter " + W)
    print(R + "[-] Searching " + target + " in SSL Certificates " + W)
    print(R + "[-] Searching " + target + " in HackerTarget " + W)
    print(R + "[-] Searching " + target + " in ThreatCrowd " + W)
    print(R + "[-] Searching " + target + " in Alienvault " + W)
    print(R + "[-] Searching " + target + " in Threatminer" + W)
    print(R + "[-] Searching " + target + " in Omnisint" + W)
    print(R + "[-] Searching " + target + " in API Sublist3r\n" + W)
    #time.sleep(0.5)
    return (0)
