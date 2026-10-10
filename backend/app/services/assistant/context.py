from sqlalchemy.orm import Session
from app.models.document import Document, ExtractedFinancialData
from app.models.planning import RecommendationRecord, TaxCalculationRecord
from app.models.user import User
from .retrieval import EmptyKnowledgeRetriever, KnowledgeRetriever

class AssistantContextBuilder:
    def __init__(self, retriever: KnowledgeRetriever | None = None):
        self.retriever = retriever or EmptyKnowledgeRetriever()

    def build(self, db: Session, user: User, question: str) -> tuple[dict, list[dict]]:
        calculation = db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).first()
        recommendation = db.query(RecommendationRecord).filter(RecommendationRecord.user_id == user.id).order_by(RecommendationRecord.created_at.desc()).first()
        documents = db.query(Document, ExtractedFinancialData).outerjoin(ExtractedFinancialData, ExtractedFinancialData.document_id == Document.id).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).limit(10).all()
        comparison = calculation.comparison if calculation else None
        context = {
            'user_profile': {'name': user.name},
            'assessment_year': calculation.assessment_year if calculation else None,
            'financial_inputs': calculation.input_data if calculation else None,
            'tax_engine_result': {
                'old_regime_tax': comparison.get('old_regime', {}).get('final_liability'),
                'new_regime_tax': comparison.get('new_regime', {}).get('final_liability'),
                'old_regime': comparison.get('old_regime'),
                'new_regime': comparison.get('new_regime'),
                'potential_difference': comparison.get('estimated_savings'),
                'recommended_regime': comparison.get('recommended_regime'),
            } if comparison else None,
            'recommendations': recommendation.recommendations if recommendation else None,
            'documents': [
                {'filename': document.filename, 'status': document.status,
                 'missing_fields': extracted.missing_fields if extracted else [],
                 'verification_required': extracted.requires_user_verification if extracted else True}
                for document, extracted in documents
            ],
        }
        sources = self.retriever.retrieve(question, user.id)
        context['retrieved_knowledge'] = sources
        return context, sources
