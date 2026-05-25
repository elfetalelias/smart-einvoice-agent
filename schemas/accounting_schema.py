from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SensEcriture(str, Enum):
    DEBIT = "Débit"
    CREDIT = "Crédit"


class CodeAlternatif(BaseModel):
    code: str
    libelle: str
    score: float


class AccountingCode(BaseModel):
    code_comptable: str = Field(description="Code PCM ex: 6125")
    libelle_compte: str = Field(description="Libellé du compte")
    justification: str = Field(description="Explication en français")
    score_confiance: float = Field(ge=0.0, le=1.0)
    validation_humaine_requise: bool
    alternatives: List[CodeAlternatif] = Field(default_factory=list)


class LigneEcriture(BaseModel):
    sens: SensEcriture
    compte: str
    libelle: str
    montant: float

    class Config:
        use_enum_values = True


class JournalEntry(BaseModel):
    date_ecriture: str
    reference: str
    ecritures: List[LigneEcriture]
    equilibre: bool
    avertissement: Optional[str] = None
