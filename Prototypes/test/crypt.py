import random

class CryptoSym:
    """Petit chiffrement symétrique XOR, même clé pour chiffrer/déchiffrer."""

    def __init__(self, cle=None, longueur_cle=16):
        if cle is None:
            self.cle = self.generer_cle(longueur_cle)
        else:
            self.cle = cle

    @staticmethod
    def generer_cle(longueur):
        caracteres = []
        for _ in range(longueur):
            code_ascii = random.randint(33, 126)
            caracteres.append(chr(code_ascii))
        return "".join(caracteres)

    def get_cle(self):
        return self.cle

    def _xor_octets(self, donnees_bytes):
        cle_bytes = self.cle.encode("latin1")
        n = len(cle_bytes)
        res = bytearray()
        for i, b in enumerate(donnees_bytes):
            k = cle_bytes[i % n]
            res.append(b ^ k)
        return bytes(res)

    def chiffrer(self, texte_clair: str) -> bytes:
        data = texte_clair.encode("latin1", errors="ignore")
        return self._xor_octets(data)

    def dechiffrer(self, donnees_chiffrees: bytes) -> str:
        data = self._xor_octets(donnees_chiffrees)
        return data.decode("latin1", errors="ignore")
