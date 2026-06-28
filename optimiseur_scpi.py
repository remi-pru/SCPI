#!/usr/bin/env python3
"""
Optimisateur d'allocation de portefeuille SCPI
===============================================
Minimise le montant non investi résiduel sous contraintes d'intégrité
(parts entières) et de poids (±2 % par rapport au poids cible).

Méthodes disponibles (par ordre de priorité) :
  1. PuLP + solveur CBC     — ILP exact, recommandé (pip install pulp)
  2. scipy.optimize.milp    — ILP exact, scipy ≥ 1.7 (pip install scipy)
  3. Force brute itérative  — exhaustive sur ~1,85 M combinaisons, quelques secondes
"""

import math
import sys
import time
from itertools import product as iproduct

# ============================================================
# 1. DONNÉES INITIALES
# ============================================================
SCPIS = [
    {"nom": "Alta Convictions", "valeur": 17_558.0, "parts": 57, "poids_cible": 17.6},
    {"nom": "ActivImmo",        "valeur": 12_199.0, "parts": 19, "poids_cible": 12.2},
    {"nom": "Cœur de Régions",  "valeur": 23_898.0, "parts": 35, "poids_cible": 23.9},
    {"nom": "Cristal Life",     "valeur": 12_689.0, "parts": 61, "poids_cible": 12.7},
    {"nom": "Cristal Rente",    "valeur": 13_809.0, "parts": 54, "poids_cible": 13.8},
    {"nom": "Sofidynamic",      "valeur": 19_848.0, "parts": 63, "poids_cible": 19.9},
]
MONTANT_NON_INVESTI_INITIAL = 1_274.0
TOLERANCE = 2.0  # ± 2 % autorisés autour du poids cible

# ============================================================
# 2. CALCUL DES DONNÉES DÉRIVÉES (ÉTAPE 1)
# ============================================================
for s in SCPIS:
    s["prix_part"] = s["valeur"] / s["parts"]

BUDGET_TOTAL = sum(s["valeur"] for s in SCPIS) + MONTANT_NON_INVESTI_INITIAL
N = len(SCPIS)


def calculer_bornes() -> list[tuple[int, int]]:
    """
    Retourne pour chaque SCPI le couple (n_min, n_max) de parts entières
    compatibles avec la contrainte de poids ±TOLERANCE%.
    """
    bornes = []
    for s in SCPIS:
        poids_min = (s["poids_cible"] - TOLERANCE) / 100.0
        poids_max = (s["poids_cible"] + TOLERANCE) / 100.0
        n_min = math.ceil(poids_min * BUDGET_TOTAL / s["prix_part"])
        n_max = math.floor(poids_max * BUDGET_TOTAL / s["prix_part"])
        n_min = max(n_min, 0)
        bornes.append((n_min, n_max))
    return bornes


# ============================================================
# 3. AFFICHAGE
# ============================================================
SEP = "─" * 82

def afficher_entete(bornes: list[tuple[int, int]]) -> None:
    print("\n" + "═" * 82)
    print("  OPTIMISATEUR D'ALLOCATION SCPI  —  Minimisation du résiduel non investi")
    print("═" * 82)
    print(f"\n  {'SCPI':<20} │ {'Prix/part':>10} │ {'Parts':>5} │ {'Valeur':>11} │ {'Cible':>6} │ Plage parts")
    print("  " + SEP)
    for i, s in enumerate(SCPIS):
        b_min, b_max = bornes[i]
        print(
            f"  {s['nom']:<20} │ {s['prix_part']:>9.2f}€ │ {s['parts']:>5} │ "
            f"{s['valeur']:>10,.0f}€ │ {s['poids_cible']:>5.1f}% │ [{b_min} … {b_max}]"
        )
    print("  " + SEP)
    nb = 1
    for b_min, b_max in bornes:
        nb *= b_max - b_min + 1
    print(f"\n  Budget total : {BUDGET_TOTAL:>12,.2f} €   |   Espace de recherche : {nb:,} combinaisons")


def afficher_resultat(nouvelles_parts: list[int], methode: str, duree: float) -> None:
    valeurs = [nouvelles_parts[i] * SCPIS[i]["prix_part"] for i in range(N)]
    total_investi = sum(valeurs)
    residuel = BUDGET_TOTAL - total_investi

    print("\n" + "═" * 82)
    print(f"  RÉSULTAT OPTIMAL  ({methode}  |  {duree:.2f}s)")
    print("═" * 82)
    print(f"\n  {'SCPI':<20} │ {'Init':>5} │ {'Delta':>6} │ {'Final':>6} │ {'Valeur':>11} │ {'Poids':>7} │ {'Écart':>7}")
    print("  " + SEP)
    for i, s in enumerate(SCPIS):
        delta = nouvelles_parts[i] - s["parts"]
        poids_f = valeurs[i] / BUDGET_TOTAL * 100
        ecart = poids_f - s["poids_cible"]
        delta_str = f"+{delta}" if delta > 0 else (str(delta) if delta < 0 else "    0")
        print(
            f"  {s['nom']:<20} │ {s['parts']:>5} │ {delta_str:>6} │ {nouvelles_parts[i]:>6} │ "
            f"{valeurs[i]:>10,.0f}€ │ {poids_f:>6.2f}% │ {ecart:>+6.2f}%"
        )
    print("  " + SEP)
    print(f"\n  Budget total           : {BUDGET_TOTAL:>12,.2f} €")
    print(f"  Total investi          : {total_investi:>12,.2f} €")
    print(f"  ★ Résiduel non investi : {residuel:>12,.2f} €")

    # Vérification des contraintes
    print("\n  Vérification des contraintes de poids :")
    all_ok = True
    for i, s in enumerate(SCPIS):
        poids_f = valeurs[i] / BUDGET_TOTAL * 100
        ok = abs(poids_f - s["poids_cible"]) <= TOLERANCE + 1e-6
        tag = "✓" if ok else "✗ VIOLATION"
        if not ok:
            all_ok = False
        lb = s["poids_cible"] - TOLERANCE
        ub = s["poids_cible"] + TOLERANCE
        print(f"    {s['nom']:<20} : {poids_f:.2f}%  ∈  [{lb:.1f}%, {ub:.1f}%]  {tag}")
    print()
    if all_ok:
        print("  ✓  Toutes les contraintes de poids sont respectées.")
    else:
        print("  ✗  Certaines contraintes sont violées — vérifiez les bornes.")


