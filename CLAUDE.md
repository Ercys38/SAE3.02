# SAE R3.02 — carrefour connecte

Simulateur de trafic urbain servant a demontrer et a mesurer l'apport d'un
dispositif de priorisation des vehicules de secours aux carrefours.

Equipe K2 X ERCYS : KUM Abdulkaan et NOUMBA Keran-Lynch.
IUT de Colmar, departement Reseaux et Telecommunications.
Client : M. Frederic Drouhin. Rendu du projet final le 15 novembre 2026.

Le plan est celui de Saint-Louis (68300), simplifie. C'est un choix de
l'equipe, pas une contrainte du client.

---

## Conventions

- **Tout est en francais** : noms de variables, de fonctions, commentaires,
  messages de commit. C'est volontaire, pour que le code reste lisible en
  soutenance. Ne pas repasser a l'anglais.
- **Aucune dependance exterieure.** tkinter, threading, queue, sqlite3,
  heapq, json, dataclasses et unittest sont tous dans la bibliotheque
  standard. `requirements.txt` est vide et doit le rester : le projet sera
  deploye sur deux VM Linux avec un simple `git clone`.
- PEP 8. Python 3.14.
- Les accents sont evites dans le code et les commentaires, pas dans les
  chaines affichees a l'utilisateur.

## La regle d'or de l'architecture

**Rien dans `simulation/` ne parle au monde exterieur**, sauf
`affichage.py` et, plus tard, `reseau.py`. Pas de `print`, pas de fichier
ouvert, pas de socket ailleurs.

C'est cette regle qui a permis de remplacer PySide6 par tkinter en ne
touchant qu'un fichier sur six. C'est elle qui permettra de passer des
files d'attente aux sockets sans reecrire la logique metier.

## Etat actuel

Fait :

| Fichier | Role |
|---|---|
| `simulation/ville.py` | le plan : carrefours, rues, files, panneaux, distances |
| `simulation/feux.py` | cycle des feux tricolores |
| `simulation/code_route.py` | priorites : feux, panneaux, priorite a droite |
| `simulation/vehicule.py` | deplacement d'une voiture, files, deboitement |
| `simulation/simulation.py` | etat global, index `Trafic`, densite |
| `simulation/affichage.py` | fenetre tkinter |
| `main.py` | point d'entree |

A ecrire :

| Fichier | Role | Etape |
|---|---|---|
| `simulation/itineraire.py` | Dijkstra sur le graphe | 3 |
| `simulation/secours.py` | le vehicule prioritaire | 3 |
| `simulation/messages.py` | format des messages echanges | 4 |
| `simulation/reseau.py` | sockets client / serveur | 4 |
| `simulation/base.py` | enregistrement des simulations en SQLite | 5 |
| `superviseur.py` | point d'entree du poste central, sur la VM 1 | 4 |

Commencer par `itineraire.py` : il ne depend que de `ville.py` et se teste
sans rien afficher.

## Decisions prises, et pourquoi

Ces choix ont tous une raison. Ne pas les defaire sans la connaitre.

**Le plan est un graphe.** Sommets = carrefours, aretes = rues. Cela rend
le calcul d'itineraire immediat et permet de changer de ville en ne
touchant qu'un fichier.

**Les panneaux sont calcules, pas ecrits a la main.** `ville.panneau()`
deduit qu'une petite rue debouchant sur une grande voie porte un
cedez-le-passage. Si le plan change, les panneaux suivent. Seuls deux stops
sont poses explicitement dans `STOPS`.

**Le gabarit d'une voiture est de 10 m, pas 5.** A l'echelle de la ville,
une vraie voiture ferait deux pixels. Toutes les distances de securite sont
calees sur ce gabarit exagere, pour que ce qui est calcule corresponde a ce
qui est dessine.

**`position()` renvoie le milieu de la file**, decalage lateral compris.
L'affichage ne refait aucun decalage. C'est ce qui rend le controle de
chevauchement fiable : il mesure exactement ce qui est a l'ecran.

**Un carrefour est attribue a un mouvement**, defini par une file d'entree
ET une file de sortie. Les voitures d'un meme mouvement se suivent sans se
croiser, elles peuvent donc y etre ensemble ; toute autre combinaison est
refusee. Regle volontairement stricte : deux voitures venues de la meme rue
ne divergent pas toujours, celle de la file interieure qui tourne a droite
coupe la file exterieure.

**`RECUL_CARREFOUR` vaut 24 m** et non 20. La ligne d'arret se mesure sur
l'axe de la rue, mais une voiture qui traverse dans la file exterieure
passe 12 m sur le cote, a hauteur de celle qui attend.

**`ZONE_DECISION` vaut 66 m.** Il faut 24 m pour s'arreter depuis 50 km/h,
plus les 24 m de recul. Decider plus tard voudrait dire ne pas pouvoir
s'arreter a temps.

**Un garde-fou de 6 s sur la priorite a droite.** Quatre voitures qui se
cedent mutuellement le passage ne repartiraient jamais.

**Les formes tkinter sont creees une fois puis deplacees** avec `coords()`.
Effacer et recreer 120 polygones trente fois par seconde ferait ramer la
fenetre.

Pistes essayees et abandonnees, inutile d'y revenir :

- laisser passer ensemble deux flux allant tout droit sur le meme axe : le
  gain est nul, les destinations etant tirees au hasard, seul un trajet sur
  trois va tout droit ;
- separer le freinage de la reservation du carrefour : resultat mitige et
  code sensiblement plus complique.

## Les invariants a ne jamais casser

Lances par `python3 -m unittest discover -s tests -t .` (environ une
minute) :

- **aucune collision** entre deux voitures d'une meme file ;
- **aucun chevauchement geometrique**, controle en rectangles orientes,
  a 40, 70 et 100 % de densite ;
- **aucun feu grille** ;
- **un seul mouvement par carrefour** ;
- a 60 % de densite, moins de 40 % des voitures a l'arret.

Le controle geometrique est le plus severe et celui qui a trouve le plus de
defauts. Le lancer apres toute modification de `vehicule.py`,
`code_route.py` ou des distances dans `ville.py`.

## A savoir

- A 100 % de densite la ville est tres embouteillee, jusqu'a 68 s
  d'attente. Le goulot est le carrefour, pas la route. C'est connu et
  assume ; 60 % est le reglage d'usage.
- Le rendu final se fera sur deux VM Linux : le superviseur sur la VM 1, le
  moteur et l'interface sur la VM 2. Une VM Linux est souvent sans ecran,
  prevoir un serveur X ou du X11 forwarding pour l'interface.
- La section 3.4 du cahier des charges classe encore la communication
  reseau entre machines en *Won't have*, alors que le deploiement sur deux
  VM l'exige. Contradiction connue, laissee en l'etat a la demande de
  l'equipe.
