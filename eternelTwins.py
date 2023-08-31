import socket
import threading
import multiprocessing
import time
import json

#Function that allows the node to retrieve its list of neighbors at round "round"
def getNeighbors(id, round):
    neighborsSet = []
    with open("network", "r") as file:
        for line in file.readlines():
            liste = line.split(" ")
            r = int(liste[0])
            src = int(liste[1])
            dst = int(liste[2])
            if(r == round and src == id):
                neighborsSet.append(dst)
    return neighborsSet


#The function responsible for sending messages to neighbors during each round.
"""
The inputs are: 
    myId: the node's ID. 
    round: the current round.
    p: the network period
    n_socket: the node socket. 
    neighborsSet: the list of neighbors. 
    tab: an array of received messages from round 0 to p-1.
    ip: the local IP address for network simulation purposes.
"""
def sendMessage(myId, round, p, n_socket, neighborsSet, tab, ip):
    #To ensure that all nodes are ready to receive messages.
    time.sleep(1)

    if(round < p):
        msg = [str(myId), str(len(neighborsSet))]
        msg = json.dumps(msg) #Convert the message to JSON format before sending it to the neighbor.
        for id in neighborsSet:
            n_socket.sendto(msg.encode("utf-8"), (ip, int(id)))
    else:
        index = round -p 
        msg = json.dumps(tab[index]) #Convert the message to JSON format before sending it to the neighbor.
        for id in neighborsSet:
            n_socket.sendto(msg.encode("utf-8"), (ip, int(id)))




#The function responsible for waiting to receive messages from neighbors during each round.
"""
eternelTwins: List of nodes that are twins with the current node in all previous rounds.
"""
def receiveMsg(round, p, n_socket, myIp, nbN, tab, eternelTwins):
   
    myNeighbors = nbN
    if(round < p):
        msgRound = []
        while nbN > 0:
            message, addr = n_socket.recvfrom(1024)
            #Debuging message
            #print("I am ", myIp, "I received : ", message.decode("utf-8"), " from ", addr)
            nbN-=1
            msgRound.append(json.loads(message.decode("utf-8")))
        msgRound.append([str(myIp), str(myNeighbors)])
        tab.append(msgRound)
    else:
        msgRound = [] 
        #A dictionary that associates each node with the number of common neighbors it has with the current node.
        compt = dict()
        #A dictionary associating each node with the number of its neighbors.
        nbNeighbors = dict()
        
        while nbN > 0:
            message, addr = n_socket.recvfrom(1024)
            message = json.loads(message)
            nbN-=1
            
            #Debuging message
            #print("I am ", myIp, " I received ", message, " from ", message)

            for elm in message:
                if(elm[0] in compt):
                    compt[elm[0]]+=1
                else:
                    compt[elm[0]] = 1 
                    nbNeighbors[elm[0]] = int(elm[1])
        
        if(round == p):
            for key, val in compt.items():
                if(val == myNeighbors and nbNeighbors[key] == myNeighbors and int(key) != int(myIp)):
                    eternelTwins.append(key)
        else:
            for elm in eternelTwins:
                if(elm not in compt or int(compt[elm]) != myNeighbors or int(nbNeighbors[elm]) != myNeighbors):
                    eternelTwins.remove(elm)

def noeud(id, p):

    round = 0
    ip = '127.0.0.1'
    programme_id = int(id)
    
    n_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    n_socket.bind((ip, programme_id))
    
    tab = []
    eternelTwins = []

    while(round != 2*p):
        if(round < p):
            listeNeighbors = getNeighbors(id, round)
        else:
            listeNeighbors = getNeighbors(id, round - p)

        #Debuging message
        #print("The neighbors of ", id, "are ", listeNeighbors)

        message = [str(id), str(len(listeNeighbors))]
        message = json.dumps(message)

        senderThread = threading.Thread(target=sendMessage, args=(programme_id, round, p, n_socket, listeNeighbors, tab, ip))
        recevThread = threading.Thread(target=receiveMsg, args=(round, p, n_socket, id, len(listeNeighbors), tab, eternelTwins))
        
        senderThread.start()
        recevThread.start()
        
        senderThread.join()
        recevThread.join()
    
       
        #Send to the master process that I finished my round
        n_socket.sendto("exit".encode("utf-8"), (ip, 3000))
        msg, addr = n_socket.recvfrom(1024)

        while int(addr[1]) != 3000:
            msg, addr = n_socket.recvfrom(1024)

        round = int(msg.decode("utf-8"))
        #Debuging message
        #print('I am ', programme_id, ", my round is ", round)
        time.sleep(0.05)
        if(round == 2*p):
            print("I am", id, "my eternel twins are : ", eternelTwins)

    n_socket.close()

def getNodesId():
    nodesId = []
    with open("nodesId", "r") as file:
        lines = file.readlines()
        for elm in lines:
            nodesId.append(int(elm))


    return nodesId

def manager(ip, idD, p):
    ip = ip
    idD = idD
    setNodes = getNodesId()
    nbNodes = len(setNodes)
    
    manager_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    manager_socket.bind((ip, idD))

    
    tabProcess = []
    i = 0
    while i < nbNodes:
        #create the processes
        tabProcess.append(multiprocessing.Process(target=noeud, args=(setNodes[i], p)))
        i+= 1
    
    i = 0
    while i < nbNodes:
        tabProcess[i].start()
        i+=1

    round = 0
    while(round < 2*p):
        nbNoued = nbNodes
        while nbNoued > 0:
            msg, adrr = manager_socket.recvfrom(1024)        
            nbNoued -= 1
        round += 1

        for id in setNodes:
            manager_socket.sendto(str(round).encode("utf-8"), (ip, id))
        
    i = 0
    while i < nbNodes:
        tabProcess[i].join()
        i+= 1
    

if __name__ == '__main__':
    manager('127.0.0.1', 3000, 3)
    #liste = getNeighbors(3001, 0)
    


    


