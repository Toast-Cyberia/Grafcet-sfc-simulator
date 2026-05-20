"""
visualizer.py
=============
Visualisation matplotlib du Grafcet et de la simulation
Tomas SOUSA — github.com/Toast-Cyberia

Génère deux figures :
  1. Schéma fonctionnel du Grafcet (diagramme SFC)
  2. Résultats de simulation : timeline étapes + états I/O + statistiques
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# Palette de couleurs cohérente
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "step_inactive": "#F0F0F0",
    "step_active":   "#2196F3",
    "step_initial":  "#1565C0",
    "step_border":   "#37474F",
    "trans_line":    "#455A64",
    "ok_green":      "#4CAF50",
    "nok_red":       "#F44336",
    "motor":         "#FF9800",
    "sensor":        "#9C27B0",
    "bg":            "#FAFAFA",
    "grid":          "#E0E0E0",
    "text":          "#212121",
}


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 : Schéma GRAFCET
# ─────────────────────────────────────────────────────────────────────────────

def draw_grafcet_diagram(ax: plt.Axes):
    """
    Dessine le schéma GRAFCET du convoyeur de tri.
    Représentation conforme à la norme NF EN 60848.
    """
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 22)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor(COLORS["bg"])
    ax.set_title(
        "Grafcet — Convoyeur de tri industriel",
        fontsize=12, fontweight="bold", pad=10, color=COLORS["text"]
    )

    # ── Coordonnées des étapes (cx, cy) ──────────────────────────────────────
    step_positions = {
        0: (5.0, 20.5),   # Init
        1: (5.0, 17.5),   # Attente pièce
        2: (5.0, 14.5),   # Transport
        3: (5.0, 11.5),   # Contrôle qualité
        4: (3.0,  7.5),   # Conforme
        5: (7.0,  7.5),   # Non-conforme
        6: (5.0,  4.0),   # Fin cycle
    }

    step_labels = {
        0: ("0", "Initialisation"),
        1: ("1", "Attente pièce"),
        2: ("2", "Transport\n(M1 = ON)"),
        3: ("3", "Contrôle\nqualité"),
        4: ("4", "Orientation\n(V1 = ON)"),
        5: ("5", "Éjection\n(V2 = ON)"),
        6: ("6", "Fin de cycle"),
    }

    initial_steps = {0}

    # ── Dessin des étapes ─────────────────────────────────────────────────────
    step_radius = 0.55
    for sid, (cx, cy) in step_positions.items():
        color = COLORS["step_initial"] if sid in initial_steps else COLORS["step_inactive"]
        lw    = 2.5 if sid in initial_steps else 1.5

        # Cercle de l'étape
        circle = plt.Circle(
            (cx, cy), step_radius,
            fc=color, ec=COLORS["step_border"], lw=lw, zorder=3
        )
        ax.add_patch(circle)

        # Numéro de l'étape
        num, label = step_labels[sid]
        num_color = "white" if sid in initial_steps else COLORS["text"]
        ax.text(cx, cy, num, ha="center", va="center",
                fontsize=10, fontweight="bold", color=num_color, zorder=4)

        # Libellé à droite (ou gauche pour les branches)
        label_x = cx + 0.85 if sid not in {5} else cx + 0.85
        label_ha = "left"
        ax.text(label_x, cy, label, ha=label_ha, va="center",
                fontsize=7.5, color=COLORS["text"], zorder=4,
                bbox=dict(fc="white", ec="none", alpha=0.6, pad=1))

    # ── Connexions et transitions ─────────────────────────────────────────────
    trans_labels = {
        "0→1": "Init OK",
        "1→2": "S1",
        "2→3": "S2",
        "3→4": "S3 = 1\n(conforme)",
        "3→5": "S3 = 0\n(non-conf.)",
        "4→6": "t ≥ 1.2 s",
        "5→6": "t ≥ 1.0 s",
        "6→1": "Fin cycle",
    }

    arrow_kw = dict(
        arrowstyle="-|>",
        color=COLORS["trans_line"],
        lw=1.5,
        mutation_scale=12,
        zorder=2,
    )

    def draw_vline(y1, y2, x, label="", label_x_offset=0.15):
        """Ligne verticale avec barre de transition."""
        ax.annotate("", xy=(x, y2), xytext=(x, y1),
                    arrowprops=dict(**arrow_kw))
        mid_y = (y1 + y2) / 2
        # Barre de transition
        ax.plot([x - 0.35, x + 0.35], [mid_y, mid_y],
                color=COLORS["trans_line"], lw=2.0, zorder=3)
        ax.text(x + 0.4 + label_x_offset, mid_y, label,
                va="center", fontsize=7, color=COLORS["trans_line"])

    def draw_hline(x1, x2, y):
        ax.plot([x1, x2], [y, y], color=COLORS["trans_line"], lw=1.2, zorder=2)

    # 0 → 1
    draw_vline(step_positions[0][1] - step_radius,
               step_positions[1][1] + step_radius,
               5.0, trans_labels["0→1"])

    # 1 → 2
    draw_vline(step_positions[1][1] - step_radius,
               step_positions[2][1] + step_radius,
               5.0, trans_labels["1→2"])

    # 2 → 3
    draw_vline(step_positions[2][1] - step_radius,
               step_positions[3][1] + step_radius,
               5.0, trans_labels["2→3"])

    # 3 → 4 (divergence OU — branche gauche)
    branch_y = step_positions[3][1] - step_radius - 0.5
    ax.plot([3.0, 7.0], [branch_y, branch_y],
            color=COLORS["trans_line"], lw=1.2)
    ax.annotate("", xy=(3.0, step_positions[4][1] + step_radius),
                xytext=(3.0, branch_y),
                arrowprops=dict(**arrow_kw))
    ax.annotate("", xy=(7.0, step_positions[5][1] + step_radius),
                xytext=(7.0, branch_y),
                arrowprops=dict(**arrow_kw))
    ax.text(2.2, branch_y, trans_labels["3→4"], va="center",
            fontsize=7, color=COLORS["ok_green"])
    ax.text(7.3, branch_y, trans_labels["3→5"], va="center",
            fontsize=7, color=COLORS["nok_red"])

    # 4 → 6 et 5 → 6 (convergence OU)
    join_y = step_positions[6][1] + step_radius + 0.5
    ax.plot([3.0, 7.0], [join_y, join_y],
            color=COLORS["trans_line"], lw=1.2)
    ax.plot([3.0, 3.0], [step_positions[4][1] - step_radius, join_y],
            color=COLORS["trans_line"], lw=1.2)
    ax.plot([7.0, 7.0], [step_positions[5][1] - step_radius, join_y],
            color=COLORS["trans_line"], lw=1.2)
    ax.annotate("", xy=(5.0, step_positions[6][1] + step_radius),
                xytext=(5.0, join_y),
                arrowprops=dict(**arrow_kw))
    ax.text(3.1, (step_positions[4][1] - step_radius + join_y) / 2,
            trans_labels["4→6"], va="center", fontsize=7, color=COLORS["trans_line"])
    ax.text(6.05, (step_positions[5][1] - step_radius + join_y) / 2,
            trans_labels["5→6"], va="center", fontsize=7, color=COLORS["trans_line"])

    # 6 → 1 (retour — ligne externe)
    x_return = 8.8
    y_top    = step_positions[1][1]
    y_bot    = step_positions[6][1] - step_radius
    ax.plot([step_positions[6][0] + step_radius, x_return], [y_bot, y_bot],
            color=COLORS["trans_line"], lw=1.2, linestyle="--")
    ax.plot([x_return, x_return], [y_bot, y_top],
            color=COLORS["trans_line"], lw=1.2, linestyle="--")
    ax.annotate("", xy=(step_positions[1][0] + step_radius, y_top),
                xytext=(x_return, y_top),
                arrowprops=dict(**arrow_kw))
    ax.text(x_return + 0.1, (y_bot + y_top) / 2, trans_labels["6→1"],
            va="center", fontsize=7, color=COLORS["trans_line"])

    # Légende
    legend_elements = [
        mpatches.Patch(fc=COLORS["step_initial"], ec=COLORS["step_border"],
                       label="Étape initiale"),
        mpatches.Patch(fc=COLORS["step_inactive"], ec=COLORS["step_border"],
                       label="Étape"),
        plt.Line2D([0], [0], color=COLORS["ok_green"], lw=1.5,
                   label="Branche conforme"),
        plt.Line2D([0], [0], color=COLORS["nok_red"], lw=1.5,
                   label="Branche rebut"),
        plt.Line2D([0], [0], color=COLORS["trans_line"], lw=1.5,
                   linestyle="--", label="Retour cycle"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=7.5,
              framealpha=0.9, edgecolor=COLORS["grid"])


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 : Résultats de simulation
# ─────────────────────────────────────────────────────────────────────────────

def plot_simulation_results(history: list, stats: dict, dt: float = 0.1):
    """
    Génère les graphes de résultats de simulation :
      - Timeline des étapes actives (diagramme de Gantt industriel)
      - État des actionneurs au fil du temps
      - État des capteurs au fil du temps
      - Camembert de production (OK / NOK)
    """
    if not history:
        print("[Visualizer] Aucune donnée à afficher.")
        return

    times = [h["time"] for h in history]
    n     = len(times)

    # ── Extraction des données ────────────────────────────────────────────────
    step_ids   = list(range(7))
    step_names = [
        "Init", "Attente pièce", "Transport",
        "Contrôle", "Conforme", "Éjection", "Fin cycle"
    ]
    step_active = np.zeros((7, n), dtype=float)
    for i, h in enumerate(history):
        for sid in h["active_steps"]:
            if 0 <= sid < 7:
                step_active[sid, i] = 1.0

    outputs_to_plot = [
        ("M1",    "Convoyeur M1",   COLORS["motor"]),
        ("V1",    "Vérin OK (V1)",  COLORS["ok_green"]),
        ("V2",    "Vérin NOK (V2)", COLORS["nok_red"]),
        ("L_OK",  "Voyant vert",    COLORS["ok_green"]),
        ("L_NOK", "Voyant rouge",   COLORS["nok_red"]),
    ]
    inputs_to_plot = [
        ("S1", "S1 - Entrée",    COLORS["sensor"]),
        ("S2", "S2 - Station",   "#1976D2"),
        ("S3", "S3 - Qualité",   "#7B1FA2"),
    ]

    # ── Mise en page ──────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(16, 10), facecolor=COLORS["bg"])
    fig.suptitle(
        "Simulation Grafcet — Convoyeur de tri industriel",
        fontsize=14, fontweight="bold", color=COLORS["text"], y=0.98
    )
    gs = gridspec.GridSpec(4, 2, figure=fig,
                           hspace=0.55, wspace=0.3,
                           left=0.07, right=0.97, top=0.93, bottom=0.07)

    ax_steps   = fig.add_subplot(gs[0, :])   # timeline étapes — pleine largeur
    ax_outputs = fig.add_subplot(gs[1, :])   # actionneurs
    ax_inputs  = fig.add_subplot(gs[2, :])   # capteurs
    ax_pie     = fig.add_subplot(gs[3, 0])   # camembert production
    ax_kpi     = fig.add_subplot(gs[3, 1])   # KPI textuels

    def style_ax(ax, title):
        ax.set_facecolor(COLORS["bg"])
        ax.grid(True, axis="y", color=COLORS["grid"], lw=0.5)
        ax.grid(True, axis="x", color=COLORS["grid"], lw=0.3, alpha=0.5)
        ax.set_title(title, fontsize=10, color=COLORS["text"], pad=4)
        ax.tick_params(labelsize=8, colors=COLORS["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["grid"])

    # ── Timeline étapes ───────────────────────────────────────────────────────
    style_ax(ax_steps, "Étapes actives (timeline)")
    step_colors = [
        "#90A4AE", "#2196F3", "#FF9800",
        "#9C27B0", "#4CAF50", "#F44336", "#607D8B"
    ]
    for sid in step_ids:
        ax_steps.fill_between(
            times, sid - 0.35, sid + 0.35,
            where=(step_active[sid] > 0.5),
            color=step_colors[sid], alpha=0.85, step="post"
        )
    ax_steps.set_yticks(step_ids)
    ax_steps.set_yticklabels(
        [f"Ét. {sid} — {step_names[sid]}" for sid in step_ids],
        fontsize=8
    )
    ax_steps.set_xlabel("Temps simulé (s)", fontsize=9)
    ax_steps.set_xlim(0, max(times))

    # ── Actionneurs ───────────────────────────────────────────────────────────
    style_ax(ax_outputs, "État des actionneurs (sorties)")
    for i, (key, label, color) in enumerate(outputs_to_plot):
        vals = np.array([h["outputs"].get(key, False) for h in history], dtype=float)
        ax_outputs.fill_between(
            times, i - 0.3, np.where(vals > 0, i + 0.3, i - 0.3),
            color=color, alpha=0.75, step="post"
        )
    ax_outputs.set_yticks(range(len(outputs_to_plot)))
    ax_outputs.set_yticklabels(
        [lbl for _, lbl, _ in outputs_to_plot], fontsize=8
    )
    ax_outputs.set_xlabel("Temps simulé (s)", fontsize=9)
    ax_outputs.set_xlim(0, max(times))

    # ── Capteurs ──────────────────────────────────────────────────────────────
    style_ax(ax_inputs, "État des capteurs (entrées)")
    for i, (key, label, color) in enumerate(inputs_to_plot):
        vals = np.array([h["inputs"].get(key, False) for h in history], dtype=float)
        ax_inputs.fill_between(
            times, i - 0.3, np.where(vals > 0, i + 0.3, i - 0.3),
            color=color, alpha=0.75, step="post"
        )
    ax_inputs.set_yticks(range(len(inputs_to_plot)))
    ax_inputs.set_yticklabels(
        [lbl for _, lbl, _ in inputs_to_plot], fontsize=8
    )
    ax_inputs.set_xlabel("Temps simulé (s)", fontsize=9)
    ax_inputs.set_xlim(0, max(times))

    # ── Camembert production ──────────────────────────────────────────────────
    ax_pie.set_facecolor(COLORS["bg"])
    ax_pie.set_title("Bilan de production", fontsize=10,
                     color=COLORS["text"], pad=4)
    total = stats.get("total", 0)
    ok    = stats.get("ok",    0)
    nok   = stats.get("nok",   0)
    if total > 0:
        wedge_props = dict(width=0.5, edgecolor="white", linewidth=1.5)
        ax_pie.pie(
            [ok, nok],
            labels=[f"Conformes\n{ok}", f"Rebuts\n{nok}"],
            colors=[COLORS["ok_green"], COLORS["nok_red"]],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=wedge_props,
            textprops={"fontsize": 9, "color": COLORS["text"]},
        )
    else:
        ax_pie.text(0.5, 0.5, "Aucune pièce traitée",
                    ha="center", va="center", transform=ax_pie.transAxes,
                    fontsize=9, color="gray")

    # ── KPI textuels ──────────────────────────────────────────────────────────
    ax_kpi.set_facecolor(COLORS["bg"])
    ax_kpi.axis("off")
    ax_kpi.set_title("Indicateurs clés (KPI)", fontsize=10,
                     color=COLORS["text"], pad=4)
    kpi_lines = [
        ("Durée simulée",  f"{max(times):.1f} s"),
        ("Cycles Grafcet", str(len(history))),
        ("Pièces traitées", str(total)),
        ("Taux conformité",
         f"{ok/max(total,1)*100:.1f} %"),
        ("Taux rebuts",
         f"{nok/max(total,1)*100:.1f} %"),
        ("Pièces/min (sim.)",
         f"{total / max(max(times), 1) * 60:.1f}"),
    ]
    y_pos = 0.88
    for label, value in kpi_lines:
        ax_kpi.text(0.05, y_pos, label + " :", fontsize=10,
                    color="#546E7A", va="top")
        ax_kpi.text(0.65, y_pos, value, fontsize=11, fontweight="bold",
                    color=COLORS["text"], va="top")
        y_pos -= 0.14

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Fonction principale d'affichage
# ─────────────────────────────────────────────────────────────────────────────

def show_all(history: list, stats: dict, dt: float = 0.1):
    """
    Affiche les deux figures (schéma Grafcet + résultats simulation).
    """
    # Figure 1 : Schéma Grafcet
    fig1, ax1 = plt.subplots(figsize=(8, 12), facecolor=COLORS["bg"])
    fig1.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.02)
    draw_grafcet_diagram(ax1)

    # Figure 2 : Résultats simulation
    fig2 = plot_simulation_results(history, stats, dt=dt)

    plt.show()
