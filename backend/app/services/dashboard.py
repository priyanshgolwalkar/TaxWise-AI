from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.planning import RecommendationRecord, TaxCalculationRecord
from app.models.user import User


def build_dashboard(user: User, db: Session) -> dict:
    calculation = db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).first()
    recommendation = db.query(RecommendationRecord).filter(RecommendationRecord.user_id == user.id).order_by(RecommendationRecord.created_at.desc()).first()
    documents = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    comparison = calculation.comparison if calculation else None
    recommended = comparison.get('recommended_regime') if comparison else None
    recent_activity = []
    if calculation:
        recent_activity.append({'type': 'tax_calculation', 'label': 'Tax comparison completed', 'created_at': calculation.created_at, 'record_id': calculation.id})
    if recommendation:
        recent_activity.append({'type': 'recommendation', 'label': 'Recommendations generated', 'created_at': recommendation.created_at, 'record_id': recommendation.id})
    recent_activity.extend({'type': 'document', 'label': f'Document uploaded: {item.filename}', 'created_at': item.created_at, 'record_id': item.id} for item in documents[:5])
    recent_activity.sort(key=lambda item: item['created_at'] or '', reverse=True)
    return {
        'user_profile': {'name': user.name},
        'summary': {
            'estimated_tax': comparison.get(f'{recommended}_regime', {}).get('final_liability') if comparison and recommended else None,
            'recommended_regime': recommended,
            'old_regime_tax': comparison.get('old_regime', {}).get('final_liability') if comparison else None,
            'new_regime_tax': comparison.get('new_regime', {}).get('final_liability') if comparison else None,
            'potential_savings': comparison.get('estimated_savings') if comparison else None,
            'total_documents': len(documents),
            'documents_needing_verification': sum(1 for item in documents if item.status == 'needs_review'),
        },
        'latest_tax_calculation': {'id': calculation.id, 'assessment_year': calculation.assessment_year, 'input_data': calculation.input_data, 'comparison': comparison, 'created_at': calculation.created_at} if calculation else None,
        'document_summary': [{'id': item.id, 'filename': item.filename, 'status': item.status, 'content_type': item.content_type, 'created_at': item.created_at} for item in documents[:10]],
        'recommendations': recommendation.recommendations if recommendation else None,
        'recent_activity': recent_activity[:10],
    }
