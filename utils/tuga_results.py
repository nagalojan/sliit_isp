#!/usr/bin/python3

# Bug Bounty Recon, search for subdomains and save in to a file
# # SUBDOM - create for SLIIT ISP module
# Coded By IT20077792
################################################################################
import os
from utils.tuga_colors import G, Y, B, R, W

def main_work_subdirs():
    rootdir = "results"
    print("\nResults: ")
    print(G + "**************************************************************" + W)
    for root, dirs, files in os.walk(rootdir):
        dirs.sort()
        if root == rootdir:
            for domain in dirs:
                print(Y + f"[Domain]", domain  + W)
