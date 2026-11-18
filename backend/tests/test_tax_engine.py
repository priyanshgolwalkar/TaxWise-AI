import pytest
from app.services.tax_engine import TaxRuleError, calculate_tax, compare_regimes
from app.services.tax_engine.calculator import slab_tax
from app.services.tax_engine.rules import RULES

def base(): return {'assessment_year':'2025-26','annual_income':1850000,'standard_deduction':75000,'deductions_80c':100000,'deductions_80d':25000,'home_loan_interest':0,'hra_exemption':0}
def test_tax_is_deterministic():
    assert calculate_tax(base(), 'new') == calculate_tax(base(), 'new')
def test_old_regime_uses_capped_deductions():
    data = base(); data.update({'deductions_80c': 500000, 'deductions_80d': 100000, 'home_loan_interest': 300000})
    result = calculate_tax(data, 'old')
    assert result['deductions'] == 475000
    assert result['deduction_breakdown']['deductions_80c'] == 150000
    assert result['deduction_breakdown']['deductions_80d'] == 75000
    assert result['deduction_breakdown']['home_loan_interest'] == 200000
    assert result['deduction_breakdown']['standard_deduction'] == 50000

def test_new_regime_does_not_apply_old_regime_deductions():
    data = base(); data['deductions_80c'] = 150000; data['home_loan_interest'] = 200000
    result = calculate_tax(data, 'new')
    assert result['deductions'] == 75000
    assert 'deductions_80c' not in result['deduction_breakdown']
def test_compare_returns_recommendation():
    result = compare_regimes(base())
    assert result['recommended_regime'] in {'old', 'new'}
    assert result['estimated_savings'] >= 0
def test_low_income_rebate_applies():
    data = base(); data['annual_income'] = 450000
    assert calculate_tax(data, 'old')['rebate'] > 0

def test_slab_tax_is_continuous_at_configured_bracket_boundaries():
    new_slabs = RULES['2025-26']['new'].slabs
    assert slab_tax(400000, new_slabs) == 20000
    assert slab_tax(400001, new_slabs) == pytest.approx(20000.1)
    assert slab_tax(800000, new_slabs) == 60000
    assert slab_tax(800001, new_slabs) == pytest.approx(60000.15)

@pytest.mark.parametrize('assessment_year,regime', [('2024-25', 'old'), ('2025-26', 'invalid')])
def test_missing_rules_fail_with_actionable_error(assessment_year, regime):
    data = base(); data['assessment_year'] = assessment_year
    with pytest.raises(TaxRuleError):
        calculate_tax(data, regime)
