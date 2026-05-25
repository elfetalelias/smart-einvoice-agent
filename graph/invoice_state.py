from typing import TypedDict, Optional, Literal, List, Dict, Any
from schemas.invoice_schema import InvoiceData
from schemas.compliance_schema import ComplianceResult
from schemas.accounting_schema import AccountingCode, JournalEntry


class ValidationHumaine(TypedDict):
    decision: Literal["accepté", "modifié", "rejeté", "confirmé", "ignoré", "corrigé"]
    commentaire: Optional[str]
    modifications: Optional[Dict[str, Any]]


class InvoiceState(TypedDict):
    # Fichier source
    fichier_path: str
    fichier_type: Literal["pdf", "xml"]
    fichier_nom: str

    # Statut du workflow
    statut: str
    etape_courante: str
    erreur: Optional[str]

    # Données extraites
    donnees_extraites: Optional[InvoiceData]
    validation_extraction: Optional[ValidationHumaine]

    # Conformité
    resultat_conformite: Optional[ComplianceResult]
    validation_conformite: Optional[ValidationHumaine]

    # Classification comptable
    code_comptable: Optional[AccountingCode]
    validation_classification: Optional[ValidationHumaine]

    # Écriture comptable
    ecriture_comptable: Optional[JournalEntry]

    # Rapport final
    rapport_final: Optional[str]
    rapport_genere: bool

    # Contexte RAG utilisé
    contexte_rag: List[str]

    # Historique des décisions humaines
    historique_validations: List[ValidationHumaine]
