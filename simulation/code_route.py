import math

from . import ville

DISTANCE_VIGILANCE = 45.0
DUREE_STOP = 1.5
BLOCAGE_MAX = 6.0
ATTENTE_SECOURS = 2.0
RAYON_CARREFOUR = 24.0
RAYON_ROND_POINT = 26.0
MORCEAUX_VIRAGE = 6
MARGE_ANGULAIRE = 0.40
ECART_TRAJECTOIRES = 11.0
ECART_PARALLELE = 7.0


def passage_autorise(vehicule, trafic):
    carrefour = vehicule.vers

    if not trajectoires_compatibles(vehicule, trafic):
        return False

    if ville.est_un_rond_point(carrefour):
        return True

    feu = trafic.feux.get(carrefour)
    if feu is not None:
        if feu.passage_autorise(ville.axe(vehicule.depuis, vehicule.vers)):
            return True
        if vehicule.prioritaire and vehicule.attente_stop >= ATTENTE_SECOURS:
            return True
        return False

    if vehicule.bloque_depuis > BLOCAGE_MAX:
        return True

    panneau = ville.panneau(carrefour, vehicule.depuis)

    if panneau == "stop":
        if vehicule.attente_stop < DUREE_STOP:
            return False
        return not quelqu_un_arrive(vehicule, trafic, "cedez")

    if panneau == "cedez":
        return not quelqu_un_arrive(vehicule, trafic, "cedez")

    return not quelqu_un_arrive(vehicule, trafic, "droite")


def trajectoires_compatibles(vehicule, trafic):
    actifs = trafic.mouvements.get(vehicule.vers)
    if not actifs:
        return True

    mien = vehicule.mouvement()

    if ville.est_un_rond_point(vehicule.vers):
        mon_arc = arc_du_mouvement(vehicule.vers, mien)
        for autre in actifs:
            if autre == mien:
                continue
            if arcs_en_conflit(mon_arc,
                               arc_du_mouvement(vehicule.vers, autre)):
                return False
        return True

    mon_trajet = trajet_dans_le_carrefour(vehicule.vers, mien)

    for autre in actifs:
        if autre == mien:
            continue
        autre_trajet = trajet_dans_le_carrefour(vehicule.vers, autre)

        ecart = distance_entre_trajets(mon_trajet, autre_trajet)

        meme_sens = autre[0] == mien[0] and autre[2] == mien[2]
        sens_oppose = autre[0] == mien[2] and autre[2] == mien[0]

        if meme_sens or sens_oppose:
            if not trajets_se_croisent(mon_trajet, autre_trajet):
                if ecart >= ECART_PARALLELE:
                    continue
            return False

        if ecart < ECART_TRAJECTOIRES:
            return False
    return True


def rayon_du_carrefour(carrefour):
    if ville.est_un_rond_point(carrefour):
        return RAYON_ROND_POINT
    return RAYON_CARREFOUR


def angle(centre, point):
    return math.atan2(point[1] - centre[1], point[0] - centre[0])


def rayon_vers(centre, point):
    dx = point[0] - centre[0]
    dy = point[1] - centre[1]
    return (dx * dx + dy * dy) ** 0.5


def tour_du_rond_point(carrefour, depart, arrivee):
    centre = ville.position(carrefour)

    debut = angle(centre, depart)
    fin = angle(centre, arrivee)
    rayon_debut = rayon_vers(centre, depart)
    rayon_fin = rayon_vers(centre, arrivee)

    ecart = fin - debut
    while ecart > -0.1:
        ecart = ecart - 2 * math.pi

    nombre = int(abs(ecart) / 0.35) + 2
    points = []
    for i in range(nombre + 1):
        part = i / nombre
        a = debut + ecart * part
        r = rayon_debut + (rayon_fin - rayon_debut) * part
        points.append((centre[0] + r * math.cos(a),
                       centre[1] + r * math.sin(a)))
    return points


def arc_du_mouvement(carrefour, mouvement):
    rayon = rayon_du_carrefour(carrefour)
    entree, voie, sortie, voie_sortie = mouvement
    depart = point_de_file(entree, carrefour, voie, False, rayon)
    arrivee = point_de_file(sortie, carrefour, voie_sortie, True, rayon)

    centre = ville.position(carrefour)
    debut = angle(centre, depart)
    fin = angle(centre, arrivee)

    ecart = fin - debut
    while ecart > -0.1:
        ecart = ecart - 2 * math.pi
    return (debut, ecart)


def angle_dans_arc(theta, debut, ecart):
    recule = (debut - theta) % (2 * math.pi)
    return recule <= abs(ecart) + MARGE_ANGULAIRE


def arcs_en_conflit(premier, second):
    if angle_dans_arc(second[0], premier[0], premier[1]):
        return True
    if angle_dans_arc(premier[0], second[0], second[1]):
        return True
    return False


def courbe_du_virage(depart, pivot, arrivee):
    points = []
    for i in range(MORCEAUX_VIRAGE + 1):
        t = i / MORCEAUX_VIRAGE
        a = (1 - t) * (1 - t)
        b = 2 * (1 - t) * t
        c = t * t
        points.append((a * depart[0] + b * pivot[0] + c * arrivee[0],
                       a * depart[1] + b * pivot[1] + c * arrivee[1]))
    return points


