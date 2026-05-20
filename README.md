# Grafcet SFC Simulator - Convoyeur de tri industriel

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Domain](https://img.shields.io/badge/domain-Industrial%20Automation-orange)
![Standard](https://img.shields.io/badge/standard-IEC%2061131--3-blueviolet)

Simulation d'un **convoyeur de tri industriel** piloté par un moteur **GRAFCET** (Sequential Function Chart - SFC) implémenté en Python

> **Objectif pédagogique :** ce projet démontre comment un automate programmable industriel (API) orchestre un procédé de tri selon une logique séquentielle GRAFCET. La simulation inclut capteurs, actionneurs et statistiques de production, avec une visualisation matplotlib.

---

## Sommaire

- [Contexte industriel](#contexte-industriel)
- [Description du procédé](#description-du-procédé)
- [Architecture du Grafcet](#architecture-du-grafcet)
- [Structure du projet](#structure-du-projet)
- [Installation et utilisation](#installation-et-utilisation)
- [Résultats de simulation](#résultats-de-simulation)
- [Extensions possibles](#extensions-possibles)
- [Références](#références)

---

## Contexte industriel

Dans une ligne de production, un **convoyeur de tri** automatise l'acheminement et la séparation des pièces selon leur conformité aux spécifications. Ce type de système est omniprésent dans :

- l'**industrie manufacturière** (tri de pièces usinées)
- l'**agroalimentaire** (contrôle qualité visuel ou dimensionnel)
- la **logistique** (tri de colis par destination)

L'automate pilote l'ensemble selon un **programme séquentiel GRAFCET**, garantissant un comportement déterministe et sûr même en cas d'aléas (pièce manquante, défaut capteur).

---

## Description du procédé

```
  ┌───────────────────────────────────────────────────────────────────┐
  │                         CONVOYEUR DE TRI                          │
  │                                                                   │
  │  [S1]──── M1 (convoyeur) ────[S2]── mesure ──[V1]──→ Sortie OK    │
  │   ↑         Entrée pièce      Station        Vérin conforme       │
  │   │                           qualité                             │
  │   │                              │                                │
  │   │                             [S3] résultat                     │
  │   │                              │                                │
  │   │                             [V2]──→ Rebut                     │
  │   │                             Vérin éjecteur                    │
  └───────────────────────────────────────────────────────────────────┘
```

### Capteurs (entrées TOR)

| Capteur | Type               | Rôle                                    |
|---------|--------------------|-----------------------------------------|
| S1      | Détecteur inductif | Présence pièce en entrée du convoyeur   |
| S2      | Détecteur optique  | Pièce arrivée à la station de mesure    |
| S3      | Capteur qualité    | Résultat du contrôle (1 = conforme)     |

### Actionneurs (sorties TOR)

| Actionneur | Type              | Rôle                              |
|------------|-------------------|-----------------------------------|
| M1         | Contacteur moteur | Mise en marche du convoyeur       |
| V1         | Électrovanne      | Vérin pneumatique sortie OK       |
| V2         | Électrovanne      | Vérin pneumatique éjection rebut  |
| L_OK       | Voyant vert       | Signalisation pièce conforme      |
| L_NOK      | Voyant rouge      | Signalisation pièce rejetée       |

---

## Architecture du Grafcet

```
        ┌───────┐
     ══ │   0   │ ══  ← Étape initiale (double cadre)
        │ Init  │
        └───────┘
             │
         Init OK
             │
        ┌───────┐
        │   1   │  Attente pièce
        └───────┘
             │
           S1
             │
        ┌───────┐
        │   2   │  Transport  —  M1 = ON
        └───────┘
             │
           S2
             │
        ┌───────┐
        │   3   │  Contrôle qualité
        └───────┘
             │
      ───────────────         ← Divergence OU
      │             │
    S3=1           S3=0
      │             │
  ┌───────┐     ┌───────┐
  │   4   │     │   5   │
  │ Conf. │     │ Rebut │    V1=ON        V2=ON
  │ V1=ON │     │ V2=ON │
  └───────┘     └───────┘
      │             │
  t≥1.2s         t≥1.0s
      │             │
      ───────────────         ← Convergence OU
             │
        ┌───────┐
        │   6   │  Fin de cycle
        └───────┘
             │
           True
             │ (boucle vers étape 1)
```

### Règles IEC 61131-3 implémentées

| Règle | Description                                                   |
|-------|---------------------------------------------------------------|
| R1    | Situation initiale définie par l'étape 0 (marquée ══)         |
| R2    | Franchissement si toutes les sources actives ET réceptivité   |
| R3    | Désactivation sources / activation destinations simultanées   |
| R4    | Plusieurs transitions franchissables en un seul cycle (scan)  |
| R5    | Stabilisation de l'état avant exécution des actions           |

---

## Structure du projet

```
grafcet-sfc-simulator/
│
├── grafcet_engine.py      # Moteur GRAFCET générique (Step, Transition, GrafcetEngine)
├── conveyor_process.py    # Procédé de tri (définition du Grafcet + simulation capteurs)
├── visualizer.py          # Visualisation matplotlib (schéma SFC + résultats)
├── main.py                # Point d'entrée CLI
├── requirements.txt       # Dépendances Python
└── README.md
```

### `grafcet_engine.py` - Moteur générique

Contient les classes fondamentales :

- **`Step`** : Étape avec timer d'activation, actions d'entrée/sortie, état actif/inactif
- **`Transition`** : Condition de franchissement, sources et destinations
- **`GrafcetEngine`** : Moteur de scrutation (cycle scan), gestion I/O, historique

Le moteur est **indépendant du procédé** : il peut être réutilisé pour n'importe quelle application GRAFCET (feu tricolore, remplissage de bouteilles, machine-outil).

### `conveyor_process.py` - Procédé de tri

Instancie le Grafcet pour le convoyeur spécifique et simule les signaux capteurs selon l'étape active. Les délais de transport et les temporisations reproduisent un comportement réaliste.

---

## Installation et utilisation

### Prérequis

- Python 3.8 ou supérieur
- pip

### Installation

```bash
git clone https://github.com/Toast-Cyberia/grafcet-sfc-simulator.git
cd grafcet-sfc-simulator
pip install -r requirements.txt
```

### Lancer la simulation

```bash
# Simulation 120 s avec visualisation (défaut)
python main.py

# Simulation 60 s
python main.py --time 60

# Mode terminal uniquement (sans matplotlib)
python main.py --no-plot

# Résultats reproductibles (graine aléatoire fixée)
python main.py --seed 42

# Affichage détaillé cycle par cycle
python main.py --verbose --time 20
```

### Utiliser le moteur dans votre propre projet

```python
from grafcet_engine import GrafcetEngine, Step, Transition

engine = GrafcetEngine()

# Définir les étapes
s0 = Step(0, "Init", initial=True)
s1 = Step(1, "Travail")
s0.on_entry(lambda: print("Initialisation"))
s1.on_entry(lambda: print("Démarrage travail"))

engine.add_step(s0).add_step(s1)

# Définir les transitions
engine.add_transition(Transition(
    trans_id=0,
    source_ids=[0], dest_ids=[1],
    condition=lambda: engine.get_input("START"),
    label="Bouton START"
))

# Boucle principale (scan cycle)
engine.set_input("START", True)
for _ in range(10):
    active = engine.cycle(dt=0.1)
    print("Étapes actives :", active)
```

---

## Résultats de simulation

L'exécution génère deux fenêtres matplotlib :

**1. Schéma GRAFCET** - diagramme SFC annoté avec étapes, transitions et réceptivités.

**2. Résultats de simulation** :
- **Timeline étapes** : diagramme de Gantt montrant l'activation de chaque étape
- **État actionneurs** : signaux M1, V1, V2, L_OK, L_NOK sur l'axe du temps
- **État capteurs** : signaux S1, S2, S3 sur l'axe du temps
- **Bilan de production** : camembert OK/NOK + KPIs (taux de conformité, cadence)

Exemple de résultats (simulation 120 s, graine 42) :

```
══════════════════════════════════════════════
  BILAN DE PRODUCTION
══════════════════════════════════════════════
  Cycles Grafcet  : 1200
  Pièces traitées : 87
  Conformes (OK)  : 63  (72.4 %)
  Rebuts  (NOK)   : 24  (27.6 %)
══════════════════════════════════════════════
```

---

## Extensions possibles

Ce projet est une base pour des développements plus avancés :

- [ ] **Ajout de divergences ET** (séquences parallèles simultanées)
- [ ] **Interface graphique Tkinter** avec état des étapes en temps réel (comme un pupître opérateur)
- [ ] **Export XLSX** des données de production (pandas + openpyxl)
- [ ] **Simulation de pannes** (capteur collé, rupture moteur) pour tester la gestion des défauts
- [ ] **Connexion OPC-UA** pour piloter un vrai automate Siemens ou Schneider via le réseau
- [ ] **Génération de code Ladder / ST** (Structured Text IEC 61131-3) depuis le Grafcet Python

---

## Références

- **NF EN 60848** - Langage de spécification GRAFCET pour diagrammes fonctionnels en séquence
- **IEC 61131-3** - Langages de programmation pour automates programmables industriels
- **Cours d'automatisme industriel** - IUT / BTS CRSA / GEII
- Michel, G. — *Grafcet : Outil de description des systèmes automatisés de production*, Dunod

---

## Auteur

**Tomas SOUSA** — Étudiant en systèmes automatisés  
[github.com/Toast-Cyberia](https://github.com/Toast-Cyberia) · [LinkedIn](https://www.linkedin.com/in/tomass-sousa/)

---

*Projet réalisé dans le cadre d'une démarche d'auto-formation à l'automatisme industriel.*
