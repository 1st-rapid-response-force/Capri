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
RRFHEARTBEAT = "http://1st-rrf.app/api/overlord/heartbeat"

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
    
    def checkserverstatus(self):
        arma = "arma3server_x64.exe"
        statuslist = []
        
        for proc in psutil.process_iter():
            if proc.name() == arma:
                commandline = proc.cmdline()
                port = proc.cmdline()
                port = port[3][6:10]
                processstatus = proc.status()
                name = ""

                # Assign name based on Port
                if port == "2302":
                    name = "aor1"
                if port == "2312":
                    name = "aor2"
                if port == "2322":
                    name = "training"

                status = {'name': name, 'port':port,'status':processstatus, 'data':{'cpu':proc.cpu_percent(interval=None), 'memory':proc.memory_percent()}}
                statuslist.insert(0,status)
        return statuslist

    def postheartbeat(self,deploymentkey, server):
        for server in config['servers']:
            statuslist = self.checkserverstatus()
            for status in statuslist:
                datajson = json.dumps(status['data'])
                siterequest = requests.post(RRFHEARTBEAT, data = {'RRF_DEPLOYMENT_KEY':deploymentkey, 'server': status['name'],'port':status['port'],'status':status['status'],'data':datajson})
                response = siterequest.json()
                if response["status"] == 1:
                    print('Capri - Heartbeat - '+str(datetime.now()))
                else:
                    print (response["message"])

            return siterequest.json()

    def verifychecksum(self, file, checksum):
        computedhash = hashlib.md5(open(file,'rb').read()).hexdigest()
        if(computedhash == checksum):
            return 1
        else:
            return 0

    def checkmissionfile(self, mission):
        missionfile = Path(config['mpmissions']+'/'+mission['filename'])
        if missionfile.is_file() :
            if self.verifychecksum(missionfile, mission['checksum']):
                return 1
            else:
                return 0
        else:
            return 0

    def downloadmissionfile(self, mission):
        missionfile = Path(config['mpmissions']+'/'+mission['filename'])
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
            self.killservers()
            self.updatemissionfiles()
            self.startservers()
            self.postheartbeat()

        if self.data.decode("utf-8") == "RRF_SERVERSTATUS":
            self.postheartbeat()

        if self.data.decode("utf-8") == "RRF_STARTSERVERS":
            self.startservers()
        if self.data.decode("utf-8") == "TEST":
            statuslist = self.postheartbeat(deploymentkey,config['servers'])
            print(statuslist)

        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

if __name__ == "__main__":
    # Import Server Config
    with open('config.json', 'r') as f:
        config = json.load(f)

    HOST, PORT = config["host"], 4475

    # Create the server, binding to localhost on port 4475
    server = socketserver.TCPServer((HOST, PORT), Capri)
    print("CSM - Started Server - Listening")
    # Import Deployment Key
    with open('.env.json', 'r') as f:
        deploymentkey = json.load(f)
        deploymentkey = deploymentkey["RRF_DEPLOYMENT_KEY"]

    arma = "arma3server_x64.exe"
    for proc in psutil.process_iter():
        if proc.name() == arma:
            port = proc.cmdline()
            print(proc.cpu_percent(interval=None))
            print(port[3][6:10])
            print(proc.cpu_percent(interval=None))
        
    pass

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()