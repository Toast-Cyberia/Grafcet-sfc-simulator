"""
conveyor_process.py
===================
Simulation d'un convoyeur de tri industriel — modèle de procédé
Tomas SOUSA — github.com/Toast-Cyberia

Procédé simulé :
----------------
Un convoyeur à bande transporte des pièces usinées vers une station
de contrôle qualité. L'automate (Grafcet) pilote le convoyeur et
l'orientation des pièces selon leur conformité.

Schéma du procédé :
-------------------

  Entrée                     Station               Sortie OK
    │                        mesure                   │
    ▼   M1 (convoyeur)         │                      ▼
  [S1]──────────────────────[S2]────────────────────[V2]──→
                                │
                               [S3] qualité
                                │
                               [V1]──→ Rebut

Capteurs (entrées TOR) :
  S1 : Présence pièce entrée convoyeur
  S2 : Pièce arrivée à la station de mesure
  S3 : Résultat contrôle qualité (1 = conforme, 0 = non-conforme)

Actionneurs (sorties TOR) :
  M1 : Moteur convoyeur (MARCHE / ARRÊT)
  V1 : Vérin éjecteur pneumatique (conforme sortie OK)
  V2 : Vérin séparateur (non-conforme → rebut)
  L_OK  : Voyant vert  (pièce conforme acceptée)
  L_NOK : Voyant rouge (pièce rejetée)

GRAFCET — Étapes :
  0 : Initialisation
  1 : Attente pièce
  2 : Transport (convoyeur en marche)
  3 : Contrôle qualité (convoyeur arrêté, mesure en cours)
  4 : Orientation conforme (V1 actionné)
  5 : Éjection non-conforme (V2 actionné)
  6 : Fin de cycle (retour attente)
"""

import random
from typing import Optional

from grafcet_engine import GrafcetEngine, Step, Transition


