import socket
import threading

host = socket.gethostname()
port = 10000
print(host)


def discuter_client(conn, address):
    reply = ""
    print(f"Nouveau client connecté : {address}")
    data = ""
    while data != "arret":
        data = conn.recv(1024).decode()  # réception et decodage des données
        print(data)  # affiche le message
        if data == "bye":
            reply = "bye"
        elif data == "arret":
            reply = "arret"
        else:
            reply = "reçu"
        conn.send(reply.encode())  # encode et envoie une réponse
    conn.close()

server_socket = socket.socket() #Création de la socket
server_socket.bind(('0.0.0.0', port)) #Association du host et du port d'écoute
server_socket.listen(1) #attente de connexion
while True:
    conn, address = server_socket.accept() #etablissement de la connexion
    t = threading.Thread(target=discuter_client, args=(conn, address,))
    t.start()
    

conn.close()
server_socket.close() #fermeture de la socket