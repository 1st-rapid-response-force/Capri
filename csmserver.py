import socketserver
import os
import requests
import json
import sys
import hashlib
import time
import subprocess
import urllib.request
import psutil
from urllib.request import urlretrieve
from datetime import timedelta, datetime, tzinfo
from pathlib import Path

RRFMISSIONS = "http://1st-rrf.com/api/missions"
RRFDEPLOYMENT = "https://1st-rrf.com/api/mission-deployment"
MISSIONDIR = r"C:\Program Files (x86)\Steam\steamapps\common\Arma 3 Server\MPMissions"

class Capri(socketserver.BaseRequestHandler):
    def getmissionlist(self):
        siterequest = requests.get(RRFMISSIONS)
        return siterequest.json()

    def getdeploymentstatus(self):
        siterequest = requests.get(RRFDEPLOYMENT)
        response = siterequest.json()
        return response['deploy']

    def postdeploymentstatus(self, deploymentkey):

        siterequest = requests.post(RRFDEPLOYMENT, data = {'RRF_DEPLOYMENT_KEY':deploymentkey})
        response = siterequest.json()
        if response["status"] == 1:
            print("Updated Deployment Status Successfully")
        else:
            print (response["message"])

        return siterequest.json()

    def postheartbeat(deploymentkey):
        pass

    def verifychecksum(self, file, checksum):
        computedhash = hashlib.md5(open(file,'rb').read()).hexdigest()
        if(computedhash == checksum):
            return 1
        else:
            return 0

    def checkmissionfile(self, mission):
        missionfile = Path(MISSIONDIR+'/'+mission['filename'])
        if missionfile.is_file() :
            if self.verifychecksum(missionfile, mission['checksum']):
                return 1
            else:
                return 0
        else:
            return 0

    def downloadmissionfile(self, mission):
        missionfile = Path(MISSIONDIR+'/'+mission['filename'])
        req = urllib.request.Request(mission['download'], headers={'User-Agent': 'Mozilla/5.0'})
        page = urllib.request.urlopen(req)
        downloadedfile = page.read()
        localfile = open(missionfile,'wb')
        localfile.write(downloadedfile)
        localfile.close()

    def updatemissionfiles(self):
        # =============== Download Mission Files
        # Connect to API and get list of all missions and determine
        # if we need to download or skip them as they are already up to date.
        missionlist = self.getmissionlist()
        print('CSM - Juggernaut requesting map update on servers')
        for mission in missionlist:
            if self.checkmissionfile(mission):
                # Mission is up-to-date
                print('CSM - {} - No issue'.format(mission['name']))
            else:
                # Download and overwrite previous file
                self.downloadmissionfile(mission)
                print('CSM - {} - Checksum Failed - File Downloaded'.format(mission['name']))

    def startservers(self):
        for server in config['servers']:
            print('CSM - Launching Server - '+server["name"])
            serverexecutable = server["exec"]
            process = subprocess.Popen([serverexecutable])
            pass
    def killservers(self):
        arma = "arma3server_x64.exe"
        print('CSM - Juggernaut requesting shutdown of all ARMA servers')
        for proc in psutil.process_iter():
            if proc.name() == arma:
                proc.kill()
        print('CSM - Killed all ARMA Servers')
        pass
 

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()

        # Determine Request
        if self.data.decode("utf-8") == "RRF_KILLSERVERS":
            self.killservers()

        if self.data.decode("utf-8") == "RRF_UPDATEMAPS":
            self.updatemissionfiles()

        if self.data.decode("utf-8") == "RRF_SERVERSTATUS":
            self.postheartbeat()

        if self.data.decode("utf-8") == "RRF_STARTSERVERS":
            self.startservers()

        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

if __name__ == "__main__":
    HOST, PORT = "localhost", 4475

    # Create the server, binding to localhost on port 4475
    server = socketserver.TCPServer((HOST, PORT), Capri)
    print("CSM - Started Server - Listening")
    # Import Deployment Key
    with open('.env.json', 'r') as f:
        deploymentkey = json.load(f)
        deploymentkey = deploymentkey["RRF_DEPLOYMENT_KEY"]

    # Import Server Config
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()