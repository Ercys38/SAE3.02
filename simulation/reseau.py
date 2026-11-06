import queue
import socket
import threading
import time

from . import messages

PORT = 9009
PORT_DECOUVERTE = 9010
APPEL = b"SAE302 qui est le superviseur"
REPONSE = b"SAE302 superviseur "
TAILLE = 4096
ATTENTE = 0.05
DELAI_DECOUVERTE = 3.0


def envoyer_une_ligne(prise, message):
    prise.sendall((messages.encoder(message) + "\n").encode("utf-8"))


def lignes_recues(prise, reste):
    try:
        morceau = prise.recv(TAILLE)
    except socket.timeout:
        return reste, []
    except OSError:
        return reste, None

    if not morceau:
        return reste, None

    reste = reste + morceau.decode("utf-8")
    lignes = reste.split("\n")
    return lignes.pop(), lignes


class Serveur:

    def __init__(self, superviseur, hote="0.0.0.0", port=PORT):
        self.superviseur = superviseur
        self.hote = hote
        self.port = port

        self.prise = None
        self.actif = False
        self.fil = None
        self.clients = 0

    def demarrer(self):
        self.prise = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.prise.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.prise.bind((self.hote, self.port))
        self.prise.listen(1)
        self.prise.settimeout(0.5)

        self.actif = True
        self.fil = threading.Thread(target=self.tourner, name="serveur",
                                    daemon=True)
        self.fil.start()

    def tourner(self):
        while self.actif:
            try:
                connexion, adresse = self.prise.accept()
            except socket.timeout:
                continue
            except OSError:
                return

            self.clients = self.clients + 1
            fil = threading.Thread(target=self.servir, args=(connexion,),
                                   name="client", daemon=True)
            fil.start()

    def servir(self, connexion):
        connexion.settimeout(ATTENTE)
        reste = ""

        while self.actif:
            reste, lignes = lignes_recues(connexion, reste)
            if lignes is None:
                break

            for ligne in lignes:
                if ligne.strip():
                    self.superviseur.envoyer(messages.decoder(ligne))

            for message in self.superviseur.messages_en_attente():
                try:
                    envoyer_une_ligne(connexion, message)
                except OSError:
                    connexion.close()
                    return

        connexion.close()

    def arreter(self):
        self.actif = False
        if self.prise is not None:
            self.prise.close()
            self.prise = None
        if self.fil is not None:
            self.fil.join(timeout=1.0)
            self.fil = None


class ClientSuperviseur:

    def __init__(self, hote="127.0.0.1", port=PORT, feux=None, verrou=None,
                 journal=None):
        self.feux = feux
        self.verrou = verrou
        if self.verrou is None:
            self.verrou = threading.Lock()
        self.journal = journal

        self.prise = socket.create_connection((hote, port), timeout=5)
        self.prise.settimeout(ATTENTE)

        self.recus = queue.Queue()
        self.envoyes = 0
        self.actif = True
        self.compteur = 0

        self.fil = threading.Thread(target=self.ecouter, name="ecoute",
                                    daemon=True)
        self.fil.start()

    def ecouter(self):
        reste = ""
        while self.actif:
            reste, lignes = lignes_recues(self.prise, reste)
            if lignes is None:
                return
            for ligne in lignes:
                if ligne.strip():
                    self.recus.put(messages.decoder(ligne))

    def envoyer(self, message):
        try:
            envoyer_une_ligne(self.prise, message)
            self.envoyes = self.envoyes + 1
        except OSError:
            self.actif = False

    def messages_en_attente(self):
        liste = []
        while True:
            try:
                liste.append(self.recus.get_nowait())
            except queue.Empty:
                return liste

    def tout_liberer(self):
        if self.feux is None:
            return
        with self.verrou:
            for carrefour in self.feux:
                self.feux[carrefour].priorite = None

    def ouvrir_une_intervention(self, densite, service, depart, arrivee):
        self.compteur = self.compteur + 1
        reference = "s" + str(self.compteur)
        self.envoyer(messages.debut_intervention(reference, densite, service,
                                                 depart, arrivee))
        return reference

    def fermer_une_intervention(self, reference, temps_avec=None,
                                temps_sans=None):
        if reference is None:
            return
        self.envoyer(messages.fin_intervention(reference, temps_avec,
                                               temps_sans))

    def demarrer(self):
        return

    def arreter(self):
        self.actif = False
        try:
            self.prise.close()
        except OSError:
            pass
        if self.fil is not None:
            self.fil.join(timeout=1.0)
            self.fil = None


class Annonceur:
    """Repond aux clients qui cherchent le superviseur sur le reseau local."""

    def __init__(self, port_du_serveur=PORT, port=PORT_DECOUVERTE):
        self.port_du_serveur = port_du_serveur
        self.port = port
        self.prise = None
        self.actif = False
        self.fil = None
        self.demandes = 0

    def demarrer(self):
        self.prise = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.prise.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.prise.bind(("", self.port))
        self.prise.settimeout(0.5)

        self.actif = True
        self.fil = threading.Thread(target=self.tourner, name="annonce",
                                    daemon=True)
        self.fil.start()

    def tourner(self):
        reponse = REPONSE + str(self.port_du_serveur).encode("utf-8")

        while self.actif:
            try:
                question, adresse = self.prise.recvfrom(TAILLE)
            except socket.timeout:
                continue
            except OSError:
                return

            if question.strip() == APPEL:
                self.demandes = self.demandes + 1
                self.prise.sendto(reponse, adresse)

    def arreter(self):
        self.actif = False
        if self.prise is not None:
            self.prise.close()
            self.prise = None
        if self.fil is not None:
            self.fil.join(timeout=1.0)
            self.fil = None


def trouver_le_superviseur(delai=DELAI_DECOUVERTE, port=PORT_DECOUVERTE):
    """Cherche le superviseur en diffusion et rend (adresse, port)."""
    prise = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    prise.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    prise.settimeout(0.5)

    fin = time.monotonic() + delai
    try:
        while time.monotonic() < fin:
            for cible in ("255.255.255.255", "127.0.0.1"):
                try:
                    prise.sendto(APPEL, (cible, port))
                except OSError:
                    continue

            try:
                reponse, adresse = prise.recvfrom(TAILLE)
            except socket.timeout:
                continue

            if not reponse.startswith(REPONSE):
                continue

            texte = reponse[len(REPONSE):].decode("utf-8").strip()
            if texte.isdigit():
                return (adresse[0], int(texte))
            return (adresse[0], PORT)
    finally:
        prise.close()

    return None
