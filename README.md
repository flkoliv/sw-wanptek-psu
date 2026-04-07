# Wanptek PSU Controller

Application desktop Windows pour piloter une alimentation Wanptek via USB / port serie.

Le programme permet de :

- visualiser la tension, le courant et la puissance
- modifier les consignes de tension et de courant
- activer ou desactiver la sortie
- activer ou desactiver l'OCP
- afficher l'historique des mesures dans une fenetre de graphe

## Captures et comportement

L'application repose sur une interface `customtkinter` avec :

- un affichage principal type LCD
- deux molettes de reglage
- une barre de boutons pour le menu, le graphe, le verrouillage, l'OCP et la sortie

## Prerequis

- Windows
- Python 3.10
- `tkinter` disponible dans l'installation Python
- une alimentation Wanptek compatible
- un adaptateur USB / serie reconnu par Windows

## Installation

### 1. Installer Python

Installer Python 3.10 depuis l'installateur officiel Windows.

Point important :

- verifier que `tcl/tk and IDLE` est bien installe

### 2. Cloner ou copier le projet

Placer le projet dans un dossier local, par exemple :

```text
~/projets/Wanptek
```

### 3. Creer l'environnement virtuel

Dans PowerShell, depuis le dossier du projet :

```powershell
py -3.10 -m venv .venv
```

### 4. Activer l'environnement virtuel

Si PowerShell bloque les scripts :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Puis activer l'environnement :

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Installer les dependances

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Lancement

### Lancement depuis le terminal

```powershell
python main.py
```

### Lancement via le lanceur Windows

```powershell
pythonw run.pyw
```

`run.pyw` utilise le Python du dossier `.venv`. Si l'environnement virtuel n'existe pas, un message d'erreur s'affiche.

## Premiere configuration

Au premier lancement :

1. cliquer sur `Menu`
2. choisir le port serie correspondant a l'alimentation
3. choisir l'adresse Modbus de l'appareil
4. choisir la vitesse serie
5. cliquer sur `Save`

Le programme tentera ensuite de se connecter automatiquement.

Les parametres sont sauvegardes dans un fichier local `param`.

## Utilisation

### Affichage principal

L'ecran principal affiche :

- la tension
- le courant
- la puissance
- l'etat OCP
- l'etat de sortie

### Boutons

- `Menu` : ouvre la fenetre de configuration serie
- `Graph` : ouvre la fenetre d'historique des mesures
- `Lock` : active ou desactive le pilotage logiciel des consignes
- `OCP` : active ou desactive la protection sur courant
- `OUT` : active ou coupe la sortie de l'alimentation

### Reglage tension / courant

Quand le mode `Lock` est actif :

- les molettes deviennent modifiables
- les nouvelles valeurs sont envoyees a l'alimentation

Quand `Lock` est inactif :

- les molettes affichent simplement les consignes courantes

### Graphe

La fenetre `Graph` affiche l'historique recent de :

- la tension
- le courant
- la puissance

Le programme conserve environ 10 minutes de mesures.

## Architecture du projet

- `~/projets/Wanptek/main.py` : point d'entree principal
- `~/projets/Wanptek/run.pyw` : lanceur Windows sans console
- `~/projets/Wanptek/PSUModel.py` : etat de l'application et configuration sauvegardee
- `~/projets/Wanptek/PSUController.py` : communication Modbus et logique de controle
- `~/projets/Wanptek/PSUView.py` : interface graphique

## Depannage

### `ModuleNotFoundError: No module named 'tkinter'`

La distribution Python installee ne contient pas Tk.

Solution :

- reinstaller Python 3.10 avec `tcl/tk and IDLE`

### PowerShell refuse `Activate.ps1`

Utiliser :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Puis :

```powershell
.\.venv\Scripts\Activate.ps1
```

### L'application ne se connecte pas

Verifier :

- que le bon port serie est selectionne
- que l'adresse Modbus est correcte
- que l'alimentation est allumee
- que le cable USB / serie fonctionne
- que le pilote serie est bien installe sur Windows

### Le graphe ne s'ouvre pas

Le graphe ne s'ouvre que si au moins une mesure a deja ete recue.

## Notes

- Le projet a ete valide avec Python 3.10.
- Le programme est optimise pour Windows.
- Le fichier `requirements.txt` contient les dependances Python du projet.

## Licence

Voir le fichier `~/projets/Wanptek/LICENSE`.
