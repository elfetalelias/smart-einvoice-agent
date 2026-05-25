"""Tests unitaires — Agent Classificateur Comptable"""
import pytest
from schemas.accounting_schema import AccountingCode, JournalEntry, LigneEcriture, SensEcriture, CodeAlternatif


class TestAccountingCodeSchema:
    def test_code_haute_confiance(self):
        code = AccountingCode(
            code_comptable="6125",
            libelle_compte="Achats non stockés de matières",
            justification="Fournitures de bureau selon PCM classe 6",
            score_confiance=0.92,
            validation_humaine_requise=False,
        )
        assert code.code_comptable == "6125"
        assert code.validation_humaine_requise is False

    def test_code_faible_confiance_requiert_validation(self):
        code = AccountingCode(
            code_comptable="6149",
            libelle_compte="Autres charges externes",
            justification="Nature ambiguë",
            score_confiance=0.55,
            validation_humaine_requise=True,
            alternatives=[
                CodeAlternatif(code="6125", libelle="Fournitures", score=0.45),
            ],
        )
        assert code.validation_humaine_requise is True
        assert len(code.alternatives) == 1


class TestJournalEntry:
    def _make_valid_entry(self) -> JournalEntry:
        return JournalEntry(
            date_ecriture="15/03/2024",
            reference="FAC-2024-0047",
            ecritures=[
                LigneEcriture(sens=SensEcriture.DEBIT, compte="6125",
                              libelle="Fournitures de bureau", montant=1060.00),
                LigneEcriture(sens=SensEcriture.DEBIT, compte="3455",
                              libelle="TVA récupérable", montant=212.00),
                LigneEcriture(sens=SensEcriture.CREDIT, compte="4411",
                              libelle="Fournisseurs", montant=1272.00),
            ],
            equilibre=True,
        )

    def test_ecriture_equilibree(self):
        entry = self._make_valid_entry()
        total_debit = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.DEBIT)
        total_credit = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.CREDIT)
        assert abs(total_debit - total_credit) < 0.01
        assert entry.equilibre is True

    def test_ecriture_trois_lignes(self):
        entry = self._make_valid_entry()
        assert len(entry.ecritures) == 3

    def test_comptes_obligatoires(self):
        entry = self._make_valid_entry()
        comptes = [l.compte for l in entry.ecritures]
        assert "3455" in comptes
        assert "4411" in comptes
