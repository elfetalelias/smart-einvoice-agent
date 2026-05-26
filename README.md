# Système Intelligent de Traitement des Factures Électroniques

Projet de fin de module — Master SDIA, Systèmes Multi-Agents FC  
Prof. RETAL Sara

---

Ce projet implémente un système multi-agent capable de traiter des factures électroniques de manière automatique. Le système extrait les données d'une facture (PDF, XML, image ou TXT), vérifie sa conformité fiscale selon la législation marocaine, classe la facture dans le Plan Comptable Marocain, génère l'écriture comptable correspondante, et produit le journal comptable final. Trois points de validation humaine sont intégrés dans le workflow pour garantir la fiabilité du traitement.

---

## Architecture

Le système est construit autour de six agents qui travaillent ensemble de manière séquentielle. Un superviseur central orchestre le flux via LangGraph — il lit l'état courant de la facture et décide quel agent appeler ensuite.

- **Superviseur** : orchestre le workflow et décide du prochain nœud selon l'état courant
- **Extracteur** : lit la facture (PDF, XML, image PNG/JPG/WEBP, TXT) et extrait les données structurées
- **Agent de Conformité** : vérifie les champs obligatoires et la cohérence fiscale (TVA, ICE, IF) via RAG
- **Classificateur Comptable** : propose un code du Plan Comptable Marocain via RAG
- **Agent d'Écriture** : génère l'écriture Débit/Crédit équilibrée
- **Journal Comptable** : compile toutes les étapes traitées dans le document final

La collaboration est **hiérarchique et séquentielle** : le Superviseur contrôle le flux via LangGraph, chaque agent dépend du résultat du précédent, et trois nœuds de validation humaine bloquent la progression jusqu'à confirmation.

---

## RAG Multi-Corpus

Le système utilise trois corpus vectorisés avec FAISS :

- **Corpus règles fiscales** (`cgi-2026.pdf`) — TVA, ICE, IF, taux applicables
  - Tool : `search_regles_fiscales`
- **Corpus normes facturation** (`cgi-2026.pdf` + `ubl_facturx.txt`) — Article 145 CGI, e-facture DGI, mentions obligatoires, sanctions
  - Tool : `search_normes_facturation`
- **Corpus Plan Comptable Marocain** (`PDF`) — classes 2, 3, 4, 6, 7
  - Tool : `search_plan_comptable`

Le routing est **implicite par LLM** : l'agent RAG (`create_react_agent`) analyse la question, choisit le ou les outils pertinents, récupère les documents et génère une réponse contextuelle. Toutes les requêtes passent par `retrieve_context()` dans `rag/rag_router_agent.py`.

---

## Human-in-the-Loop

Trois points de contrôle sont intégrés dans le graphe LangGraph :

1. **Validation #1** — après l'extraction : l'utilisateur vérifie et corrige les données extraites
2. **Validation #2** — après la conformité : l'utilisateur confirme ou ignore les avertissements fiscaux
3. **Validation #3** — après la classification : l'utilisateur accepte ou corrige le code comptable proposé

---

## Tech Stack

- Python 3.11+
- LangChain
- LangGraph
- OpenAI GPT-4o-mini
- FAISS (index vectoriels)
- Streamlit (interface web)
- Pydantic v2
- uv (gestionnaire de dépendances)
- pytest

---

## Installation

```bash
git clone https://github.com/elfetalelias/smart-einvoice-agent.git
cd smart-einvoice-agent

uv venv
source .venv/bin/activate
uv sync
```

---

## Configuration

Créer un fichier `.env` à la racine du projet :

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_PATH=rag/indexes
FAISS_INDEX_TAX=rag/indexes/tax_rules_index
FAISS_INDEX_STANDARDS=rag/indexes/einvoice_standards_index
FAISS_INDEX_ACCOUNTING=rag/indexes/accounting_plan_index
RAG_TOP_K=5
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.7
OUTPUT_DIR=data/outputs
```

Un fichier `.env.example` est fourni avec toutes les variables.

Avant de lancer l'application, ingérer les corpus RAG :

```bash
uv run python rag/ingest.py
```

---

## Lancer l'application

```bash
uv run streamlit run app.py
```

---

## Structure du projet

```
smart-einvoice-agent/
├── agents/
│   ├── supervisor_agent.py
│   ├── extractor_agent.py
│   ├── compliance_agent.py
│   ├── accounting_classifier_agent.py
│   ├── journal_entry_agent.py
│   └── reporter_agent.py
├── graph/
│   ├── invoice_state.py
│   ├── invoice_graph.py
│   └── nodes.py
├── tools/
│   ├── pdf_reader_tool.py
│   ├── xml_reader_tool.py
│   ├── tax_rules_retriever_tool.py
│   ├── einvoice_standards_retriever_tool.py
│   └── accounting_plan_retriever_tool.py
├── rag/
│   ├── rag_router_agent.py
│   ├── vector_store.py
│   ├── ingest.py
│   └── corpora/
│       ├── regles_fiscales_marocaines/
│       ├── normes_facturation_electronique/
│       └── plan_comptable_marocain/
├── prompts/
│   ├── superviseur.txt
│   ├── extracteur.txt
│   ├── conformite.txt
│   ├── classificateur_comptable.txt
│   ├── ecriture_comptable.txt
│   └── rapporteur.txt
├── config/
│   ├── llm.py
│   └── settings.py
├── schemas/
│   ├── invoice_schema.py
│   ├── compliance_schema.py
│   └── accounting_schema.py
├── tests/
├── app.py
├── pyproject.toml
├── uv.lock
└── .env.example
```

---

## Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=. --cov-report=term-missing
```

93 tests, couverture 88%.
