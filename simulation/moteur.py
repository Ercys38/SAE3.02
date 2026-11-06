import threading
import time

from . import ville
from . import messages
from .secours import DISTANCE_ONDE

PAS = 0.033
PERIODE_POSITION = 0.1


class Moteur:

    def __init__(self, simulation, superviseur, verrou=None):
        self.simulation = simulation
        self.superviseur = superviseur

        self.verrou = verrou
        if self.verrou is None:
            self.verrou = superviseur.verrou

        self.facteur = 1
        self.actif = False
        self.fil = None

        self.depuis_la_derniere_position = 0.0
        self.carrefours_tenus = {}
        self.alertes = {}
        self.envoyes = 0
        self.recus = 0

        self.simulation.supervise = True

    def avancer(self, dt):
        with self.verrou:
            self.simulation.avancer(dt)

        self.depuis_la_derniere_position = self.depuis_la_derniere_position + dt
        if self.depuis_la_derniere_position >= PERIODE_POSITION:
            self.depuis_la_derniere_position = 0.0
            self.annoncer_les_secours()

        self.appliquer_les_reponses()

    def secours_en_course(self):
        liste = []
        for v in self.simulation.vehicules:
            if v.prioritaire and not v.sorti:
                liste.append(v)
        return liste

    def annoncer_les_secours(self):
        if not self.simulation.priorite_active:
            self.superviseur.tout_liberer()
            self.carrefours_tenus = {}
            return

        presents = []

        for v in self.secours_en_course():
            presents.append(v.id)
            vises = self.annoncer_un_secours(v)
            self.liberer_les_anciens(v.id, vises)
            self.carrefours_tenus[v.id] = vises

        for identifiant in list(self.carrefours_tenus):
            if identifiant not in presents:
                self.liberer_les_anciens(identifiant, [])
                self.carrefours_tenus.pop(identifiant, None)

    def annoncer_un_secours(self, vehicule):
        vises = []

        axe = ville.axe(vehicule.depuis, vehicule.vers)
        self.emettre(messages.position(vehicule, vehicule.vers,
                                       vehicule.reste, axe))
        vises.append(vehicule.vers)

        if vehicule.suivant is None or vehicule.reste > DISTANCE_ONDE:
            return vises

        axe_suivant = ville.axe(vehicule.vers, vehicule.suivant)
        self.emettre(messages.position(vehicule, vehicule.suivant,
                                       vehicule.reste, axe_suivant))
        vises.append(vehicule.suivant)
        return vises

    def liberer_les_anciens(self, identifiant, vises):
        anciens = self.carrefours_tenus.get(identifiant, [])
        for carrefour in anciens:
            if carrefour not in vises:
                self.emettre(messages.creer(messages.LIBERATION, identifiant,
                                            {"carrefour": carrefour}))

    def emettre(self, message):
        self.superviseur.envoyer(message)
        self.envoyes = self.envoyes + 1

    def appliquer_les_reponses(self):
        for message in self.superviseur.messages_en_attente():
            self.recus = self.recus + 1
            genre = message["type"]
            contenu = message["contenu"]

            if genre == messages.ALERTE_PROXIMITE:
                self.alertes[contenu["carrefour"]] = contenu["distance"]
            elif genre == messages.ACCORD_PRIORITE:
                self.regler_un_feu(contenu["carrefour"], contenu["axe"])
            elif genre == messages.LIBERATION:
                self.regler_un_feu(contenu["carrefour"], None)
                self.alertes.pop(contenu["carrefour"], None)

        with self.verrou:
            self.simulation.carrefours_alertes = dict(self.alertes)

    def regler_un_feu(self, carrefour, axe):
        if carrefour not in self.simulation.feux:
            return
        with self.verrou:
            self.simulation.feux[carrefour].priorite = axe

    def tourner(self):
        prochain = time.monotonic()

        while self.actif:
            for i in range(self.facteur):
                self.avancer(PAS)

            prochain = prochain + PAS
            attente = prochain - time.monotonic()
            if attente > 0:
                time.sleep(attente)
            else:
                prochain = time.monotonic()

    def demarrer(self):
        self.actif = True
        self.fil = threading.Thread(target=self.tourner, name="moteur",
                                    daemon=True)
        self.fil.start()

    def arreter(self):
        self.actif = False
        if self.fil is not None:
            self.fil.join(timeout=1.0)
            self.fil = None
