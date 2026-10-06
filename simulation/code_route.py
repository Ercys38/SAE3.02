from . import ville

DISTANCE_VIGILANCE = 45.0
DUREE_STOP = 1.5
BLOCAGE_MAX = 6.0
RAYON_CARREFOUR = 18.0
ECART_TRAJECTOIRES = 7.5


def passage_autorise(vehicule, trafic):
    carrefour = vehicule.vers

    if not trajectoires_compatibles(vehicule, trafic):
        return False

    if vehicule.bloque_depuis > BLOCAGE_MAX:
        return True

    feu = trafic.feux.get(carrefour)
    if feu is not None:
        return feu.passage_autorise(ville.axe(vehicule.depuis, vehicule.vers))

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
    segment_mien = trajet_dans_le_carrefour(vehicule.vers, mien)

    for autre in actifs:
        if autre == mien:
            continue
        autre_segment = trajet_dans_le_carrefour(vehicule.vers, autre)
        if distance_entre_segments(segment_mien, autre_segment) < ECART_TRAJECTOIRES:
            return False
    return True


def trajet_dans_le_carrefour(carrefour, mouvement):
    entree, voie, sortie, voie_sortie = mouvement
    depart = point_de_file(entree, carrefour, voie, False)
    arrivee = point_de_file(sortie, carrefour, voie_sortie, True)
    return (depart, arrivee)


def point_de_file(branche, carrefour, voie, sortant):
    xc, yc = ville.position(carrefour)
    xb, yb = ville.position(branche)

    longueur = ((xb - xc) ** 2 + (yb - yc) ** 2) ** 0.5
    if longueur < 0.001:
        longueur = 0.001
    ux = (xb - xc) / longueur
    uy = (yb - yc) / longueur

    if sortant:
        ecart = ville.decalage_voie(carrefour, branche, voie)
        droite_x = -uy
        droite_y = ux
    else:
        ecart = ville.decalage_voie(branche, carrefour, voie)
        droite_x = uy
        droite_y = -ux

    x = xc + ux * RAYON_CARREFOUR + droite_x * ecart
    y = yc + uy * RAYON_CARREFOUR + droite_y * ecart
    return (x, y)


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
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0

    proche_x = x1 + t * dx
    proche_y = y1 + t * dy
    return ((px - proche_x) ** 2 + (py - proche_y) ** 2) ** 0.5


def sens(p, q, r):
    valeur = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if abs(valeur) < 1e-9:
        return 0
    if valeur > 0:
        return 1
    return -1


def sur_le_segment(p, q, r):
    if q[0] < min(p[0], r[0]) - 1e-9 or q[0] > max(p[0], r[0]) + 1e-9:
        return False
    if q[1] < min(p[1], r[1]) - 1e-9 or q[1] > max(p[1], r[1]) + 1e-9:
        return False
    return True


def se_croisent(premier, second):
    a, b = premier
    c, d = second

    s1 = sens(a, b, c)
    s2 = sens(a, b, d)
    s3 = sens(c, d, a)
    s4 = sens(c, d, b)

    if s1 != s2 and s3 != s4:
        return True
    if s1 == 0 and sur_le_segment(a, c, b):
        return True
    if s2 == 0 and sur_le_segment(a, d, b):
        return True
    if s3 == 0 and sur_le_segment(c, a, d):
        return True
    if s4 == 0 and sur_le_segment(c, b, d):
        return True
    return False


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
