# Installation et lancement
.
## Sur une machine neuve
.
Installer git et tkinter. Sous Debian ou Ubuntu :
.
```bash
sudo apt update
sudo apt install -y git python3-tk
```
.
Si `sudo` répond que l'utilisateur n'est pas dans le fichier sudoers, passer
par root une seule fois :
.
```bash
su -
apt update
apt install -y git python3-tk
usermod -aG sudo toto
exit
```
.
puis se déconnecter et se reconnecter.
.
Récupérer le projet :
.
```bash
git clone https://github.com/Ercys38/SAE3.02.git
cd SAE3.02
```
.
Vérifier que tout est en place :
.
```bash
python3 --version
python3 -c "import tkinter; print('tkinter disponible')"
```
.
Il faut Python 3.10 ou plus récent.
.
## Lancer sur une seule machine
.
```bash
cd ~/SAE3.02
python3 main.py local
```
.
La fenêtre s'ouvre avec le plan, les trois curseurs et les boutons d'appel.
Tout tourne dans le même programme, superviseur compris, et la base
`historique.db` se crée toute seule à la racine.
.
## Lancer sur deux machines
.
La VM1 tient le poste central, la VM2 fait tourner la simulation et la
fenêtre.
.
### Le réseau, sur les deux
.
Dans VirtualBox, éteindre les deux VM. Pour chacune, Configuration puis
Réseau : l'adaptateur 1 en NAT pour avoir Internet, l'adaptateur 2 activé en
Réseau privé hôte. Le NAT seul ne suffit pas, il isole les VM l'une de
l'autre.
.
Redémarrer, puis sur chaque VM relever l'adresse privée :
.
```bash
ip -4 addr show | grep 192.168.56
```
.
Les deux doivent répondre une adresse en 192.168.56.x. Si une carte reste
sans adresse :
.
```bash
nmcli device status
nmcli device connect enp0s8
```
.
Vérifier depuis la VM2 que la VM1 répond :
.
```bash
ping -c 3 <adresse de la VM1>
```
.
### VM1 — le superviseur
.
```bash
cd ~/SAE3.02
rm -f historique.db
python3 serveur.py
```
.
Elle affiche son port, puis un état chaque seconde : nombre de clients,
messages reçus, interventions enregistrées, carrefours sous priorité. Laisser
ce terminal ouvert et visible, c'est lui qui montre que les deux machines
travaillent ensemble.
.
### VM2 — la simulation
.
```bash
cd ~/SAE3.02
