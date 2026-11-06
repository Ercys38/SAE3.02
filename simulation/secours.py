import random

from . import ville
from .vehicule import Vehicule, LIMITES

DISTANCE_ALERTE = 500.0
DISTANCE_ONDE = 180.0
DISTANCE_ARRIVEE = 14.0
SURVITESSE = 1.3

SERVICES = ("pompiers", "samu", "police")


class Secours(Vehicule):

    def __init__(self, depuis, vers, avance=0.0, voie=0, itineraire=None,
                 service="pompiers", destination=None):
        if itineraire is None:
            itineraire = []
        self.itineraire = itineraire
        self.service = service
        self.destination = destination

        Vehicule.__init__(self, depuis, vers, avance, voie)

        self.prioritaire = True
        self.temps_de_trajet = 0.0
        self.arrive = False

    @property
    def vitesse_max(self):
        categorie = ville.categorie(self.depuis, self.vers)
        return LIMITES[categorie] * SURVITESSE

    def rue_suivante(self, carrefour, precedent, voie=0):
        for i in range(len(self.itineraire) - 1):
            if self.itineraire[i] == carrefour:
                return self.itineraire[i + 1]

        choix = []
        for v in ville.voisins(carrefour):
            if v != precedent:
                choix.append(v)
        if not choix:
            return precedent
        return random.choice(choix)

    def vehicule_devant(self, trafic):
        for v in trafic.file(self.depuis, self.vers, self.voie):
            if v.avance <= self.avance:
                continue
            if abs(v.ecart_urgence) > 0.1 and v.reservation is None:
                continue
            return v
        return None

    def tenter_de_deboiter(self, trafic, dt):
        return

    def mise_a_jour(self, trafic, dt):
        self.temps_de_trajet = self.temps_de_trajet + dt
        Vehicule.mise_a_jour(self, trafic, dt)

        if self.sorti:
            self.arrive = True
            return

        if self.destination is None:
            return

        if self.vers == self.destination and self.reste < DISTANCE_ARRIVEE:
            self.arrive = True
            self.sorti = True


def alerter_les_feux(vehicules, feux):
    for carrefour in feux:
        feux[carrefour].priorite = None

    for v in vehicules:
        if not v.prioritaire:
            continue
        if v.reste > DISTANCE_ALERTE:
            continue

        if v.vers in feux:
            feux[v.vers].priorite = ville.axe(v.depuis, v.vers)

        if v.reste > DISTANCE_ONDE:
            continue
        if v.suivant is None or v.suivant not in feux:
            continue
        feux[v.suivant].priorite = ville.axe(v.vers, v.suivant)
