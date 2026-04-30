# Firesim
📋 Description
FireSim A* est un projet de simulation multi-agents développé en Python.
Des pompiers autonomes naviguent sur une grille 2D pour atteindre et éteindre des foyers d'incendie, en évitant les murs et obstacles grâce à l'algorithme A*.
Le projet couvre trois grands thèmes :

POO — héritage, encapsulation, interaction entre objets
A* Pathfinding — recherche de chemin optimal sur grille avec obstacles
Simulation multi-agents — comportement émergent, ressources limitées, propagation

🗂️ Fichiers
firesim-astar/
├── simulation_astar.py     # Simulation console (terminal)
├── firesim_astar.html      # Interface web interactive
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier

🧠 Algorithme A*
A* calcule le chemin le plus court entre deux points sur une grille en évitant les obstacles.
Formule
f(n) = g(n) + h(n)
TermeSignificationg(n)Nombre de cases parcourues depuis le départh(n)Distance de Manhattan jusqu'à la cible (heuristique)f(n)Coût estimé total — on choisit toujours le f minimal

🏗️ Architecture des classes
Agent                           ← classe de base (x, y)
├── Pompier  (agent actif)
│   ├── feu_le_plus_proche()   ← A* vers chaque feu, garde le plus court
│   ├── avancer()              ← suit le chemin A* case par case
│   └── eteindre()             ← supprime le feu, consomme 1 eau
├── Feu      (agent passif)
│   └── vieillir()             ← intensité croît avec l'âge
└── Mur                        ← obstacle infranchissable

Environnement
├── initialiser()              ← place les agents + génère les murs
├── obstacles()                ← murs + positions des autres pompiers
├── afficher()                 ← rendu terminal (colorama) + chemin visible
├── mettre_a_jour()            ← boucle : A* → avancer → éteindre
└── _propager_feux()           ← propagation si intensité ≥ 2

⚙️ Règles de simulation
RègleDétailDéplacement1 case par tour, chemin calculé par A*ExtinctionDistance ≤ 1 (case adjacente ou même case)EauLimitée — 1 unité consommée par extinctionMursInfranchissables — A* contourne automatiquementPropagationFeu d'intensité ≥ 2 peut s'étendre à un voisin libreRecalculA* recalcule si la cible disparaît ou si un obstacle bloque le chemin

🎮 Conditions de fin
len(feux) == 0✅ Victoire
all(pompier.eau == 0)❌ Défaite — eau épuisée
tour == nb_tours_max⏱️ Timeout


👤 Auteur
ouissal sarkouh
Étudiant en ingénierie de données et systèmes decisionnels
🔗 github.com/ouissalsarkouh283
