"""
=============================================================
 FIRESIM PRO v2.0 — AVEC ALGORITHME A*
=============================================================
 Auteur     : [Ton nom]
 Date       : 2025
 Langage    : Python 3.x
 Dépendances: colorama  (pip install colorama)

 NOUVEAUTÉS v2.0 (par rapport à v1)
 ------------------------------------
 - Algorithme A* remplace le déplacement naïf
 - Murs / obstacles sur la grille (les pompiers contournent)
 - Feu qui se propage aux cases adjacentes
 - Pompiers qui recalculent leur chemin si bloqué
 - Affichage du chemin A* en temps réel dans le terminal
 - Rapport final enrichi (distance totale parcourue)

 ALGORITHME A*
 -------------
 f(n) = g(n) + h(n)
   g(n) = coût réel depuis le départ (nombre de pas)
   h(n) = heuristique = distance de Manhattan jusqu'à la cible
 La case choisie à chaque étape est celle avec le f(n) minimal.
 On utilise une file de priorité (heapq) pour l'efficacité.

 COMPARAISON avec v1
 -------------------
 v1 (naïf) :  if abs(dx) >= abs(dy): self.x += 1 if dx>0 else -1
              → bloqué par les murs, chemin sous-optimal

 v2 (A*)   :  chemin = astar(debut, fin, obstacles)
              self.x, self.y = chemin[1]
              → contourne tous les obstacles, chemin optimal garanti
=============================================================
"""

from colorama import Fore, Style, init
import random
import heapq
import time
import os

init(autoreset=True)


# ═══════════════════════════════════════════════════════════
#  ALGORITHME A*
# ═══════════════════════════════════════════════════════════

def astar(debut, fin, largeur, hauteur, obstacles):
    """
    Algorithme A* sur grille 2D avec obstacles.

    Paramètres :
        debut      : (x, y) position de départ
        fin        : (x, y) position cible
        largeur    : nombre de colonnes de la grille
        hauteur    : nombre de lignes de la grille
        obstacles  : set de (x, y) — cases infranchissables

    Retourne :
        Liste de (x, y) du chemin optimal (inclut départ et fin).
        [] si aucun chemin n'existe.

    Complexité : O(n log n) avec n = nombre de cases explorées
    """

    # Cas trivial
    if debut == fin:
        return [debut]

    # Heuristique admissible : distance de Manhattan
    # (ne surestime jamais le vrai coût → A* reste optimal)
    def h(pos):
        return abs(pos[0] - fin[0]) + abs(pos[1] - fin[1])

    # File de priorité : (f, g, position, chemin)
    # f = g + h, g = coût depuis le départ
    file_priorite = []
    heapq.heappush(file_priorite, (h(debut), 0, debut, [debut]))

    # Cases déjà évaluées (on ne les revisite pas)
    visites = set()

    while file_priorite:
        f, g, position, chemin = heapq.heappop(file_priorite)

        # Déjà traité ?
        if position in visites:
            continue
        visites.add(position)

        # Arrivée à destination !
        if position == fin:
            return chemin

        # Exploration des 4 voisins cardinaux
        x, y = position
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            vx, vy = x + dx, y + dy

            # Vérification : dans la grille, pas un obstacle, pas visité
            if not (0 <= vx < largeur and 0 <= vy < hauteur):
                continue
            if (vx, vy) in obstacles:
                continue
            if (vx, vy) in visites:
                continue

            nouveau_g = g + 1
            nouveau_f = nouveau_g + h((vx, vy))
            heapq.heappush(
                file_priorite,
                (nouveau_f, nouveau_g, (vx, vy), chemin + [(vx, vy)])
            )

    # Aucun chemin trouvé (cible inaccessible)
    return []


# ═══════════════════════════════════════════════════════════
#  CLASSES D'AGENTS
# ═══════════════════════════════════════════════════════════

class Agent:
    """Classe de base : position x, y sur la grille."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


# ───────────────────────────────────────────────────────────

class Feu(Agent):
    """
    Agent passif — foyer d'incendie.
    Nouveauté v2 : peut se propager aux cases adjacentes libres.
    """
    def __init__(self, x, y):
        super().__init__(x, y)
        self.age       = 0
        self.intensite = 1  # 1=petit, 2=moyen, 3=intense

    def vieillir(self):
        self.age += 1
        if self.age > 2:
            self.intensite = min(3, self.intensite + 0.6)

    def symbole_colore(self):
        if self.intensite >= 3:
            return Fore.RED + Style.BRIGHT + "F" + Style.RESET_ALL
        elif self.intensite >= 2:
            return Fore.YELLOW + Style.BRIGHT + "f" + Style.RESET_ALL
        else:
            return Fore.RED + "f" + Fore.RESET


# ───────────────────────────────────────────────────────────

class Mur:
    """Case infranchissable — obstacle pour A*."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


