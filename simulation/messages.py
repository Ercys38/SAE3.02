import json
import time

POSITION = "position"
DEMANDE_PRIORITE = "demande_priorite"
ACCORD_PRIORITE = "accord_priorite"
ALERTE_PROXIMITE = "alerte_proximite"
LIBERATION = "liberation"
DEBUT_INTERVENTION = "debut_intervention"
FIN_INTERVENTION = "fin_intervention"

TYPES = (POSITION, DEMANDE_PRIORITE, ACCORD_PRIORITE, ALERTE_PROXIMITE,
         LIBERATION, DEBUT_INTERVENTION, FIN_INTERVENTION)

CHAMPS = ("type", "emetteur", "heure", "contenu")


def creer(genre, emetteur, contenu=None):
    if genre not in TYPES:
        raise ValueError("type de message inconnu : " + str(genre))

    if contenu is None:
        contenu = {}

    return {"type": genre,
            "emetteur": str(emetteur),
            "heure": round(time.time(), 3),
            "contenu": contenu}


def encoder(message):
    return json.dumps(message)


def decoder(texte):
    message = json.loads(texte)

    if not isinstance(message, dict):
        raise ValueError("message mal forme")

    for champ in CHAMPS:
        if champ not in message:
            raise ValueError("champ manquant : " + champ)

    if message["type"] not in TYPES:
        raise ValueError("type de message inconnu : " + str(message["type"]))

    return message


def position(vehicule, carrefour, distance, axe):
    return creer(POSITION, vehicule.id,
                 {"service": vehicule.service,
                  "carrefour": carrefour,
                  "distance": round(distance, 1),
                  "axe": axe})


def demande_priorite(vehicule, carrefour, axe):
    return creer(DEMANDE_PRIORITE, vehicule.id,
                 {"carrefour": carrefour, "axe": axe})


def accord_priorite(carrefour, axe):
    return creer(ACCORD_PRIORITE, "superviseur",
                 {"carrefour": carrefour, "axe": axe})


def alerte_proximite(carrefour, axe, distance):
    return creer(ALERTE_PROXIMITE, "superviseur",
                 {"carrefour": carrefour,
                  "axe": axe,
                  "distance": round(distance, 1)})


def liberation(vehicule, carrefour):
    return creer(LIBERATION, vehicule.id, {"carrefour": carrefour})


def debut_intervention(reference, densite, service, depart, arrivee):
    return creer(DEBUT_INTERVENTION, "simulation",
                 {"reference": reference,
                  "densite": densite,
                  "service": service,
                  "depart": depart,
                  "arrivee": arrivee})


def fin_intervention(reference, temps_avec=None, temps_sans=None):
    return creer(FIN_INTERVENTION, "simulation",
                 {"reference": reference,
                  "temps_avec": temps_avec,
                  "temps_sans": temps_sans})
