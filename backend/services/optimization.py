"""
Advanced module: energy-mix optimization.

Given a demand target (typically the forecast peak or aggregated 24 h demand),
recommend how much each source should generate to MINIMISE cost, while meeting
demand and respecting capacity, a carbon cap and a minimum renewable share.

This is a small linear program solved with PuLP. It is decision support on top
of the forecast, not a real grid dispatch model.
"""
import pulp

from config import ENERGY_SOURCES


def optimize_mix(demand: float, carbon_limit: float | None = None,
                 renewable_min: float | None = None,
                 capacities: dict | None = None) -> dict:
    """
    min  sum(cost_s * x_s)
    s.t. sum(x_s) >= demand
         0 <= x_s <= capacity_s
         sum(emissions_s * x_s) <= carbon_limit           (if given)
         sum(x_s for renewable) >= renewable_min * sum(x_s) (if given)
    """
    sources = ENERGY_SOURCES
    caps = capacities or {}

    prob = pulp.LpProblem("energy_mix", pulp.LpMinimize)
    x = {
        s: pulp.LpVariable(f"gen_{s}", lowBound=0, upBound=caps.get(s, meta["capacity"]))
        for s, meta in sources.items()
    }

    # Objective: total cost.
    prob += pulp.lpSum(meta["cost"] * x[s] for s, meta in sources.items())

    # Meet demand.
    prob += pulp.lpSum(x.values()) >= demand, "meet_demand"

    # Carbon cap.
    if carbon_limit is not None:
        prob += pulp.lpSum(meta["emissions"] * x[s] for s, meta in sources.items()) <= carbon_limit, "carbon_cap"

    # Minimum renewable share: renewable generation >= share * total generation.
    # Rearranged to stay linear: sum(renewable) - share * sum(all) >= 0.
    if renewable_min is not None:
        prob += (
            pulp.lpSum(x[s] for s, m in sources.items() if m["renewable"])
            - renewable_min * pulp.lpSum(x.values()) >= 0,
            "renewable_share",
        )

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    feasible = pulp.LpStatus[status] == "Optimal"

    if not feasible:
        return {
            "feasible": False,
            "message": _explain_infeasible(demand, carbon_limit, renewable_min, caps),
            "allocation": [], "total_cost": None,
            "total_emissions": None, "renewable_share": None,
        }

    alloc, total_gen, total_cost, total_emis, renew_gen = [], 0.0, 0.0, 0.0, 0.0
    for s, meta in sources.items():
        g = float(x[s].value() or 0.0)
        total_gen += g
        total_cost += meta["cost"] * g
        total_emis += meta["emissions"] * g
        if meta["renewable"]:
            renew_gen += g
        alloc.append({
            "source": s, "generation_mwh": round(g, 1),
            "cost": round(meta["cost"] * g, 1),
            "emissions": round(meta["emissions"] * g, 1),
            "selected": g > 1e-6,
        })

    return {
        "feasible": True,
        "message": "Optimal mix found.",
        "demand": round(demand, 1),
        "allocation": alloc,
        "total_cost": round(total_cost, 1),
        "total_emissions": round(total_emis, 1),
        "renewable_share": round(renew_gen / total_gen, 4) if total_gen else 0.0,
    }


def _explain_infeasible(demand, carbon_limit, renewable_min, caps) -> str:
    """Give a human reason instead of just 'infeasible'."""
    total_cap = sum(caps.get(s, m["capacity"]) for s, m in ENERGY_SOURCES.items())
    renew_cap = sum(caps.get(s, m["capacity"]) for s, m in ENERGY_SOURCES.items() if m["renewable"])
    reasons = []
    if demand > total_cap:
        reasons.append(f"demand ({demand:.0f} MW) exceeds total capacity ({total_cap:.0f} MW)")
    if renewable_min is not None and renewable_min * demand > renew_cap:
        reasons.append(
            f"the renewable-share floor ({renewable_min:.0%}) needs more renewable capacity "
            f"than available ({renew_cap:.0f} MW)"
        )
    if carbon_limit is not None:
        min_emis = _min_emissions_for_demand(demand, caps)
        if min_emis is not None and carbon_limit < min_emis:
            reasons.append(
                f"the carbon cap ({carbon_limit:.0f}) is below the cleanest feasible mix "
                f"(~{min_emis:.0f} kgCO2e)"
            )
    if not reasons:
        reasons.append("the combination of constraints leaves no feasible allocation")
    return "No feasible mix: " + "; ".join(reasons) + "."


def _min_emissions_for_demand(demand, caps) -> float | None:
    """Cheapest-emissions feasibility probe: minimise emissions s.t. demand + capacity."""
    prob = pulp.LpProblem("min_emissions", pulp.LpMinimize)
    x = {s: pulp.LpVariable(f"e_{s}", lowBound=0, upBound=caps.get(s, m["capacity"]))
         for s, m in ENERGY_SOURCES.items()}
    prob += pulp.lpSum(m["emissions"] * x[s] for s, m in ENERGY_SOURCES.items())
    prob += pulp.lpSum(x.values()) >= demand
    if pulp.LpStatus[prob.solve(pulp.PULP_CBC_CMD(msg=False))] != "Optimal":
        return None
    return sum(m["emissions"] * (x[s].value() or 0) for s, m in ENERGY_SOURCES.items())
