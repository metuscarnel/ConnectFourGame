import pygame
import sys
import random
import json
import os
import math
import threading
from datetime import datetime
from copy import deepcopy

# ============================
# COULEURS & CONFIG
# ============================
BLEU_FONCE = (20, 30, 60)
BLEU_GRILLE = (41, 128, 185)
BLANC = (236, 240, 241)
ROUGE = (231, 76, 60)
JAUNE = (241, 196, 15)
VERT = (46, 204, 113)
GRIS = (149, 165, 166)
NOIR = (0, 0, 0)
ORANGE = (230, 126, 34)

MENU = "MENU"
PARAMETRES = "PARAMETRES"
JEU = "JEU"

DIFF_ALEATOIRE = 0
DIFF_FACILE = 2
DIFF_MOYEN = 4
DIFF_DIFFICILE = 5

TAILLE_CASE = 80
RAYON = 35
BANDE_HAUTE = 120


class ConnectFourGame:
    """Classe principale du jeu Puissance 4 avec IA Minimax."""
    
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.config = {"lignes": 8, "colonnes": 9, "joueur_start": 1}
        self.charger_config()
        self.setup_display()

        # Fonts
        self.font_big = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 25)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.font_mini = pygame.font.SysFont("Arial", 14)

        # State
        self.state = MENU
        self.mode_jeu = 1  # 0 = 0 joueurs, 1 = 1 joueur vs IA, 2 = 2 joueurs
        self.difficulte = DIFF_FACILE
        self.reset_game_data()
        
        # IA state
        self.ai_computing = False
        self.ai_col_to_play = None
        self.temp_message = ""
        self.temp_message_timer = 0
        self.ai_thread = None
        self.ai_scores_lock = threading.Lock()
        self.current_col_computing = -1

    def setup_display(self):
        """Configure la fenêtre selon la taille du plateau."""
        larg = self.config["colonnes"] * TAILLE_CASE
        haut = self.config["lignes"] * TAILLE_CASE + BANDE_HAUTE
        self.ecran = pygame.display.set_mode((larg, haut))
        pygame.display.set_caption("Puissance 4 - Minimax AI")

    def reset_game_data(self):
        """Réinitialise toutes les données de jeu."""
        self.plateau = [[0]*self.config["colonnes"] for _ in range(self.config["lignes"])]
        self.tour = self.config["joueur_start"]
        self.historique = []
        self.replay_buffer = []
        self.game_over = False
        self.message = ""
        self.gagnants = []
        self.partie_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.scores_ia = [None]*self.config["colonnes"]
        self.ia_thinking_progress = 0
        self.ai_computing = False
        self.ai_col_to_play = None
        self.current_col_computing = -1
        if hasattr(self, 'ai_thread') and self.ai_thread and self.ai_thread.is_alive():
            self.ai_thread.join(timeout=0.1)

    # ============================
    # CONFIG & SAUVEGARDE
    # ============================
    
    def charger_config(self):
        """Charge la configuration depuis config.json. Crée le fichier s'il n'existe pas."""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    self.config = json.load(f)
                print("✓ Configuration chargée depuis config.json")
            except Exception as e:
                print(f"✗ Erreur lors de la lecture de config.json: {e}")
                print("  Utilisation de la configuration par défaut.")
        else:
            # Créer config.json avec la configuration par défaut
            print("✓ config.json introuvable. Création avec la configuration par défaut...")
            self.sauver_config()
            print("✓ config.json créé avec succès.")

    def sauver_config(self):
        """Sauvegarde la configuration dans config.json (formaté pour lisibilité)."""
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde de config.json: {e}")

    def sauvegarder_partie(self):
        """Sauvegarde la partie en cours."""
        data = {
            "id": self.partie_id,
            "config": self.config,
            "historique": self.historique,
            "mode": self.mode_jeu,
            "diff": self.difficulte
        }
        filename = f"save_{self.partie_id}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        self.show_temp_message(f"Partie sauvegardée: {filename}")

    def charger_partie_fichier(self, nom_fichier):
        """Charge une partie depuis un fichier."""
        if not os.path.exists(nom_fichier):
            self.show_temp_message("Fichier introuvable!")
            return
        try:
            with open(nom_fichier, "r") as f:
                data = json.load(f)
            self.config = data["config"]
            self.setup_display()
            self.reset_game_data()
            self.partie_id = data["id"]
            self.mode_jeu = data["mode"]
            self.difficulte = data.get("diff", DIFF_FACILE)
            for move in data["historique"]:
                col, lig, jou = move
                self.plateau[lig][col] = jou
                self.historique.append(move)
            if self.historique:
                self.tour = 3 - self.historique[-1][2]
            else:
                self.tour = self.config["joueur_start"]
            self.state = JEU
            self.show_temp_message("Partie chargée!")
        except Exception as e:
            self.show_temp_message(f"Erreur chargement: {e}")

    # ============================
    # LOGIQUE MOTEUR
    # ============================
    
    def obtenir_ligne_vide(self, plateau, col):
        """Retourne la ligne vide la plus basse dans la colonne col, ou -1."""
        for r in range(self.config["lignes"]-1, -1, -1):
            if plateau[r][col] == 0:
                return r
        return -1

    def jouer_coup(self, col):
        """Joue un coup dans la colonne donnée."""
        if self.game_over:
            return False
        ligne = self.obtenir_ligne_vide(self.plateau, col)
        if ligne != -1:
            self.plateau[ligne][col] = self.tour
            self.historique.append((col, ligne, self.tour))
            self.replay_buffer = []
            # Reset scores IA après coup humain
            if self.mode_jeu == 1 and self.tour == 1:
                self.scores_ia = [None]*self.config["colonnes"]
            self.verifier_victoire_et_tour()
            return True
        return False

    def undo_coup(self):
        """Annule le dernier coup (Ctrl+Z)."""
        if not self.historique:
            return
        col, lig, ancien_joueur = self.historique.pop()
        self.replay_buffer.append((col, lig, ancien_joueur))
        self.plateau[lig][col] = 0
        self.tour = ancien_joueur
        self.game_over = False
        self.gagnants = []
        self.message = ""
        self.scores_ia = [None]*self.config["colonnes"]

    def redo_coup(self):
        """Refait le dernier coup annulé (Ctrl+Y)."""
        if not self.replay_buffer:
            return
        col, lig, joueur = self.replay_buffer.pop()
        self.plateau[lig][col] = joueur
        self.historique.append((col, lig, joueur))
        self.verifier_victoire_et_tour()

    def verifier_victoire_et_tour(self):
        """Vérifie la victoire et change de tour."""
        gagnant = self.check_victory_coords(self.plateau)
        if gagnant:
            self.game_over = True
            self.gagnants = gagnant
            nom = "ROUGE" if self.plateau[gagnant[0][0]][gagnant[0][1]] == 1 else "JAUNE"
            self.message = f"VICTOIRE {nom}!"
        elif len(self.historique) >= self.config["lignes"]*self.config["colonnes"]:
            self.game_over = True
            self.message = "MATCH NUL"
        else:
            self.tour = 3 - self.tour

    def check_victory_coords(self, board):
        """Vérifie s'il y a une victoire et retourne les coordonnées des 4 pions alignés."""
        R, C = self.config["lignes"], self.config["colonnes"]
        # Horizontal
        for r in range(R):
            for c in range(C-3):
                if board[r][c] != 0 and board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                    return [(r, c+i) for i in range(4)]
        # Vertical
        for r in range(R-3):
            for c in range(C):
                if board[r][c] != 0 and board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                    return [(r+i, c) for i in range(4)]
        # Diagonale descendante
        for r in range(R-3):
            for c in range(C-3):
                if board[r][c] != 0 and board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                    return [(r+i, c+i) for i in range(4)]
        # Diagonale montante
        for r in range(3, R):
            for c in range(C-3):
                if board[r][c] != 0 and board[r][c] == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                    return [(r-i, c+i) for i in range(4)]
        return None

    # ============================
    # IA MINIMAX
    # ============================
    
    def evaluate_window(self, window, joueur):
        """Évalue une fenêtre de 4 cases pour le joueur."""
        score = 0
        adversaire = 3 - joueur
        
        count_joueur = window.count(joueur)
        count_adversaire = window.count(adversaire)
        count_vide = window.count(0)
        
        if count_joueur == 4:
            score += 100
        elif count_joueur == 3 and count_vide == 1:
            score += 5
        elif count_joueur == 2 and count_vide == 2:
            score += 2
            
        if count_adversaire == 3 and count_vide == 1:
            score -= 4
        elif count_adversaire == 2 and count_vide == 2:
            score -= 1
            
        return score

    def score_position(self, board, joueur):
        """Évalue le plateau pour le joueur donné."""
        score = 0
        R, C = self.config["lignes"], self.config["colonnes"]
        
        # Score centre
        centre_col = C // 2
        centre_array = [board[r][centre_col] for r in range(R)]
        centre_count = centre_array.count(joueur)
        score += centre_count * 3
        
        # Horizontal
        for r in range(R):
            for c in range(C-3):
                window = [board[r][c+i] for i in range(4)]
                score += self.evaluate_window(window, joueur)
        
        # Vertical
        for r in range(R-3):
            for c in range(C):
                window = [board[r+i][c] for i in range(4)]
                score += self.evaluate_window(window, joueur)
        
        # Diagonale descendante
        for r in range(R-3):
            for c in range(C-3):
                window = [board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, joueur)
        
        # Diagonale montante
        for r in range(3, R):
            for c in range(C-3):
                window = [board[r-i][c+i] for i in range(4)]
                score += self.evaluate_window(window, joueur)
        
        return score

    def is_terminal_node(self, board):
        """Vérifie si le nœud est terminal (victoire ou plateau plein)."""
        return self.check_victory_coords(board) is not None or len(self.get_valid_moves(board)) == 0

    def get_valid_moves(self, board):
        """Retourne la liste des colonnes jouables."""
        return [c for c in range(self.config["colonnes"]) if board[0][c] == 0]

    def minimax(self, board, depth, alpha, beta, maximizing_player, joueur_ia):
        """Algorithme Minimax avec élagage alpha-beta."""
        # Progression mise à jour de manière thread-safe
        with self.ai_scores_lock:
            self.ia_thinking_progress = min(100, self.ia_thinking_progress + 0.3)
        
        valid_moves = self.get_valid_moves(board)
        is_terminal = self.is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.check_victory_coords(board):
                    # Vérifier qui a gagné
                    winner_coords = self.check_victory_coords(board)
                    winner = board[winner_coords[0][0]][winner_coords[0][1]]
                    if winner == joueur_ia:
                        return (None, 100000000)
                    else:
                        return (None, -100000000)
                else:  # Match nul
                    return (None, 0)
            else:  # depth == 0
                return (None, self.score_position(board, joueur_ia))
        
        if maximizing_player:
            value = -math.inf
            best_col = random.choice(valid_moves) if valid_moves else None
            for col in valid_moves:
                row = self.obtenir_ligne_vide(board, col)
                temp_board = [row[:] for row in board]
                temp_board[row][col] = joueur_ia
                new_score = self.minimax(temp_board, depth-1, alpha, beta, False, joueur_ia)[1]
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = math.inf
            best_col = random.choice(valid_moves) if valid_moves else None
            for col in valid_moves:
                row = self.obtenir_ligne_vide(board, col)
                temp_board = [row[:] for row in board]
                temp_board[row][col] = 3 - joueur_ia
                new_score = self.minimax(temp_board, depth-1, alpha, beta, True, joueur_ia)[1]
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    def get_ai_move_minimax(self):
        """Calcule le meilleur coup avec Minimax et affiche les scores en temps réel."""
        with self.ai_scores_lock:
            self.ia_thinking_progress = 0
        
        joueur_ia = self.tour
        valid_moves = self.get_valid_moves(self.plateau)
        
        if not valid_moves:
            return None
        
        # Calculer les scores pour chaque colonne progressivement
        scores = []
        total_moves = len(valid_moves)
        
        for idx, col in enumerate(range(self.config["colonnes"])):
            # Indiquer quelle colonne est en cours de calcul
            with self.ai_scores_lock:
                self.current_col_computing = col
            
            if col in valid_moves:
                row = self.obtenir_ligne_vide(self.plateau, col)
                temp_board = [row[:] for row in self.plateau]
                temp_board[row][col] = joueur_ia
                
                # Reset progression pour cette colonne
                with self.ai_scores_lock:
                    self.ia_thinking_progress = (idx / total_moves) * 100
                
                score = self.minimax(temp_board, self.difficulte-1, -math.inf, math.inf, False, joueur_ia)[1]
                scores.append((col, score))
                
                # Mettre à jour le score en temps réel (thread-safe)
                with self.ai_scores_lock:
                    self.scores_ia[col] = score
            else:
                scores.append((col, None))
                with self.ai_scores_lock:
                    self.scores_ia[col] = None
        
        # Calcul terminé
        with self.ai_scores_lock:
            self.ia_thinking_progress = 100
            self.current_col_computing = -1
        
        # Choisir le meilleur coup
        valid_scores = [(c, s) for c, s in scores if s is not None]
        if valid_scores:
            best_col = max(valid_scores, key=lambda x: x[1])[0]
            return best_col
        
        return random.choice(valid_moves)

    def get_ai_move_random(self):
        """Retourne un coup aléatoire."""
        valid_moves = self.get_valid_moves(self.plateau)
        return random.choice(valid_moves) if valid_moves else None

    def ai_compute_thread(self, mode):
        """Thread de calcul de l'IA."""
        if mode == 0:  # Mode 0 joueurs
            pygame.time.wait(500)
            col = self.get_ai_move_random()
        elif self.difficulte == DIFF_ALEATOIRE:
            pygame.time.wait(300)
            col = self.get_ai_move_random()
        else:
            col = self.get_ai_move_minimax()
        
        self.ai_col_to_play = col
    
    def update_ai_move(self):
        """Gère le tour de l'IA avec calcul en arrière-plan."""
        if self.game_over or self.state != JEU:
            return
        
        # Mode 0 joueurs: les deux jouent automatiquement
        if self.mode_jeu == 0:
            if not self.ai_computing:
                self.ai_computing = True
                self.ai_col_to_play = None
                self.ai_thread = threading.Thread(target=self.ai_compute_thread, args=(0,))
                self.ai_thread.start()
            elif self.ai_col_to_play is not None:
                # Le calcul est terminé
                if self.ai_col_to_play is not None:
                    self.jouer_coup(self.ai_col_to_play)
                self.ai_computing = False
                self.ai_col_to_play = None
        
        # Mode 1 joueur: IA joue en tant que joueur 2 (JAUNE)
        elif self.mode_jeu == 1 and self.tour == 2:
            if not self.ai_computing:
                self.ai_computing = True
                self.ai_col_to_play = None
                # Réinitialiser les scores
                with self.ai_scores_lock:
                    self.scores_ia = [None] * self.config["colonnes"]
                    self.ia_thinking_progress = 0
                # Lancer le thread de calcul
                self.ai_thread = threading.Thread(target=self.ai_compute_thread, args=(1,))
                self.ai_thread.start()
            elif self.ai_col_to_play is not None:
                # Le calcul est terminé
                if self.ai_col_to_play is not None:
                    self.jouer_coup(self.ai_col_to_play)
                with self.ai_scores_lock:
                    self.ia_thinking_progress = 0
                self.ai_computing = False
                self.ai_col_to_play = None

    # ============================
    # AFFICHAGE
    # ============================
    
    def draw_board(self):
        """Dessine le plateau de jeu."""
        for r in range(self.config["lignes"]):
            for c in range(self.config["colonnes"]):
                x = c * TAILLE_CASE
                y = r * TAILLE_CASE + BANDE_HAUTE
                pygame.draw.rect(self.ecran, BLEU_GRILLE, (x, y, TAILLE_CASE, TAILLE_CASE))
                
                val = self.plateau[r][c]
                couleur = BLANC
                if val == 1:
                    couleur = ROUGE
                elif val == 2:
                    couleur = JAUNE
                
                # Highlight winning line
                if (r, c) in self.gagnants:
                    pygame.draw.circle(self.ecran, VERT, 
                                     (x + TAILLE_CASE // 2, y + TAILLE_CASE // 2), RAYON + 5)
                
                pygame.draw.circle(self.ecran, couleur, 
                                 (x + TAILLE_CASE // 2, y + TAILLE_CASE // 2), RAYON)

    def draw_top_bar(self):
        """Dessine la barre supérieure avec infos."""
        pygame.draw.rect(self.ecran, BLEU_FONCE, (0, 0, self.ecran.get_width(), BANDE_HAUTE))
        
        # Tour actuel
        if not self.game_over:
            tour_text = "Tour: ROUGE" if self.tour == 1 else "Tour: JAUNE"
            tour_color = ROUGE if self.tour == 1 else JAUNE
            surf = self.font_med.render(tour_text, True, tour_color)
            self.ecran.blit(surf, (10, 10))
        
        # Message (victoire, nul, etc.)
        if self.message:
            msg_surf = self.font_big.render(self.message, True, VERT if "VICTOIRE" in self.message else ORANGE)
            self.ecran.blit(msg_surf, (10, 50))
        
        # Message temporaire
        if self.temp_message_timer > 0:
            temp_surf = self.font_small.render(self.temp_message, True, BLANC)
            self.ecran.blit(temp_surf, (10, 85))
        
        # Barre de progression IA (thread-safe)
        if self.ai_computing and self.mode_jeu == 1 and self.tour == 2 and self.difficulte != DIFF_ALEATOIRE:
            bar_width = 200
            bar_height = 20
            bar_x = self.ecran.get_width() - bar_width - 10
            bar_y = 10
            pygame.draw.rect(self.ecran, GRIS, (bar_x, bar_y, bar_width, bar_height))
            
            with self.ai_scores_lock:
                current_progress = self.ia_thinking_progress
                current_col = self.current_col_computing
            
            progress_width = int(bar_width * (current_progress / 100))
            pygame.draw.rect(self.ecran, VERT, (bar_x, bar_y, progress_width, bar_height))
            
            if current_col >= 0:
                prog_text = self.font_mini.render(f"IA calcule col {current_col}... {int(current_progress)}%", True, BLANC)
            else:
                prog_text = self.font_mini.render(f"IA calcule... {int(current_progress)}%", True, BLANC)
            self.ecran.blit(prog_text, (bar_x, bar_y + bar_height + 2))

    def draw_ai_scores(self):
        """Affiche les scores Minimax sous chaque colonne en temps réel."""
        if self.mode_jeu == 1 and self.difficulte != DIFF_ALEATOIRE:
            # Afficher les scores pendant le calcul de l'IA ou après
            if self.ai_computing or (self.tour == 2 and any(s is not None for s in self.scores_ia)):
                with self.ai_scores_lock:
                    scores_copy = self.scores_ia.copy()
                    current_col = self.current_col_computing
                
                for col in range(self.config["colonnes"]):
                    x = col * TAILLE_CASE + TAILLE_CASE // 2
                    y = BANDE_HAUTE - 30
                    
                    # Highlight de la colonne en cours de calcul
                    if col == current_col:
                        pygame.draw.circle(self.ecran, ORANGE, (x, y), 12)
                    
                    if scores_copy[col] is not None:
                        score_text = str(int(scores_copy[col]))
                        color = JAUNE if col != current_col else BLANC
                        surf = self.font_mini.render(score_text, True, color)
                        rect = surf.get_rect(center=(x, y))
                        self.ecran.blit(surf, rect)
                    elif col == current_col:
                        # Afficher un indicateur de calcul
                        surf = self.font_mini.render("...", True, BLANC)
                        rect = surf.get_rect(center=(x, y))
                        self.ecran.blit(surf, rect)

    def draw_game(self):
        """Dessine l'écran de jeu complet."""
        self.ecran.fill(BLEU_FONCE)
        self.draw_board()
        self.draw_top_bar()
        self.draw_ai_scores()
        
        # Instructions
        inst_text = "M: Menu | S: Save | L: Load | R: Reset | Ctrl+Z: Undo | Ctrl+Y: Redo"
        inst_surf = self.font_mini.render(inst_text, True, GRIS)
        self.ecran.blit(inst_surf, (5, self.ecran.get_height() - 20))

    def draw_menu(self):
        """Dessine le menu principal."""
        self.ecran.fill(BLEU_FONCE)
        
        title = self.font_big.render("PUISSANCE 4 - MINIMAX AI", True, JAUNE)
        title_rect = title.get_rect(center=(self.ecran.get_width()//2, 50))
        self.ecran.blit(title, title_rect)
        
        options = [
            "0 - Mode 0 joueurs (Auto)",
            "1 - Mode 1 joueur vs IA",
            "2 - Mode 2 joueurs",
            "P - Paramètres",
            "L - Charger partie",
            "Q - Quitter"
        ]
        
        y = 150
        for opt in options:
            surf = self.font_med.render(opt, True, BLANC)
            rect = surf.get_rect(center=(self.ecran.get_width()//2, y))
            self.ecran.blit(surf, rect)
            y += 50

    def draw_settings(self):
        """Dessine le menu des paramètres."""
        self.ecran.fill(BLEU_FONCE)
        
        title = self.font_big.render("PARAMETRES", True, ORANGE)
        title_rect = title.get_rect(center=(self.ecran.get_width()//2, 50))
        self.ecran.blit(title, title_rect)
        
        settings_info = [
            f"Lignes: {self.config['lignes']} (Flèches Haut/Bas)",
            f"Colonnes: {self.config['colonnes']} (Flèches Gauche/Droite)",
            f"Joueur départ: {'ROUGE' if self.config['joueur_start'] == 1 else 'JAUNE'} (J)",
            f"Difficulté IA: {self.get_difficulty_name()} (D)",
            "",
            "Entrée - Retour au menu",
        ]
        
        y = 150
        for info in settings_info:
            surf = self.font_med.render(info, True, BLANC)
            rect = surf.get_rect(center=(self.ecran.get_width()//2, y))
            self.ecran.blit(surf, rect)
            y += 45

    def get_difficulty_name(self):
        """Retourne le nom de la difficulté."""
        if self.difficulte == DIFF_ALEATOIRE:
            return "Aléatoire"
        elif self.difficulte == DIFF_FACILE:
            return "Facile (2)"
        elif self.difficulte == DIFF_MOYEN:
            return "Moyen (4)"
        elif self.difficulte == DIFF_DIFFICILE:
            return "Difficile (5)"
        return f"Perso ({self.difficulte})"

    # ============================
    # GESTION ÉVÉNEMENTS
    # ============================
    
    def handle_game_click(self, mx, my):
        """Gère les clics dans le jeu."""
        if self.game_over or self.ai_computing:
            return
        
        # Mode 0 joueurs: pas de clics
        if self.mode_jeu == 0:
            return
        
        # Mode 1 joueur: seulement le joueur 1 (ROUGE) peut cliquer
        if self.mode_jeu == 1 and self.tour == 2:
            return
        
        # Déterminer la colonne cliquée
        col = mx // TAILLE_CASE
        if 0 <= col < self.config["colonnes"]:
            self.jouer_coup(col)

    def handle_game_keys(self, event):
        """Gère les touches en jeu."""
        if event.key == pygame.K_m:
            self.state = MENU
            self.reset_game_data()
        elif event.key == pygame.K_s:
            self.sauvegarder_partie()
        elif event.key == pygame.K_l:
            self.load_last_save()
        elif event.key == pygame.K_r:
            self.reset_game_data()
            self.show_temp_message("Jeu réinitialisé!")
        elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.undo_coup()
        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.redo_coup()

    def handle_menu_keys(self, event):
        """Gère les touches dans le menu."""
        if event.key == pygame.K_0:
            self.mode_jeu = 0
            self.reset_game_data()
            self.state = JEU
        elif event.key == pygame.K_1:
            self.mode_jeu = 1
            self.reset_game_data()
            self.state = JEU
        elif event.key == pygame.K_2:
            self.mode_jeu = 2
            self.reset_game_data()
            self.state = JEU
        elif event.key == pygame.K_p:
            self.state = PARAMETRES
        elif event.key == pygame.K_l:
            self.load_last_save()
        elif event.key == pygame.K_q:
            pygame.quit()
            sys.exit()

    def handle_settings_keys(self, event):
        """Gère les touches dans les paramètres."""
        if event.key == pygame.K_UP:
            self.config["lignes"] = min(12, self.config["lignes"] + 1)
            self.sauver_config()
            self.setup_display()
        elif event.key == pygame.K_DOWN:
            self.config["lignes"] = max(4, self.config["lignes"] - 1)
            self.sauver_config()
            self.setup_display()
        elif event.key == pygame.K_RIGHT:
            self.config["colonnes"] = min(15, self.config["colonnes"] + 1)
            self.sauver_config()
            self.setup_display()
        elif event.key == pygame.K_LEFT:
            self.config["colonnes"] = max(4, self.config["colonnes"] - 1)
            self.sauver_config()
            self.setup_display()
        elif event.key == pygame.K_j:
            self.config["joueur_start"] = 3 - self.config["joueur_start"]
            self.sauver_config()
        elif event.key == pygame.K_d:
            difficulties = [DIFF_ALEATOIRE, DIFF_FACILE, DIFF_MOYEN, DIFF_DIFFICILE]
            current_idx = difficulties.index(self.difficulte) if self.difficulte in difficulties else 1
            next_idx = (current_idx + 1) % len(difficulties)
            self.difficulte = difficulties[next_idx]
        elif event.key == pygame.K_RETURN:
            self.state = MENU

    # ============================
    # HELPERS
    # ============================
    
    def show_temp_message(self, msg):
        """Affiche un message temporaire."""
        self.temp_message = msg
        self.temp_message_timer = 180  # 3 secondes à 60 FPS

    def load_last_save(self):
        """Charge la dernière sauvegarde."""
        saves = [f for f in os.listdir(".") if f.startswith("save_") and f.endswith(".json")]
        if saves:
            saves.sort(reverse=True)
            self.charger_partie_fichier(saves[0])
        else:
            self.show_temp_message("Aucune sauvegarde trouvée!")

    # ============================
    # BOUCLE PRINCIPALE
    # ============================
    
    def run(self):
        """Boucle principale du jeu."""
        while True:
            # Événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN and self.state == JEU:
                    mx, my = pygame.mouse.get_pos()
                    self.handle_game_click(mx, my)
                
                if event.type == pygame.KEYDOWN:
                    if self.state == JEU:
                        self.handle_game_keys(event)
                    elif self.state == MENU:
                        self.handle_menu_keys(event)
                    elif self.state == PARAMETRES:
                        self.handle_settings_keys(event)
            
            # Mise à jour
            if self.state == JEU:
                self.update_ai_move()
                if self.temp_message_timer > 0:
                    self.temp_message_timer -= 1
            
            # Affichage
            if self.state == MENU:
                self.draw_menu()
            elif self.state == PARAMETRES:
                self.draw_settings()
            elif self.state == JEU:
                self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    game = ConnectFourGame()
    game.run()
