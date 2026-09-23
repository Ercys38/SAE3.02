"""
Les vehicules civils.

Chaque vehicule roule tout seul. Il ne connait pas la simulation entiere :
il regarde seulement la voiture devant lui, dans sa file, et le carrefour
qui arrive. Les regles de priorite sont dans code_route.py.

Une avenue a deux files par sens, une petite rue une seule. Un vehicule
garde sa file, sauf s'il est ralenti et qu'il y a la place a cote.
"""

import random

from . import ville
from . import code_route

# --- Reglages -------------------------------------------------------------
VITESSE_AVENUE = 13.9      # m/s, soit 50 km/h
VITESSE_RUE = 8.3          # m/s, soit 30 km/h
ACCELERATION = 2.0         # m/s2
FREINAGE = 4.0             # m/s2

# Le gabarit est volontairement plus grand qu'une vraie voiture. A
# l'echelle de la ville, une voiture de 5 m ne ferait que deux pixels et
# serait invisible. Toutes les distances de securite sont calees sur ce
# gabarit, pour que ce qui est dessine corresponde a ce qui est calcule.
LONGUEUR_VOITURE = 10.0    # m : gabarit d'une voiture
ECART_MINIMUM = 4.0        # m : espace laisse entre deux voitures a l'arret
RECUL_CARREFOUR = 24.0     # m : distance d'arret avant le centre du carrefour.
                           # Elle est mesuree sur l'axe de la rue, alors
                           # qu'une voiture qui traverse dans la file
                           # exterieure passe 12 m sur le cote : il faut
                           # reculer d'autant pour ne pas la toucher.
PLACE_DE_SORTIE = 24.0     # m : place exigee de l'autre cote pour s'engager
SURCOUT_VIRAGE = 16.0      # m : voir distance_a_la_voiture_de_devant
ZONE_DECISION = 66.0       # m avant le carrefour : c'est la qu'on decide.
                           # Il faut 24 m pour s'arreter depuis 50 km/h, plus
                           # les 20 m de recul : en decider plus tard voudrait
                           # dire ne pas pouvoir s'arreter a temps.
DEGAGEMENT = 26.0          # m apres le carrefour : on ne le libere qu'une
                           # fois vraiment degage, sinon le suivant s'engage
                           # alors qu'on est encore dedans.

# --- Changement de file ---------------------------------------------------
MARGE_DEBOITEMENT = 34.0   # m : place exigee devant et derriere dans la file visee
DELAI_DEBOITEMENT = 4.0    # s : on ne se deporte pas sans arret
GAIN_MINIMUM = 1.5         # m/s : on ne double que si la file d'a cote est plus rapide


def vitesse_permise(distance, marge):
    """
    Vitesse maximale pour pouvoir s'arreter avant l'obstacle, en gardant
    la marge demandee. Sert aussi bien a garder ses distances derriere une
    voiture qu'a s'arreter au feu.
    """
    utile = distance - marge
    if utile <= 0:
        return 0.0
    return (2 * FREINAGE * utile) ** 0.5