# ============================================================
# 4. MÉTHODE A : ILP via PuLP  (pip install pulp)
# ============================================================
def resoudre_pulp(bornes: list[tuple[int, int]]) -> list[int] | None:
    import pulp  # noqa: PLC0415

    prob = pulp.LpProblem("SCPI_Allocation", pulp.LpMaximize)

    n_vars = [
        pulp.LpVariable(f"n_{i}", lowBound=bornes[i][0], upBound=bornes[i][1], cat="Integer")
        for i in range(N)
    ]
    total_investi = pulp.lpSum(n_vars[i] * SCPIS[i]["prix_part"] for i in range(N))

    prob += total_investi                   # Objectif : maximiser le montant investi
    prob += total_investi <= BUDGET_TOTAL   # Contrainte budgétaire

    # Contraintes de poids (redondantes avec les bornes, mais explicites pour la lisibilité)
    for i, s in enumerate(SCPIS):
        pmin = (s["poids_cible"] - TOLERANCE) / 100.0 * BUDGET_TOTAL
        pmax = (s["poids_cible"] + TOLERANCE) / 100.0 * BUDGET_TOTAL
        prob += n_vars[i] * s["prix_part"] >= pmin
        prob += n_vars[i] * s["prix_part"] <= pmax

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        return [int(round(pulp.value(n_vars[i]))) for i in range(N)]
    return None


# ============================================================
# 5. MÉTHODE B : ILP via scipy.optimize.milp  (scipy ≥ 1.7)
# ============================================================
def resoudre_scipy(bornes: list[tuple[int, int]]) -> list[int] | None:
    from scipy.optimize import LinearConstraint, milp, Bounds  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    prix = np.array([s["prix_part"] for s in SCPIS])

    # On minimise le négatif du total investi (= maximiser)
    c = -prix

    # Contrainte budgétaire : sum(n_i * prix_i) <= BUDGET_TOTAL
    A = prix.reshape(1, -1)
    contraintes = LinearConstraint(A, -np.inf, BUDGET_TOTAL)

    lb = np.array([b[0] for b in bornes], dtype=float)
    ub = np.array([b[1] for b in bornes], dtype=float)
    bounds = Bounds(lb=lb, ub=ub)

    integrality = np.ones(N)  # toutes les variables sont entières

    res = milp(c, constraints=contraintes, integrality=integrality, bounds=bounds)

    if res.success:
        return [int(round(x)) for x in res.x]
    return None


# ============================================================
# 6. MÉTHODE C : Force brute exhaustive (fallback garanti)
# ============================================================
def resoudre_force_brute(bornes: list[tuple[int, int]]) -> list[int] | None:
    """
    Parcourt toutes les combinaisons entières valides dans les plages de parts
    et retient celle qui maximise le montant investi sans dépasser le budget.
    Environ 1,85 M combinaisons pour les données fournies.
    """
    prix = [s["prix_part"] for s in SCPIS]
    meilleur_total = -1.0
    meilleures_parts: tuple | None = None

    ranges = [range(b[0], b[1] + 1) for b in bornes]

    for combo in iproduct(*ranges):
        total = sum(combo[i] * prix[i] for i in range(N))
        if total <= BUDGET_TOTAL and total > meilleur_total:
            meilleur_total = total
            meilleures_parts = combo

    return list(meilleures_parts) if meilleures_parts is not None else None


# ============================================================
# 7. PROGRAMME PRINCIPAL
# ============================================================
def main() -> None:
    bornes = calculer_bornes()
    afficher_entete(bornes)

    stratégies = [
        ("PuLP / CBC",          resoudre_pulp,         "pulp"),
        ("scipy.optimize.milp", resoudre_scipy,        "scipy"),
        ("Force brute",         resoudre_force_brute,  None),
    ]

    for nom_methode, fn, module in stratégies:
        if module:
            try:
                __import__(module)
            except ImportError:
                print(f"\n  [{nom_methode}] module '{module}' absent — ignoré.")
                continue

        print(f"\n  Résolution en cours : {nom_methode} …")
        t0 = time.perf_counter()
        try:
            solution = fn(bornes)
        except Exception as e:
            print(f"  Erreur : {e}")
            continue
        duree = time.perf_counter() - t0

        if solution is not None:
            afficher_resultat(solution, nom_methode, duree)
            return

        print(f"  [{nom_methode}] Aucune solution trouvée (durée : {duree:.2f}s).")

    print("\n  Aucune solution n'a été trouvée. Vérifiez les données ou élargissez la tolérance.")
    sys.exit(1)


if __name__ == "__main__":
    main()
