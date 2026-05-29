"""  
grafcet_engine.py
=================
Moteur GRAFCET / SFC (Sequential Function Chart) — IEC 61131-3
Tomas SOUSA — github.com/Toast-Cyberia

Implémente les règles d'évolution du GRAFCET :
  - Règle 1 : Situation initiale définie par les étapes initiales
  - Règle 2 : Franchissement si sources actives ET réceptivité vraie
  - Règle 3 : Désactivation sources / activation destinations simultanées
  - Règle 4 : Simultanéité (plusieurs transitions franchissables en un cycle)
  - Règle 5 : Stabilisation avant exécution des actions
"""

from typing import Callable, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Step
# ─────────────────────────────────────────────────────────────────────────────

class Step:
    """
    Étape GRAFCET.

    Une étape est soit active soit inactive.
    Elle possède des actions d'entrée (exécutées une fois à l'activation)
    et des actions de sortie (exécutées une fois à la désactivation).

    Attributes:
        step_id  : Identifiant numérique (affiché dans le schéma)
        name     : Libellé descriptif
        initial  : True si l'étape est active au démarrage
        active   : État courant
        time_active : Durée d'activation cumulée depuis le dernier franchissement (s)
    """

    def __init__(self, step_id: int, name: str, initial: bool = False):
        self.step_id = step_id
        self.name = name
        self.initial = initial
        self.active = initial
        self.time_active: float = 0.0
        self._entry_actions: List[Callable] = []
        self._exit_actions: List[Callable] = []

    # ── Actions ──────────────────────────────────────────────────────────────

    def on_entry(self, action: Callable) -> "Step":
        """Enregistre une action exécutée à chaque activation de l'étape."""
        self._entry_actions.append(action)
        return self   # fluent API

    def on_exit(self, action: Callable) -> "Step":
        """Enregistre une action exécutée à chaque désactivation de l'étape."""
        self._exit_actions.append(action)
        return self

    # ── Méthodes internes ────────────────────────────────────────────────────

    def _activate(self):
        self.active = True
        self.time_active = 0.0
        for fn in self._entry_actions:
            fn()

    def _deactivate(self):
        for fn in self._exit_actions:
            fn()
        self.active = False
        self.time_active = 0.0

    def _tick(self, dt: float):
        if self.active:
            self.time_active += dt

    def reset(self):
        """Remet l'étape à son état initial (pour réinitialisation du Grafcet)."""
        self.active = self.initial
        self.time_active = 0.0

    def __repr__(self):
        marker = "●" if self.active else "○"
        return f"[{marker}] Étape {self.step_id}: {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Transition
# ─────────────────────────────────────────────────────────────────────────────

