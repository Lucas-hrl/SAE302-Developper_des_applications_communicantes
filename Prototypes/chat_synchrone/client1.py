import socket
host = '127.0.0.1'
port = 10000
message = "arret"
reply = ""

client1_socket = socket.socket()  # Création de la socket
client1_socket.connect((host, port))  # Connexion au host et au port :host = "" -> localhost
while reply != "bye":

    client1_socket.send(message.encode()) #envoi et codage des donnees
    reply = client1_socket.recv(1024).decode() # reception et decodage des donnees reçu
    print(reply) #affichage de la reponse
client1_socket.close()  # fermeture de la communication