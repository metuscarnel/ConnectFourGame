
---

# Puissance 4 - Minimax AI

Une implémentation robuste et configurable du jeu **Puissance 4** en Python avec **Pygame**. Ce projet intègre une intelligence artificielle basée sur l'algorithme **Minimax** avec élagage Alpha-Beta, capable de calculer ses coups dans un thread séparé tout en affichant son processus de décision en temps réel.

## 📋 Fonctionnalités

* **3 Modes de Jeu :**
* **0 Joueurs (Auto) :** L'IA joue contre elle-même (Démonstration).
* **1 Joueur vs IA :** Humain contre Ordinateur.
* **2 Joueurs :** Multijoueur local (tour par tour).


* **Intelligence Artificielle Avancée :**
* Algorithme Minimax avec élagage Alpha-Beta.
* 4 niveaux de difficulté (Aléatoire, Facile, Moyen, Difficile).
* Calcul multithreadé (l'interface reste fluide pendant que l'IA réfléchit).
* **Visualisation de l'IA :** Affichage en temps réel des scores évalués pour chaque colonne et barre de progression de la réflexion.


* **Système de jeu complet :**
* **Undo / Redo :** Annulation et rétablissement des coups infinis (`Ctrl+Z`, `Ctrl+Y`).
* Détection de victoire (horizontale, verticale, diagonale) et de match nul.
* Surbrillance visuelle de l'alignement gagnant.


* **Personnalisation & Persistance :**
* Taille de la grille dynamique (nombre de lignes et colonnes modifiable).
* Choix du joueur qui commence.
* Système de **Sauvegarde/Chargement** (format JSON).
* Fichier de configuration `config.json` persistant.



## 🛠 Prérequis

* **Python 3.x**
* **Pygame**

## 🚀 Installation

1. Clonez ou téléchargez ce dépôt.
2. Ouvrez un terminal dans le dossier du projet.
3. Installez la dépendance requise :

```bash
pip install pygame

```

## ▶️ Lancement

Exécutez simplement le script principal :

```bash
python connect_four.py

```

