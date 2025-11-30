import random
from sympy import isprime


class RSA:
    """
    Classe utilitaire implémentant l'algorithme de chiffrement RSA "à la main".

    Principe :
    RSA repose sur la difficulté mathématique de factoriser un grand nombre entier (n)
    en deux nombres premiers (p et q).
    - Clé Publique (pour chiffrer) : (e, n)
    - Clé Privée (pour déchiffrer) : (d, n)
    """

    @staticmethod
    def pgcd(a, b):
        """
        Calcule le Plus Grand Commun Diviseur (Algorithme d'Euclide).
        Sert à vérifier que deux nombres sont "premiers entre eux" (pas de diviseur commun).
        """
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def inv_modulaire(a, m):
        """
        Calcule l'inverse modulaire de 'a' modulo 'm' via l'Algorithme d'Euclide étendu.

        On cherche un nombre 'x' tel que : (a * x) % m == 1.
        Cela sert à calculer la clé privée 'd' à partir de la clé publique 'e'.
        """
        m0, x0, x1 = m, 0, 1
        if m == 1: return 0
        while a > 1:
            # On effectue des divisions successives
            q = a // m
            m, a = a % m, m
            x0, x1 = x1 - q * x0, x0
        # Si le résultat est négatif, on le remet positif modulo m0
        if x1 < 0: x1 += m0
        return x1

    @staticmethod
    def generer_premier(bits=256):
        """
        Génère un nombre premier aléatoire d'une taille donnée (en bits).
        Utilise la librairie 'sympy.isprime' pour valider le fait qu'il soit primaire.
        """
        while True:
            #On tire un grand nombre entier au hasard
            num = random.getrandbits(bits)
            #On s'assure qu'il est impair (les nombres pairs ne sont pas premiers sauf 2)
            if num % 2 == 0: num += 1
            #On vérifie s'il est premier
            if isprime(num):
                return num

    @staticmethod
    def generer_cles():
        """
        Génère la paire de clés RSA.
        Retourne : ( (e,n), (d,n) ) -> (Clé Publique, Clé Privée)
        """
        print("Génération des nombres premiers p et q...")
        #Choix de deux grands nombres premiers secrets
        p = RSA.generer_premier()
        q = RSA.generer_premier()

        #Calcul du module public n (partie commune aux deux clés)
        n = p * q

        # Calcul de l'indicateur d'Euler (phi)
        # C'est le secret qui permet de lier la clé publique à la clé privée.
        # Si on ne connait pas p et q, il est quasi impossible de trouver phi.
        phi = (p - 1) * (q - 1)

        # Choix de l'exposant public 'e'
        # 65537 est un standard en crypto (bon compromis sécurité/vitesse)
        e = 65537

        # Vérification de sécurité : 'e' doit être premier avec 'phi'
        while RSA.pgcd(e, phi) != 1:
            e = random.randrange(3, phi, 2)

        # Calcul de l'exposant privé 'd'
        # d est l'inverse mathématique de e.
        d = RSA.inv_modulaire(e, phi)

        # On retourne les couples.
        # (e, n) est public : tout le monde peut chiffrer.
        # (d, n) est privé : seul le propriétaire peut déchiffrer.
        return ((e, n), (d, n))

    @staticmethod
    def chiffrer(message_str, cle_publique):
        """
        Chiffre un message texte avec la clé publique.
        Formule : C = M^e mod n
        """
        e, n = cle_publique

        # Conversion du texte en octets (UTF-8)
        m_bytes = message_str.encode('utf-8')

        # Conversion des octets en un immense nombre entier
        # RSA ne fonctionne que sur des nombres, pas sur du texte.
        m_int = int.from_bytes(m_bytes, byteorder='big')

        # Vérification que le message n'est pas plus grand que la clé
        if m_int >= n:
            raise ValueError("Erreur Crypto : Message trop long pour la taille de la clé !")

        # Application de la formule RSA
        # pow(base, exp, mod) calcule (base ** exp) % mod très rapidement
        c_int = pow(m_int, e, n)

        # On renvoie le résultat sous forme de texte (string) pour pouvoir l'envoyer
        return str(c_int)

    @staticmethod
    def dechiffrer(chiffre_str, cle_privee):
        """
        Déchiffre un message (string de nombres) avec la clé privée.
        Formule : M = C^d mod n
        """
        d, n = cle_privee

        # On récupère le grand entier
        c_int = int(chiffre_str)

        # Application de la formule inverse RSA
        # Cela permet de retrouver le nombre original 'm_int'
        m_int = pow(c_int, d, n)

        # Conversion inverse : Nombre entier -> Octets
        # On calcule le nombre d'octets nécessaires pour stocker ce nombre
        # (bit_length + 7) // 8 est une formule standard pour arrondir à l'octet supérieur
        nb_bytes = (m_int.bit_length() + 7) // 8
        m_bytes = m_int.to_bytes(nb_bytes, byteorder='big')

        # Conversion Octets -> Texte original
        return m_bytes.decode('utf-8')