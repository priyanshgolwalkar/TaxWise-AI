from .rules import RULES

class TaxRuleError(ValueError):
    """Raised when a calculation requests an unsupported configured rule set."""

def get_rules(assessment_year: str, regime: str):
    if assessment_year not in RULES:
        raise TaxRuleError(f'No tax rules configured for assessment year {assessment_year}')
    if regime not in RULES[assessment_year]:
        raise TaxRuleError(f'No {regime} regime rules configured for assessment year {assessment_year}')
    return RULES[assessment_year][regime]

def slab_tax(income: float, slabs: tuple[tuple[float, float], ...]) -> float:
    tax, lower = 0.0, 0.0
    for upper, rate in slabs:
        taxable = max(0.0, min(income, upper) - lower); tax += taxable * rate; lower = upper
        if income <= upper: break
    if income > lower: tax += (income - lower) * .30
    return tax

def calculate_tax(data: dict, regime: str) -> dict:
    rules = get_rules(data.get('assessment_year', '2025-26'), regime)
    deduction_breakdown = {'standard_deduction': rules.standard_deduction}
    if regime == 'old':
        deduction_breakdown.update({
            'deductions_80c': min(data.get('deductions_80c', 0), 150000),
            'deductions_80d': min(data.get('deductions_80d', 0), 75000),
            'home_loan_interest': min(data.get('home_loan_interest', 0), 200000),
            'hra_exemption': data.get('hra_exemption', 0),
        })
    deductions = sum(deduction_breakdown.values())
    taxable = max(0.0, data['annual_income'] - deductions)
    tax_before_rebate = slab_tax(taxable, rules.slabs)
    rebate = rules.rebate_amount if taxable <= rules.rebate_limit else 0
    tax_after_rebate = max(0.0, tax_before_rebate - rebate)
    cess = tax_after_rebate * .04
    return {'regime': regime, 'gross_income': data['annual_income'], 'deductions': deductions, 'deduction_breakdown': deduction_breakdown, 'taxable_income': taxable, 'tax_before_rebate': tax_before_rebate, 'rebate': rebate, 'tax_after_rebate': tax_after_rebate, 'cess': cess, 'final_liability': tax_after_rebate + cess}

def compare_regimes(data: dict) -> dict:
    old, new = calculate_tax(data, 'old'), calculate_tax(data, 'new')
    return {'old_regime': old, 'new_regime': new, 'recommended_regime': 'old' if old['final_liability'] < new['final_liability'] else 'new', 'estimated_savings': abs(old['final_liability'] - new['final_liability'])}
