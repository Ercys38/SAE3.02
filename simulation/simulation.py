import random

from . import ville
from . import vehicule
from . import secours
from .feux import Feu
from .vehicule import Vehicule, LONGUEUR_VOITURE

MAX_VEHICULES = 130
DENSITE_PAR_DEFAUT = 30
PLACE_A_L_ENTREE = 4 * LONGUEUR_VOITURE


def liberer_le_carrefour(mouvements, occupants, carrefour, identifiant):
    dedans = occupants.get(carrefour)
    if dedans is not None:
        dedans.discard(identifiant)
        if not dedans:
            occupants.pop(carrefour, None)

    actifs = mouvements.get(carrefour)
    if actifs is None:
        return

    for cle in list(actifs.keys()):
        actifs[cle].discard(identifiant)
        if not actifs[cle]:
            del actifs[cle]

    if not actifs:
        mouvements.pop(carrefour, None)


class Trafic:

    def __init__(self, vehicules, feux, mouvements, occupants,
                 priorite_active=True):
        self.feux = feux
        self.mouvements = mouvements
        self.occupants = occupants
        self.priorite_active = priorite_active

        self.par_file = {}
        self.vers_carrefour = {}

        for v in vehicules:
            self.ranger(v)

        for liste in self.par_file.values():
            liste.sort(key=lambda v: v.avance)

    def ranger(self, vehicule):
        cle = (vehicule.depuis, vehicule.vers, vehicule.voie)
        if cle not in self.par_file:
            self.par_file[cle] = []
        self.par_file[cle].append(vehicule)

        if vehicule.vers not in self.vers_carrefour:
            self.vers_carrefour[vehicule.vers] = []
        self.vers_carrefour[vehicule.vers].append(vehicule)

    def file(self, depuis, vers, voie):
        return self.par_file.get((depuis, vers, voie), ())

    def vehicule_devant(self, vehicule):
        for v in self.file(vehicule.depuis, vehicule.vers, vehicule.voie):
            if v.avance > vehicule.avance:
                return v
        return None

    def deplacer(self, vehicule, ancienne_cle, ancien_vers):
        liste = self.par_file.get(ancienne_cle)
        if liste is not None and vehicule in liste:
            liste.remove(vehicule)

        vises = self.vers_carrefour.get(ancien_vers)
        if vises is not None and vehicule in vises:
            vises.remove(vehicule)

        self.ranger(vehicule)
        self.par_file[(vehicule.depuis, vehicule.vers,
                       vehicule.voie)].sort(key=lambda v: v.avance)

    def file_libre(self, depuis, vers, voie, avance, marge):
        for v in self.file(depuis, vers, voie):
            if abs(v.avance - avance) < marge:
                return False
        return True

    def reserver(self, vehicule):
        if vehicule.vers not in self.mouvements:
            self.mouvements[vehicule.vers] = {}
        actifs = self.mouvements[vehicule.vers]

        cle = vehicule.mouvement()
        if cle not in actifs:
            actifs[cle] = set()
        actifs[cle].add(vehicule.id)

        if vehicule.vers not in self.occupants:
            self.occupants[vehicule.vers] = set()
        self.occupants[vehicule.vers].add(vehicule.id)

    def liberer(self, carrefour, identifiant):
        liberer_le_carrefour(self.mouvements, self.occupants,
                             carrefour, identifiant)