class ConveyorProcess:
    """
    Modèle de procédé : convoyeur de tri industriel.

    Cette classe encapsule :
    - Le moteur Grafcet
    - La description du procédé (étapes + transitions)
    - La simulation des signaux capteurs
    - Les statistiques de production

    Usage :
        process = ConveyorProcess()
        for _ in range(500):
            process.update(dt=0.1)
    """

    # Durées configurables (secondes simulées)
    TRANSPORT_DURATION   = 2.0   # temps de transport entre S1 et S2
    MEASURE_DURATION     = 0.8   # temps de mesure à la station
    ACTUATOR_DURATION    = 1.2   # durée de course du vérin (conforme)
    EJECTION_DURATION    = 1.0   # durée d'éjection (non-conforme)
    PIECE_ARRIVAL_RATE   = 0.08  # probabilité par cycle d'arriver une pièce
    CONFORMITY_RATE      = 0.72  # taux de pièces conformes (72 %)

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.engine = GrafcetEngine()
        self._piece_quality: Optional[bool] = None
        self.stats = {"total": 0, "ok": 0, "nok": 0, "cycles": 0}
        self._build_grafcet()

    # ── Accesseurs pratiques ─────────────────────────────────────────────────

    def _inp(self, name: str) -> bool:
        return self.engine.get_input(name, False)

    def _out(self, name: str, value: bool):
        self.engine.set_output(name, value)

    def _step(self, sid: int) -> Step:
        return self.engine.steps[sid]

    def _active(self, sid: int) -> bool:
        return self.engine.steps[sid].active

    # ── Construction du Grafcet ──────────────────────────────────────────────

    def _build_grafcet(self):
        """Instancie les étapes et transitions du Grafcet de tri."""
        e = self.engine

        # ── Étapes ──────────────────────────────────────────────────────────
        s0 = Step(0, "Initialisation", initial=True)
        s1 = Step(1, "Attente pièce")
        s2 = Step(2, "Transport")
        s3 = Step(3, "Contrôle qualité")
        s4 = Step(4, "Orientation → sortie OK")
        s5 = Step(5, "Éjection → rebut")
        s6 = Step(6, "Fin de cycle")

        # Actions lors de l'activation de chaque étape
        s0.on_entry(lambda: self._all_outputs_off())

        s1.on_entry(lambda: (
            self._out("M1", False),     # convoyeur arrêté
            self._out("L_OK",  False),
            self._out("L_NOK", False),
        ))

        s2.on_entry(lambda: (
            self._out("M1", True),      # démarrage convoyeur
        ))

        s3.on_entry(lambda: (
            self._out("M1", False),     # arrêt pour mesure
        ))

        s4.on_entry(lambda: (
            self._out("V1",   True),    # vérin conforme
            self._out("L_OK", True),    # voyant vert
        ))
        s4.on_exit(lambda: (
            self._out("V1",   False),
            self._out("L_OK", False),
        ))

        s5.on_entry(lambda: (
            self._out("V2",    True),   # vérin éjection
            self._out("L_NOK", True),   # voyant rouge
        ))
        s5.on_exit(lambda: (
            self._out("V2",    False),
            self._out("L_NOK", False),
        ))

        for step in (s0, s1, s2, s3, s4, s5, s6):
            e.add_step(step)

        # ── Transitions ──────────────────────────────────────────────────────
        # T0 → 1 : Initialisation terminée (franchissement immédiat)
        e.add_transition(Transition(
            0, [0], [1],
            condition=lambda: True,
            label="Init OK",
        ))

        # T1 → 2 : Pièce détectée à l'entrée
        e.add_transition(Transition(
            1, [1], [2],
            condition=lambda: self._inp("S1"),
            label="S1 pièce détectée",
        ))

        # T2 → 3 : Pièce arrivée à la station de mesure
        e.add_transition(Transition(
            2, [2], [3],
            condition=lambda: self._inp("S2"),
            label="S2 station mesure",
        ))

        # T3 → 4 : Mesure terminée, pièce conforme
        e.add_transition(Transition(
            3, [3], [4],
            condition=lambda: (
                self._inp("S3") and self._piece_quality is True
            ),
            label="Conforme (S3=1)",
        ))

        # T3 → 5 : Mesure terminée, pièce non-conforme
        e.add_transition(Transition(
            4, [3], [5],
            condition=lambda: (
                self._inp("S3") and self._piece_quality is False
            ),
            label="Non-conforme (S3=0)",
        ))

        # T4 → 6 : Orientation terminée (temporisation)
        e.add_transition(Transition(
            5, [4], [6],
            condition=lambda: self._step(4).time_active >= self.ACTUATOR_DURATION,
            label=f"t ≥ {self.ACTUATOR_DURATION}s",
        ))

        # T5 → 6 : Éjection terminée (temporisation)
        e.add_transition(Transition(
            6, [5], [6],
            condition=lambda: self._step(5).time_active >= self.EJECTION_DURATION,
            label=f"t ≥ {self.EJECTION_DURATION}s",
        ))

        # T6 → 1 : Retour attente pièce suivante
        e.add_transition(Transition(
            7, [6], [1],
            condition=lambda: True,
            label="Retour attente",
        ))

    # ── Simulation des capteurs ───────────────────────────────────────────────

    def _simulate_inputs(self):
        """
        Met à jour les signaux capteurs en fonction de l'étape active.
        Cette méthode modélise les retours terrain de manière réaliste.
        """
        # S1 : arrivée aléatoire de pièce quand on est en attente
        if self._active(1):
            if random.random() < self.PIECE_ARRIVAL_RATE:
                conforming = random.random() < self.CONFORMITY_RATE
                self._piece_quality = conforming
                self.stats["total"] += 1
                if conforming:
                    self.stats["ok"] += 1
                else:
                    self.stats["nok"] += 1
                self.engine.set_input("S1", True)
            else:
                self.engine.set_input("S1", False)
        else:
            self.engine.set_input("S1", False)

        # S2 : pièce arrivée en station après le délai de transport
        if self._active(2):
            elapsed = self._step(2).time_active
            self.engine.set_input("S2", elapsed >= self.TRANSPORT_DURATION)
        else:
            self.engine.set_input("S2", False)

        # S3 : résultat de mesure disponible après le délai de mesure
        if self._active(3):
            elapsed = self._step(3).time_active
            if elapsed >= self.MEASURE_DURATION:
                self.engine.set_input("S3", True)
            else:
                self.engine.set_input("S3", False)
        else:
            self.engine.set_input("S3", False)

    def _all_outputs_off(self):
        """Mise à zéro de tous les actionneurs (sécurité initialisation)."""
        for name in ("M1", "V1", "V2", "L_OK", "L_NOK"):
            self._out(name, False)

    # ── Boucle principale ────────────────────────────────────────────────────

    def update(self, dt: float = 0.1) -> dict:
        """
        Exécute un pas de simulation :
          1. Mise à jour des capteurs simulés
          2. Un cycle Grafcet
          3. Retour du snapshot

        Args:
            dt: Pas de temps simulé (secondes)

        Returns:
            Dictionnaire snapshot (cycle, étapes actives, I/O, stats)
        """
        self._simulate_inputs()
        active = self.engine.cycle(dt=dt)
        self.stats["cycles"] += 1

        return {
            "cycle":        self.engine.cycle_count,
            "time":         round(self.engine.cycle_count * dt, 2),
            "active_steps": active,
            "step_names":   [self.engine.steps[s].name for s in active],
            "inputs":       dict(self.engine.inputs),
            "outputs":      dict(self.engine.outputs),
            "stats":        dict(self.stats),
        }

    # ── Lecture des résultats ────────────────────────────────────────────────

    @property
    def history(self):
        """Accès à l'historique complet des cycles Grafcet."""
        return self.engine.history

    def print_summary(self):
        """Affiche un résumé de production dans le terminal."""
        s = self.stats
        total = s["total"] if s["total"] > 0 else 1
        print("\n" + "═" * 50)
        print("  BILAN DE PRODUCTION")
        print("═" * 50)
        print(f"  Cycles Grafcet  : {s['cycles']}")
        print(f"  Pièces traitées : {s['total']}")
        print(f"  Conformes (OK)  : {s['ok']}  ({s['ok']/total*100:.1f} %)")
        print(f"  Rebuts  (NOK)   : {s['nok']}  ({s['nok']/total*100:.1f} %)")
        print("═" * 50)