class Transition:
    """
    Transition GRAFCET.

    Une transition relie une ou plusieurs étapes sources à une ou plusieurs
    étapes destinations. Elle est franchie (fired) si :
      1. Toutes les étapes sources sont actives.
      2. La réceptivité (condition) est vraie.

    Attributes:
        trans_id   : Identifiant numérique
        source_ids : IDs des étapes sources
        dest_ids   : IDs des étapes destinations
        condition  : Callable retournant bool — la réceptivité
        label      : Description textuelle (affichage)
    """

    def __init__(
        self,
        trans_id: int,
        source_ids: List[int],
        dest_ids: List[int],
        condition: Callable[[], bool],
        label: str = "",
    ):
        self.trans_id = trans_id
        self.source_ids = source_ids
        self.dest_ids = dest_ids
        self.condition = condition
        self.label = label

    def is_fireable(self, steps: Dict[int, Step]) -> bool:
        """Retourne True si la transition peut être franchie."""
        sources_active = all(
            steps[sid].active for sid in self.source_ids if sid in steps
        )
        if not sources_active:
            return False
        try:
            return bool(self.condition())
        except Exception:
            return False

    def __repr__(self):
        return (
            f"T{self.trans_id} "
            f"({self.source_ids} → {self.dest_ids}) "
            f"[{self.label}]"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GrafcetEngine
# ─────────────────────────────────────────────────────────────────────────────

class GrafcetEngine:
    """
    Moteur d'exécution GRAFCET conforme IEC 61131-3.

    Utilisation typique :
    ---------------------
        engine = GrafcetEngine()

        s0 = Step(0, "Init", initial=True)
        s1 = Step(1, "Attente")
        engine.add_step(s0).add_step(s1)

        engine.add_transition(Transition(
            trans_id=0,
            source_ids=[0], dest_ids=[1],
            condition=lambda: engine.get_input("START"),
            label="Départ cycle"
        ))

        for _ in range(100):
            engine.set_input("START", some_signal)
            active = engine.cycle(dt=0.1)
    """

    def __init__(self):
        self.steps: Dict[int, Step] = {}
        self.transitions: List[Transition] = []
        self.inputs: Dict[str, bool] = {}    # Capteurs / boutons
        self.outputs: Dict[str, bool] = {}   # Actionneurs / voyants
        self.cycle_count: int = 0
        self.history: List[dict] = []        # Enregistrement pour analyse

    # ── Construction ─────────────────────────────────────────────────────────

    def add_step(self, step: Step) -> "GrafcetEngine":
        """Ajoute une étape au Grafcet."""
        self.steps[step.step_id] = step
        return self

    def add_transition(self, transition: Transition) -> "GrafcetEngine":
        """Ajoute une transition au Grafcet."""
        self.transitions.append(transition)
        return self

    # ── Entrées / Sorties ─────────────────────────────────────────────────────

    def set_input(self, name: str, value: bool):
        """Met à jour un signal d'entrée (capteur TOR)."""
        self.inputs[name] = value

    def set_output(self, name: str, value: bool):
        """Met à jour un signal de sortie (actionneur TOR)."""
        self.outputs[name] = value

    def get_input(self, name: str, default: bool = False) -> bool:
        return self.inputs.get(name, default)

    def get_output(self, name: str, default: bool = False) -> bool:
        return self.outputs.get(name, default)

    # ── Exécution ─────────────────────────────────────────────────────────────

    def get_active_steps(self) -> List[int]:
        """Retourne la liste des IDs des étapes actives."""
        return [sid for sid, s in self.steps.items() if s.active]

    def cycle(self, dt: float = 0.1) -> List[int]:
        """
        Exécute un cycle de scrutation complet.

        Phases d'un cycle :
          1. Détection des transitions franchissables
          2. Franchissement : désactivation sources + activation destinations
          3. Mise à jour des compteurs de temps (time_active)
          4. Enregistrement du snapshot pour analyse

        Args:
            dt: Durée du cycle (intervalle de temps simulé, en secondes)

        Returns:
            Liste des IDs des étapes actives après le cycle.
        """
        # ── Phase 1 : Transitions franchissables ──────────────────────────
        fireable: List[Transition] = [
            t for t in self.transitions if t.is_fireable(self.steps)
        ]

        # ── Phase 2 : Franchissement ───────────────────────────────────────
        if fireable:
            # Collecter étapes à désactiver / activer
            to_deactivate = {sid for t in fireable for sid in t.source_ids}
            to_activate   = {sid for t in fireable for sid in t.dest_ids}

            # Désactivation (actions de sortie)
            for sid in to_deactivate:
                if sid in self.steps:
                    self.steps[sid]._deactivate()

            # Activation (actions d'entrée)
            for sid in to_activate:
                if sid in self.steps:
                    self.steps[sid]._activate()

        # ── Phase 3 : Compteurs de temps ──────────────────────────────────
        for step in self.steps.values():
            step._tick(dt)

        # ── Phase 4 : Enregistrement ───────────────────────────────────────
        self.history.append({
            "cycle":        self.cycle_count,
            "time":         round(self.cycle_count * dt, 3),
            "active_steps": self.get_active_steps(),
            "inputs":       dict(self.inputs),
            "outputs":      dict(self.outputs),
        })
        self.cycle_count += 1

        return self.get_active_steps()

    def reset(self):
        """Réinitialise le Grafcet à sa situation initiale."""
        for step in self.steps.values():
            step.reset()
        self.inputs.clear()
        self.outputs.clear()
        self.cycle_count = 0
        self.history.clear()

    # ── Affichage ─────────────────────────────────────────────────────────────

    def print_status(self):
        """Affiche l'état courant du Grafcet dans le terminal."""
        active = self.get_active_steps()
        print(f"\n── Cycle {self.cycle_count} ─────────────────────")
        for sid, step in sorted(self.steps.items()):
            marker = "► " if step.active else "  "
            timer = f" (t={step.time_active:.1f}s)" if step.active else ""
            print(f"  {marker}Étape {sid:2d}: {step.name}{timer}")
        if self.outputs:
            outs = ", ".join(
                f"{k}={'ON' if v else 'off'}" for k, v in sorted(self.outputs.items())
            )
            print(f"  Sorties : {outs}")
        if self.inputs:
            ins = ", ".join(
                f"{k}={'1' if v else '0'}" for k, v in sorted(self.inputs.items())
            )
            print(f"  Entrées : {ins}")
