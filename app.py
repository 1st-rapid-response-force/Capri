import requests
import json
import sys
import hashlib
import subprocess
from pathlib import Path
import urllib.request
from urllib.request import urlretrieve

RRFMISSIONS = "http://1st-rrf.com/api/missions"
MISSIONDIR = r"C:\Users\Guillermo\Development\Python\Capri\MPMissions"

def getmissionlist():
    siterequest = requests.get(RRFMISSIONS)
    return siterequest.json()

def verifychecksum(file, checksum):
    computedhash = hashlib.md5(open(file,'rb').read()).hexdigest()
    if(computedhash == checksum):
        return 1
    else:
        return 0

def checkmissionfile(mission):
    missionfile = Path(MISSIONDIR+'/'+mission['filename'])
    if missionfile.is_file() :
        if verifychecksum(missionfile, mission['checksum']):
            return 1
        else:
            return 0
    else:
        return 0

def downloadmissionfile(mission):
    missionfile = Path(MISSIONDIR+'/'+mission['filename'])
    req = urllib.request.Request(mission['download'], headers={'User-Agent': 'Mozilla/5.0'})
    page = urllib.request.urlopen(req)
    downloadedfile = page.read()
    localfile = open(missionfile,'wb')
    localfile.write(downloadedfile)
    localfile.close()

def main(argv):
    # Grab Mission List
    missionlist = getmissionlist()

    # Connect to API and get list of all missions and determine
    # if we need to download or skip them as they are already up to date.
    for mission in missionlist:
        if checkmissionfile(mission):
            # Mission is up-to-date
            print('{} - No issue'.format(mission['name']))
        else:
            # Download and overwrite previous file
            downloadmissionfile(mission)
            print('{} - Checksum Failed - File Downloaded'.format(mission['name']))

    # At this step all missions should have been updated successfully.
    mods = "-mod=mods/cba;mods/afrf;mods/usaf;mods/modpack;"
    serverExecutable = r'D:\Steam\steamapps\common\Arma 3 Server\arma3server.exe'
    print('Launching Server')
    aor1Process = subprocess.Popen([serverExecutable, mods, '-checkSignatures','-config=aor1.cfg','-port=2302','-name=aorone', '-serverMod=mods/rrfserver;', '-filePatching'])


if __name__ == "__main__":
    main(sys.argv)