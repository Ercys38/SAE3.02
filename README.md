<h1 align="center">Avenue de Bâle</h1>

<p align="center">
  Priorisation des véhicules de secours en carrefour urbain connecté<br>
  <em>SAÉ R3.02 — Développer une application communicante</em><br>
  IUT de Colmar — Réseaux &amp; Télécommunications
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/d%C3%A9pendances-aucune-success">
  <img src="https://img.shields.io/badge/interface-tkinter-informational">
  <img src="https://img.shields.io/badge/base-SQLite-003B57?logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/r%C3%A9seau-TCP%2FJSON-orange">
</p>

<p align="center"><img src="docs/apercu.png" width="100%"></p>

---

## Le problème

Quand il y a de la circulation, les véhicules d'urgence perdent du temps aux
carrefours. Les voitures n'ont pas la place de se ranger, celles qui sont
arrêtées au feu ne peuvent pas bouger. Un véhicule prioritaire a le droit de
franchir un rouge, mais sous la responsabilité du conducteur, et c'est
dangereux.

Le client, M. Frédéric Drouhin, a donc deux besoins qui vont ensemble :
**gagner du temps** sur le trajet et **éviter les accidents**. Aller plus vite
en provoquant des accidents ne réglerait rien.

## La réponse

Un simulateur qui met le dispositif en évidence et le chiffre. On y règle la
densité de circulation, on appelle un service, et on regarde le véhicule
traverser la ville — une fois avec le dispositif, une fois sans.

| Densité | Sans dispositif | Avec dispositif | Gain |
|:--:|:--:|:--:|:--:|
| 20 % | 106,0 s | 70,9 s | **33 %** |
| 60 % | 164,6 s | 70,4 s | **57 %** |
| 100 % | 204,5 s | 84,5 s | **59 %** |

<sub>Traversée de l'avenue d'ouest en est, 1,1 km et 6 carrefours, moyenne sur
8 trajets par ligne. Reproductible avec `python3 mesures.py`.</sub>

Le gain monte avec la circulation : sans dispositif le véhicule subit les
files, avec le dispositif son temps bouge à peine quelle que soit la densité.

## Démarrage

```bash
sudo apt install python3-tk     # Debian, tkinter est dans un paquet séparé
python3 main.py
```

Aucune dépendance à installer, tout vient de la bibliothèque standard. Il faut
un terminal ouvert dans la session graphique : en SSH ou en root, tkinter
répond `no display name and no $DISPLAY`.

## Ce que fait la maquette

| | |
|---|---|
| **Ville en graphe** | une avenue de 1,1 km, six rues, cinq carrefours à feux, un rond-point |
| **Trafic autonome** | jusqu'à 130 voitures qui respectent feux, stops, cédez-le-passage et priorité à droite |
| **Deux files par sens** | sans quoi une voiture ne pourrait que freiner, pas se ranger |
| **Onde verte** | les feux passent au vert devant le véhicule de secours, puis reprennent leur cycle |
| **Alerte de proximité** | les véhicules à moins de 500 m sont prévenus de son arrivée et de sa direction |
| **Rangement réaliste** | les civils se déportent progressivement sur la droite, sauf ceux qui doivent d'abord dégager le carrefour |
| **Itinéraire** | calculé par Dijkstra du bâtiment du service jusqu'au lieu d'intervention |
| **Mesure du gain** | chaque intervention est chronométrée et archivée en base |

## Architecture

Trois threads, des messages JSON, un verrou sur l'état partagé.

```mermaid
flowchart LR
    A["Thread principal<br/>affichage tkinter"] -->|lit l'état<br/>sous verrou| B["Thread moteur<br/>trafic, pas de 33 ms"]
    B -->|position 10 fois/s<br/>libération| C["Thread superviseur<br/>poste central"]
    C -->|accord de priorité<br/>alerte de proximité| B
    C --> D[("SQLite<br/>historique")]
```

Le superviseur n'a pas besoin d'être dans la même application. Les mêmes
messages passent alors par une socket TCP, une ligne de JSON par message.

```mermaid
flowchart LR
    subgraph VM1["VM 1"]
        S["serveur.py<br/>superviseur + SQLite"]
    end
    subgraph VM2["VM 2"]
        M["main.py<br/>simulation + fenêtre"]
    end
    M -->|"position, libération"| S
    S -->|"accord, alerte"| M
```

```bash
# sur la VM qui héberge le superviseur
python3 serveur.py

# sur la VM qui héberge la simulation, avec l'adresse de la première
python3 main.py 192.168.x.y
```

Les deux VM doivent être en réseau interne ou en pont dans VirtualBox, pas en
NAT simple. Sans argument, `main.py` garde tout en local.

## Les messages

Chaque message porte son type, l'identifiant de l'émetteur, l'heure et un
contenu.

```json
{"type": "accord_priorite", "emetteur": "superviseur",
 "heure": 1793956056.042,
 "contenu": {"carrefour": "C3", "axe": "vertical"}}
```

| Type | Sens | Rôle |
|---|---|---|
| `position` | véhicule → superviseur | où il est, à quelle distance du prochain carrefour |
| `demande_priorite` | véhicule → superviseur | il réclame le vert |
| `accord_priorite` | superviseur → carrefour | le vert est accordé sur cet axe |
| `alerte_proximite` | superviseur → véhicules | un secours arrive à moins de 500 m |
| `liberation` | véhicule → superviseur | le carrefour est rendu |

## La base

`historique.db` se crée toute seule à la racine. Une table `interventions` :
date, densité, service, départ, arrivée, temps avec le dispositif, temps sans.

```bash
python3 -c "
from simulation.journal import Journal
j = Journal()
for ligne in j.dernieres():
    print(ligne)
print('gain moyen', j.gain_moyen(), 's')
"
```

## Le code

| Fichier | Rôle |
|---|---|
| `main.py` | lance l'application |
| `serveur.py` | lance le superviseur seul, pour la deuxième machine |
| `mesures.py` | compare les temps avec et sans dispositif |
| `simulation/ville.py` | le plan, les rues, Dijkstra |
| `simulation/feux.py` | les feux tricolores |
| `simulation/code_route.py` | qui a le droit de passer dans un carrefour |
| `simulation/vehicule.py` | la conduite autonome des voitures |
| `simulation/secours.py` | les véhicules prioritaires |
| `simulation/simulation.py` | l'état du trafic à un instant donné |
| `simulation/affichage.py` | la fenêtre tkinter |
| `simulation/messages.py` | le format JSON des échanges |
| `simulation/superviseur.py` | le poste central |
| `simulation/moteur.py` | le thread qui fait avancer le trafic |
| `simulation/reseau.py` | le serveur TCP et son client |
| `simulation/journal.py` | la base SQLite |

PEP 8, noms et commentaires en français, aucune dépendance extérieure.

## L'équipe

**K2 X ERCYS** — KUM Abdulkaan et NOUMBA Keran-Lynch.

KUM Abdulkaan : interface, affichage du plan, panneau de contrôle, trafic
civil et conduite autonome. NOUMBA Keran-Lynch : modélisation de la ville,
itinéraires, superviseur, threads et base de données. À deux : le format des
messages, les tests, la documentation et le dépôt.

<sub>Maquette rendue le 15 novembre 2026. Elle ne commande aucun feu réel.</sub>
