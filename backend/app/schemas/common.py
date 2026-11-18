from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class TaxInput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    assessment_year: str = Field(default='2025-26', min_length=1, max_length=20)
    annual_income: float = Field(ge=0)
    standard_deduction: float = Field(
        default=75000,
        ge=0,
        exclude=True,
        description='Legacy input retained for compatibility; the active tax rules determine this deduction.',
    )
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