# ───────────────────────────────────────────────────────────

class Pompier(Agent):
    """
    Agent actif intelligent v2.
    Utilise A* pour calculer le chemin optimal vers le feu
    le plus proche, en évitant les murs et les autres pompiers.
    """
    def __init__(self, id_, x, y, eau_max):
        super().__init__(x, y)
        self.id         = id_
        self.eau        = eau_max
        self.eau_max    = eau_max
        self.eteints    = 0
        self.chemin     = []        # Chemin A* courant
        self.cible      = None      # Feu actuellement ciblé
        self.dist_totale = 0        # Total de cases parcourues

    # ── Trouver le feu accessible le plus proche ──
    def feu_le_plus_proche(self, liste_feux, obstacles, largeur, hauteur):
        """
        Cherche le feu le plus proche ACCESSIBLE via A*.
        Retourne (feu, chemin) ou (None, []).
        """
        meilleur_feu    = None
        meilleur_chemin = []
        meilleure_dist  = float('inf')

        for f in liste_feux:
            chemin = astar(
                (self.x, self.y),
                (f.x, f.y),
                largeur, hauteur,
                obstacles
            )
            if chemin and len(chemin) < meilleure_dist:
                meilleure_dist  = len(chemin)
                meilleur_feu    = f
                meilleur_chemin = chemin

        return meilleur_feu, meilleur_chemin

    # ── Avancer d'une case selon le chemin A* ──
    def avancer(self, grille):
        """Suit le chemin A* d'une case."""
        if len(self.chemin) > 1:
            grille[self.y][self.x] = None
            self.x, self.y = self.chemin[1]
            self.chemin    = self.chemin[1:]
            self.dist_totale += 1
            # Ne poser le pompier que si la case est libre
            if grille[self.y][self.x] is None:
                grille[self.y][self.x] = self

    # ── Éteindre un feu adjacent ──
    def eteindre(self, feu, grille):
        grille[feu.y][feu.x] = None
        self.eau    -= 1
        self.eteints += 1
        self.chemin  = []
        self.cible   = None

    def est_actif(self):
        return self.eau > 0

    def barre_eau(self):
        pct = self.eau / self.eau_max
        n   = int(pct * 10)
        col = Fore.GREEN if pct > 0.5 else Fore.YELLOW if pct > 0.2 else Fore.RED
        return col + "█" * n + Fore.WHITE + Style.DIM + "░" * (10 - n) + Style.RESET_ALL

    def symbole_colore(self):
        return Fore.CYAN + Style.BRIGHT + f"P{self.id}" + Style.RESET_ALL


# ═══════════════════════════════════════════════════════════
#  ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════

