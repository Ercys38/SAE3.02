"""
Le code de la route.

Tout ce qui dit a un vehicule s'il a le droit de s'engager dans un
carrefour est regroupe ici, et nulle part ailleurs. Trois regles, dans
cet ordre de priorite :

  1. les feux tricolores, quand le carrefour en est equipe ;
  2. les panneaux : stop et cedez-le-passage ;
  3. a defaut, la priorite a droite.

Les vehicules de secours ne sont pas encore traites : ils arriveront a
l'etape suivante.
"""

from . import ville

DISTANCE_VIGILANCE = 45.0   # m : distance a laquelle on surveille les autres
DUREE_STOP = 1.5            # s d'arret complet exige par un stop
BLOCAGE_MAX = 6.0           # s : au-dela, on force le passage


def passage_autorise(vehicule, trafic):
    """Le vehicule a-t-il le droit de s'engager dans le carrefour ?"""
    carrefour = vehicule.vers

    # Le carrefour n'accepte ensemble que des trajectoires qui ne se
    # croisent pas. Cette regle passe avant toutes les autres.
    if not trajectoires_compatibles(vehicule, trafic):
        return False

    # Garde-fou : quatre voitures qui se cedent mutuellement la priorite a
    # droite ne repartiraient jamais. Au bout de quelques secondes, la
    # premiere bloquee passe. C'est ce que font les vrais conducteurs.
    if vehicule.bloque_depuis > BLOCAGE_MAX:
        return True

    # 1. Les feux.
    feu = trafic.feux.get(carrefour)
    if feu is not None:
        return feu.passage_autorise(ville.axe(vehicule.depuis, vehicule.vers))

    # 2. Les panneaux.
    panneau = ville.panneau(carrefour, vehicule.depuis)

    if panneau == "stop":
        if vehicule.attente_stop < DUREE_STOP:
            return False  # l'arret complet n'est pas encore marque
        return not quelqu_un_arrive(vehicule, trafic, "cedez")

    if panneau == "cedez":
        return not quelqu_un_arrive(vehicule, trafic, "cedez")

    # 3. Pas de panneau : priorite a droite.
    return not quelqu_un_arrive(vehicule, trafic, "droite")


def trajectoires_compatibles(vehicule, trafic):
    """
    Le vehicule peut-il entrer dans le carrefour sans croiser quelqu'un ?

    Un seul mouvement a la fois. Un mouvement, c'est une file d'entree et
    une file de sortie : les voitures qui l'empruntent se suivent, elles ne
    se croisent jamais, donc elles peuvent etre plusieurs dans le carrefour.
    Toute autre combinaison est refusee.

    On pourrait etre moins strict, mais pas simplement : deux voitures
    venues de la meme rue ne divergent pas toujours. Celle de la file
    interieure qui tourne a droite coupe la file exterieure qui va tout
    droit. Laisser passer ensemble deux flux tout droit sur le meme axe a
    ete essaye : le gain est nul, parce que seul un trajet sur trois va
    tout droit. La regle stricte est donc gardee.
    """
    actifs = trafic.mouvements.get(vehicule.vers)
    if not actifs:
        return True
    return list(actifs) == [vehicule.mouvement()]


def quelqu_un_arrive(vehicule, trafic, regle):
    """
    Y a-t-il un vehicule a qui l'on doit ceder le passage ?

    regle = "cedez"  : on cede a tous ceux qui sont sur la voie prioritaire,
                       c'est-a-dire ceux qui n'ont eux-memes aucun panneau.
    regle = "droite" : on ne cede qu'a celui qui vient de notre droite.
    """
    carrefour = vehicule.vers

    for autre in trafic.vers_carrefour.get(carrefour, ()):
        if autre.id == vehicule.id:
            continue
        if autre.depuis == vehicule.depuis:
            continue                      # meme file : il est devant, pas a cote
        if autre.reste > DISTANCE_VIGILANCE:
            continue                      # encore trop loin pour compter

        if regle == "cedez":
            if ville.panneau(carrefour, autre.depuis) is None:
                return True               # lui est prioritaire, on attend
        else:
            if vient_de_la_droite(vehicule, autre):
                return True

    return False


def vient_de_la_droite(vehicule, autre):
    """L'autre vehicule aborde-t-il le carrefour par la droite du notre ?"""
    dx, dy = vehicule.direction()

    # En coordonnees ecran l'axe y descend, donc la droite du vehicule est
    # le vecteur (-dy, dx).
    droite_x, droite_y = -dy, dx

    # De quel cote du carrefour l'autre arrive-t-il ?
    x0, y0 = ville.position(vehicule.vers)
    x1, y1 = ville.position(autre.depuis)
    cx, cy = x1 - x0, y1 - y0
    norme = max((cx * cx + cy * cy) ** 0.5, 0.001)

    produit = (cx / norme) * droite_x + (cy / norme) * droite_y
    return produit > 0.7
