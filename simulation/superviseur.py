import queue
import threading

from . import ville
from . import messages
from .secours import DISTANCE_ALERTE, DISTANCE_ONDE

ATTENTE = 0.05


class Superviseur:

    def __init__(self, feux=None, verrou=None, journal=None):
        self.feux = feux
        self.verrou = verrou
        if self.verrou is None:
            self.verrou = threading.Lock()
        self.journal = journal

        self.entree = queue.Queue()
        self.sortie = queue.Queue()

        self.priorites = {}
        self.alertes = {}
        self.recus = 0
        self.envoyes = 0

        self.actif = False
        self.fil = None

    def envoyer(self, message):
        self.entree.put(message)

    def repondre(self, message):
        self.sortie.put(message)
        self.envoyes = self.envoyes + 1

    def messages_en_attente(self):
        liste = []
        while True:
            try:
                liste.append(self.sortie.get_nowait())
            except queue.Empty:
                return liste

    def traiter(self, message):
        self.recus = self.recus + 1
        genre = message["type"]
        contenu = message["contenu"]

        if genre == messages.POSITION:
            self.traiter_une_position(message["emetteur"], contenu)
        elif genre == messages.DEMANDE_PRIORITE:
            self.accorder(message["emetteur"], contenu["carrefour"],
                          contenu["axe"])
        elif genre == messages.LIBERATION:
            self.liberer(message["emetteur"], contenu["carrefour"])

    def traiter_une_position(self, emetteur, contenu):
        carrefour = contenu["carrefour"]
        distance = contenu["distance"]
        axe = contenu["axe"]

        if distance > DISTANCE_ALERTE:
            return

        self.alertes[carrefour] = distance
        self.repondre(messages.alerte_proximite(carrefour, axe, distance))

        if distance <= DISTANCE_ONDE:
            self.accorder(emetteur, carrefour, axe)

    def a_des_feux(self, carrefour):
        if self.feux is not None:
            return carrefour in self.feux
        if carrefour not in ville.CARREFOURS:
            return False
        return ville.CARREFOURS[carrefour]["feux"]

    def regler_un_feu(self, carrefour, axe):
        if self.feux is None or carrefour not in self.feux:
            return
        with self.verrou:
            self.feux[carrefour].priorite = axe

    def accorder(self, emetteur, carrefour, axe):
        if not self.a_des_feux(carrefour):
            return

        proprietaire = self.priorites.get(carrefour)
        if proprietaire is not None and proprietaire != emetteur:
            return

        self.regler_un_feu(carrefour, axe)
        self.priorites[carrefour] = emetteur
        self.repondre(messages.accord_priorite(carrefour, axe))

    def liberer(self, emetteur, carrefour):
        if self.priorites.get(carrefour) != emetteur:
            return

        self.regler_un_feu(carrefour, None)
        self.priorites.pop(carrefour, None)
        self.alertes.pop(carrefour, None)
        self.repondre(messages.creer(messages.LIBERATION, "superviseur",
                                     {"carrefour": carrefour}))

    def tout_liberer(self):
        for carrefour in list(self.priorites):
            self.regler_un_feu(carrefour, None)
            self.repondre(messages.creer(messages.LIBERATION, "superviseur",
                                         {"carrefour": carrefour}))
        self.priorites.clear()
        self.alertes.clear()

    def ouvrir_une_intervention(self, densite, service, depart, arrivee):
        if self.journal is None:
            return None
        return self.journal.enregistrer(densite, service, depart, arrivee)

    def fermer_une_intervention(self, identifiant, temps_avec=None,
                                temps_sans=None):
        if self.journal is None or identifiant is None:
            return
        self.journal.completer(identifiant, temps_avec, temps_sans)

    def tourner(self):
        while self.actif:
            try:
                message = self.entree.get(timeout=ATTENTE)
            except queue.Empty:
                continue
            self.traiter(message)

    def demarrer(self):
        self.actif = True
        self.fil = threading.Thread(target=self.tourner, name="superviseur",
                                    daemon=True)
        self.fil.start()

    def arreter(self):
        self.actif = False
        if self.fil is not None:
            self.fil.join(timeout=1.0)
            self.fil = None
