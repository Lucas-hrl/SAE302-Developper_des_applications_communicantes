import socket
import threading

host = '127.0.0.1'
port = 10000

def ecouter(socket: socket):
    while True:
        reply = socket.recv(1024).decode()  # reception et decodage des donnees reçu
        print(reply)  # affichage de la reponse
        if reply == "bye":
            socket.close()
        elif reply == "arret":
            socket.close()
            client2_socket.close()
            break

client2_socket = socket.socket() #Création de la socket
client2_socket.connect((host, port)) #Connexion au host et au port :host = "" -> localhost
t = threading.Thread(target=ecouter, args=(client2_socket,))
t.start()
print("Chat connecté ! Tapez 'bye' pour quitter.")
while True:
    message = input("-> ")
    client2_socket.send(message.encode())  # envoi et codage des donnees
    if message == "bye":
        t.join()
        break
    elif message == "arret":
        t.join()
        break

client2_socket.close() #fermeture de la communication