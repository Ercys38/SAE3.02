"""
Calcul d'itineraire sur le plan de la ville.

Le plan est un graphe (voir ville.py) : on y cherche le plus court chemin
avec l'algorithme de Dijkstra, sur une file de priorite (heapq).

Par defaut, le cout d'une rue est sa longueur en metres. On peut passer une
autre fonction de cout, par exemple un temps de parcours qui tient compte
des embouteillages : le vehicule de secours s'en servira.

Ce fichier ne depend que de ville.py et ne parle pas au monde exterieur.
"""

import heapq

from . import ville


def plus_court_chemin(depart, arrivee, cout=None):
    """
    Plus court chemin entre deux carrefours.

    "cout" est une fonction (depuis, vers) -> nombre positif. Si elle est
    absente, on prend la longueur de la rue.

    Renvoie (chemin, total) : la liste des carrefours traverses, depart et
    arrivee compris, et la somme des couts. Renvoie (None, inf) si
    l'arrivee est inatteignable.
    """
    if depart not in ville.CARREFOURS:
        raise ValueError(f"carrefour inconnu : {depart}")
    if arrivee not in ville.CARREFOURS:
        raise ValueError(f"carrefour inconnu : {arrivee}")
    if cout is None:
        cout = ville.longueur

    meilleur = {depart: 0.0}
    precedent = {}
    a_voir = [(0.0, depart)]
    fini = set()

    while a_voir:
        total, courant = heapq.heappop(a_voir)
        if courant in fini:
            continue  # entree perimee : on a deja trouve mieux
        if courant == arrivee:
            return reconstruire(precedent, depart, arrivee), total
        fini.add(courant)

        for voisin in ville.voisins(courant):
            if voisin in fini:
                continue
            etape = cout(courant, voisin)
            if etape < 0:
                raise ValueError("Dijkstra n'accepte pas de cout negatif")
            nouveau = total + etape
            if nouveau < meilleur.get(voisin, float("inf")):
                meilleur[voisin] = nouveau
                precedent[voisin] = courant
                heapq.heappush(a_voir, (nouveau, voisin))

    return None, float("inf")


def reconstruire(precedent, depart, arrivee):
    """Remonte la table des predecesseurs pour obtenir le chemin."""
    chemin = [arrivee]
    while chemin[-1] != depart:
        chemin.append(precedent[chemin[-1]])
    chemin.reverse()
    return chemin


def longueur_chemin(chemin):
    """Longueur totale d'un chemin, en metres."""
    return sum(ville.longueur(a, b) for a, b in zip(chemin, chemin[1:]))


def description(chemin):
    """
    Liste des rues empruntees, sans repeter une rue suivie sur plusieurs
    troncons. Sert a l'affichage du trajet du vehicule de secours.
    """
    rues = []
    for a, b in zip(chemin, chemin[1:]):
        nom = ville.nom_rue(a, b)
        if not rues or rues[-1] != nom:
            rues.append(nom)
    return rues
