# Écarts entre le cahier des charges et la version livrée

SAÉ R3.02 — Équipe K2 X ERCYS — novembre 2026

Trois choses ont été faites au-delà du périmètre annoncé. La communication
réseau réelle entre deux machines, d'abord, qui était classée en Won't have :
le superviseur s'expose en serveur TCP et la simulation s'y connecte depuis
l'autre VM, avec les mêmes messages JSON que ceux décrits au 2.2. Le
déploiement sur deux VM et le titre de la SAÉ la rendaient difficile à
écarter. Ensuite le réseau routier : une avenue de 1,1 km avec six rues, cinq
carrefours à feux et un rond-point, au lieu du carrefour unique envisagé —
c'est ce qui permet de démontrer l'onde verte sur plusieurs carrefours
successifs, ce qu'un carrefour isolé ne montre pas. Enfin trois services
d'urgence distincts, avec leurs bâtiments de départ et leur code couleur, et
un superviseur capable d'en gérer plusieurs à la fois, ce qui était aussi en
Won't have.

Une fonctionnalité annoncée n'est pas livrée : le recalcul d'itinéraire selon
la densité observée. C'était un Should have chiffré à huit heures, et le
rétroplanning prévoyait explicitement que le jalon J5 sauterait en premier en
cas de retard. C'est ce qui s'est passé. L'itinéraire est calculé une fois au
départ par Dijkstra et suivi jusqu'au bout.

Restent deux corrections de détail. Le cahier des charges annonce Python
3.14 ; tout a été écrit et testé sur la 3.13 de la VM Debian, et le code
n'utilise rien de postérieur à la 3.10. Et heapq et dataclasses, annoncés au
2.3, ne servent pas : Dijkstra est écrit avec des listes simples, suffisant
pour un graphe de quinze nœuds, et les messages sont des dictionnaires
puisqu'ils finissent en JSON.
