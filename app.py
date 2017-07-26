import os
import requests
import json
import sys
import hashlib
import time
import subprocess
from pathlib import Path
import urllib.request
from urllib.request import urlretrieve
from datetime import timedelta, datetime, tzinfo
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--exe",dest ="armaexecutable", help="ARMA Executable")
parser.add_argument("-n", "--name",dest ="name", help="Server Name")
parser.add_argument("-p", "--port",dest ="port", help="Server Port")
parser.add_argument("-c", "--config",dest ="config", help="Server Config")

RRFMISSIONS = "http://1st-rrf.com/api/missions"
RRFDEPLOYMENT = "https://1st-rrf.com/api/mission-deployment"
MISSIONDIR = r"C:\Users\Guillermo\Development\Python\Capri\MPMissions"
MODS = "-mod=mods/cba;mods/rhsafrf;mods/rhsusaf;mods/modpack;"

def getmissionlist():
    siterequest = requests.get(RRFMISSIONS)
    return siterequest.json()

def getdeploymentstatus():
    siterequest = requests.get(RRFDEPLOYMENT)
    response = siterequest.json()
    return response['deploy']

def postdeploymentstatus(deploymentkey):
    
    siterequest = requests.post(RRFDEPLOYMENT, data = {'RRF_DEPLOYMENT_KEY':deploymentkey})
    response = siterequest.json()
    if response["status"] == 1:
        print("Updated Deployment Status Successfully")
    else:
        print (response["message"])
    
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

def launchserver(serverexecutable, name, port, config):
    #================= Launch Server
    # At this step all missions should have been updated successfully.
    print('Capri - Launching Server')
    print(name)
    process = subprocess.Popen([serverexecutable, MODS, '-checkSignatures','-config='+config,'-port='+port,'-name='+name, '-serverMod=mods/rrfserver;', '-filePatching'])
    return process

def updatemissionfiles():
    # =============== Download Mission Files
    # Connect to API and get list of all missions and determine
    # if we need to download or skip them as they are already up to date.
    missionlist = getmissionlist()
    for mission in missionlist:
        if checkmissionfile(mission):
            # Mission is up-to-date
            print('Capri - {} - No issue'.format(mission['name']))
        else:
            # Download and overwrite previous file
            downloadmissionfile(mission)
            print('Capri - {} - Checksum Failed - File Downloaded'.format(mission['name']))

def main(argv):
    # Grab Mission List and Status
    status = getdeploymentstatus()
    args = parser.parse_args()


    # Import Deployment Key
    with open('.env.json', 'r') as f:
        deploymentkey = json.load(f)
        deploymentkey = deploymentkey["RRF_DEPLOYMENT_KEY"]

    # Get Initial Time
    start = datetime.now()
    start = start.replace(minute=0,second=0)

    # Get expiration time
    expiration = start.replace(hour=start.hour+1)
    
    # Starting Game Server  name, port, config
    gameprocess = launchserver(args.armaexecutable, args.name, args.port, args.config)
    # Begin Program Loop
    while 1:
        #Time Check
        if start > expiration:
            if status:
                # Kill Servers
                print("Capri - Killing ARMA Server")
                gameprocess.terminate()
                time.sleep(20)

                # Update mission files
                print("Capri - Updating Mission Files")
                updatemissionfiles()
                postdeploymentstatus(deploymentkey)
                time.sleep(20)

                # Start Server
                gameprocess = launchserver(args.armaexecutable, args.name, args.port, args.config)
                time.sleep(20)

            # Increase the expiration date by 1 hour
            expiration = expiration.replace(hour=expiration.hour+1)
        # Sleep for 1 minute
        time.sleep(60)
        
        # Update time and status
        start = start.now()
        #TODO HEARTBEAT
        print('Capri - Heartbeat: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
        status = getdeploymentstatus()


if __name__ == "__main__":
    main(sys.argv)