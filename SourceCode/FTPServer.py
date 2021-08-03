########## AUTHOR: DIANA MUNYARADZI ##########
########## STUDENT NUMBER: 1034382 ###########
############ SERVER SOURCE CODE ##############

import os
import time
import math
import socket
import threading

class serverThread(threading.Thread):
    
    # Initialize parameters
    def __init__(self, connection, address, userDatabase, currentDirectory, IP, port):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address
        self.serverIP = IP
        self.serverPort = port
        self.baseWD = currentDirectory
        self.cwd = self.baseWD
        self.rest = False
        self.PASVmode = False
        self.isLoggedIn = False
        self.users = userDatabase
        self.validUser = False
        self.isConnected = True
        self.islist = False
        self.mode = 'I' #Default Mode which is the ASCII mode
        self.allowDelete = True
    
    def run(self):

        self.isConnected = True
        # Welcome Message
        response = "220 Welcome to your local host"
        self.sendReply(response)
        # Wait for connection from client (Continuous polling)
        while True:
            cmd = self.connection.recv(256).decode()
            
            if not cmd or not self.isConnected : break
            else:
                print('Received: ', cmd)
                try:
                    func = getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception as err:
                    print('Error: ', err)
                    response = '500 Syntax error, command unrecognized.'
                    self.sendReply(response)
        
        self.connection.close() # Close the connection
   
    def sendReply(self,reply):
        self.connection.send((reply + '\r\n').encode())
    
    def notLoggedInMessage(self):
        response = '530 Please login with USER and PASS.'
        self.sendReply(response)

    def paramError(self,cmd):
        response = '501 \'' + cmd[:-2] + '\': parameter not understood.' 
        self.sendReply(response)
    
    # Resetting the server status
    def resetState(self):
        self.isLoggedIn = False
        self.validUser = False
        self.user = None


    def SYST(self,cmd):
        response = '215 UNIX Type: L8.'
        self.sendReply(response)
    
    def USER(self,cmd):
        self.resetState() # Reset user status
        self.user = cmd[5:-2] # Extract username in the command
        users = open(self.users, 'r').read() # Open the database with the registered users
        
        # Check if user exists on the database
        for u in users.split('\n'):
            if self.user == u.split(' ')[0] and len(u.split(' ')[0]) != 0:
                self.validUser = True
                response = '331 User name okay, need password.'
                self.sendReply(response)
                break
                
        if not self.validUser:    
            response = '530 Invalid User.'
            self.sendReply(response)
            self.validUser = False
    
    def PASS(self,cmd):
        if self.validUser:
            password = cmd[5:-2]
            pws = open(self.users, 'r').read()

            # Check if password matches user
            for p in pws.split('\n'):
                if len(p.split(' ')[0]) != 0:
                    if password == p.split(' ')[1] and self.user == p.split(' ')[0]:
                        self.isLoggedIn = True
                        response = '230 User logged in, proceed.'
                        self.sendReply(response)
                        break

            if not self.isLoggedIn:
                response = '530 Invalid password for '  + self.user
                self.sendReply(response)
        else:
            self.notLoggedInMessage()
    
    def QUIT(self,cmd):

        if self.isLoggedIn:
            self.resetState()
            response = '221 Logged out'
            self.sendReply(response)
    
        else:
            response = '221 Service closing control connection'
            self.sendReply(response)
            self.isConnected = False
        

    def STRU(self,cmd):
         # Obsolete command
        stru = cmd[5]

        if stru == 'F':
            response = '200 F.'
        else:
            response = '504 Command obsolete'

        self.sendReply(response)

    def MODE(self,cmd):
        
        # Obsolete command
        mode = cmd[5]

        if mode == 'S':
            response = '200 MODE set to stream.'
        else:
            response = '504 Command obsolete'

        self.sendReply(response)

     # Checks if Protocol Interpreter connection is alive  
    def NOOP(self,cmd):
        response = '200 OK.'
        self.sendReply(response)
    
    def TYPE(self,cmd):

        # ASCII or Binary Mode
        mode = cmd[5]
        
        # Confirm I or A
        if mode.upper() == 'I':
            self.mode = mode
            response = '200 Binary mode.'
            self.sendReply(response)
        elif mode.upper() == 'A':
            self.mode = mode
            response = '200 ASCII mode.'
            self.sendReply(response)
        else:
            # Unknown parameter
            self.paramError(cmd)

    def PWD(self,cmd):
        
        # Cant't print working directory if not looged in
        if self.isLoggedIn:
            
            # The path relative to the root
            tempDir = '/' + self.cwd
            cwd = os.path.relpath(tempDir,'/')
            
            if cwd == '.':
                cwd = '/'
            else:
                cwd = '/' + cwd 
            response = '257' + ' "' + cwd + '" is the current dir.'
            self.sendReply(response)

        else:
            self.notLoggedInMessage()

    def CWD(self,cmd):

        if self.isLoggedIn: 
            # Retrieve the directory
            chwd = cmd[4:-2]
         
            # Determine the base directory
            if chwd == '.' or chwd == '/':
                self.cwd = self.baseWD
                response = '250 OK.'
                self.sendReply(response)
            else:
            
                # Consider /dir or dir
                if chwd[0] == '/':
                    chwd = chwd[1:]

                tempWorkDirectory = os.path.join(self.cwd, chwd)
            
                # Validating path
                if os.path.exists(tempWorkDirectory):
                    self.cwd = tempWorkDirectory
                    response = '250 OK.'
                    self.sendReply(response)
                else:
                    response = '550 The system cannot find the file specified.'
                    self.sendReply(response)
           
        else:
            self.notLoggedInMessage()

    def PASV(self,cmd):
        if self.isLoggedIn:

            # Establish passive mode 
            self.PASVmode = True

            # Establish TCP connection 
            self.serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.serverSocket.bind((self.serverIP,0))
            self.serverSocket.listen(1)
            ip, port = self.serverSocket.getsockname()
        
            # Format IP address according to RFC959 memo
            ip = ip.split('.')
            ip = ','.join(ip)
        
            # Establish port number according to the RFC959 memo
            a1 = math.floor(port/256)
            a2 = port%256
            print('Open...\nIP: ' + str(ip) +'\nPORT: '+ str(port))
        
            # Send the IP address and port number to the client
            response = '227 Entering Passive Mode (' + str(ip) + ',' + str(a1) + ',' +str(a2) + ').'
            self.sendReply(response)

        else:
            self.notLoggedInMessage()

    def PORT(self,cmd):
        
        # Cant't try to establish connection without logging in
        if self.isLoggedIn:
    
            # check if Passive Mode
            if self.PASVmode:
                self.serverSocket.close()
                self.PASVmode = False

            # Split the connection settings
            conSettings = cmd[5:].split(',')
        
            # Generate the IP address from the connection settings 
            self.DTPaddr = '.'.join(conSettings[:4])

            # Generate the PORT from the connection settings
            # This is with respect to RFC959
            self.DTPport = ((int(conSettings[4])<<8)) + int(conSettings[5])
            
            print('Connected to :', self.DTPaddr, self.DTPport)
            # Acknowledge
            response = '200 Got it.'
            self.sendReply(response)

            self.DTPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.DTPsocket.connect((self.DTPaddr,self.DTPport))

        else:
            self.notLoggedInMessage()

    def startDTPsocket(self):
        
        try:
            if self.PASVmode:
                self.DTPsocket, address = self.serverSocket.accept()
                print('connect: ', address)
                
        except socket.error:
            response = '425 Failed to establish data connection'
            self.sendReply(response)

    def stopDTPsocket(self):

        self.DTPsocket.close()
        if self.PASVmode:
            self.serverSocket.close()
    
    # Establish mode of sending data
    def sendData(self, data):
        if not self.islist and self.mode == 'I':
            self.DTPsocket.send((data))   
        else:
            self.DTPsocket.send((data+'\r\n').encode())

    # Prints the directory list
    def LIST(self, cmd):
        if self.isLoggedIn:

            response = '150 File status okay; about to open data connection.'
            self.sendReply(response)
            print('Directory list ', self.cwd)
            
            # Prepare the socket for a pending data transfer
            self.startDTPsocket()

            # Retrieve each file from the list
            for l in os.listdir(self.cwd):
                ll = self.toList(os.path.join(self.cwd,l))

                # Send as str/ASCII
                self.islist = True
                self.sendData(ll)
                self.islist = False
            self.stopDTPsocket()

            response = '200 Listing completed.'
            self.sendReply(response)

        else:
            self.notLoggedInMessage()
    
    def toList(self,l):

        st = os.stat(l)
        fullmode ='rwxrwxrwx'
        mode = ''
        
        # Prepare the directory listing so it matches the RFC959 memo
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        
        d = (os.path.isdir(l)) and 'd' or '-'
        fhist = time.strftime(' %b %d %H:%M ',time.gmtime(st.st_mtime))
        return d + mode+ '\t1 user'+'\t group \t\t' + str(st.st_size) + '\t' + fhist + '\t' + os.path.basename(l)
    
    def MKD(self,cmd):

        #Can't make new directory if not logged in
        if self.isLoggedIn:
            dirName = os.path.join(self.cwd,cmd[4:-2])
            os.mkdir(dirName)
            response = '257 Directory created.'
            self.sendReply(response)
        else:
            self.notLoggedInMessage()

    def RMD(self,cmd):
        
        # Can't delete directory if not logged in
        if self.isLoggedIn:
            
            dirName = os.path.join(self.cwd,cmd[4:-2])

            # Check if specified path exists

            if os.path.exists(dirName):

                # Allow deletion if only deletion is allowed
                if self.allowDelete:
                    os.rmdir(dirName)
                    response = '250 Directory deleted.'
                    self.sendReply(response)
                else:
                    response = '450 Not allowed.'
                    self.sendReply(response)
            else:
                response = '550 The system cannot find the file specified.'
                self.sendReply(response)
        else:
            self.notLoggedInMessage()

      
    def STOR(self,cmd):
        if self.isLoggedIn:

            # Create file path
            fileName = os.path.join(self.cwd,cmd[5:-2])
            print('Uploading: ', fileName)

            # Establish mode to use
            if self.mode == 'I':
                oFile = open(fileName,'wb')
            else:
                oFile = open(fileName, 'w')
        
            response = '150 Opening data connection.'
            self.sendReply(response)

            # Ready the socket for upload
            self.startDTPsocket()
            
            while True:
                data = self.DTPsocket.recv(8192)
                #print(data)
                if not data: 
                    break
                oFile.write(data)
            
            self.stopDTPsocket()
            response = '226 Transfer complete.'
            self.sendReply(response)
            print('Upload completed successfully')
            oFile.close()
            
        else:
            self.notLoggedInMessage()

    def RETR(self,cmd):

        # Cant retrieve files if not logged in
        if self.isLoggedIn:
         
            fileName = os.path.join(self.cwd, cmd[5:-2])
            
            # For Filezilla
            if fileName[0] == '/':
                fileName = fileName[1:]
            
            # Check if file exist
            if os.path.exists(fileName):
                print('Downloading :', fileName)
             
                 # Mode?
                if self.mode == 'I':
                    rFile = open(fileName, 'rb')
                else:
                    rFile = open(fileName, 'r')
                    
             
                # Open data connection
                response = '150 Opening file data connection.'
                self.sendReply(response)

                # Read file 8192 bytes at a time
                data = rFile.read(8192)
                self.startDTPsocket()
               
                # Send the file
                while data:
                    self.sendData(data)
                    data = rFile.read(8192)
                rFile.close()
                self.stopDTPsocket()
                response = '226 Transfer complete.'
                self.sendReply(response)
            else:
                # File does not exist or the path does not exist
                response = '550 The system cannot find the file specified.'
                self.sendReply(response)
        else:
            self.notLoggedInMessage()


# Class waits for client to request TCP connection        
class FTPserver(threading.Thread):

    def __init__(self,userDatabase,homeDirectory,IP,Port):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.serverIP = IP
        self.serverPort = Port
        self.sock.bind((self.serverIP, self.serverPort))
        self.userDatabase = userDatabase
        self.homeDirectory = homeDirectory
        threading.Thread.__init__(self)
    
    def run(self):
        self.sock.listen(5)
        while True:
            connectionSocket, address = self.sock.accept()
            thread = serverThread(connectionSocket, address,self.userDatabase, self.homeDirectory,self.serverIP,self.serverPort)
            thread.daemon = True
            thread.start()
    
    def stop(self):
        self.sock.close()

def Main():
    
    serverPort = 21
    serverIP =  socket.gethostbyname(socket.gethostname())
    
    # Database with registered users login details
    users = './registeredUsers.txt'

    # Default directory
    homeDirectory = '.'

    # Create a new thread for each new connection
    clientThread = FTPserver(users,homeDirectory,serverIP,serverPort)
    clientThread.daemon = True
    clientThread.start()

    print('On server IP:', serverIP, 'Port number: ', serverPort)
    input('Enter to end...\n')
    clientThread.stop()
    
Main() # Run the main function