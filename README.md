# Système Intelligent de Traitement et Classification Comptable des Factures Électroniques

> Système multi-agent LangGraph + LangChain avec RAG multi-corpus et validation humaine  
> Projet de fin de module — Architecture Multi-Agents

---

## Table des Matières

1. [Problématique](#problématique)
2. [Objectifs](#objectifs)
3. [Correspondance avec les Consignes](#correspondance-avec-les-consignes)
4. [Architecture Globale](#architecture-globale)
5. [Workflow Détaillé](#workflow-détaillé)
6. [Justification de l'Orchestration](#justification-de-lorchestration)
7. [Agents du Système](#agents-du-système)
8. [RAG Multi-Corpus](#rag-multi-corpus)
9. [Human-in-the-Loop](#human-in-the-loop)
10. [Stack Technique](#stack-technique)
11. [Installation](#installation)
12. [Configuration .env](#configuration-env)
13. [Structure du Projet](#structure-du-projet)
14. [Tests](#tests)
15. [Limitations](#limitations)

---

## Problématique

Les entreprises marocaines traitent chaque jour des dizaines ou centaines de factures fournisseurs.
Ce processus est aujourd'hui manuel, lent et sujet aux erreurs :

- Vérification manuelle de la conformité fiscale (TVA, ICE, IF, mentions obligatoires)
- Classification comptable laborieuse selon le Plan Comptable Marocain (PCM)
- Risque d'erreurs dans les écritures comptables
- Manque d'un assistant intelligent pour guider le comptable

Comment automatiser intelligemment l'extraction, la vérification et la classification comptable
des factures électroniques tout en gardant le comptable humain au centre des décisions ?

---

## Objectifs

1. Extraire automatiquement les données d'une facture PDF ou XML avec un score de confiance
2. Vérifier la conformité fiscale selon la législation marocaine via RAG
3. Classifier la facture avec un code du Plan Comptable Marocain via RAG
4. Générer une écriture comptable suggérée (Débit/Crédit)
5. Intégrer trois points de validation humaine obligatoires
6. Produire un rapport final structuré en français
7. Offrir une interface web intuitive en français

---

## Correspondance avec les Consignes

| Consigne du Professeur | Implémentation dans le Projet |
|---|---|
| Système multi-agent autonome/semi-autonome | 6 agents spécialisés orchestrés par un Superviseur |
| LangChain pour agents et tools | Tous les agents et tools utilisent LangChain |
| LangGraph pour orchestration | invoice_graph.py — StateGraph complet |
| Collaboration hiérarchique justifiée | Superviseur -> Agents spécialisés (détail section 6) |
| RAG agentique multi-corpus | 3 corpus, 3 retrievers, routing dynamique |
| Human-in-the-Loop | 3 points de validation : extraction, conformité, classification |
| Interface web fonctionnelle | Streamlit multipage en français |
| Structure projet claire | 8 dossiers séparés par responsabilité |
| Gestion des prompts | Dossier prompts/ avec un fichier par agent |
| LangChain + LangGraph avec logique claire | LangChain = agents/tools, LangGraph = orchestration |
| uv pour reproductibilité | pyproject.toml + uv.lock + uv sync |
| README complet | Ce document |

---

## Architecture Globale

```
+-------------------------------------------------------------+
|                     INTERFACE STREAMLIT                      |
|         (Téléversement -> Validation -> Rapport)            |
+---------------------+---------------------------------------+
                      |
+---------------------v---------------------------------------+
|                   LANGGRAPH WORKFLOW                         |
|                                                             |
|  +-------------+                                           |
|  | SUPERVISEUR | <-- contrôle le flux, gère InvoiceState  |
|  +------+------+                                           |
|         |                                                   |
|    +----v--------------------------------------------+     |
|    |            WORKFLOW SÉQUENTIEL HIÉRARCHIQUE      |     |
|    |                                                  |     |
|    |  1. EXTRACTEUR  ──────────────────────────────► |     |
|    |  2. [VALIDATION HUMAINE #1]                     |     |
|    |  3. CONFORMITÉ  ──────────────────────────────► |     |
|    |  4. [VALIDATION HUMAINE #2]                     |     |
|    |  5. CLASSIFICATEUR COMPTABLE  ────────────────► |     |
|    |  6. [VALIDATION HUMAINE #3]                     |     |
|    |  7. ÉCRITURE COMPTABLE  ──────────────────────► |     |
|    |  8. RAPPORTEUR  ──────────────────────────────► |     |
|    +--------------------------------------------------+     |
+-------------------------------------------------------------+
                      |
+---------------------v---------------------------------------+
|                   RAG MULTI-CORPUS                           |
|                                                             |
|  +----------------+ +-----------------+ +---------------+  |
|  | CORPUS FISCAL  | | CORPUS NORMES   | | CORPUS PCM    |  |
|  | MAROCAIN       | | FACTURATION     | | (Plan Compta) |  |
|  |                | | ÉLECTRONIQUE    | |               |  |
|  | • TVA          | | • UBL           | | • Classe 6    |  |
|  | • ICE/IF       | | • Factur-X      | | • Classe 2    |  |
|  | • Mentions     | | • EN 16931      | | • Classe 4    |  |
|  +----------------+ +-----------------+ +---------------+  |
|                                                             |
|  Routing dynamique : question -> corpus(s) pertinent(s)    |
+-------------------------------------------------------------+
```

---

## Workflow Détaillé

```
UTILISATEUR téléverse facture (PDF/XML)
         |
         v
[NOEUD: extract_invoice]
  Agent Extracteur lit le fichier
  -> extrait : fournisseur, numéro, date, ICE, IF, HT, TVA, TTC, lignes
  -> calcule score_confiance_extraction
         |
         v
[NOEUD: human_validation_1]  <-- VALIDATION HUMAINE #1
  Streamlit affiche les données extraites
  Utilisateur : Accepter / Modifier / Rejeter
         |
         v
[NOEUD: check_compliance]
  Agent Conformité appelle search_regles_fiscales()
  -> vérifie champs obligatoires, cohérence TVA
  -> produit liste d'avertissements
         |
         v
[NOEUD: human_validation_2]  <-- VALIDATION HUMAINE #2
  Streamlit affiche les avertissements
  Utilisateur : Confirmer / Ignorer les avertissements
         |
         v
[NOEUD: classify_accounting]
  Agent Classificateur appelle search_plan_comptable()
  -> propose code PCM + justification
  -> score_confiance_classification
         |
         v
[NOEUD: human_validation_3]  <-- VALIDATION HUMAINE #3
  Streamlit affiche le code proposé
  Utilisateur : Accepter / Corriger le code
         |
         v
[NOEUD: generate_journal_entry]
  Agent Écriture Comptable
  -> génère Débit / Crédit selon code validé
         |
         v
[NOEUD: generate_report]
  Agent Rapporteur
  -> rapport final en français (toutes les étapes)
         |
         v
RAPPORT FINAL affiché + téléchargeable
```

---

## Justification de l'Orchestration

### Choix : Architecture Hiérarchique avec séquence guidée

Le traitement d'une facture est intrinsèquement séquentiel avec dépendances :
- On ne peut pas classifier avant d'extraire
- On ne peut pas générer l'écriture avant de classifier
- Chaque étape dépend du résultat de la précédente

Le Superviseur lit l'état global (InvoiceState), décide du prochain nœud, gère les bifurcations
(rejet -> arrêt, modification -> re-extraction) et garantit que les validations humaines bloquent le flux.

---

## Agents du Système

### Agent Superviseur
Orchestre l'ensemble du workflow. Lit InvoiceState et décide du prochain nœud.

### Agent Extracteur
Lit et structure les données de la facture (PDF ou XML).
Retourne : fournisseur, numéro, date, ICE, IF, HT, TVA, TTC, lignes, score_confiance.

### Agent de Conformité
Vérifie la conformité fiscale marocaine via RAG corpus fiscal.
Retourne : liste d'avertissements, références législatives, score_conformite.

### Agent de Classification Comptable
Propose un code du Plan Comptable Marocain via RAG corpus PCM.
Retourne : code_comptable, libelle, justification, score_confiance, alternatives.

### Agent d'Écriture Comptable
Génère l'écriture Débit/Crédit selon le code validé.
Retourne : liste d'écritures équilibrées.

### Agent Rapporteur
Compile toutes les informations en un rapport final structuré en français.

---

## RAG Multi-Corpus

Trois corpus vectorisés avec FAISS :

1. Corpus Fiscal Marocain (TVA, ICE, mentions obligatoires)
   Tool : search_regles_fiscales(query)

2. Corpus Normes Facturation Électronique (UBL, Factur-X, EN 16931)
   Tool : search_normes_facturation(query)

3. Corpus Plan Comptable Marocain (Classes 2, 3, 4, 6, 7)
   Tool : search_plan_comptable(query)

Routing dynamique : analyse sémantique de la question -> sélection corpus pertinents.

---

## Human-in-the-Loop

### Validation #1 — Données Extraites
Actions : Accepter / Modifier / Rejeter

### Validation #2 — Résultats de Conformité
Actions : Confirmer / Ignorer avec justification

### Validation #3 — Classification Comptable
Actions : Accepter / Corriger le code manuellement

---

## Stack Technique

- Python 3.11+
- LangChain 0.3+
- LangGraph 0.2+
- OpenAI GPT-4o (ou Ollama llama3 en local)
- FAISS pour les index vectoriels
- Streamlit 1.35+
- Pydantic 2.x
- pypdf 4.x
- lxml 5.x
- python-dotenv
- uv (gestionnaire de dépendances)
- pytest + pytest-asyncio

---

## Installation

```bash
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Cloner le projet
git clone https://github.com/<username>/smart-einvoice-agent.git
cd smart-einvoice-agent

# Créer l'environnement et installer les dépendances
uv venv
source .venv/bin/activate
uv sync

# Copier les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Ingérer les corpus RAG
python rag/ingest.py

# Lancer l'application
streamlit run app.py
```

---

## Configuration .env

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_PATH=rag/indexes
FAISS_INDEX_TAX=rag/indexes/tax_rules_index
FAISS_INDEX_STANDARDS=rag/indexes/einvoice_standards_index
FAISS_INDEX_ACCOUNTING=rag/indexes/accounting_plan_index
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
EXTRACTION_CONFIDENCE_THRESHOLD=0.8
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.7
OUTPUT_DIR=data/outputs
LOG_LEVEL=INFO
```

---

## Structure du Projet

```
smart-einvoice-agent/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── app.py
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
│   ├── accounting_plan_retriever_tool.py
│   └── validation_tools.py
├── rag/
│   ├── ingest.py
│   ├── vector_store.py
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
├── data/
│   ├── sample_invoices/
│   └── outputs/
└── tests/
    ├── test_extractor_agent.py
    ├── test_compliance_agent.py
    ├── test_accounting_classifier.py
    ├── test_rag_retrievers.py
    └── test_invoice_graph.py
```

---

## Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=. --cov-report=html
```

---

## Limitations

1. Dépendance LLM : la qualité d'extraction dépend du modèle utilisé
2. Corpus RAG statique : les corpus doivent être mis à jour manuellement
3. Formats supportés : PDF texte et XML uniquement (pas d'OCR complet)
4. Législation : basé sur la réglementation marocaine au moment du développement
5. Non-remplacement expert : le système est un assistant, pas un expert-comptable certifié
