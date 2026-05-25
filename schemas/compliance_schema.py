from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from enum import Enum


class NiveauAvertissement(str, Enum):
    CRITIQUE = "critique"
    MAJEUR = "majeur"
    MINEUR = "mineur"


class Avertissement(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    code: str = Field(description="Code ex: TVA_INCOHERENTE")
    message: str = Field(description="Message en français")
    niveau: NiveauAvertissement
    reference_legale: Optional[str] = Field(default=None)


class ComplianceResult(BaseModel):
    conforme: bool
    avertissements: List[Avertissement] = Field(default_factory=list)
    references_rag: List[str] = Field(default_factory=list)
    score_conformite: float = Field(ge=0.0, le=1.0)
    resume: str