def point_de_rencontre(depart, direction_depart, arrivee, direction_arrivee):
    ux, uy = direction_depart
    vx, vy = direction_arrivee

    det = uy * vx - ux * vy
    if abs(det) < 0.01:
        return ((depart[0] + arrivee[0]) / 2, (depart[1] + arrivee[1]) / 2)

    ex = arrivee[0] - depart[0]
    ey = arrivee[1] - depart[1]

    t = (ey * vx - ex * vy) / det
    if t < 0:
        t = 0
    return (depart[0] + ux * t, depart[1] + uy * t)


def trajet_dans_le_carrefour(carrefour, mouvement, rayon=None):
    if rayon is None:
        rayon = rayon_du_carrefour(carrefour)

    entree, voie, sortie, voie_sortie = mouvement
    depart = point_de_file(entree, carrefour, voie, False, rayon)
    arrivee = point_de_file(sortie, carrefour, voie_sortie, True, rayon)

    if ville.est_un_rond_point(carrefour):
        return tour_du_rond_point(carrefour, depart, arrivee)

    direction_depart = ville.tangente_rue(entree, carrefour, 1.0)
    direction_arrivee = ville.tangente_rue(carrefour, sortie, 0.0)

    pivot = point_de_rencontre(depart, direction_depart,
                               arrivee, direction_arrivee)
    return courbe_du_virage(depart, pivot, arrivee)


def morceaux(trajet):
    paires = []
    for i in range(len(trajet) - 1):
        paires.append((trajet[i], trajet[i + 1]))
    return paires


def distance_entre_trajets(premier, second):
    plus_court = None
    for a in morceaux(premier):
        for b in morceaux(second):
            d = distance_entre_segments(a, b)
            if plus_court is None or d < plus_court:
                plus_court = d
    return plus_court


def trajets_se_croisent(premier, second):
    for a in morceaux(premier):
        for b in morceaux(second):
            if se_croisent(a, b):
                return True
    return False


def point_de_file(branche, carrefour, voie, sortant, rayon=None):
    if rayon is None:
        rayon = RAYON_CARREFOUR

    if sortant:
        depart = carrefour
        arrivee = branche
    else:
        depart = branche
        arrivee = carrefour

    longueur = ville.longueur(depart, arrivee)
    if longueur < 1.0:
        longueur = 1.0

    part = rayon / longueur
    if not sortant:
        part = 1.0 - part
    part = min(max(part, 0.0), 1.0)

    x, y = ville.point_sur_rue(depart, arrivee, part)
    dx, dy = ville.tangente_rue(depart, arrivee, part)
    ecart = ville.decalage_voie(depart, arrivee, voie)
    return (x - dy * ecart, y + dx * ecart)


def distance_entre_segments(premier, second):
    if se_croisent(premier, second):
        return 0.0
    a, b = premier
    c, d = second
    return min(distance_point_segment(a, c, d),
               distance_point_segment(b, c, d),
               distance_point_segment(c, a, b),
               distance_point_segment(d, a, b))


def distance_point_segment(point, extremite1, extremite2):
    px, py = point
    x1, y1 = extremite1
    x2, y2 = extremite2

    dx = x2 - x1
    dy = y2 - y1
    carre = dx * dx + dy * dy
    if carre < 1e-9:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    t = ((px - x1) * dx + (py - y1) * dy) / carre
    t = min(max(t, 0.0), 1.0)

    proche_x = x1 + t * dx
    proche_y = y1 + t * dy
    return ((px - proche_x) ** 2 + (py - proche_y) ** 2) ** 0.5


def se_croisent(premier, second):
    a, b = premier
    c, d = second

    ux = b[0] - a[0]
    uy = b[1] - a[1]
    vx = d[0] - c[0]
    vy = d[1] - c[1]

    det = uy * vx - ux * vy
    if abs(det) < 1e-9:
        return False

    ex = c[0] - a[0]
    ey = c[1] - a[1]

    t = (ey * vx - ex * vy) / det
    u = (ey * ux - ex * uy) / det

    return 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0


def quelqu_un_arrive(vehicule, trafic, regle):
    carrefour = vehicule.vers

    for autre in trafic.vers_carrefour.get(carrefour, ()):
        if autre.id == vehicule.id:
            continue
        if autre.depuis == vehicule.depuis:
            continue
        if autre.reste > DISTANCE_VIGILANCE:
            continue

        if regle == "cedez":
            if ville.panneau(carrefour, autre.depuis) is None:
                return True
        else:
            if vient_de_la_droite(vehicule, autre):
                return True

    return False


def vient_de_la_droite(vehicule, autre):
    dx, dy = vehicule.direction()
    droite_x = -dy
    droite_y = dx

    x0, y0 = ville.position(vehicule.vers)
    x1, y1 = ville.position(autre.depuis)
    cx = x1 - x0
    cy = y1 - y0

    norme = (cx * cx + cy * cy) ** 0.5
    if norme < 0.001:
        norme = 0.001

    produit = (cx / norme) * droite_x + (cy / norme) * droite_y
    return produit > 0.7
