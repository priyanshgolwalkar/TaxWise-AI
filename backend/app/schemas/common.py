from typing import Literal
from pydantic import BaseModel, Field

class TaxInput(BaseModel):
    assessment_year: str = '2025-26'
    annual_income: float = Field(ge=0)
    standard_deduction: float = Field(default=75000, ge=0)
    deductions_80c: float = Field(default=0, ge=0)
    deductions_80d: float = Field(default=0, ge=0)
    home_loan_interest: float = Field(default=0, ge=0)
    hra_exemption: float = Field(default=0, ge=0)

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None

class RecommendationRequest(TaxInput):
    regime: Literal['old', 'new'] = 'old'
    profile: dict = Field(default_factory=dict)
    tax_result: dict | None = None
