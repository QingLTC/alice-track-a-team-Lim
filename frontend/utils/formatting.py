"""Small display helpers so numbers look the same everywhere."""


def mw(x):
    return "-" if x is None else f"{x:,.0f} MW"


def pct(x):
    return "-" if x is None else f"{x:.2f} %"


def eur(x):
    return "-" if x is None else f"EUR {x:,.0f}"


def tco2(x):
    """kgCO2e -> tonnes, for readability."""
    return "-" if x is None else f"{x/1000:,.0f} tCO2e"
