from . import ville
from .vehicule import Vehicule, LIMITES

DISTANCE_ALERTE = 500.0
SURVITESSE = 1.3


class Secours(Vehicule):

    def __init__(self, depuis, vers, avance=0.0, voie=0):
        Vehicule.__init__(self, depuis, vers, avance, voie)
        self.prioritaire = True
        self.temps_de_trajet = 0.0

    @property
    def vitesse_max(self):
        categorie = ville.categorie(self.depuis, self.vers)
        return LIMITES[categorie] * SURVITESSE

    def rue_suivante(self, carrefour, precedent, voie=0):
        choix = []
        for v in ville.voisins(carrefour):
            if v != precedent:
                choix.append(v)
        if not choix:
            return precedent

        x0, y0 = ville.position(carrefour)
        xp, yp = ville.position(precedent)

        meilleur = choix[0]
        meilleur_score = None
        for v in choix:
            xv, yv = ville.position(v)
            score = (xp - x0) * (xv - x0) + (yp - y0) * (yv - y0)
            if meilleur_score is None or score < meilleur_score:
                meilleur_score = score
                meilleur = v
        return meilleur

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


def alerter_les_feux(vehicules, feux):
    for carrefour in feux:
        feux[carrefour].priorite = None

    for v in vehicules:
        if not v.prioritaire:
            continue
        if v.vers not in feux:
            continue
        if v.reste > DISTANCE_ALERTE:
            continue
        feux[v.vers].priorite = ville.axe(v.depuis, v.vers)
