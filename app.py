import requests
import json
import sys
import hashlib
from pathlib import Path

RRFMISSIONS = "http://1st-rrf.com/api/missions"
MISSIONDIR = r"C:\Users\rodri\Development\Python\ArmaOctet\MPMissions"

def getMissionList():
    siteRequest = requests.get(RRFMISSIONS)
    return siteRequest.json()

def verifyChecksum(file, checksum):
    computedHash = hashlib.md5(open(file,'rb').read()).hexdigest()

    if(computedHash == checksum):
        return 1
    else:
        return 0

def main(argv):
    # Grab Mission List
    missionList = getMissionList()

    #quick checksum check
    #print(verifyChecksum("malden-test-2.pbo",missionList[0]['checksum']))


    # Go through all files determine if we need to redownload everything
    for mission in missionList:
        my_file = Path(MISSIONDIR+'/'+mission['filename'])
        if my_file.is_file():
            print('its there!')
        else: 
            print('its not there!')
        pass

    print(missionList[0]['download'])
    pass

if __name__ == "__main__":
    main(sys.argv)