class Vehicule:
    compteur = 0

    def __init__(self, depuis, vers, avance=0.0, voie=0):
        Vehicule.compteur += 1
        self.id = Vehicule.compteur

        # Le vehicule est sur la rue qui va de "depuis" vers "vers",
        # a "avance" metres du depart, dans la file "voie".
        # La file 0 est la plus a droite.
        self.depuis = depuis
        self.vers = vers
        self.avance = avance
        self.voie = min(voie, ville.voies(depuis, vers) - 1)

        self.vitesse = 0.0
        self.attente_stop = 0.0      # temps deja passe a l'arret a un stop
        self.bloque_depuis = 0.0     # temps passe immobile avant un carrefour
        self.reservation = None      # carrefour que l'on s'est reserve
        self.depuis_deboitement = DELAI_DEBOITEMENT
        self.prioritaire = False     # True pour un vehicule de secours
        self.suivant = self.rue_suivante(vers, depuis)

    # --- informations simples --------------------------------------------
    @property
    def vitesse_max(self):
        if ville.categorie(self.depuis, self.vers) == "avenue":
            return VITESSE_AVENUE
        return VITESSE_RUE

    @property
    def longueur_rue(self):
        return ville.longueur(self.depuis, self.vers)

    @property
    def reste(self):
        """Distance restante jusqu'au carrefour, en metres."""
        return self.longueur_rue - self.avance

    def mouvement(self):
        """
        Le mouvement que le vehicule va effectuer dans le carrefour :
        par quelle rue et quelle file il entre, par quelle rue et quelle
        file il ressort. Les files comptent : deux voitures venues de deux
        files differentes qui visent la meme file de sortie se rejoignent
        au milieu du carrefour.
        """
        return (self.depuis, self.voie, self.suivant, self.voie_apres())

    def voie_apres(self):
        """
        File que l'on occupera apres le carrefour. On garde la meme, sauf
        si la rue suivante en a moins : on se rabat alors a droite.
        """
        return min(self.voie, ville.voies(self.vers, self.suivant) - 1)

    def direction(self):
        """Vecteur unitaire du sens de marche."""
        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        d = self.longueur_rue
        return ((x2 - x1) / d, (y2 - y1) / d)

    def position(self):
        """
        Coordonnees (x, y) du vehicule, en metres, au milieu de sa file.
        Le decalage lateral vient de ville.py : le calcul et le dessin
        partagent ainsi la meme geometrie.
        """
        x1, y1 = ville.position(self.depuis)
        x2, y2 = ville.position(self.vers)
        part = self.avance / self.longueur_rue
        x = x1 + (x2 - x1) * part
        y = y1 + (y2 - y1) * part

        dx, dy = self.direction()
        ecart = ville.decalage_voie(self.depuis, self.vers, self.voie)
        # la droite du sens de marche, en coordonnees ecran, est (-dy, dx)
        return (x - dy * ecart, y + dx * ecart)

    # --- deplacement ------------------------------------------------------
    def mise_a_jour(self, trafic, dt):
        self.liberer_le_carrefour(trafic)
        self.tenter_de_deboiter(trafic, dt)

        cible = self.vitesse_max

        # 1. Ne pas rentrer dans la voiture de devant.
        devant = trafic.vehicule_devant(self)
        ecart = self.distance_a_la_voiture_de_devant(trafic, devant)
        if ecart is not None:
            cible = min(cible, vitesse_permise(ecart, ECART_MINIMUM))

        # 2. Faut-il s'arreter avant le carrefour ?
        if self.reservation is None and self.reste <= ZONE_DECISION:
            if self.a_le_droit_de_passer(trafic, devant):
                self.reservation = self.vers
                trafic.reserver(self)
            else:
                cible = min(cible, vitesse_permise(self.reste, RECUL_CARREFOUR))

        # 3. Accelerer ou freiner.
        if cible > self.vitesse:
            self.vitesse = min(cible, self.vitesse + ACCELERATION * dt)
        else:
            self.vitesse = max(cible, self.vitesse - FREINAGE * dt)
        self.vitesse = max(0.0, self.vitesse)

        self.compter_les_arrets(dt)

        # 4. Avancer.
        self.avance += self.vitesse * dt
        if self.avance >= self.longueur_rue:
            self.changer_de_rue(trafic)

    def distance_a_la_voiture_de_devant(self, trafic, devant):
        """
        Distance libre devant nous, en metres, ou None s'il n'y a personne.

        On regarde aussi de l'autre cote du carrefour. Sans cela, une
        voiture le franchirait a pleine vitesse pour decouvrir ensuite une
        file a l'arret juste derriere, trop tard pour s'arreter.
        """
        if devant is not None:
            return devant.avance - self.avance - LONGUEUR_VOITURE

        file_suivante = trafic.file(self.vers, self.suivant, self.voie_apres())
        if not file_suivante:
            return None

        premier = file_suivante[0]   # la liste est triee par avance

        # La distance le long du trajet passe par le centre du carrefour,
        # mais deux voitures qui tournent se rapprochent a la corde : a vol
        # d'oiseau elles sont plus pres que ce que le trajet laisse croire.
        # On exige donc un ecart plus large des que la voiture de devant est
        # de l'autre cote du carrefour.
        return (self.reste + premier.avance
                - LONGUEUR_VOITURE - SURCOUT_VIRAGE)

    def a_le_droit_de_passer(self, trafic, devant):
        """
        Trois conditions, toutes necessaires :
          - etre le premier de sa file, sinon une voiture arretee devant
            nous nous empecherait d'avancer alors qu'on bloque le carrefour ;
          - pouvoir ressortir, car on ne s'engage pas dans un carrefour
            qu'on ne pourra pas degager ;
          - et bien sur, que le code de la route l'autorise.
        """
        if devant is not None:
            return False
        if not self.sortie_degagee(trafic):
            return False
        return code_route.passage_autorise(self, trafic)

    def sortie_degagee(self, trafic):
        """
        Y a-t-il la place de se ranger de l'autre cote du carrefour ?
        On ne regarde pas si l'autre roule ou non : une voiture lente
        occupe la place autant qu'une voiture arretee.
        """
        for v in trafic.file(self.vers, self.suivant, self.voie_apres()):
            if v.avance < PLACE_DE_SORTIE:
                return False
        return True

    # --- changement de file ----------------------------------------------
    def tenter_de_deboiter(self, trafic, dt):
        """
        On ne se deporte que pour doubler, jamais a l'approche d'un
        carrefour : changer de file juste avant de tourner serait a la fois
        dangereux et illisible a l'ecran.
        """
        self.depuis_deboitement += dt

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
            return   # celui de devant ne nous ralentit pas vraiment

        for visee in (self.voie + 1, self.voie - 1):
            if not 0 <= visee < nombre:
                continue
            if trafic.file_libre(self.depuis, self.vers, visee,
                                 self.avance, MARGE_DEBOITEMENT):
                ancienne = (self.depuis, self.vers, self.voie)
                self.voie = visee
                self.depuis_deboitement = 0.0
                trafic.deplacer(self, ancienne, self.vers)
                return

    # --- passage au carrefour ---------------------------------------------
    def compter_les_arrets(self, dt):
        """Tient a jour le temps d'arret au stop et le temps de blocage."""
        immobile = self.vitesse < 0.3
        proche = self.reste < ZONE_DECISION

        if immobile and self.reste < RECUL_CARREFOUR + 4.0:
            self.attente_stop += dt
        if immobile and proche:
            self.bloque_depuis += dt
        else:
            self.bloque_depuis = 0.0

    def changer_de_rue(self, trafic):
        """Arrive au carrefour : on passe sur la rue choisie."""
        depasse = self.avance - self.longueur_rue
        precedent = self.depuis
        ancienne = (self.depuis, self.vers, self.voie)
        ancien_vers = self.vers

        nouvelle_voie = self.voie_apres()
        self.depuis = self.vers
        self.vers = self.suivant or self.rue_suivante(self.depuis, precedent)
        self.voie = min(nouvelle_voie, ville.voies(self.depuis, self.vers) - 1)
        self.avance = min(depasse, self.longueur_rue * 0.5)
        self.suivant = self.rue_suivante(self.vers, self.depuis)

        self.attente_stop = 0.0
        self.bloque_depuis = 0.0
        self.depuis_deboitement = 0.0
        trafic.deplacer(self, ancienne, ancien_vers)

    def rue_suivante(self, carrefour, precedent):
        """
        Le trafic civil n'a pas de destination : a chaque carrefour, chaque
        voiture tire une rue au hasard. On evite le demi-tour, sauf si la
        rue d'ou l'on vient est la seule possible.
        """
        choix = [v for v in ville.voisins(carrefour) if v != precedent]
        if not choix:
            choix = [precedent]
        return random.choice(choix)

    def liberer_le_carrefour(self, trafic):
        """Une fois degage, on rend le carrefour aux autres."""
        if self.reservation is None:
            return
        deja_passe = self.reservation != self.vers
        if deja_passe and self.avance > DEGAGEMENT:
            trafic.liberer(self.reservation, self.id)
            self.reservation = None
