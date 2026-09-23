"""
Plan simplifie du centre de Saint-Louis (68300).

Le plan est un GRAPHE :
  - les sommets sont les carrefours,
  - les aretes sont les rues.

Il y a deux niveaux de voirie :
  - les grandes voies (avenues et rues principales), reliant les carrefours
    A a I, dont trois sont equipes de feux ;
  - les petites rues, qui traversent l'interieur de chaque bloc et se
    croisent en son centre (P1 a P4).

Toutes les distances sont en metres. L'origine (0, 0) est en haut a gauche.

Ce fichier ne contient que des DONNEES : pour changer la ville, on change
ce fichier et rien d'autre.
"""

# --- Les carrefours -------------------------------------------------------
# "feux"       : True si le carrefour est equipe de feux tricolores.
# "principal"  : True pour les grands carrefours, False pour les croisements
#                de petites rues (change seulement la facon de les dessiner).
CARREFOURS = {
    # les grands carrefours
    "A": {"pos": (0, 0),       "feux": False, "principal": True},
    "B": {"pos": (700, 0),     "feux": True,  "principal": True},
    "C": {"pos": (1400, 0),    "feux": False, "principal": True},
    "D": {"pos": (0, 700),     "feux": False, "principal": True},
    "E": {"pos": (700, 700),   "feux": True,  "principal": True},
    "F": {"pos": (1400, 700),  "feux": True,  "principal": True},
    "G": {"pos": (0, 1400),    "feux": False, "principal": True},
    "H": {"pos": (700, 1400),  "feux": False, "principal": True},
    "I": {"pos": (1400, 1400), "feux": False, "principal": True},

    # les debouches des petites rues, au milieu des grandes voies
    "AB": {"pos": (350, 0),     "feux": False, "principal": False},
    "BC": {"pos": (1050, 0),    "feux": False, "principal": False},
    "DE": {"pos": (350, 700),   "feux": False, "principal": False},
    "EF": {"pos": (1050, 700),  "feux": False, "principal": False},
    "GH": {"pos": (350, 1400),  "feux": False, "principal": False},
    "HI": {"pos": (1050, 1400), "feux": False, "principal": False},
    "AD": {"pos": (0, 350),     "feux": False, "principal": False},
    "DG": {"pos": (0, 1050),    "feux": False, "principal": False},
    "BE": {"pos": (700, 350),   "feux": False, "principal": False},
    "EH": {"pos": (700, 1050),  "feux": False, "principal": False},
    "CF": {"pos": (1400, 350),  "feux": False, "principal": False},
    "FI": {"pos": (1400, 1050), "feux": False, "principal": False},

    # le croisement des deux petites rues, au centre de chaque bloc
    "P1": {"pos": (350, 350),   "feux": False, "principal": False},
    "P2": {"pos": (1050, 350),  "feux": False, "principal": False},
    "P3": {"pos": (350, 1050),  "feux": False, "principal": False},
    "P4": {"pos": (1050, 1050), "feux": False, "principal": False},
}

# --- Les rues -------------------------------------------------------------
# (depart, arrivee, nom, categorie)
# La categorie vaut "avenue" pour les grandes voies et "rue" pour les
# petites. Elle ne sert qu'a l'affichage et, plus tard, a la vitesse.
# La circulation se fait dans les deux sens.
RUES = [
    # --- les grandes voies, coupees en deux par le debouche d'une petite rue
    ("A", "AB", "Avenue de Bale", "avenue"),
    ("AB", "B", "Avenue de Bale", "avenue"),
    ("B", "BC", "Avenue de Bale", "avenue"),
    ("BC", "C", "Avenue de Bale", "avenue"),

    ("D", "DE", "Rue de Mulhouse", "avenue"),
    ("DE", "E", "Rue de Mulhouse", "avenue"),
    ("E", "EF", "Rue de Mulhouse", "avenue"),
    ("EF", "F", "Rue de Mulhouse", "avenue"),

    ("G", "GH", "Rue de Huningue", "avenue"),
    ("GH", "H", "Rue de Huningue", "avenue"),
    ("H", "HI", "Rue de Huningue", "avenue"),
    ("HI", "I", "Rue de Huningue", "avenue"),

    ("A", "AD", "Avenue du General de Gaulle", "avenue"),
    ("AD", "D", "Avenue du General de Gaulle", "avenue"),
    ("D", "DG", "Avenue du General de Gaulle", "avenue"),
    ("DG", "G", "Avenue du General de Gaulle", "avenue"),

    ("B", "BE", "Rue de Saint-Exupery", "avenue"),
    ("BE", "E", "Rue de Saint-Exupery", "avenue"),
    ("E", "EH", "Rue de Saint-Exupery", "avenue"),
    ("EH", "H", "Rue de Saint-Exupery", "avenue"),

    ("C", "CF", "Boulevard de l'Europe", "avenue"),
    ("CF", "F", "Boulevard de l'Europe", "avenue"),
    ("F", "FI", "Boulevard de l'Europe", "avenue"),
    ("FI", "I", "Boulevard de l'Europe", "avenue"),

    # --- bloc 1 (A B E D)
    ("AD", "P1", "Rue des Vergers", "rue"),
    ("P1", "BE", "Rue des Vergers", "rue"),
    ("AB", "P1", "Rue du Moulin", "rue"),
    ("P1", "DE", "Rue du Moulin", "rue"),

    # --- bloc 2 (B C F E)
    ("BE", "P2", "Rue des Tilleuls", "rue"),
    ("P2", "CF", "Rue des Tilleuls", "rue"),
    ("BC", "P2", "Rue de la Gare", "rue"),
    ("P2", "EF", "Rue de la Gare", "rue"),

    # --- bloc 3 (D E H G)
    ("DG", "P3", "Rue des Ecoles", "rue"),
    ("P3", "EH", "Rue des Ecoles", "rue"),
    ("DE", "P3", "Rue du Stade", "rue"),
    ("P3", "GH", "Rue du Stade", "rue"),

    # --- bloc 4 (E F I H)
    ("EH", "P4", "Rue des Jardins", "rue"),
    ("P4", "FI", "Rue des Jardins", "rue"),
    ("EF", "P4", "Rue de la Poste", "rue"),
    ("P4", "HI", "Rue de la Poste", "rue"),
]


