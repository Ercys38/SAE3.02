LARGEUR_VOIE = 8.0

CARREFOURS = {
    "C": {"pos": (400, 400), "feux": True, "principal": True},
    "O": {"pos": (0, 400), "feux": False, "principal": False},
    "E": {"pos": (800, 400), "feux": False, "principal": False},
    "N": {"pos": (400, 0), "feux": False, "principal": False},
    "S": {"pos": (400, 800), "feux": False, "principal": False},
}

RUES = [
    ("O", "C", "Avenue de Bale", "avenue"),
    ("C", "E", "Avenue de Bale", "avenue"),
    ("N", "C", "Rue du Moulin", "rue"),
    ("C", "S", "Rue du Moulin", "rue"),
]

STOPS = []


def position(carrefour):
    return CARREFOURS[carrefour]["pos"]


def voisins(carrefour):
    resultat = []
    for depart, arrivee, nom, cat in RUES:
        if depart == carrefour:
            resultat.append(arrivee)
        elif arrivee == carrefour:
            resultat.append(depart)
    return resultat


def categorie(depart, arrivee):
    for a, b, nom, cat in RUES:
        if (a, b) == (depart, arrivee) or (b, a) == (depart, arrivee):
            return cat
    return "rue"


def nom_rue(depart, arrivee):
    for a, b, nom, cat in RUES:
        if (a, b) == (depart, arrivee) or (b, a) == (depart, arrivee):
            return nom
    return "?"


def voies(depuis, arrivee):
    if categorie(depuis, arrivee) == "avenue":
        return 2
    return 1


def decalage_voie(depuis, arrivee, voie):
    nombre = voies(depuis, arrivee)
    return LARGEUR_VOIE * (nombre - voie - 0.5)


def panneau(carrefour, provenance):
    if CARREFOURS[carrefour]["feux"]:
        return None

    if (carrefour, provenance) in STOPS:
        return "stop"

    il_y_a_une_avenue = False
    for voisin in voisins(carrefour):
        if categorie(carrefour, voisin) == "avenue":
            il_y_a_une_avenue = True

    if il_y_a_une_avenue and categorie(carrefour, provenance) == "rue":
        return "cedez"

    return None


def entrees():
    resultat = []
    for carrefour in CARREFOURS:
        if len(voisins(carrefour)) == 1:
            resultat.append(carrefour)
    return resultat


def est_une_sortie(carrefour):
    return len(voisins(carrefour)) == 1


def longueur(depart, arrivee):
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def axe(depart, arrivee):
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    if abs(x2 - x1) > abs(y2 - y1):
        return "horizontal"
    return "vertical"


def taille_ville():
    largeur = 0
    hauteur = 0
    for carrefour in CARREFOURS:
        x, y = position(carrefour)
        if x > largeur:
            largeur = x
        if y > hauteur:
            hauteur = y
    return largeur, hauteur
