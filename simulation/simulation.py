"""
L'etat de la simulation et son avancement dans le temps.

La simulation contient les feux et les vehicules civils. Elle ne sait rien
de l'affichage.
"""

import random

from . import ville
from .feux import Feu
from .vehicule import Vehicule, LONGUEUR_VOITURE

MAX_VEHICULES = 120        # nombre de voitures a 100 % de densite
DENSITE_PAR_DEFAUT = 30    # en pourcentage


class Trafic:
    """
    Photographie du trafic a un instant donne.

    On la reconstruit a chaque pas de temps. Elle evite que chaque vehicule
    ait a parcourir toute la liste des autres pour trouver celui qui le
    precede : on range une bonne fois pour toutes les vehicules par rue et
    par carrefour vise.
    """

    def __init__(self, vehicules, feux, mouvements, occupants):
        self.feux = feux
        self.mouvements = mouvements    # carrefour -> (depuis, vers) en cours
        self.occupants = occupants      # carrefour -> ids des vehicules dedans

        # Les vehicules sont ranges par file, et non par rue : deux voitures
        # cote a cote sur une avenue a deux files ne se genent pas.
        self.par_file = {}
        self.vers_carrefour = {}

        for v in vehicules:
            self.par_file.setdefault((v.depuis, v.vers, v.voie), []).append(v)
            self.vers_carrefour.setdefault(v.vers, []).append(v)

        for liste in self.par_file.values():
            liste.sort(key=lambda v: v.avance)

    def file(self, depuis, vers, voie):
        """Les vehicules d'une file, tries du plus proche du depart au plus loin."""
        return self.par_file.get((depuis, vers, voie), ())

    def vehicule_devant(self, vehicule):
        """Le vehicule le plus proche devant celui-ci, dans sa file."""
        for v in self.file(vehicule.depuis, vehicule.vers, vehicule.voie):
            if v.avance > vehicule.avance:
                return v
        return None

    def deplacer(self, vehicule, ancienne_cle, ancien_vers):
        """
        Met l'index a jour quand un vehicule change de file ou de rue.

        Sans cela, les vehicules traites plus tard dans le meme pas de
        temps verraient une photographie perimee : deux voitures pourraient
        se deporter au meme endroit, chacune croyant la place libre.
        """
        liste = self.par_file.get(ancienne_cle)
        if liste is not None and vehicule in liste:
            liste.remove(vehicule)

        vises = self.vers_carrefour.get(ancien_vers)
        if vises is not None and vehicule in vises:
            vises.remove(vehicule)

        nouvelle = self.par_file.setdefault(
            (vehicule.depuis, vehicule.vers, vehicule.voie), [])
        nouvelle.append(vehicule)
        nouvelle.sort(key=lambda v: v.avance)
        self.vers_carrefour.setdefault(vehicule.vers, []).append(vehicule)

    def file_libre(self, depuis, vers, voie, avance, marge):
        """Y a-t-il la place de se deporter dans cette file ?"""
        for v in self.file(depuis, vers, voie):
            if abs(v.avance - avance) < marge:
                return False
        return True

    def reserver(self, vehicule):
        """On inscrit le mouvement du vehicule parmi ceux en cours."""
        actifs = self.mouvements.setdefault(vehicule.vers, {})
        actifs.setdefault(vehicule.mouvement(), set()).add(vehicule.id)
        self.occupants.setdefault(vehicule.vers, set()).add(vehicule.id)

    def liberer(self, carrefour, identifiant):
        """Le vehicule sort du carrefour ; son mouvement s'efface avec lui."""
        dedans = self.occupants.get(carrefour)
        if dedans is not None:
            dedans.discard(identifiant)
            if not dedans:
                self.occupants.pop(carrefour, None)

        actifs = self.mouvements.get(carrefour)
        if actifs is None:
            return
        for cle, ids in list(actifs.items()):
            ids.discard(identifiant)
            if not ids:
                del actifs[cle]
        if not actifs:
            self.mouvements.pop(carrefour, None)


class Simulation:
    def __init__(self):
        # Un objet Feu pour chaque carrefour equipe.
        # Le decalage evite que tous changent en meme temps.
        self.feux = {}
        decalage = 0.0
        for nom, infos in ville.CARREFOURS.items():
            if infos["feux"]:
                self.feux[nom] = Feu(decalage=decalage)
                decalage += 5.0

        self.vehicules = []
        # Un carrefour est attribue a un mouvement (une rue d'arrivee et une
        # rue de sortie) et non a une seule voiture : les vehicules d'un
        # meme mouvement se suivent, ils ne se croisent pas.
        self.mouvements = {}        # carrefour -> {mouvement: ids en cours}
        self.occupants = {}         # carrefour -> ids des vehicules dedans
        self.densite = DENSITE_PAR_DEFAUT
        self.temps = 0.0

    # --- avancement -------------------------------------------------------
    def avancer(self, dt):
        """Fait avancer toute la simulation de dt secondes."""
        self.temps += dt

        for feu in self.feux.values():
            feu.avancer(dt)

        self.ajuster_le_nombre_de_vehicules()

        trafic = Trafic(self.vehicules, self.feux, self.mouvements, self.occupants)
        for vehicule in self.vehicules:
            vehicule.mise_a_jour(trafic, dt)

    # --- gestion du nombre de vehicules -----------------------------------
    def nombre_vise(self):
        return int(MAX_VEHICULES * self.densite / 100)

    def ajuster_le_nombre_de_vehicules(self):
        """
        Ramene doucement le nombre de voitures vers celui demande par le
        curseur de densite. On n'en ajoute ou n'en retire qu'une par pas de
        temps, pour que le changement se voie progressivement.
        """
        vise = self.nombre_vise()

        if len(self.vehicules) < vise:
            nouveau = self.creer_un_vehicule()
            if nouveau is not None:
                self.vehicules.append(nouveau)

        elif len(self.vehicules) > vise:
            partant = self.vehicules.pop()
            if partant.reservation is not None:
                Trafic.liberer(self, partant.reservation, partant.id)

    def creer_un_vehicule(self):
        """
        Place une voiture sur une rue au hasard, a un endroit libre.
        Renvoie None si aucune place n'a ete trouvee ; on reessaiera au pas
        de temps suivant.
        """
        occupes = {}
        for v in self.vehicules:
            occupes.setdefault((v.depuis, v.vers, v.voie), []).append(v.avance)

        for _essai in range(20):
            depuis, vers, _nom, _cat = random.choice(ville.RUES)
            if random.random() < 0.5:
                depuis, vers = vers, depuis

            voie = random.randrange(ville.voies(depuis, vers))
            longueur = ville.longueur(depuis, vers)
            # on ne fait pas apparaitre une voiture a l'entree d'un carrefour
            avance = random.uniform(0.15 * longueur, 0.75 * longueur)

            deja_la = occupes.get((depuis, vers, voie), ())
            if any(abs(a - avance) < 4 * LONGUEUR_VOITURE for a in deja_la):
                continue

            return Vehicule(depuis, vers, avance, voie)

        return None
