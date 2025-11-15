import socket
host = '127.0.0.1'
port = 10000
message = "coucou"
reply = ""


client2_socket = socket.socket() #Création de la socket
client2_socket.connect((host, port)) #Connexion au host et au port :host = "" -> localhost
while reply != "bye":
    client2_socket.send(message.encode()) #envoi et codage des donnees
    reply = client2_socket.recv(1024).decode() # reception et decodage des donnees reçu
    print(reply) #affichage de la reponse

client2_socket.close() #fermeture de la communication