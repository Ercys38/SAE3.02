import random

from . import ville
from . import code_route

VITESSE_AVENUE = 13.9
VITESSE_RUE = 8.3

LIMITES = {"avenue": VITESSE_AVENUE, "rue": VITESSE_RUE}
ACCELERATION = 2.0
FREINAGE = 4.0

LONGUEUR_VOITURE = 10.0
LARGEUR_VOITURE = 4.0
ECART_MINIMUM = 4.0
RECUL_CARREFOUR = 24.0
PLACE_DE_SORTIE = 24.0
SURCOUT_VIRAGE = 16.0
ZONE_DECISION = 66.0
DEGAGEMENT = 26.0
ABANDON_RESERVATION = 4.0

DISTANCE_RABATTEMENT = 120.0
DISTANCE_SIRENE = 40.0
DISTANCE_PRIORITE = 90.0
RETOUR_SECOURS = 25.0
VITESSE_DEPORT = 3.0
DEPORT_DROITE = 5.5
ANGLE_DEPORT = 0.12
ALLURE_RABATTEMENT = 0.35

MARGE_DEBOITEMENT = 34.0
DELAI_DEBOITEMENT = 4.0
GAIN_MINIMUM = 1.5


def distance(premier, second):
    dx = second[0] - premier[0]
    dy = second[1] - premier[1]
    return (dx * dx + dy * dy) ** 0.5


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
        self.ecart_urgence = 0.0
        self.vitesse_laterale = 0.0
        self.precedent = None
        self.voie_entree = voie
        self.prioritaire = False
        self.sorti = False
        self.suivant = self.rue_suivante(vers, depuis, self.voie)

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

    def passage_carrefour(self):
        rayon = code_route.RAYON_CARREFOUR

        if self.reste < rayon and not ville.est_une_sortie(self.vers):
            carrefour = self.vers
            entree = self.depuis
            sortie = self.suivant
            depart = code_route.point_de_file(entree, carrefour,
                                              self.voie, False)
            arrivee = code_route.point_de_file(sortie, carrefour,
                                               self.voie_apres(), True)
            part = (rayon - self.reste) / (2 * rayon)
        elif self.precedent is not None and self.avance < rayon:
            carrefour = self.depuis
            entree = self.precedent
            sortie = self.vers
            depart = code_route.point_de_file(entree, carrefour,
                                              self.voie_entree, False)
            arrivee = code_route.point_de_file(sortie, carrefour,
                                               self.voie, True)
            part = (rayon + self.avance) / (2 * rayon)
        else:
            return None

        return (depart, arrivee, part)

    def retard_carrefour(self):
        passage = self.passage_carrefour()
        if passage is None:
            return 0.0

        depart, arrivee, part = passage
        chemin = distance(depart, arrivee)
        modele = 2 * code_route.RAYON_CARREFOUR
        if chemin > modele:
            return 0.0
        return part * (modele - chemin)

    def direction(self):
        passage = self.passage_carrefour()
        if passage is not None:
            depart, arrivee, part = passage
            dx = arrivee[0] - depart[0]
            dy = arrivee[1] - depart[1]
            d = (dx * dx + dy * dy) ** 0.5
            if d > 0.001:
                return (dx / d, dy / d)

        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        d = self.longueur_rue
        dx = (x2 - x1) / d
        dy = (y2 - y1) / d

        if abs(self.vitesse_laterale) > 0.01:
            penche = self.vitesse_laterale * ANGLE_DEPORT
            if penche > ANGLE_DEPORT:
                penche = ANGLE_DEPORT
            if penche < -ANGLE_DEPORT:
                penche = -ANGLE_DEPORT
            ex = dx - dy * penche
            ey = dy + dx * penche
            norme = (ex * ex + ey * ey) ** 0.5
            if norme > 0.001:
                return (ex / norme, ey / norme)

        return (dx, dy)

    def position(self):
        passage = self.passage_carrefour()
        if passage is not None:
            depart, arrivee, part = passage
            x = depart[0] + (arrivee[0] - depart[0]) * part
            y = depart[1] + (arrivee[1] - depart[1]) * part
            if abs(self.ecart_urgence) > 0.01:
                dx, dy = self.direction()
                x = x - dy * self.ecart_urgence
                y = y + dx * self.ecart_urgence
            return (x, y)

        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        part = self.avance / self.longueur_rue
        x = x1 + (x2 - x1) * part
        y = y1 + (y2 - y1) * part

        dx, dy = self.direction()
        ecart = ville.decalage_voie(self.depuis, self.vers, self.voie)
        ecart = ecart + self.ecart_urgence
        return (x - dy * ecart, y + dx * ecart)

    def mise_a_jour(self, trafic, dt):
        self.liberer_le_carrefour(trafic)
        self.tenter_de_deboiter(trafic, dt)
        doit_ceder = self.ceder_le_passage(trafic, dt)

        cible = self.vitesse_max

        devant = self.vehicule_devant(trafic)
        ecart = self.distance_a_la_voiture_de_devant(trafic, devant)
        if ecart is not None:
            cible = min(cible, vitesse_permise(ecart, ECART_MINIMUM))

        if self.reservation is None and self.reste <= ZONE_DECISION:
            if self.a_le_droit_de_passer(trafic, devant):
                self.reservation = self.vers
                trafic.reserver(self)
            else:
                cible = min(cible, vitesse_permise(self.reste, RECUL_CARREFOUR))

        if doit_ceder is not None and self.reservation is None:
            cible = min(cible, doit_ceder)

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

    def vehicule_devant(self, trafic):
        return trafic.vehicule_devant(self)

    def ecart_vise(self, trafic):
        if self.prioritaire or self.voie != 0:
            return 0.0

        if trafic.priorite_active:
            portee = DISTANCE_RABATTEMENT
        else:
            portee = DISTANCE_SIRENE

        for autre in trafic.vers_carrefour.get(self.vers, ()):
            if not autre.prioritaire:
                continue
            if autre.depuis != self.depuis:
                continue
            if autre.avance > self.avance + RETOUR_SECOURS:
                continue
            if self.avance - autre.avance > portee:
                continue
            return DEPORT_DROITE

        return 0.0

    def ceder_le_passage(self, trafic, dt):
        vise = self.ecart_vise(trafic)
        avant = self.ecart_urgence

        if self.ecart_urgence < vise:
            self.ecart_urgence = min(vise, self.ecart_urgence
                                     + VITESSE_DEPORT * dt)
        elif self.ecart_urgence > vise:
            self.ecart_urgence = max(vise, self.ecart_urgence
                                     - VITESSE_DEPORT * dt)

        if dt > 0:
            self.vitesse_laterale = (self.ecart_urgence - avant) / dt
        else:
            self.vitesse_laterale = 0.0

        if vise == 0.0 or self.prioritaire:
            return None

        if self.ecart_urgence < vise - 0.3:
            return self.vitesse_max * ALLURE_RABATTEMENT
        return 0.0

    def distance_a_la_voiture_de_devant(self, trafic, devant):
        if devant is not None:
            avance_vue = devant.avance - devant.retard_carrefour()
            return avance_vue - self.avance - LONGUEUR_VOITURE

        file_suivante = trafic.file(self.vers, self.suivant, self.voie_apres())
        if not file_suivante:
            return None

        premier = file_suivante[0]
        return self.reste + premier.avance - LONGUEUR_VOITURE - SURCOUT_VIRAGE

    def secours_en_approche(self, trafic):
        if not trafic.priorite_active:
            return False

        for autre in trafic.vers_carrefour.get(self.vers, ()):
            if not autre.prioritaire:
                continue
            if autre.reste < DISTANCE_PRIORITE:
                return True
        return False

    def a_le_droit_de_passer(self, trafic, devant):
        if devant is not None:
            return False
        if not self.prioritaire and abs(self.ecart_urgence) > 0.1:
            return False
        if not self.prioritaire and self.secours_en_approche(trafic):
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
                self.suivant = self.rue_suivante(self.vers, self.depuis,
                                                 self.voie)
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
        self.ecart_urgence = 0.0
        self.precedent = precedent
        self.voie_entree = self.voie
        self.depuis = self.vers
        if self.suivant is not None:
            self.vers = self.suivant
        else:
            self.vers = self.rue_suivante(self.depuis, precedent, self.voie)
        self.voie = min(nouvelle_voie, ville.voies(self.depuis, self.vers) - 1)
        self.avance = min(depasse, self.longueur_rue * 0.5)
        self.suivant = self.rue_suivante(self.vers, self.depuis, self.voie)

        self.attente_stop = 0.0
        self.bloque_depuis = 0.0
        self.depuis_deboitement = 0.0
        trafic.deplacer(self, ancienne, ancien_vers)

    def mouvements_permis(self, voie, nombre):
        if nombre < 2:
            return ("droite", "tout_droit", "gauche")
        if voie == 0:
            return ("droite",)
        return ("tout_droit", "gauche")

    def rue_suivante(self, carrefour, precedent, voie):
        voisins = []
        for v in ville.voisins(carrefour):
            if v != precedent:
                voisins.append(v)
        if not voisins:
            return precedent

        permis = self.mouvements_permis(voie, ville.voies(precedent, carrefour))

        choix = []
        for v in voisins:
            if ville.genre_de_mouvement(precedent, carrefour, v) in permis:
                choix.append(v)

        if not choix:
            choix = voisins
        return random.choice(choix)

    def liberer_le_carrefour(self, trafic):
        if self.reservation is None:
            return

        deja_passe = self.reservation != self.vers
        if deja_passe:
            if self.avance > DEGAGEMENT:
                trafic.liberer(self.reservation, self.id)
                self.reservation = None
            return

        if self.reste <= code_route.RAYON_CARREFOUR:
            return

        if self.bloque_depuis > ABANDON_RESERVATION:
            trafic.liberer(self.reservation, self.id)
            self.reservation = None
            return

        if not self.prioritaire and self.secours_en_approche(trafic):
            trafic.liberer(self.reservation, self.id)
            self.reservation = None
