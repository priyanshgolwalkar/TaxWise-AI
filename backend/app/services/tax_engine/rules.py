from dataclasses import dataclass
@dataclass(frozen=True)
class RegimeRules:
    standard_deduction: float
    rebate_limit: float
    rebate_amount: float
    slabs: tuple[tuple[float, float], ...]

# Replace with project-team-approved rules before production use.
RULES = {
 '2025-26': {
  'new': RegimeRules(75000, 1200000, 60000, ((400000,.05),(800000,.10),(1200000,.15),(1600000,.20),(2000000,.25),(2400000,.30))),
  'old': RegimeRules(50000, 500000, 12500, ((250000,.05),(500000,.20),(1000000,.30))),
 }
}