class Environnement:
    def __init__(self, config):
        self.largeur     = config["largeur"]
        self.hauteur     = config["hauteur"]
        self.propagation = config["propagation"]
        self.grille      = [[None] * self.largeur for _ in range(self.hauteur)]
        self.pompiers    = []
        self.feux        = []
        self.murs        = set()    # Ensemble des positions (x,y) de murs
        self.total_eteints = 0
        self.journal     = []

    # ── Obtenir les obstacles pour A* ──
    def obstacles(self, pompier_exclu=None):
        """
        Retourne le set des cases infranchissables :
        murs + positions des autres pompiers.
        Les feux NE sont PAS des obstacles (le pompier doit y aller).
        """
        obs = set(self.murs)
        for p in self.pompiers:
            if p is not pompier_exclu:
                obs.add((p.x, p.y))
        return obs

    # ── Initialisation ──
    def initialiser(self, nb_pompiers, nb_feux, eau_max, densite_murs=0.12):
        """Place tous les agents et génère les murs aléatoirement."""
        cases_utilisees = set()

        def case_libre():
            while True:
                x = random.randint(0, self.largeur  - 1)
                y = random.randint(0, self.hauteur - 1)
                if (x, y) not in cases_utilisees and (x, y) not in self.murs:
                    cases_utilisees.add((x, y))
                    return x, y

        # Générer les murs (obstacles) — environ densite_murs % des cases
        nb_murs = int(self.largeur * self.hauteur * densite_murs)
        for _ in range(nb_murs):
            x = random.randint(0, self.largeur  - 1)
            y = random.randint(0, self.hauteur - 1)
            if (x, y) not in cases_utilisees:
                self.murs.add((x, y))
                self.grille[y][x] = Mur(x, y)

        # Placer les pompiers
        for i in range(nb_pompiers):
            x, y = case_libre()
            p = Pompier(i + 1, x, y, eau_max)
            self.pompiers.append(p)
            self.grille[y][x] = p

        # Placer les feux
        for _ in range(nb_feux):
            x, y = case_libre()
            f = Feu(x, y)
            self.feux.append(f)
            self.grille[y][x] = f

        self._log(f"Init v2 A* — {nb_pompiers} pompier(s), {nb_feux} feux, {len(self.murs)} murs")

    # ── Affichage terminal ──
    def afficher(self, tour, nb_tours):
        """Affiche la grille avec les chemins A* visibles."""
        # Construire le set des cases "chemin" pour l'affichage
        cases_chemin = set()
        for p in self.pompiers:
            for cx, cy in p.chemin[1:]:   # Exclure la position du pompier
                cases_chemin.add((cx, cy))

        print(Fore.WHITE + Style.BRIGHT + "═" * (self.largeur * 3))
        print(f"  FIRESIM PRO v2 (A*)  |  Tour {tour}/{nb_tours}  |  "
              f"Feux: {Fore.RED}{len(self.feux)}{Fore.WHITE}  |  "
              f"Éteints: {Fore.GREEN}{self.total_eteints}{Fore.WHITE}"
              + Style.RESET_ALL)
        print(Fore.WHITE + Style.BRIGHT + "═" * (self.largeur * 3))

        for y in range(self.hauteur):
            print(" ", end="")
            for x in range(self.largeur):
                cell = self.grille[y][x]
                if isinstance(cell, Pompier):
                    print(cell.symbole_colore(), end=" ")
                elif isinstance(cell, Feu):
                    print(cell.symbole_colore(), end=" ")
                elif isinstance(cell, Mur):
                    print(Fore.WHITE + Style.DIM + "█" + Style.RESET_ALL, end=" ")
                elif (x, y) in cases_chemin:
                    # Afficher le chemin A* en pointillés
                    print(Fore.BLUE + Style.DIM + "·" + Style.RESET_ALL, end=" ")
                else:
                    print(Fore.BLACK + Style.BRIGHT + "." + Style.RESET_ALL, end=" ")
            print()

        print()
        for p in self.pompiers:
            longueur = len(p.chemin)
            statut   = f"chemin:{longueur}cases" if longueur > 1 else ("À SEC ❌" if not p.est_actif() else "en attente")
            print(f"  {p.symbole_colore()} | Pos:({p.x},{p.y}) | "
                  f"Eau:{p.barre_eau()} {p.eau}/{p.eau_max} | "
                  f"Éteints:{Fore.GREEN}{p.eteints}{Fore.RESET} | "
                  f"Dist:{p.dist_totale} | {statut}")

        print()
        if self.journal:
            print(Fore.WHITE + Style.DIM + "  Journal (3 derniers) :" + Style.RESET_ALL)
            for entry in self.journal[-3:]:
                print(Fore.WHITE + Style.DIM + f"    {entry}" + Style.RESET_ALL)
        print()

    # ── Mise à jour ──
    def mettre_a_jour(self):
        """
        Un tour de simulation :
        1. Chaque pompier recalcule son chemin A* si nécessaire
        2. Avance d'une case ou éteint si adjacent
        3. Les feux vieillissent et peuvent se propager
        """
        feux_eteints = []

        for p in self.pompiers:
            if not p.est_actif():
                continue

            feux_dispos = [f for f in self.feux if f not in feux_eteints]
            if not feux_dispos:
                break

            obs = self.obstacles(pompier_exclu=p)

            # Recalculer le chemin si :
            # - pas de chemin en cours
            # - la cible n'existe plus
            # - le chemin est devenu invalide (obstacle apparu)
            besoin_recalcul = (
                not p.chemin or
                p.cible not in feux_dispos or
                any(pos in obs for pos in p.chemin)
            )

            if besoin_recalcul:
                cible, chemin = p.feu_le_plus_proche(feux_dispos, obs, self.largeur, self.hauteur)
                if cible:
                    p.cible  = cible
                    p.chemin = chemin
                    self._log(f"P{p.id} recalcule A* → ({cible.x},{cible.y}) [{len(chemin)} cases]")
                else:
                    self._log(f"P{p.id} aucun feu accessible !")
                    continue

            # Adjacent au feu ? → éteindre
            if p.cible and abs(p.x - p.cible.x) + abs(p.y - p.cible.y) <= 1:
                feux_eteints.append(p.cible)
                self.total_eteints += 1
                self._log(f"P{p.id} éteint ({p.cible.x},{p.cible.y}) eau:{p.eau - 1}")
                p.eteindre(p.cible, self.grille)
                self.grille[p.y][p.x] = p
            else:
                # Avancer d'une case selon A*
                p.avancer(self.grille)

        # Retirer les feux éteints
        for f in feux_eteints:
            if f in self.feux:
                self.feux.remove(f)

        # Vieillir les feux + propagation
        for f in list(self.feux):
            f.vieillir()

        self._propager_feux()

    # ── Propagation du feu ──
    def _propager_feux(self):
        """
        Nouveauté v2 : les feux intenses se propagent
        aux cases adjacentes libres.
        """
        nouveaux_feux = []
        for f in self.feux:
            if f.intensite >= 2 and random.random() < self.propagation:
                voisins = [
                    (f.x,   f.y-1),
                    (f.x,   f.y+1),
                    (f.x-1, f.y),
                    (f.x+1, f.y),
                ]
                random.shuffle(voisins)
                for vx, vy in voisins:
                    if not (0 <= vx < self.largeur and 0 <= vy < self.hauteur):
                        continue
                    if self.grille[vy][vx] is None:
                        nf = Feu(vx, vy)
                        nouveaux_feux.append(nf)
                        self.grille[vy][vx] = nf
                        self._log(f"🔥 Propagation → ({vx},{vy})")
                        break   # Un seul voisin à la fois

        self.feux.extend(nouveaux_feux)

        # Apparition spontanée (probabilité plus faible en v2)
        if len(self.feux) < self.largeur * self.hauteur * 0.35:
            if random.random() < self.propagation * 0.4:
                occupees = {(p.x, p.y) for p in self.pompiers} | \
                           {(f.x, f.y) for f in self.feux} | self.murs
                for _ in range(20):
                    x = random.randint(0, self.largeur  - 1)
                    y = random.randint(0, self.hauteur - 1)
                    if (x, y) not in occupees:
                        nf = Feu(x, y)
                        self.feux.append(nf)
                        self.grille[y][x] = nf
                        self._log(f"🔥 Nouveau feu spontané ({x},{y})")
                        break

    def _log(self, msg):
        self.journal.append(msg)
        if len(self.journal) > 60:
            self.journal.pop(0)

    def victoire(self):
        return len(self.feux) == 0

    def defaite(self):
        return all(not p.est_actif() for p in self.pompiers)


