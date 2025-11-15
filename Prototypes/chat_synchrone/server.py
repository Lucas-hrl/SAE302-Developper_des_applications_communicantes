import socket
host = socket.gethostname()
port = 10000
reply = "bye"
print(host)
data = ""

server_socket = socket.socket()  # Création de la socket
server_socket.bind(('0.0.0.0', port))  # Association du host et du port d'écoute
server_socket.listen(1)  # attente de connexion
while data != "arret":
    conn, address = server_socket.accept() #etablissement de la connexion
    data = conn.recv(1024).decode() #réception et decodage des données
    print(data) #affiche le message
    conn.send(reply.encode()) #encode et envoie une réponse
    conn.close()

conn.close()
server_socket.close() #fermeture de la socket