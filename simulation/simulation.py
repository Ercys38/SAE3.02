import random

from . import ville
from .feux import Feu
from . import vehicule
from . import secours
from .vehicule import Vehicule, LONGUEUR_VOITURE

MAX_VEHICULES = 50
DENSITE_PAR_DEFAUT = 30


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
        self.priorite_active = priorite_active
        self.mouvements = mouvements
        self.occupants = occupants

        self.par_file = {}
        self.vers_carrefour = {}

        for v in vehicules:
            cle = (v.depuis, v.vers, v.voie)
            if cle not in self.par_file:
                self.par_file[cle] = []
            self.par_file[cle].append(v)

            if v.vers not in self.vers_carrefour:
                self.vers_carrefour[v.vers] = []
            self.vers_carrefour[v.vers].append(v)

        for liste in self.par_file.values():
            liste.sort(key=lambda v: v.avance)

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

        cle = (vehicule.depuis, vehicule.vers, vehicule.voie)
        if cle not in self.par_file:
            self.par_file[cle] = []
        self.par_file[cle].append(vehicule)
        self.par_file[cle].sort(key=lambda v: v.avance)

        if vehicule.vers not in self.vers_carrefour:
            self.vers_carrefour[vehicule.vers] = []
        self.vers_carrefour[vehicule.vers].append(vehicule)

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
        for vehicule in self.vehicules:
            vehicule.mise_a_jour(trafic, dt)

        self.retirer_les_vehicules_sortis()

    def retirer_les_vehicules_sortis(self):
        restants = []
        for v in self.vehicules:
            if v.sorti:
                if v.reservation is not None:
                    self.liberer(v.reservation, v.id)
            else:
                restants.append(v)
        self.vehicules = restants

    def liberer(self, carrefour, identifiant):
        liberer_le_carrefour(self.mouvements, self.occupants,
                             carrefour, identifiant)

    def entree_libre(self, depuis, vers):
        for v in self.vehicules:
            if (v.depuis, v.vers, v.voie) != (depuis, vers, 0):
                continue
            if v.avance < 4 * LONGUEUR_VOITURE:
                return False
        return True

    def lancer_un_secours(self, depuis=None):
        if depuis is None:
            candidats = ville.entrees()
            random.shuffle(candidats)
        else:
            candidats = [depuis]

        for entree in candidats:
            vers = ville.voisins(entree)[0]
            if not self.entree_libre(entree, vers):
                continue
            vehicule_secours = secours.Secours(entree, vers, 0.0, 0)
            self.vehicules.append(vehicule_secours)
            return vehicule_secours

        return None

    def regler_la_vitesse(self, kmh):
        vehicule.LIMITES["avenue"] = kmh / 3.6
        vehicule.LIMITES["rue"] = kmh * 0.6 / 3.6

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
        occupes = {}
        for v in self.vehicules:
            cle = (v.depuis, v.vers, v.voie)
            if cle not in occupes:
                occupes[cle] = []
            occupes[cle].append(v.avance)

        entrees = ville.entrees()
        random.shuffle(entrees)

        for entree in entrees:
            depuis = entree
            vers = ville.voisins(entree)[0]

            files = list(range(ville.voies(depuis, vers)))
            random.shuffle(files)
            for voie in files:
                libre = True
                for avance in occupes.get((depuis, vers, voie), ()):
                    if avance < 4 * LONGUEUR_VOITURE:
                        libre = False
                if libre:
                    return Vehicule(depuis, vers, 0.0, voie)

        return None
