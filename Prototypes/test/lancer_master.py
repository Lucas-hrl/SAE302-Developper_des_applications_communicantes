"""
Script de lancement du Master.
Usage : python lancer_master.py <PORT> [IP_ECOUTE]
"""

import sys
import time
from master_crypt import Master, get_ip

if __name__ == "__main__":
    # On force au moins un argument (le port)
    if len(sys.argv) < 2:
        print("Usage : python lancer_master.py <PORT> [IP_ECOUTE]")
        print("Exemple : python lancer_master.py 9016")
        print("Exemple : python lancer_master.py 9016 192.168.1.28")
        sys.exit(1)

    # Récupération des arguments
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Erreur : Le port doit être un nombre entier.")
        sys.exit(1)

    # Si l'IP est donnée on la prend, sinon on détecte l'IP locale
    if len(sys.argv) >= 3:
        ip = sys.argv[2]
    else:
        ip = get_ip()

    print(f"--- Lancement du Master sur {ip}:{port} ---")

    # On instancie le Master
    master = Master(ip, port)

    # Démarrage de l'écoute
    master.demarrer_ecoute()

    print(">> Master en ligne. En attente de routeurs...")
    print(">> Ctrl+C pour arrêter.\n")

    # Boucle infinie pour garder le programme actif
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du Master...")
        master.running = False
        if master.master_socket_ecoute:
            try:
                master.master_socket_ecoute.close()
            except:
                pass
        print("Master arrêté proprement.")