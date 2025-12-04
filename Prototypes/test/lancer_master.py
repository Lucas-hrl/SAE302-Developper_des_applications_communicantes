import sys
import time
from master_crypt import Master, get_ip

if __name__ == "__main__":
    # Récupérer les arguments ou utiliser les valeurs par défaut
    if len(sys.argv) >= 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        ip = get_ip()
        port = int(sys.argv[1])
    else:
        ip = get_ip()
        port = 9016

    print(f"Démarrage du Master sur {ip}:{port}")
    master = Master(ip, port)
    master.demarrer_ecoute()

    # Garder le programme en vie
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du Master...")
        master.running = False
        # Fermer le socket pour débloquer l'accept()
        if master.master_socket_ecoute:
            master.master_socket_ecoute.close()
        print("Master arrêté.")
