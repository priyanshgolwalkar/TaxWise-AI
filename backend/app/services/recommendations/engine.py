from app.services.tax_engine import calculate_tax

def _impact(data: dict, field: str, additional: float) -> float:
    current = calculate_tax(data, 'old')['final_liability']
    hypothetical = {**data, field: data.get(field, 0) + additional}
    return round(max(0, current - calculate_tax(hypothetical, 'old')['final_liability']))

def get_recommendations(data: dict) -> dict:
    regime, income = data.get('regime', 'old'), data['annual_income']
    items = []
    if regime == 'old' and data.get('deductions_80c', 0) < 150000:
        gap = 150000 - data.get('deductions_80c', 0)
        items.append({'title': 'Complete Section 80C planning', 'category': 'Investments', 'priority': 'high', 'amount': gap, 'impact': _impact(data, 'deductions_80c', gap), 'applicable_regime': 'old', 'reason': 'Your old-regime 80C usage is below the configured cap.', 'explanation': 'Potential impact is estimated by comparing the deterministic engine output before and after the remaining eligible room.'})
    if regime == 'old' and data.get('deductions_80d', 0) < 75000:
        gap = 75000 - data.get('deductions_80d', 0)
        items.append({'title': 'Review health insurance cover', 'category': 'Insurance', 'priority': 'review', 'amount': gap, 'impact': _impact(data, 'deductions_80d', gap), 'applicable_regime': 'old', 'reason': 'Eligible health insurance premiums may qualify under 80D.', 'explanation': 'Confirm policy ownership, premium payment, and eligibility before treating this as a deduction.'})
    if regime == 'new':
        items.append({'title': 'Compare before investing', 'category': 'Regime planning', 'priority': 'review', 'amount': 0, 'impact': 0, 'applicable_regime': 'new', 'reason': 'Most old-regime deductions are not applied in this selected regime.', 'explanation': 'This is a planning reminder, not a deduction recommendation. Compare the saved regime results before investing for tax reasons.'})
    return {'regime': regime, 'items': items, 'explainable': True, 'source': 'deterministic tax engine and configured eligibility rules', 'note': f'Recommendations are potentially applicable for income of {income:,.0f} and require user verification.'}
