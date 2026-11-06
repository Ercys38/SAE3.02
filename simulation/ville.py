LARGEUR_VOIE = 8.0

CARREFOURS = {
    "C1": {"pos": (160, 228), "feux": True, "principal": True},
    "C2": {"pos": (320, 210), "feux": True, "principal": True},
    "C3": {"pos": (480, 200), "feux": True, "principal": True},
    "C4": {"pos": (640, 205), "feux": True, "principal": True},
    "C5": {"pos": (800, 222), "feux": False, "principal": True,
           "rond_point": True},
    "C6": {"pos": (960, 248), "feux": True, "principal": True},

    "O": {"pos": (0, 250), "feux": False, "principal": False},
    "E": {"pos": (1120, 275), "feux": False, "principal": False},

    "N1": {"pos": (150, 60), "feux": False, "principal": False},
    "S1": {"pos": (335, 380), "feux": False, "principal": False},
    "N2": {"pos": (470, 40), "feux": False, "principal": False},
    "S2": {"pos": (650, 375), "feux": False, "principal": False},
    "N3": {"pos": (815, 55), "feux": False, "principal": False},
    "N4": {"pos": (640, 50), "feux": False, "principal": False},
    "S3": {"pos": (975, 400), "feux": False, "principal": False},
}

RUES = [
    ("O", "C1", "Avenue de Bale", "avenue"),
    ("C1", "C2", "Avenue de Bale", "avenue"),
    ("C2", "C3", "Avenue de Bale", "avenue"),
    ("C3", "C4", "Avenue de Bale", "avenue"),
    ("C4", "C5", "Avenue de Bale", "avenue"),
    ("C5", "C6", "Avenue de Bale", "avenue"),
    ("C6", "E", "Avenue de Bale", "avenue"),

    ("N1", "C1", "Rue du Moulin", "rue"),
    ("C2", "S1", "Rue de Huningue", "rue"),
    ("N2", "C3", "Rue des Vosges", "rue"),
    ("N4", "C4", "Rue de Saint-Louis", "rue"),
    ("C4", "S2", "Rue de Saint-Louis", "rue"),
    ("N3", "C5", "Rue des Trois Frontieres", "rue"),
    ("C6", "S3", "Rue de la Gare", "rue"),
]

BATIMENTS = {
    "Caserne des pompiers": {"pos": (90, 95), "service": "pompiers",
                             "acces": "N1"},
    "Hopital de Saint-Louis": {"pos": (720, 395), "service": "samu",
                               "acces": "S2"},
    "Commissariat": {"pos": (880, 70), "service": "police",
                     "acces": "N3"},
}

STOPS = []


def position(carrefour):
    return CARREFOURS[carrefour]["pos"]


def longueur(depart, arrivee):
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def point_sur_rue(depart, arrivee, part):
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    return (x1 + (x2 - x1) * part, y1 + (y2 - y1) * part)


def tangente_rue(depart, arrivee, part):
    x1, y1 = position(depart)
    x2, y2 = position(arrivee)
    d = longueur(depart, arrivee)
    if d < 0.001:
        d = 0.001
    return ((x2 - x1) / d, (y2 - y1) / d)


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


def est_un_rond_point(carrefour):
    return CARREFOURS[carrefour].get("rond_point", False)


def panneau(carrefour, provenance):
    if CARREFOURS[carrefour]["feux"]:
        return None

    if est_un_rond_point(carrefour):
        return "cedez"

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


def axe(depart, arrivee):
    dx, dy = tangente_rue(depart, arrivee, 1.0)
    if abs(dx) > abs(dy):
        return "horizontal"
    return "vertical"


def genre_de_mouvement(precedent, carrefour, suivant):
    ux, uy = tangente_rue(precedent, carrefour, 1.0)
    vx, vy = tangente_rue(carrefour, suivant, 0.0)

    if ux * vx + uy * vy > 0.5:
        return "tout_droit"
    if ux * vy - uy * vx > 0:
        return "droite"
    return "gauche"


def itineraire(depart, arrivee):
    distances = {depart: 0.0}
    venant_de = {}
    a_voir = [depart]
    vus = []

    while a_voir:
        courant = a_voir[0]
        for n in a_voir:
            if distances[n] < distances[courant]:
                courant = n
        a_voir.remove(courant)
        vus.append(courant)

        if courant == arrivee:
            break

        for voisin in voisins(courant):
            if voisin in vus:
                continue
            total = distances[courant] + longueur(courant, voisin)
            if voisin not in distances or total < distances[voisin]:
                distances[voisin] = total
                venant_de[voisin] = courant
                if voisin not in a_voir:
                    a_voir.append(voisin)

    if arrivee not in distances:
        return []

    chemin = [arrivee]
    while chemin[-1] != depart:
        chemin.append(venant_de[chemin[-1]])
    chemin.reverse()
    return chemin


def batiments_du_service(service):
    resultat = []
    for nom in BATIMENTS:
        if BATIMENTS[nom]["service"] == service:
            resultat.append(nom)
    return resultat


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