# --- Les panneaux ---------------------------------------------------------
# Carrefours equipes d'un STOP, decrits par (carrefour, provenance).
# Partout ailleurs, la regle est deduite automatiquement par panneau().
STOPS = [
    ("DE", "P1"),
    ("EH", "P4"),
]


def panneau(carrefour, provenance):
    """
    Panneau rencontre par un vehicule qui arrive a "carrefour" en venant
    de "provenance".

    Renvoie "stop", "cedez", ou None.
    None signifie qu'il n'y a pas de panneau : c'est alors la priorite a
    droite qui s'applique, sauf si le carrefour a des feux.

    La regle est calculee et non ecrite a la main : une petite rue qui
    debouche sur une grande voie porte un cedez-le-passage. Comme cela,
    si on modifie le plan, les panneaux suivent tout seuls.
    """
    if CARREFOURS[carrefour]["feux"]:
        return None  # ce sont les feux qui commandent

    if (carrefour, provenance) in STOPS:
        return "stop"

    categories_du_carrefour = [categorie(carrefour, v) for v in voisins(carrefour)]
    if "avenue" in categories_du_carrefour and categorie(carrefour, provenance) == "rue":
        return "cedez"

    return None


# --- Les voies ------------------------------------------------------------
# Une avenue a deux files dans chaque sens, une petite rue une seule.
LARGEUR_VOIE = 8.0   # m


def voies(depuis, arrivee):
    """Nombre de files de circulation dans un sens."""
    if categorie(depuis, arrivee) == "avenue":
        return 2
    return 1


def decalage_voie(depuis, arrivee, voie):
    """
    Distance entre l'axe de la rue et le milieu d'une file, en metres.

    La file 0 est la plus a droite, donc la plus eloignee de l'axe. On
    roule a droite : le decalage se compte vers la droite du sens de marche.
    """
    nombre = voies(depuis, arrivee)
    return LARGEUR_VOIE * (nombre - voie - 0.5)


def position(carrefour):
    """Coordonnees (x, y) du carrefour, en metres."""
    return CARREFOURS[carrefour]["pos"]


def voisins(carrefour):
    """Liste des carrefours directement accessibles depuis celui-ci."""
    resultat = []
    for depart, arrivee, _nom, _cat in RUES:
        if depart == carrefour:
            resultat.append(arrivee)
        elif arrivee == carrefour:
            resultat.append(depart)
    return resultat


def longueur(depart, arrivee):
    """Longueur de la rue entre deux carrefours, en metres."""
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def nom_rue(depart, arrivee):
    """Nom de la rue reliant les deux carrefours."""
    for a, b, nom, _cat in RUES:
        if (a, b) == (depart, arrivee) or (b, a) == (depart, arrivee):
            return nom
    return "?"


def categorie(depart, arrivee):
    """Categorie de la rue : "avenue" ou "rue"."""
    for a, b, _nom, cat in RUES:
        if (a, b) == (depart, arrivee) or (b, a) == (depart, arrivee):
            return cat
    return "rue"


def axe(depart, arrivee):
    """
    Axe de circulation de la rue : "horizontal" ou "vertical".
    Sert aux feux : a un carrefour, un seul des deux axes est vert a la fois.
    """
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    if abs(x2 - x1) > abs(y2 - y1):
        return "horizontal"
    return "vertical"


def taille_ville():
    """Largeur et hauteur du plan, en metres."""
    xs = [position(c)[0] for c in CARREFOURS]
    ys = [position(c)[1] for c in CARREFOURS]
    return max(xs), max(ys)
