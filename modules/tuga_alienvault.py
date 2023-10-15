# subdom - crt module, write by IT20077792
# Bug Bounty , search for subdomains and save in to a file
# Coded for SLIIT-ISP project
# import modules
import time
import requests
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # disable the Insecure Request Warning in Http

# Import internal modules
from modules import tuga_useragents #random user-agent
# Import internal functions named "write_file" from a module located in a package named "utils"
from utils.tuga_functions import write_file
from utils.tuga_functions import DeleteDuplicate
from utils.tuga_colors import G, Y, B, R, W
################################################################################
class Alienvault:
    def __init__(self, target):
        self.target = target     # Stores the target passed to the class when an instance is created.
        self.module_name = "Alienvault"  #  Stores the name module as "Alienvault."
        self.engine = "alienvault"       # Stores name engine as "alienvault
        self.response = self.engine_url() # URL

        if self.response != 1:
            self.enumerate(self.response, target) # Call the function enumerate
        else:
            pass
################################################################################
    def engine_url(self):
        try:   # Construct the URL and send an HTTP GET request
            response = requests.get(f'https://otx.alienvault.com/api/v1/indicators/domain/{self.target}/passive_dns').text
            return response
        except requests.ConnectionError:   # If connection error occurs, set the response to 1 and return it
            response = 1
            return response
################################################################################
    def enumerate(self, response, target):
        subdomains = []      # Initialize a list to store subdomains
        self.subdomainscount = 0    # Initialize a count
        start_time = time.time()      # Record the start time
        #################################
        try:
            extract_sub = json.loads(response)
            # JSON (JavaScript Object Notation) , lightweight data interchange format
            #print(extract_sub)
            for i in extract_sub['passive_dns']:
                subdomains = i['hostname']  #  Extract subdomains from the response
                self.subdomainscount = self.subdomainscount + 1   # Increment the subdomains count
                #print(f"    [*] {subdomains}")
                write_file(subdomains, target)    # Write the subdomain to a file
        except Exception as e:
            pass
        #################################
