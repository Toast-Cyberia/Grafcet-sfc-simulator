"""  
main.py
=======
Point d'entrée — Simulation Grafcet : Convoyeur de tri industriel
Tomas SOUSA — github.com/Toast-Cyberia

Usage :
    python main.py                  # simulation 120 s avec visualisation
    python main.py --time 60        # simulation 60 s
    python main.py --no-plot        # mode texte uniquement (sans matplotlib)
    python main.py --seed 42        # reproductibilité (graine aléatoire)
"""

import argparse
import sys

from conveyor_process import ConveyorProcess
from visualizer import show_all


# ─────────────────────────────────────────────────────────────────────────────
# Paramètres de simulation
# ─────────────────────────────────────────────────────────────────────────────

DT            = 0.1    # pas de temps (s) — correspond à un cycle API ~100 ms
PRINT_EVERY   = 50     # afficher le statut tous les N cycles


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simulation Grafcet — Convoyeur de tri industriel"
    )
    parser.add_argument(
        "--time", type=float, default=120.0,
        help="Durée de simulation en secondes (défaut : 120 s)"
    )
    parser.add_argument(
        "--no-plot", action="store_true",
        help="Désactiver la visualisation matplotlib (mode terminal uniquement)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Graine pour la reproductibilité des résultats"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Afficher chaque cycle dans le terminal"
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation(sim_time: float, seed: int = None, verbose: bool = False):
    """
    Exécute la simulation du convoyeur de tri.

    Args:
        sim_time : Durée totale simulée (secondes)
        seed     : Graine aléatoire pour reproductibilité
        verbose  : Affichage détaillé cycle par cycle

    Returns:
        (history, stats) tuple
    """
    process = ConveyorProcess(seed=seed)
    total_cycles = int(sim_time / DT)

    print("=" * 60)
    print("  SIMULATION GRAFCET — Convoyeur de tri industriel")
    print("=" * 60)
    print(f"  Durée simulée   : {sim_time:.0f} s")
    print(f"  Pas de temps    : {DT*1000:.0f} ms / cycle")
    print(f"  Cycles à jouer  : {total_cycles}")
    print(f"  Taux conf. cible: {process.CONFORMITY_RATE*100:.0f} %")
    print("=" * 60)
    print()

    for i in range(total_cycles):
        snapshot = process.update(dt=DT)

        if verbose or (i % PRINT_EVERY == 0):
            t      = snapshot["time"]
            active = snapshot["active_steps"]
            names  = snapshot["step_names"]
            outs   = {k: v for k, v in snapshot["outputs"].items() if v}
            out_str = ", ".join(outs.keys()) if outs else "—"
            print(
                f"  t={t:7.1f}s │ "
                f"Étapes actives: {active} {names} │ "
                f"Sorties ON: {out_str}"
            )

    print()
    process.print_summary()
    return process.history, process.stats


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    history, stats = run_simulation(
        sim_time=args.time,
        seed=args.seed,
        verbose=args.verbose,
    )

    if not args.no_plot:
        print("\n[Visualizer] Affichage des graphiques... (fermez les fenêtres pour quitter)")
        show_all(history, stats, dt=DT)
    else:
        print("\n[Info] Mode --no-plot : visualisation désactivée.")


if __name__ == "__main__":
    main()
