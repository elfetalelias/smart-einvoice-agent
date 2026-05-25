from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class LigneFacture(BaseModel):
    description: str
    quantite: float
    prix_unitaire: float
    montant_ht: float
    taux_tva: float


class InvoiceData(BaseModel):
    fournisseur: str = Field(description="Nom du fournisseur")
    numero_facture: str = Field(description="Numéro de la facture")
    date_facture: str = Field(description="Date de la facture (DD/MM/YYYY)")
    ice: Optional[str] = Field(default=None, description="ICE du fournisseur")
    if_fournisseur: Optional[str] = Field(default=None, description="IF du fournisseur")
    montant_ht: float = Field(description="Montant hors taxes")
    taux_tva: float = Field(description="Taux de TVA appliqué (%)")
    montant_tva: float = Field(description="Montant de la TVA")
    montant_ttc: float = Field(description="Montant toutes taxes comprises")
    devise: str = Field(default="MAD", description="Devise")
    lignes_facture: List[LigneFacture] = Field(default_factory=list)
    score_confiance: float = Field(ge=0.0, le=1.0, description="Score de confiance 0-1")
    champs_manquants: List[str] = Field(default_factory=list)