*(Remplacez `connect_four.py` par le nom réel de votre fichier script s'il est différent).*

## 🎮 Utilisation

### Menu Principal

Au lancement, utilisez les touches du clavier pour naviguer :

* `0`, `1`, `2` : Sélectionner le mode de jeu.
* `P` : Accéder aux paramètres (taille grille, difficulté, etc.).
* `L` : Charger la dernière sauvegarde.
* `Q` : Quitter.

### En Jeu

* **Pour jouer :** Cliquez avec la souris sur une colonne pour y déposer un jeton.
* **Tour de l'IA :** Une barre de progression s'affiche en haut à droite. Les scores d'évaluation apparaissent sous les colonnes pour montrer les intentions de l'IA.

## ⚙️ Configuration (`config.json`)

Le fichier `config.json` est généré automatiquement au premier lancement s'il est absent. Vous pouvez le modifier manuellement ou via le menu "Paramètres" (`P`) du jeu.

| Champ | Type | Description |
| --- | --- | --- |
| `lignes` | `int` | Nombre de lignes du plateau (défaut: 8, min: 4, max: 12). |
| `colonnes` | `int` | Nombre de colonnes du plateau (défaut: 9, min: 4, max: 15). |
| `joueur_start` | `int` | Qui commence ? `1` pour ROUGE (Humain/P1), `2` pour JAUNE (IA/P2). |

## 💾 Système de Sauvegarde

Le jeu permet de sauvegarder l'état exact de la partie à tout moment via la touche `S`.

* **Format :** JSON.
* **Nommage :** `save_YYYYMMDD_HHMMSS.json`.
* **Contenu :** Historique des coups, configuration du plateau, mode de jeu et difficulté.

## 🧠 Explication de l'IA

Le moteur d'IA utilise différentes approches selon la difficulté :

1. **Aléatoire :** Joue une colonne valide au hasard.
2. **Minimax (Facile/Moyen/Difficile) :**
* L'IA simule les coups futurs jusqu'à une certaine profondeur (2, 4 ou 5 coups).
* **Fonction d'évaluation :** Elle favorise le contrôle du centre, les alignements de 2 ou 3 pions, et bloque les tentatives adverses.
* **Visualisation :** Les chiffres jaunes sous la grille indiquent le score heuristique de chaque coup possible (plus le chiffre est haut, plus l'IA juge le coup favorable).



## ⌨️ Contrôles et Raccourcis

| Contexte | Touche / Action | Effet |
| --- | --- | --- |
| **Global** | `Q` (Menu) / `Croix fenêtre` | Quitter le jeu |
| **Menu** | `0`, `1`, `2` | Choisir le mode de jeu |
|  | `P` | Ouvrir les paramètres |
|  | `L` | Charger la dernière sauvegarde |
| **Jeu** | **Clic Gauche** | Placer un jeton |
|  | `Ctrl` + `Z` | **Undo** (Annuler le dernier coup) |
|  | `Ctrl` + `Y` | **Redo** (Refaire le coup annulé) |
|  | `S` | Sauvegarder la partie |
|  | `L` | Charger la dernière sauvegarde |
|  | `R` | Réinitialiser la partie courante |
|  | `M` | Retour au Menu principal |
| **Paramètres** | `↑` / `↓` | Changer le nombre de lignes |
|  | `←` / `→` | Changer le nombre de colonnes |
|  | `D` | Changer la difficulté de l'IA |
|  | `J` | Changer le joueur de départ |
|  | `Entrée` | Valider et retourner au Menu |

## 🏗 Architecture du Projet

Le projet tient en un seul fichier structuré autour de la classe `ConnectFourGame`.

* **Gestion d'état (`state`) :** Transition entre `MENU`, `PARAMETRES` et `JEU`.
* **Moteur (`jouer_coup`, `check_victory_coords`) :** Logique pure du Puissance 4, indépendante de l'affichage.
* **IA (`minimax`, `ai_compute_thread`) :**
* L'IA tourne dans un `threading.Thread` pour ne pas bloquer l'interface graphique (`pygame`).
* Utilisation d'un `threading.Lock` (`ai_scores_lock`) pour mettre à jour les scores visuels et la progression de manière sécurisée.


* **Affichage (`draw_*`) :** Toutes les méthodes de rendu Pygame.

## ➕ Comment étendre le projet

* **Nouvelles heuristiques :** Modifier la méthode `evaluate_window` pour affiner la stratégie de l'IA.
* **Réseau :** La structure `jouer_coup(col)` est isolée, ce qui faciliterait l'ajout d'une couche réseau (sockets) pour jouer à distance.
* **Graphismes :** Les constantes de couleurs et tailles (`TAILLE_CASE`, `BLEU_FONCE`, etc.) sont définies en début de fichier et peuvent être ajustées pour changer le thème ("skin").

## ⚠️ Limitations connues

* **Performances IA :** En profondeur "Difficile" (5) sur de très grandes grilles (ex: 12x15), le temps de calcul peut augmenter significativement.
* **Résolution :** La fenêtre s'adapte à la taille de la grille. Une grille excessivement grande (ex: 20x20) pourrait dépasser la taille de l'écran physique, car il n'y a pas de système de défilement (scroll) ou de redimensionnement automatique des cases (zoom).

## 📄 Exemple de fichier de sauvegarde

Voici à quoi ressemble un fichier `save_*.json` généré par le jeu :

```json
{
  "id": "20231027_143022",
  "config": {
    "lignes": 8,
    "colonnes": 9,
    "joueur_start": 1
  },
  "historique": [
    [4, 7, 1],
    [3, 7, 2],
    [4, 6, 1]
  ],
  "mode": 1,
  "diff": 4
}

```

## 📜 Licence

Non spécifiée.