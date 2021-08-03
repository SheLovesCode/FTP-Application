########## AUTHOR: DIANA MUNYARADZI ##########
########## STUDENT NUMBER: 1034382 ###########
############ CLIENT SOURCE CODE ##############

import os
import sys
import time
import math
import socket

class FTPclient:
    def __init__(self, clientName):

         # Initialize class variables
        self.user = None
        self.alive = False
        self.retrieveMessage = []
        self.IPsocket = None
        self.loggedIn = False
        self.DTPsocket = None
        self.errorResponse = False
        self.remoteDirectoryList = []
        self.statusMessage = ' '
        self.clientName = clientName
        
    def initConnection(self, serverIPname, serverIPport):

        self.serverIPname = serverIPname
        self.serverIPport = serverIPport
       
        self.IPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Try to connect to server
        try:

            self.IPsocket.connect((self.serverIPname, self.serverIPport))
            print(self.IPsocket.recv(8192).decode())

        except:

            errorMessage = 'Failed to connect ' + self.serverIPname
            self.statusMessage = errorMessage
            print(errorMessage)
            self.errorResponse = True
            time.sleep(3)
            return

        self.alive = True
        
        print('Connected to Server ;)')
    
    def getStatus(self):
        
        return self.statusMessage

    def login(self, userName, password):

        # enter username
        cmd = 'USER ' + userName
        self.send(cmd)
        self.printServerReply(self.getServerReply())

        if not self.errorResponse:
            # enter password
            cmd = 'PASS ' + password
            self.send(cmd)
            self.printServerReply(self.getServerReply())

            if not self.errorResponse:
                self.loggedIn = True
                self.user = userName
                message =('Login Success\n')
                print(message)
                self.statusMessage = message
                

    def send(self, cmd):
        # Sending commands to server
        self.IPsocket.send((cmd + '\r\n').encode())
        # Dont print or log the password
        if cmd[:4] != 'PASS':
            print('Client: ', cmd)
            self.retrieveMessage.append('Client: ' + cmd)

    def getServerReply(self):

        response = self.IPsocket.recv(8192).decode()
        self.retrieveMessage.append('Server: ' + response)

        # Notify if this an error
        if response[0] != '5' and response[0] != '4':
            self.errorResponse = False
        else:
            self.errorResponse = True
        return response

    def printServerReply(self, response):
        print('Server :', response)
    
    # Establishes mode of transfer
    def setMode(self, mode):
        if mode.upper() == 'I' or mode.upper() == 'A':
            self.mode = mode
            cmd = 'TYPE '  + mode
            self.send(cmd)
            self.printServerReply(self.getServerReply())

        else:
            message = ('Client : Error unknown mode')
            self.statusMessage = message
            print(message)


    def startPassiveDTPconnection(self):

        # Ask for a passive connection
        cmd = 'PASV'
        self.send(cmd)
        response = self.getServerReply()
        self.printServerReply(response)

        if not self.errorResponse:
            firstIndex = response.find('(')
            endIndex = response.find(')')

            # Obtain the server DTP address and Port
            address = response[firstIndex+1:endIndex].split(',')
            self.serverDTPname = '.'.join(address[:-2])
            self.serverDTPport = (int(address[4]) << 8) + int(address[5])
            print(self.serverDTPname, self.serverDTPport)

            try:
                # Connect to the server DTP
                self.DTPsocket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.DTPsocket.connect(
                    (self.serverDTPname, self.serverDTPport))
                self.statusMessage = 'Passive Connection Success, Ready to receive'
                print('Passive Connection Success, Ready to receive\n')
                
                self.dataConnectionAlive = True

            except:

                print('Failed to connect to ', self.serverDTPname)
                self.statusMessage = 'Failed to connect to '+ self.serverDTPname
                self.dataConnectionAlive = False
                time.sleep(3)
                return

    def startActiveConnection(self):

        # Request for an active connection
        self.clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clientSocket.bind((self.clientName,0))
        self.clientSocket.listen(1)

        ip, port = self.clientSocket.getsockname()
         
        # Prepare the IP address and port with respect to the RFC959 standard
        ip = ip.split('.')
        ip = ','.join(ip)
        p1 = math.floor(port/256)
        p2 = port%256
    
        print('Requested...\n IP: ' + ip + '\nPort: ' + str(port))
        self.statusMessage = 'Requested... IP: ' + ip + 'Port: ' + str(port)
        
        cmd = 'PORT ' + ip + ',' + str(p1) + ',' + str(p2)
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        
        # Establish the connection
        self.DTPsocket, address = self.clientSocket.accept()
        print('Connected to :' , address)
        self.statusMessage  = 'Connected to :' +  str(address)
        self.dataConnectionAlive = True


    def getList(self):
        
        self.remoteDirectoryList = []
        if self.dataConnectionAlive and self.alive:

            cmd = 'LIST'
            self.send(cmd)
            self.printServerReply(self.getServerReply())
            
            print('\nReceiving Data...\n')
            self.statusMessage = 'Receiving Data...'

            while True:
                # Get the directory list
                data = self.DTPsocket.recv(1024)
                print(data.decode())
                self.remoteDirectoryList.append(data.decode())

                if not data:
                    break

            print('Directory Listing Done!\n')
            self.statusMessage ='Directory Listing Done!'
            self.DTPsocket.close()
            self.printServerReply(self.getServerReply())
    
    def downloadFile(self,fileName):
        
        cmd = 'RETR ' +  fileName
        self.send(cmd) # Send download command
        self.printServerReply(self.getServerReply()) # Print the response from the server
         
        if not self.errorResponse:
            
            # Create Downloads folder if not exist
            downloadFolder = 'Downloads'
            if not os.path.exists(downloadFolder):
                os.makedirs(downloadFolder)
            
            # Mode of data transfer
            if self.mode == 'I':
                outfile = open(downloadFolder + '/' + fileName, 'wb')
            else:
                outfile = open(downloadFolder + '/' + fileName, 'w')
            
            # Receive the data packets
            print('Receiving data...')
            self.statusMessage = 'Receiving data...'
            
            while True:
                data = self.DTPsocket.recv(8192)
                if not data:
                    break
                outfile.write(data)
            outfile.close()

            print('Transfer Succesful')
            self.statusMessage = 'Transfer Successfull'
            self.DTPsocket.close()
            self.printServerReply(self.getServerReply())
            
    
    def uploadFile(self,filePath):
        #Check if file path is valid
        if os.path.exists(filePath):
            # Get the file name
            if '/' in filePath:
                f_index = filePath.rindex('/')
                fileName = filePath[f_index+1:]
            else:
                fileName = filePath

            # Send Command
            cmd = 'STOR ' + fileName
            self.send(cmd)
            self.printServerReply(self.getServerReply())
        
            # Check if there are any errors
            if not self.errorResponse:
                print('Uploading ' + fileName + ' to server...')
                self.statusMessage = 'Uploading ' + fileName + ' to server...'

                if self.mode == 'I':
                    uFile = open(filePath, 'rb')
                else:
                    uFile = open(filePath, 'r')
                
                # Send packets of the file
                data =  uFile.read(8192)

                while data:
                    if self.mode == 'I':
                        self.DTPsocket.send(data)
                    else:
                        self.DTPsocket.send(data.encode())
                    data = uFile.read(8192)

                uFile.close()
                print('Upload was successful')
                self.statusMessage = ' Upload Success'
                self.DTPsocket.close()
                self.printServerReply(self.getServerReply())
                
        else:
            print('Error: invalid path!')
            self.statusMessage = 'Error: invalid path!'
            self.DTPsocket.close()
            
    def returnDirList(self):
        return self.remoteDirectoryList
    
    def getComm(self):
        return self.retrieveMessage
    
    def clearComm(self):
        self.retrieveMessage.clear()
    
    # Create a new directory on the server
    def makeDir(self,folderName):
        cmd = 'MKD ' + folderName
        self.send(cmd)
        self.printServerReply(self.getServerReply())
    
    # Delete directory on server
    def remDir(self,folderName):
        cmd = 'RMD ' + folderName
        self.send(cmd)
        self.printServerReply(self.getServerReply())

    # Change working directory
    def changeWD(self,dir_):
        cmd = 'CWD ' + dir_
        self.send(cmd)
        self.printServerReply(self.getServerReply())

    # Log user out (closes TCP connection)    
    def logout(self):
        cmd = 'QUIT'
        self.send(cmd)
        self.printServerReply(self.getServerReply())
        self.statusMessage = 'Logged out, Connection Closed'
        
    def checkConnection(self):
        cmd = 'NOOP'
        self.send(cmd)
        self.printServerReply(self.getServerReply())