# ═══════════════════════════════════════════════════════════
#  MENU & BOUCLE PRINCIPALE
# ═══════════════════════════════════════════════════════════

CONFIG = {
    "largeur"     : 14,
    "hauteur"     : 14,
    "nb_pompiers" : 2,
    "nb_feux"     : 5,
    "eau_max"     : 12,
    "propagation" : 0.25,
    "densite_murs": 0.12,
    "nb_tours"    : 120,
    "delai"       : 0.30,
    "clear"       : True,
}

PRESETS = {
    "1": {"nom": "Urbain (murs denses)",  "largeur":14,"hauteur":14,"nb_pompiers":3,"nb_feux":5, "eau_max":10,"propagation":0.20,"densite_murs":0.18},
    "2": {"nom": "Forêt (feux rapides)",  "largeur":18,"hauteur":18,"nb_pompiers":2,"nb_feux":8, "eau_max":8, "propagation":0.40,"densite_murs":0.08},
    "3": {"nom": "Industriel (obstacles)","largeur":12,"hauteur":12,"nb_pompiers":4,"nb_feux":4, "eau_max":15,"propagation":0.15,"densite_murs":0.22},
    "4": {"nom": "Crise (chaos total)",   "largeur":16,"hauteur":16,"nb_pompiers":1,"nb_feux":12,"eau_max":6, "propagation":0.45,"densite_murs":0.10},
}