class Simulation:

    def __init__(self):
        self.feux = {}
        decalage = 0.0
        for nom in ville.CARREFOURS:
            if ville.CARREFOURS[nom]["feux"]:
                self.feux[nom] = Feu(decalage=decalage)
                decalage = decalage + 5.0

        self.vehicules = []
        self.mouvements = {}
        self.occupants = {}
        self.densite = DENSITE_PAR_DEFAUT
        self.temps = 0.0
        self.priorite_active = True

    def avancer(self, dt):
        self.temps = self.temps + dt

        if self.priorite_active:
            secours.alerter_les_feux(self.vehicules, self.feux)
        else:
            for carrefour in self.feux:
                self.feux[carrefour].priorite = None

        for feu in self.feux.values():
            feu.avancer(dt)

        self.ajuster_le_nombre_de_vehicules()

        trafic = Trafic(self.vehicules, self.feux, self.mouvements,
                        self.occupants, self.priorite_active)
        for vehicule_courant in self.vehicules:
            vehicule_courant.mise_a_jour(trafic, dt)

        self.retirer_les_vehicules_sortis()

    def liberer(self, carrefour, identifiant):
        liberer_le_carrefour(self.mouvements, self.occupants,
                             carrefour, identifiant)

    def retirer_les_vehicules_sortis(self):
        restants = []
        for v in self.vehicules:
            if not v.sorti:
                restants.append(v)
            elif v.reservation is not None:
                self.liberer(v.reservation, v.id)
        self.vehicules = restants

    def regler_la_vitesse(self, kmh):
        vehicule.LIMITES["avenue"] = kmh / 3.6
        vehicule.LIMITES["rue"] = kmh * 0.6 / 3.6

    def entree_libre(self, depuis, vers):
        for v in self.vehicules:
            if (v.depuis, v.vers, v.voie) != (depuis, vers, 0):
                continue
            if v.avance < PLACE_A_L_ENTREE:
                return False
        return True

    def choisir_une_intervention(self, depart):
        possibles = []
        for sortie in ville.entrees():
            if sortie != depart:
                possibles.append(sortie)
        if not possibles:
            return None
        return random.choice(possibles)

    def lancer_un_secours(self, service=None, depuis=None, itineraire=None,
                          destination=None):
        if service is None:
            service = random.choice(secours.SERVICES)

        if depuis is None and itineraire:
            depuis = itineraire[0]

        if depuis is None:
            batiments = ville.batiments_du_service(service)
            if batiments:
                depuis = ville.BATIMENTS[batiments[0]]["acces"]

        if depuis is None:
            return None

        vers = ville.voisins(depuis)[0]
        if not self.entree_libre(depuis, vers):
            return None

        if destination is None and not itineraire:
            destination = self.choisir_une_intervention(depuis)

        if not itineraire and destination is not None:
            itineraire = ville.itineraire(depuis, destination)

        if itineraire:
            destination = itineraire[-1]

        nouveau = secours.Secours(depuis, vers, 0.0, 0, itineraire,
                                  service, destination)
        self.vehicules.append(nouveau)
        return nouveau

    def nombre_vise(self):
        return int(MAX_VEHICULES * self.densite / 100)

    def civils(self):
        liste = []
        for v in self.vehicules:
            if not v.prioritaire:
                liste.append(v)
        return liste

    def ajuster_le_nombre_de_vehicules(self):
        vise = self.nombre_vise()
        civils = self.civils()

        if len(civils) < vise:
            nouveau = self.creer_un_vehicule()
            if nouveau is not None:
                self.vehicules.append(nouveau)

        elif len(civils) > vise:
            partant = civils[-1]
            self.vehicules.remove(partant)
            if partant.reservation is not None:
                self.liberer(partant.reservation, partant.id)

    def creer_un_vehicule(self):
        entrees = ville.entrees()
        random.shuffle(entrees)

        for depuis in entrees:
            vers = ville.voisins(depuis)[0]

            files = list(range(ville.voies(depuis, vers)))
            random.shuffle(files)

            for voie in files:
                if self.place_libre(depuis, vers, voie):
                    return Vehicule(depuis, vers, 0.0, voie)

        return None

    def place_libre(self, depuis, vers, voie):
        for v in self.vehicules:
            if (v.depuis, v.vers, v.voie) != (depuis, vers, voie):
                continue
            if v.avance < PLACE_A_L_ENTREE:
                return False
        return True
