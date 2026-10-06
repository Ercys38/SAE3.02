import random

from . import ville
from . import code_route

VITESSE_AVENUE = 13.9
VITESSE_RUE = 8.3

LIMITES = {"avenue": VITESSE_AVENUE, "rue": VITESSE_RUE}
ACCELERATION = 2.0
FREINAGE = 4.0

LONGUEUR_VOITURE = 10.0
LARGEUR_VOITURE = 5.0
ECART_MINIMUM = 4.0
RECUL_CARREFOUR = 24.0
PLACE_DE_SORTIE = 24.0
SURCOUT_VIRAGE = 16.0
ZONE_DECISION = 66.0
DEGAGEMENT = 26.0

MARGE_DEBOITEMENT = 34.0
DELAI_DEBOITEMENT = 4.0
GAIN_MINIMUM = 1.5


def vitesse_permise(distance, marge):
    utile = distance - marge
    if utile <= 0:
        return 0.0
    return (2 * FREINAGE * utile) ** 0.5


class Vehicule:
    compteur = 0

    def __init__(self, depuis, vers, avance=0.0, voie=0):
        Vehicule.compteur = Vehicule.compteur + 1
        self.id = Vehicule.compteur

        self.depuis = depuis
        self.vers = vers
        self.avance = avance
        self.voie = min(voie, ville.voies(depuis, vers) - 1)

        self.vitesse = 0.0
        self.attente_stop = 0.0
        self.bloque_depuis = 0.0
        self.reservation = None
        self.depuis_deboitement = DELAI_DEBOITEMENT
        self.prioritaire = False
        self.sorti = False
        self.suivant = self.rue_suivante(vers, depuis)

    @property
    def vitesse_max(self):
        return LIMITES[ville.categorie(self.depuis, self.vers)]

    @property
    def longueur_rue(self):
        return ville.longueur(self.depuis, self.vers)

    @property
    def reste(self):
        return self.longueur_rue - self.avance

    def mouvement(self):
        return (self.depuis, self.voie, self.suivant, self.voie_apres())

    def voie_apres(self):
        return min(self.voie, ville.voies(self.vers, self.suivant) - 1)

    def direction(self):
        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        d = self.longueur_rue
        return ((x2 - x1) / d, (y2 - y1) / d)

    def position(self):
        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        part = self.avance / self.longueur_rue
        x = x1 + (x2 - x1) * part
        y = y1 + (y2 - y1) * part

        dx, dy = self.direction()
        ecart = ville.decalage_voie(self.depuis, self.vers, self.voie)
        return (x - dy * ecart, y + dx * ecart)

    def mise_a_jour(self, trafic, dt):
        self.liberer_le_carrefour(trafic)
        self.tenter_de_deboiter(trafic, dt)

        cible = self.vitesse_max

        devant = trafic.vehicule_devant(self)
        ecart = self.distance_a_la_voiture_de_devant(trafic, devant)
        if ecart is not None:
            cible = min(cible, vitesse_permise(ecart, ECART_MINIMUM))

        if self.reservation is None and self.reste <= ZONE_DECISION:
            if self.a_le_droit_de_passer(trafic, devant):
                self.reservation = self.vers
                trafic.reserver(self)
            else:
                cible = min(cible, vitesse_permise(self.reste, RECUL_CARREFOUR))

        if cible > self.vitesse:
            self.vitesse = min(cible, self.vitesse + ACCELERATION * dt)
        else:
            self.vitesse = max(cible, self.vitesse - FREINAGE * dt)
        if self.vitesse < 0.0:
            self.vitesse = 0.0

        self.compter_les_arrets(dt)

        self.avance = self.avance + self.vitesse * dt
        if self.avance >= self.longueur_rue:
            if ville.est_une_sortie(self.vers):
                self.sorti = True
            else:
                self.changer_de_rue(trafic)

    def distance_a_la_voiture_de_devant(self, trafic, devant):
        if devant is not None:
            return devant.avance - self.avance - LONGUEUR_VOITURE

        file_suivante = trafic.file(self.vers, self.suivant, self.voie_apres())
        if not file_suivante:
            return None

        premier = file_suivante[0]
        return self.reste + premier.avance - LONGUEUR_VOITURE - SURCOUT_VIRAGE

    def a_le_droit_de_passer(self, trafic, devant):
        if devant is not None:
            return False
        if not self.sortie_degagee(trafic):
            return False
        return code_route.passage_autorise(self, trafic)

    def sortie_degagee(self, trafic):
        for v in trafic.file(self.vers, self.suivant, self.voie_apres()):
            if v.avance < PLACE_DE_SORTIE:
                return False
        return True

    def tenter_de_deboiter(self, trafic, dt):
        self.depuis_deboitement = self.depuis_deboitement + dt

        nombre = ville.voies(self.depuis, self.vers)
        if nombre < 2:
            return
        if self.depuis_deboitement < DELAI_DEBOITEMENT:
            return
        if self.reste < ZONE_DECISION + 40 or self.avance < 40:
            return
        if self.reservation is not None:
            return

        devant = trafic.vehicule_devant(self)
        if devant is None:
            return
        if devant.vitesse > self.vitesse - GAIN_MINIMUM:
            return

        for visee in (self.voie + 1, self.voie - 1):
            if visee < 0 or visee >= nombre:
                continue
            if trafic.file_libre(self.depuis, self.vers, visee,
                                 self.avance, MARGE_DEBOITEMENT):
                ancienne = (self.depuis, self.vers, self.voie)
                self.voie = visee
                self.depuis_deboitement = 0.0
                trafic.deplacer(self, ancienne, self.vers)
                return

    def compter_les_arrets(self, dt):
        immobile = self.vitesse < 0.3
        proche = self.reste < ZONE_DECISION

        if immobile and self.reste < RECUL_CARREFOUR + 4.0:
            self.attente_stop = self.attente_stop + dt
        if immobile and proche:
            self.bloque_depuis = self.bloque_depuis + dt
        else:
            self.bloque_depuis = 0.0

    def changer_de_rue(self, trafic):
        depasse = self.avance - self.longueur_rue
        precedent = self.depuis
        ancienne = (self.depuis, self.vers, self.voie)
        ancien_vers = self.vers

        nouvelle_voie = self.voie_apres()
        self.depuis = self.vers
        if self.suivant is not None:
            self.vers = self.suivant
        else:
            self.vers = self.rue_suivante(self.depuis, precedent)
        self.voie = min(nouvelle_voie, ville.voies(self.depuis, self.vers) - 1)
        self.avance = min(depasse, self.longueur_rue * 0.5)
        self.suivant = self.rue_suivante(self.vers, self.depuis)

        self.attente_stop = 0.0
        self.bloque_depuis = 0.0
        self.depuis_deboitement = 0.0
        trafic.deplacer(self, ancienne, ancien_vers)

    def rue_suivante(self, carrefour, precedent):
        choix = []
        for v in ville.voisins(carrefour):
            if v != precedent:
                choix.append(v)
        if not choix:
            choix = [precedent]
        return random.choice(choix)

    def liberer_le_carrefour(self, trafic):
        if self.reservation is None:
            return
        deja_passe = self.reservation != self.vers
        if deja_passe and self.avance > DEGAGEMENT:
            trafic.liberer(self.reservation, self.id)
            self.reservation = None
