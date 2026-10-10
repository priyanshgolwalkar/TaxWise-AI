from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.planning import RecommendationRecord, Report, TaxCalculationRecord
from app.models.user import User


def generate_report(user: User, db: Session) -> dict:
    calculation = db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).first()
    recommendation = db.query(RecommendationRecord).filter(RecommendationRecord.user_id == user.id).order_by(RecommendationRecord.created_at.desc()).first()
    if calculation is None:
        raise ValueError('Create a tax calculation before generating a report')
    comparison = calculation.comparison
    content = {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'assessment_year': calculation.assessment_year,
        'income_summary': calculation.input_data,
        'deduction_summary': comparison.get('old_regime', {}).get('deduction_breakdown', {}),
        'old_regime': comparison.get('old_regime'),
        'new_regime': comparison.get('new_regime'),
        'regime_comparison': comparison,
        'recommended_regime': comparison.get('recommended_regime'),
        'potential_savings': comparison.get('estimated_savings'),
        'recommendations': recommendation.recommendations if recommendation else None,
        'document_count': db.query(Document).filter(Document.user_id == user.id).count(),
        'disclaimer': 'This report is an estimate for planning and education. Verify documents, eligibility, and filing positions with a qualified tax professional.',
    }
    report = Report(user_id=user.id, title=f"FY {calculation.assessment_year} Tax Planning Report", content=content, status='draft')
    db.add(report)
    db.commit()
    db.refresh(report)
    return serialize_report(report)


def serialize_report(report: Report) -> dict:
    return {'id': report.id, 'title': report.title, 'status': report.status, 'content': report.content, 'created_at': report.created_at}