def afficher_menu():
    print(Fore.RED + Style.BRIGHT + r"""
  ███████╗██╗██████╗ ███████╗███████╗██╗███╗   ███╗  ██╗   ██╗██████╗
  ██╔════╝██║██╔══██╗██╔════╝██╔════╝██║████╗ ████║  ██║   ██║╚════██╗
  █████╗  ██║██████╔╝█████╗  ███████╗██║██╔████╔██║  ██║   ██║ █████╔╝
  ██╔══╝  ██║██╔══██╗██╔══╝  ╚════██║██║██║╚██╔╝██║  ╚██╗ ██╔╝██╔═══╝
  ██║     ██║██║  ██║███████╗███████║██║██║ ╚═╝ ██║   ╚████╔╝ ███████╗
  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝     ╚═╝    ╚═══╝  ╚══════╝
    """ + Style.RESET_ALL)
    print(Fore.CYAN + "  Simulation multi-agents avec algorithme A*\n" + Fore.RESET)
    print("  Légende : "
          + Fore.CYAN + "P" + Fore.RESET + "=Pompier  "
          + Fore.RED  + "F" + Fore.RESET + "=Feu  "
          + Fore.WHITE + Style.DIM + "█" + Style.RESET_ALL + "=Mur  "
          + Fore.BLUE + Style.DIM + "·" + Style.RESET_ALL + "=Chemin A*\n")
    print("  Scénarios prédéfinis :")
    for k, v in PRESETS.items():
        print(f"  [{k}] {v['nom']:28} — {v['nb_pompiers']}P {v['nb_feux']}F "
              f"eau:{v['eau_max']} murs:{int(v['densite_murs']*100)}% prop:{int(v['propagation']*100)}%")
    print("  [5] Configuration personnalisée")
    print("  [0] Quitter\n")


def saisir_int(prompt, min_v, max_v, defaut):
    try:
        v = input(f"  {prompt} [{min_v}-{max_v}] (défaut={defaut}) : ").strip()
        return int(v) if v else defaut
    except ValueError:
        return defaut


def config_perso():
    print(Fore.CYAN + "\n  Configuration personnalisée :" + Fore.RESET)
    c = dict(CONFIG)
    c["largeur"]      = saisir_int("Largeur grille",     6, 24, 14)
    c["hauteur"]      = saisir_int("Hauteur grille",     6, 24, 14)
    c["nb_pompiers"]  = saisir_int("Nombre de pompiers", 1,  6,  2)
    c["nb_feux"]      = saisir_int("Feux initiaux",      1, 20,  5)
    c["eau_max"]      = saisir_int("Eau par pompier",    3, 40, 12)
    murs_pct          = saisir_int("Densité murs (%)",   0, 30, 12)
    c["densite_murs"] = murs_pct / 100
    spread            = saisir_int("Propagation (%)",    0, 60, 25)
    c["propagation"]  = spread / 100
    return c


def lancer(cfg):
    env = Environnement(cfg)
    env.initialiser(
        cfg["nb_pompiers"], cfg["nb_feux"],
        cfg["eau_max"],     cfg["densite_murs"]
    )

    for tour in range(1, cfg["nb_tours"] + 1):
        if cfg["clear"]:
            os.system('cls' if os.name == 'nt' else 'clear')

        env.afficher(tour, cfg["nb_tours"])

        if env.victoire():
            print(Fore.GREEN + Style.BRIGHT +
                  f"\n  ✅ VICTOIRE ! Tous les feux éteints en {tour} tours.\n")
            break
        if env.defaite():
            print(Fore.RED + Style.BRIGHT +
                  f"\n  ❌ DÉFAITE — Eau épuisée. {len(env.feux)} feux restants.\n")
            break

        env.mettre_a_jour()
        time.sleep(cfg["delai"])
    else:
        print(Fore.YELLOW +
              f"\n  Simulation terminée ({cfg['nb_tours']} tours max). "
              f"{len(env.feux)} feux restants.\n")

    # Rapport final
    print(Fore.WHITE + Style.BRIGHT + "─" * 55 + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "  RAPPORT FINAL" + Style.RESET_ALL)
    print(f"  Feux éteints   : {Fore.GREEN}{env.total_eteints}{Fore.RESET}")
    print(f"  Feux restants  : {Fore.RED}{len(env.feux)}{Fore.RESET}")
    print(f"  Murs / obstacles : {len(env.murs)}")
    for p in env.pompiers:
        print(f"  Pompier P{p.id}    : {p.eteints} extinctions | "
              f"{p.dist_totale} cases parcourues (A*) | eau restante: {p.eau}")
    print(Fore.WHITE + Style.BRIGHT + "─" * 55 + Style.RESET_ALL)


def main():
    while True:
        if CONFIG["clear"]:
            os.system('cls' if os.name == 'nt' else 'clear')

        afficher_menu()
        choix = input("  Votre choix : ").strip()

        if choix == "0":
            print(Fore.YELLOW + "\n  Au revoir !\n")
            break
        elif choix in PRESETS:
            cfg = dict(CONFIG)
            cfg.update(PRESETS[choix])
            lancer(cfg)
        elif choix == "5":
            cfg = config_perso()
            lancer(cfg)
        else:
            print(Fore.RED + "  Choix invalide.\n")
            continue

        input("\n  Appuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    main()
