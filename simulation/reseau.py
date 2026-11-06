import queue
import socket
import threading

from . import messages

PORT = 9009
TAILLE = 4096
ATTENTE = 0.05


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
        if self.journal is None:
            return None
        return self.journal.enregistrer(densite, service, depart, arrivee)

    def fermer_une_intervention(self, identifiant, temps_avec=None,
                                temps_sans=None):
        if self.journal is None or identifiant is None:
            return
        self.journal.completer(identifiant, temps_avec, temps_sans)

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
