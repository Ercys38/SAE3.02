# Déroulé de la démonstration

## Avant

Les deux VM en réseau interne ou en accès par pont, pas en NAT. Vérifier que
la diffusion passe : lancer `python3 serveur.py` sur la VM1, puis sur la VM2
`python3 -c "from simulation.reseau import trouver_le_superviseur; print(trouver_le_superviseur())"`.
Une adresse doit s'afficher. Si c'est `None`, la diffusion est bloquée et il
faudra donner l'adresse à la main.

Vider l'historique pour partir propre : `rm -f historique.db` sur la VM1.

## Pendant

Sur la VM1, `python3 serveur.py`. Il affiche son port et annonce qu'il attend.
Laisser la fenêtre visible : à chaque seconde il montre le nombre de clients,
les messages reçus, les interventions en base et les carrefours sous priorité.
C'est la preuve visuelle que les deux machines travaillent ensemble.

Sur la VM2, `python3 main.py`. Aucune adresse n'est tapée, la ligne
« superviseur trouvé » apparaît. Montrer que les compteurs du serveur se
mettent à bouger.

Monter la densité à 70 %, laisser le trafic se former, puis appeler les
pompiers. Montrer trois choses : les feux qui passent au vert devant le camion
sur plusieurs carrefours d'affilée, les voitures qui se rangent sur la droite,
et le chronomètre à côté de la légende.

Décocher « Priorité aux feux » et rappeler un service, même densité. Le même
trajet prend deux à trois fois plus longtemps. C'est la démonstration du gain.

Sur la VM1, `python3 historique.py` : les deux trajets sont en base, avec les
temps et le gain.

## Si quelque chose lâche

La VM1 ne démarre pas, ou la diffusion ne passe pas : sur la VM2,
`python3 main.py local`. Tout tourne sur une seule machine, superviseur
compris, et la démonstration se poursuit sans le réseau.

La fenêtre refuse de s'ouvrir avec `no display name` : le terminal est en SSH
ou en root, en rouvrir un dans la session graphique.

## Les chiffres à citer

Mesures reproductibles avec `python3 mesures.py`, huit trajets par ligne :
33 % de gain à 20 % de densité, 57 % à 60 %, 59 % à 100 %. Et la suite de
tests, `python3 -m unittest discover -s tests`, 41 tests en cinq minutes,
dont celui qui vérifie qu'aucun véhicule ne se superpose à l'écran.
