"""
GO / MARGINAL / KILL decision framework for use case prioritisation.
"""

from dataclasses import dataclass


@dataclass
class Decision:
    label: str          # "GO", "MARGINAL", "KILL"
    p_viable: float     # probability of viability
    reasoning: str      # short explanation


def decide(p_viable: float, gross_margin_median: float,
           go_threshold: float = 0.60, marginal_threshold: float = 0.30,
           incumbent_type: str = "standard") -> Decision:
    """Determine GO/MARGINAL/KILL for a use case.

    For standard use cases: P(customer_saving >= required_margin) >= go_threshold
    For greenfield use cases: P(positive NPV) is used instead.
    """
    if incumbent_type == "greenfield":
        # Greenfield: no incumbent to beat, just need positive economics
        if p_viable >= 0.50 and gross_margin_median > 0:
            return Decision("GO", p_viable, "Positive NPV in majority of simulations")
        elif p_viable >= 0.25:
            return Decision("MARGINAL", p_viable, "Some simulations show positive NPV")
        else:
            return Decision("KILL", p_viable, "Negative NPV in most simulations")
    else:
        # Standard: must beat incumbent by required margin
        if p_viable >= go_threshold:
            return Decision("GO", p_viable, f"P(viable)={p_viable:.0%} >= {go_threshold:.0%}")
        elif p_viable >= marginal_threshold:
            return Decision("MARGINAL", p_viable,
                            f"P(viable)={p_viable:.0%} between {marginal_threshold:.0%} and {go_threshold:.0%}")
        else:
            return Decision("KILL", p_viable,
                            f"P(viable)={p_viable:.0%} < {marginal_threshold:.0%}")
