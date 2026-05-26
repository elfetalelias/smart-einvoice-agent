"""Genere le rapport PDF du projet de fin de module."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

MARINE = (0, 31, 96)


class Rapport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(
            0, 8,
            "Master SDIA  -  Prof. RETAL Sara  -  Systemes Multi-Agents FC",
            align="C",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def _reset_x(self):
        self.set_x(self.l_margin)

    def h1(self, text):
        self.ln(5)
        self._reset_x()
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*MARINE)
        self.cell(self.epw, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
        self.set_text_color(30, 30, 30)

    def h2(self, text):
        self.ln(3)
        self._reset_x()
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(40, 80, 150)
        self.cell(self.epw, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(30, 30, 30)

    def body(self, text):
        self._reset_x()
        self.set_font("Helvetica", "", 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(self.epw, 6, text)
        self.ln(2)

    def bullet(self, items):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(30, 30, 30)
        for item in items:
            self._reset_x()
            self.multi_cell(self.epw, 6, f"  - {item}")

    def code(self, text):
        self._reset_x()
        self.set_font("Courier", "", 9)
        self.set_fill_color(245, 245, 245)
        self.set_draw_color(200, 200, 200)
        self.multi_cell(self.epw, 5, text, border=1, fill=True)
        self.set_font("Helvetica", "", 11)
        self.ln(2)


pdf = Rapport()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(15, 20, 15)

# -- Page de titre --
pdf.add_page()
pdf.ln(28)
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(*MARINE)
pdf.multi_cell(
    0, 12,
    "Systeme Intelligent de Traitement\ndes Factures Electroniques",
    align="C",
)
pdf.ln(5)
pdf.set_font("Helvetica", "", 13)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(
    0, 8,
    "Systeme multi-agent LangGraph + LangChain\navec RAG multi-corpus et validation humaine",
    align="C",
)
pdf.ln(16)
pdf.set_draw_color(*MARINE)
pdf.set_line_width(0.6)
pdf.line(40, pdf.get_y(), 170, pdf.get_y())
pdf.ln(12)
pdf.set_text_color(40, 40, 40)
for label, val in [
    ("Etudiant",    "ILYASS ELFATTAL"),
    ("Filiere",     "Master SDIA"),
    ("Module",      "Systemes Multi-Agents FC"),
    ("Professeur",  "Prof. RETAL Sara"),
    ("GitHub",      "github.com/elfetalelias/smart-einvoice-agent"),
]:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 9, f"{label} :", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 9, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# -- 1. Introduction --
pdf.add_page()
pdf.h1("1. Introduction et Problematique")
pdf.body(
    "Les entreprises marocaines traitent chaque jour de nombreuses factures fournisseurs. "
    "Ce processus est encore largement manuel : verification de la conformite fiscale, "
    "classification comptable selon le Plan Comptable Marocain (PCM), saisie des ecritures "
    "Debit/Credit. Cela prend du temps et genere des erreurs.\n\n"
    "L'objectif de ce projet est d'automatiser ce traitement en construisant un systeme "
    "multi-agent intelligent qui orchestre plusieurs agents specialises, s'appuie sur un "
    "systeme RAG multi-corpus pour acceder a la legislation marocaine en vigueur, et "
    "garde le comptable humain au centre des decisions importantes."
)

pdf.h1("2. Objectifs")
pdf.bullet([
    "Extraire les donnees d'une facture (PDF, XML, image) avec un score de confiance",
    "Verifier la conformite fiscale selon le CGI 2026 et l'Article 145 (TVA, ICE, IF)",
    "Classifier la facture avec un code du Plan Comptable Marocain via RAG",
    "Generer l'ecriture comptable Debit/Credit et verifier son equilibre",
    "Integrer trois points de validation humaine obligatoires dans le workflow",
    "Produire le journal comptable final structure",
    "Interface web avec traitement batch et export Excel/CSV (bonus)",
])

# -- 2. Architecture --
pdf.h1("3. Architecture du Systeme")
pdf.body(
    "Le systeme est construit autour de six agents qui travaillent ensemble de maniere "
    "sequentielle. Un superviseur central orchestre le flux via LangGraph - il lit l'etat "
    "courant de la facture et decide quel agent appeler ensuite.\n\n"
    "L'extracteur prend en charge la lecture de la facture, que ce soit un PDF natif, "
    "un fichier XML ou une image, et produit des donnees structurees via un schema Pydantic. "
    "L'agent de conformite interroge ensuite le corpus RAG pour verifier les champs "
    "obligatoires selon l'Article 145 du CGI et la coherence de la TVA. Le classificateur "
    "comptable propose un code du Plan Comptable Marocain avec un score de confiance, "
    "toujours en s'appuyant sur le RAG. L'agent d'ecriture genere alors l'ecriture "
    "Debit/Credit en s'assurant que la somme est equilibree. Enfin, le journal comptable "
    "compile toutes les etapes traitees dans un document final."
)

pdf.h2("Workflow LangGraph (graph/invoice_graph.py)")
pdf.code(
    "  [extract_invoice]\n"
    "       |\n"
    "  [human_validation_1]  <-- Validation #1 : donnees extraites\n"
    "       |\n"
    "  [check_compliance]\n"
    "       |\n"
    "  [human_validation_2]  <-- Validation #2 : conformite fiscale\n"
    "       |\n"
    "  [classify_accounting]\n"
    "       |\n"
    "  [human_validation_3]  <-- Validation #3 : code comptable PCM\n"
    "       |\n"
    "  [generate_journal_entry]\n"
    "       |\n"
    "  [journal_comptable]  -->  END"
)
pdf.body(
    "Le choix d'une architecture hierarchique et sequentielle se justifie par la nature "
    "meme du traitement d'une facture : on ne peut pas classifier avant d'extraire, ni "
    "generer l'ecriture avant de verifier la conformite. Les trois noeuds de validation "
    "humaine bloquent le flux jusqu'a confirmation explicite de l'utilisateur."
)

# -- 3. RAG Multi-Corpus --
pdf.add_page()
pdf.h1("4. RAG Multi-Corpus")
pdf.body(
    "Le systeme utilise trois corpus vectorises avec FAISS, chacun indexe separement. "
    "Un agent RAG central (create_react_agent de langgraph.prebuilt) recoit la question, "
    "choisit lui-meme le ou les outils pertinents, recupere les passages et formule "
    "une reponse en francais. Ce routing est implicite - le choix du corpus n'est "
    "jamais code en dur dans les agents metier."
)

pdf.h2("Les trois corpus")
pdf.bullet([
    "Corpus regles fiscales (cgi-2026.pdf) - TVA, ICE, IF, taux applicables"
    "\n      Tool : search_regles_fiscales(query)",
    "Corpus normes facturation (cgi-2026.pdf + ubl_facturx.txt) - Article 145 CGI,"
    "\n      mentions obligatoires, sanctions, e-facture DGI"
    "\n      Tool : search_normes_facturation(query)",
    "Corpus Plan Comptable Marocain (PDF) - classes 2, 3, 4, 6, 7, codes comptables"
    "\n      Tool : search_plan_comptable(query)",
])

pdf.h2("Routing implicite par LLM")
pdf.body(
    "Tous les agents metier appellent retrieve_context() definie dans "
    "rag/rag_router_agent.py. Cette fonction construit l'agent RAG, lui envoie la "
    "question sous forme de message, et retourne le contenu du dernier message de "
    "la reponse. Le LLM choisit automatiquement le bon outil selon le contexte de "
    "la question posee."
)

# -- 4. Human-in-the-Loop --
pdf.h1("5. Human-in-the-Loop")
pdf.body(
    "Trois points de controle sont integres dans le graphe LangGraph. "
    "A chaque point, le workflow attend une action explicite de l'utilisateur."
)

pdf.h2("Validation #1 - Donnees extraites")
pdf.body(
    "L'interface affiche les donnees extraites (fournisseur, montants, ICE, IF, lignes). "
    "L'utilisateur peut corriger les montants avant de valider. "
    "Actions : Accepter / Annuler."
)

pdf.h2("Validation #2 - Conformite fiscale")
pdf.body(
    "Les avertissements sont affiches avec leur niveau (CRITIQUE, MAJEUR, MINEUR) "
    "et la reference legale associee (ex : Article 145 CGI). "
    "Actions : Confirmer / Ignorer les avertissements et continuer."
)

pdf.h2("Validation #3 - Classification comptable")
pdf.body(
    "Le code PCM propose est affiche avec sa justification et son score de confiance. "
    "Si la confiance est insuffisante (sous le seuil configure), un avertissement s'affiche. "
    "L'utilisateur peut corriger le code avant de generer l'ecriture."
)

# -- 5. Interface --
pdf.add_page()
pdf.h1("6. Interface Utilisateur (Bonus)")
pdf.body(
    "L'interface est developpee avec Streamlit (app.py). Elle permet de traiter "
    "plusieurs factures en parallele via ThreadPoolExecutor."
)
pdf.bullet([
    "Etape 1 - Telechargement et extraction (PDF, XML, image, TXT)",
    "Etape 2 - Validation des donnees extraites avec correction possible",
    "Etape 3 - Resultats de conformite fiscale avec niveaux d'avertissement",
    "Etape 4 - Classification PCM avec correction manuelle du code",
    "Etape 5 - Journal comptable complet + export Excel (XLSX) et CSV",
])
pdf.body(
    "Le traitement batch utilise jusqu'a 5 workers en parallele. Chaque worker "
    "appelle directement les noeuds LangGraph (graph/nodes.py) de maniere independante "
    "par facture, ce qui permet de traiter plusieurs factures simultanement."
)

# -- 6. Stack Technique --
pdf.h1("7. Stack Technique")
pdf.bullet([
    "Python 3.11+",
    "LangChain - agents, tools, ChatPromptTemplate, with_structured_output",
    "LangGraph - StateGraph, conditional_edges, TypedDict InvoiceState",
    "OpenAI GPT-4o-mini - extraction, conformite, classification, journal",
    "FAISS - index vectoriels pour les trois corpus RAG",
    "Pydantic v2 - schemas structures (InvoiceData, ComplianceResult, AccountingCode, JournalEntry)",
    "Streamlit - interface web avec traitement batch",
    "pytest + pytest-cov - 93 tests, couverture 88%",
    "uv - gestionnaire de dependances (pyproject.toml + uv.lock)",
])

# -- 7. Structure du projet --
pdf.h1("8. Structure du Projet")
pdf.body(
    "Le projet est organise en modules separes selon les responsabilites. "
    "Le dossier agents/ contient les six agents specialises. "
    "Le dossier graph/ regroupe la logique LangGraph : l'etat partage (InvoiceState), "
    "le graphe (invoice_graph.py) et les noeuds (nodes.py). "
    "Les tools LangChain (lecteurs PDF/XML et retrievers FAISS) sont dans tools/. "
    "Le systeme RAG est isole dans rag/ avec ses corpus dans rag/corpora/. "
    "Les prompts de chaque agent sont stockes en fichiers .txt dans prompts/. "
    "La configuration (LLM, settings) est dans config/, les schemas Pydantic dans schemas/. "
    "L'interface Streamlit est dans app.py, les tests dans tests/ (93 tests, 88% couverture)."
)

# -- 8. Installation --
pdf.h1("9. Installation")
pdf.code(
    "git clone https://github.com/elfetalelias/smart-einvoice-agent.git\n"
    "cd smart-einvoice-agent\n\n"
    "uv venv\n"
    "source .venv/bin/activate\n"
    "uv sync\n\n"
    "cp .env.example .env\n"
    "# Ajouter OPENAI_API_KEY dans .env\n\n"
    "uv run python rag/ingest.py    # indexer les corpus RAG\n"
    "uv run streamlit run app.py    # lancer l'application"
)

# -- 9. Tests --
pdf.h1("10. Tests")
pdf.body("93 tests, couverture globale 88%. Les agents metier sont couverts a 100%.")
pdf.code(
    "uv run pytest tests/ -v\n"
    "uv run pytest tests/ --cov=. --cov-report=term-missing"
)
pdf.bullet([
    "test_extractor_agent.py - schemas InvoiceData, extraction XML/PDF",
    "test_compliance_agent.py - coherence TVA, taux valides marocains",
    "test_accounting_classifier.py - classification PCM, seuil de confiance",
    "test_agents_additional.py - compliance, classifier, journal, nodes LangGraph",
    "test_coverage_boost.py - couverture interne agents + RAG + tools",
    "test_invoice_graph.py - graphe LangGraph complet",
    "test_rag_retrievers.py - retrievers FAISS",
])

# -- 10. Conclusion --
pdf.add_page()
pdf.h1("11. Conclusion")
pdf.body(
    "Ce projet implemente un systeme multi-agent complet pour le traitement des factures "
    "electroniques marocaines. Les quatre points du projet de fin de module sont couverts :\n\n"
    "- Workflow agentique : graphe LangGraph avec 8 noeuds et supervision hierarchique\n"
    "- RAG multi-corpus : 3 corpus, 3 retrievers, routing implicite par LLM (create_react_agent)\n"
    "- Human-in-the-Loop : 3 points de validation avec correction possible a chaque etape\n"
    "- Interface web (bonus) : Streamlit avec traitement batch, export Excel/CSV\n\n"
    "Les bonnes pratiques du cours sont respectees : separation agents/tools/graph/config, "
    "gestion des prompts dans prompts/, pas de melange LangChain/LangGraph sans logique claire, "
    "README complet, reproductibilite via uv.lock, et couverture de tests a 88%."
)

pdf.h2("Lien GitHub")
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(20, 60, 200)
pdf.cell(0, 8, "https://github.com/elfetalelias/smart-einvoice-agent", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# -- Export --
output = "rapport_projet_fin_module.pdf"
pdf.output(output)
print(f"Rapport genere : {output}")
