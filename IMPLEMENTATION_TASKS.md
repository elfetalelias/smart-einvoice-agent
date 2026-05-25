# Plan d'Implémentation par Phases
# Système Intelligent de Traitement des Factures Électroniques

> Durée estimée totale : 4 à 6 semaines (étudiant temps partiel)
> Chaque phase produit un livrable testable et démontrable.

---

## VUE D'ENSEMBLE DES PHASES

| Phase | Titre | Durée | Livrable |
|---|---|---|---|
| 0 | Infrastructure & Setup | 2h | Environnement reproductible |
| 1 | Schémas & Types | 3h | Modèles Pydantic validés |
| 2 | Tools LangChain | 4h | 5 tools fonctionnels |
| 3 | Pipeline RAG | 6h | 3 corpus indexés et interrogeables |
| 4 | Agents LangChain | 8h | 6 agents fonctionnels |
| 5 | Graphe LangGraph | 4h | Workflow orchestré de bout en bout |
| 6 | Interface Streamlit | 6h | UI complète en français |
| 7 | Tests & Validation | 4h | Couverture >= 80% |
| 8 | Documentation & Rapport | 4h | README + Rapport PDF académique |

---

## PHASE 0 — Infrastructure & Setup

**Objectif :** Environnement de développement reproductible avec uv.

### Tâches

#### T0.1 — Installer uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version  # Vérifier : uv 0.4.x ou supérieur
```
**Critère de succès :** `uv --version` affiche une version.

---

#### T0.2 — Initialiser le projet
```bash
mkdir smart-einvoice-agent
cd smart-einvoice-agent
uv venv
source .venv/bin/activate
```
**Critère de succès :** Environnement virtuel créé dans `.venv/`.

---

#### T0.3 — Créer pyproject.toml
Fichier déjà présent dans ce repo. Vérifier les dépendances et installer :
```bash
uv sync
```
**Critère de succès :** `uv sync` termine sans erreur.

---

#### T0.4 — Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec votre clé API OpenAI :
OPENAI_API_KEY=sk-votre-vraie-cle
```
**Critère de succès :** `.env` contient une clé valide.

---

#### T0.5 — Créer la structure de dossiers
```bash
mkdir -p agents graph tools rag/corpora/{regles_fiscales_marocaines,normes_facturation_electronique,plan_comptable_marocain}
mkdir -p rag/indexes prompts config schemas data/{sample_invoices,outputs} tests
```
**Critère de succès :** Tous les dossiers existent.

---

#### T0.6 — Initialiser git
```bash
git init
git add .gitignore
git commit -m "chore: initialisation du projet"
```
**Critère de succès :** Premier commit créé.

---

**LIVRABLE PHASE 0 :** Environnement Python 3.11 avec toutes les dépendances installées.

---

## PHASE 1 — Schémas & Types Pydantic

**Objectif :** Définir les structures de données partagées entre tous les agents.
**Principe :** Les schémas sont le contrat entre les agents.

### Tâches

#### T1.1 — Implémenter config/settings.py
Fichier : `config/settings.py`

- [ ] Classe `Settings` basée sur `pydantic_settings.BaseSettings`
- [ ] Lecture des variables depuis `.env`
- [ ] Tous les paramètres (LLM, RAG, seuils de confiance)
- [ ] Instance `settings` exportée

**Test :** `from config.settings import settings; print(settings.openai_model)`

---

#### T1.2 — Implémenter config/llm.py
Fichier : `config/llm.py`

- [ ] Fonction `get_llm(temperature) -> ChatOpenAI`
- [ ] Fonction `get_embeddings() -> OpenAIEmbeddings`
- [ ] Support optionnel Ollama (commenté)

**Test :** `from config.llm import get_llm; llm = get_llm(); print(type(llm))`

---

#### T1.3 — Implémenter schemas/invoice_schema.py
Fichier : `schemas/invoice_schema.py`

Classes à créer :
- [ ] `LigneFacture(BaseModel)` : description, quantite, prix_unitaire, montant_ht, taux_tva
- [ ] `InvoiceData(BaseModel)` : tous les champs de la facture + score_confiance + champs_manquants
- [ ] Validations : score_confiance entre 0 et 1, devise par défaut "MAD"

**Test :** `pytest tests/test_extractor_agent.py::TestInvoiceDataSchema -v`

---

#### T1.4 — Implémenter schemas/compliance_schema.py
Fichier : `schemas/compliance_schema.py`

Classes à créer :
- [ ] `NiveauAvertissement(Enum)` : critique, majeur, mineur
- [ ] `Avertissement(BaseModel)` : code, message, niveau, reference_legale
- [ ] `ComplianceResult(BaseModel)` : conforme, avertissements, references_rag, score_conformite, resume

**Test :** `pytest tests/test_compliance_agent.py::TestComplianceSchema -v`

---

#### T1.5 — Implémenter schemas/accounting_schema.py
Fichier : `schemas/accounting_schema.py`

Classes à créer :
- [ ] `SensEcriture(Enum)` : Débit, Crédit
- [ ] `CodeAlternatif(BaseModel)` : code, libelle, score
- [ ] `AccountingCode(BaseModel)` : code_comptable, libelle, justification, score_confiance, alternatives
- [ ] `LigneEcriture(BaseModel)` : sens, compte, libelle, montant
- [ ] `JournalEntry(BaseModel)` : date, reference, ecritures, equilibre, avertissement

**Test :** `pytest tests/test_accounting_classifier.py::TestAccountingCodeSchema -v`

---

#### T1.6 — Implémenter graph/invoice_state.py
Fichier : `graph/invoice_state.py`

- [ ] `ValidationHumaine(TypedDict)` : decision, commentaire, modifications
- [ ] `InvoiceState(TypedDict)` : tous les champs du workflow complet

**Test :** `python -c "from graph.invoice_state import InvoiceState; print('OK')"`

---

**LIVRABLE PHASE 1 :** Tous les schémas Pydantic définis et testés unitairement.

---

## PHASE 2 — Tools LangChain

**Objectif :** Implémenter les 5 outils utilisés par les agents.
**Principe :** Chaque tool est décorée `@tool` et a une docstring en français.

### Tâches

#### T2.1 — Implémenter tools/pdf_reader_tool.py
Fichier : `tools/pdf_reader_tool.py`

- [ ] Décorateur `@tool` sur `read_pdf_invoice(file_path: str) -> Dict`
- [ ] Utilise `pypdf.PdfReader` pour extraire le texte
- [ ] Retourne `texte_complet`, `nombre_pages`, `pages`
- [ ] Gestion des PDF sans texte (scan) : retourne message d'erreur clair

**Test manuel :**
```python
from tools.pdf_reader_tool import read_pdf_invoice
result = read_pdf_invoice.invoke({"file_path": "data/sample_invoices/facture_test_01.txt"})
print(result["texte_complet"][:200])
```

---

#### T2.2 — Implémenter tools/xml_reader_tool.py
Fichier : `tools/xml_reader_tool.py`

- [ ] Décorateur `@tool` sur `read_xml_invoice(file_path: str) -> Dict`
- [ ] Utilise `lxml.etree` pour parser l'XML
- [ ] Fonction récursive `element_to_dict(elem)` pour aplatir l'arbre
- [ ] Retourne `xml_parse` (JSON string) et `racine`

**Test :** Créer un fichier XML minimal et vérifier le parsing.

---

#### T2.3 — Implémenter tools/tax_rules_retriever_tool.py
Fichier : `tools/tax_rules_retriever_tool.py`

- [ ] Instance FAISS lazy-loaded (singleton `_store`)
- [ ] Décorateur `@tool` sur `search_regles_fiscales(query: str) -> str`
- [ ] Format de sortie : `[N] Source\nContenu\n---`
- [ ] Docstring décrit clairement quand l'utiliser

**Test :** `pytest tests/test_rag_retrievers.py::TestRagRetrievers::test_search_regles_fiscales_returns_text -v`

---

#### T2.4 — Implémenter tools/einvoice_standards_retriever_tool.py
(Même pattern que T2.3 mais pour le corpus normes)

- [ ] `search_normes_facturation(query: str) -> str`
- [ ] Singleton `_store` sur `settings.faiss_index_standards`

**Test :** `pytest tests/test_rag_retrievers.py::TestRagRetrievers::test_search_normes_facturation -v`

---

#### T2.5 — Implémenter tools/accounting_plan_retriever_tool.py
(Même pattern que T2.3 mais pour le PCM)

- [ ] `search_plan_comptable(query: str) -> str`
- [ ] Singleton `_store` sur `settings.faiss_index_accounting`

**Test :** `pytest tests/test_rag_retrievers.py::TestRagRetrievers::test_search_plan_comptable_returns_text -v`

---

**LIVRABLE PHASE 2 :** 5 tools LangChain fonctionnels et testés.

---

## PHASE 3 — Pipeline RAG Multi-Corpus

**Objectif :** Indexer les 3 corpus dans FAISS et valider la recherche sémantique.

### Tâches

#### T3.1 — Préparer les documents du Corpus Fiscal Marocain
Dossier : `rag/corpora/regles_fiscales_marocaines/`

- [ ] `tva_maroc.txt` : taux TVA, champs obligatoires, article 145 CGI
- [ ] `facturation_electronique.txt` : règles facture électronique, conservation
- [ ] Optionnel : ajouter d'autres extraits du CGI

**Format requis :** Fichiers .txt encodés UTF-8, chaque fichier = 1 thème.

---

#### T3.2 — Préparer les documents du Corpus Normes Facturation
Dossier : `rag/corpora/normes_facturation_electronique/`

- [ ] `ubl_facturx.txt` : structure UBL, Factur-X, EN 16931
- [ ] `peppol_guide.txt` (optionnel) : guide PEPPOL

---

#### T3.3 — Préparer les documents du Plan Comptable Marocain
Dossier : `rag/corpora/plan_comptable_marocain/`

- [ ] `pcm_classe6.txt` : comptes de charges (60xx)
- [ ] `pcm_tva_fournisseurs.txt` : comptes 3455, 4411
- [ ] `pcm_classe2.txt` (optionnel) : immobilisations

---

#### T3.4 — Implémenter rag/vector_store.py
Fichier : `rag/vector_store.py`

- [ ] `load_or_create_store(index_path) -> FAISS`
- [ ] `save_store(store, index_path)`
- [ ] `create_store_from_documents(documents, index_path) -> FAISS`
- [ ] `search_documents(store, query, k) -> List[Document]`
- [ ] Gestion d'erreur si index manquant

---

#### T3.5 — Implémenter rag/ingest.py
Fichier : `rag/ingest.py`

- [ ] `ingest_corpus(corpus_name, index_path)` pour chaque corpus
- [ ] `DirectoryLoader` sur `*.txt`
- [ ] `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`
- [ ] Affichage du nombre de chunks créés
- [ ] Fonction `main()` appelable en ligne de commande

**Exécution :**
```bash
python rag/ingest.py
# Sortie attendue :
# === INGESTION DES CORPUS RAG ===
# [INGESTION] regles_fiscales_marocaines -> rag/indexes/tax_rules_index
#   [INFO] 2 documents -> 8 chunks
#   [OK] Index sauvegardé
```

---

#### T3.6 — Valider la recherche RAG
Tests de recherche sémantique :
```python
# Test 1 : Corpus fiscal
from tools.tax_rules_retriever_tool import search_regles_fiscales
result = search_regles_fiscales.invoke({"query": "ICE obligatoire sur facture"})
assert "Article 145" in result or "ICE" in result

# Test 2 : PCM
from tools.accounting_plan_retriever_tool import search_plan_comptable
result = search_plan_comptable.invoke({"query": "achat fournitures de bureau"})
assert "6125" in result
```

**Test automatisé :** `pytest tests/test_rag_retrievers.py -v`

---

**LIVRABLE PHASE 3 :** 3 index FAISS créés, recherche sémantique validée sur les 3 corpus.

---

## PHASE 4 — Agents LangChain

**Objectif :** Implémenter les 6 agents, chacun avec son prompt et ses tools.

### Tâches

#### T4.1 — Écrire et valider les prompts
Dossier : `prompts/`

Pour chaque fichier `.txt` :
- [ ] `superviseur.txt` : logique de routing des statuts
- [ ] `extracteur.txt` : instructions d'extraction structurée + format JSON attendu
- [ ] `conformite.txt` : règles de vérification + références légales à citer
- [ ] `classificateur_comptable.txt` : logique de classification PCM + seuil de confiance
- [ ] `ecriture_comptable.txt` : structure écriture Débit/Crédit + avertissement obligatoire
- [ ] `rapporteur.txt` : structure du rapport final en sections numérotées

**Critère qualité :** Chaque prompt doit mentionner explicitement le format de sortie attendu (JSON ou Markdown).

---

#### T4.2 — Implémenter agents/extractor_agent.py
Fichier : `agents/extractor_agent.py`

- [ ] `run_extractor_agent(file_path, file_type) -> InvoiceData`
- [ ] `create_tool_calling_agent` avec LLM + tools [pdf_reader, xml_reader]
- [ ] `AgentExecutor` avec verbose=False en production
- [ ] Parsing du JSON de sortie avec gestion d'erreur
- [ ] Return `InvoiceData` validée par Pydantic

**Test :** `pytest tests/test_extractor_agent.py -v`

---

#### T4.3 — Implémenter agents/compliance_agent.py
Fichier : `agents/compliance_agent.py`

- [ ] `run_compliance_agent(invoice_data) -> ComplianceResult`
- [ ] Tools : [search_regles_fiscales, search_normes_facturation]
- [ ] L'agent doit appeler au moins 1 tool RAG
- [ ] Return `ComplianceResult` avec avertissements et références

**Test :** `pytest tests/test_compliance_agent.py -v`

---

#### T4.4 — Implémenter agents/accounting_classifier_agent.py
Fichier : `agents/accounting_classifier_agent.py`

- [ ] `run_accounting_classifier_agent(invoice_data) -> AccountingCode`
- [ ] Tool : [search_plan_comptable]
- [ ] Si score < seuil → `validation_humaine_requise = True` automatiquement
- [ ] Return `AccountingCode` avec alternatives

**Test :** `pytest tests/test_accounting_classifier.py -v`

---

#### T4.5 — Implémenter agents/journal_entry_agent.py
Fichier : `agents/journal_entry_agent.py`

- [ ] `run_journal_entry_agent(invoice_data, accounting_code) -> JournalEntry`
- [ ] Utilise LLM via `prompt | llm | JsonOutputParser()`
- [ ] Calcul et vérification automatique de l'équilibre (Débit = Crédit)
- [ ] Les écritures incluent obligatoirement 3455 et 4411

**Règle comptable :**
```
Débit  6xxx  HT     = montant_ht
Débit  3455  TVA    = montant_tva
Crédit 4411  TTC    = montant_ttc
```

---

#### T4.6 — Implémenter agents/reporter_agent.py
Fichier : `agents/reporter_agent.py`

- [ ] `run_reporter_agent(state: InvoiceState) -> str`
- [ ] Utilise LLM via `prompt | llm | StrOutputParser()`
- [ ] Passe l'état complet sérialisé en JSON
- [ ] Retourne un rapport Markdown complet en français
- [ ] Inclut les décisions humaines enregistrées

---

#### T4.7 — Implémenter agents/supervisor_agent.py
Fichier : `agents/supervisor_agent.py`

- [ ] `decide_next_node(state: InvoiceState) -> str`
- [ ] Table de routing complète couvrant tous les statuts
- [ ] Toujours retourner "END" en cas d'erreur
- [ ] Pas d'appel LLM : routing déterministe basé sur l'état

**Test :** `pytest tests/test_invoice_graph.py::TestSupervisorAgent -v`

---

**LIVRABLE PHASE 4 :** 6 agents fonctionnels, chacun peut être invoqué indépendamment.

---

## PHASE 5 — Graphe LangGraph

**Objectif :** Assembler le workflow complet avec LangGraph StateGraph.

### Tâches

#### T5.1 — Implémenter graph/nodes.py
Fichier : `graph/nodes.py`

- [ ] `node_extract_invoice(state) -> InvoiceState`
- [ ] `node_check_compliance(state) -> InvoiceState`
- [ ] `node_classify_accounting(state) -> InvoiceState`
- [ ] `node_generate_journal_entry(state) -> InvoiceState`
- [ ] `node_generate_report(state) -> InvoiceState`
- [ ] `node_human_validation_1/2/3(state) -> InvoiceState`
- [ ] Chaque nœud : try/except → met `statut = "erreur"` + `erreur = str(e)`
- [ ] Chaque nœud : retourne `{**state, ...modifications}` (pattern immuable)

---

#### T5.2 — Implémenter graph/invoice_graph.py
Fichier : `graph/invoice_graph.py`

- [ ] Fonction `build_invoice_graph() -> CompiledGraph`
- [ ] `StateGraph(InvoiceState)`
- [ ] Ajouter les 8 nœuds
- [ ] `set_entry_point("extract_invoice")`
- [ ] Arêtes directes entre nœuds séquentiels
- [ ] `add_conditional_edges` aux nœuds de validation humaine
- [ ] Compiler et retourner
- [ ] Exposer `invoice_graph = build_invoice_graph()` au niveau module

---

#### T5.3 — Tester le graphe de bout en bout (mock)
```python
from graph.invoice_graph import invoice_graph
from graph.invoice_state import InvoiceState

# Tester avec un état simulé complet
# Chaque transition doit mettre à jour le statut correctement
```

**Test :** `pytest tests/test_invoice_graph.py -v`

---

#### T5.4 — Visualiser le graphe (optionnel)
```python
from graph.invoice_graph import invoice_graph
from IPython.display import Image
Image(invoice_graph.get_graph().draw_mermaid_png())
```
Utile pour le rapport et la démonstration.

---

**LIVRABLE PHASE 5 :** Workflow LangGraph compilé, transitions validées, routing superviseur fonctionnel.

---

## PHASE 6 — Interface Streamlit

**Objectif :** Interface web en français avec les 3 points de validation humaine.

### Tâches

#### T6.1 — Architecture de app.py
Fichier : `app.py`

Structure en fonctions séparées :
- [ ] `init_session()` : initialise `st.session_state` avec valeurs par défaut
- [ ] `barre_progression()` : sidebar avec progression des étapes
- [ ] `etape_1_telechargement()` : upload fichier + bouton lancer
- [ ] `etape_2_donnees_extraites()` : tableau des données + validation #1
- [ ] `etape_3_conformite()` : avertissements + validation #2
- [ ] `etape_4_classification()` : code PCM + validation #3
- [ ] `etape_5_ecriture()` : tableau écriture + bouton rapport
- [ ] `etape_6_rapport()` : affichage + téléchargement
- [ ] `main()` : orchestre toutes les étapes

---

#### T6.2 — Implémenter l'upload de fichier
Section "Téléversement" :
- [ ] `st.file_uploader` avec types ["pdf", "xml"]
- [ ] Sauvegarde en `tempfile.NamedTemporaryFile`
- [ ] Affichage du nom et type du fichier
- [ ] Bouton "Lancer l'analyse" déclenche l'extraction

---

#### T6.3 — Implémenter l'affichage des données extraites
Section "Données Extraites" :
- [ ] Tableau fournisseur avec `st.table`
- [ ] Tableau montants avec formatage `{:,.2f}`
- [ ] Tableau lignes de facture avec `st.dataframe`
- [ ] Indicateur score de confiance (🟢/🟡/🔴)
- [ ] Liste des champs manquants en avertissement

---

#### T6.4 — Implémenter les 3 boutons de Validation Humaine

**Validation #1 (extraction) :**
- [ ] Bouton "✅ Accepter"
- [ ] Expander "✏️ Modifier" avec formulaire d'édition
- [ ] Bouton "❌ Rejeter" avec arrêt du workflow

**Validation #2 (conformité) :**
- [ ] Bouton "✅ Confirmer"
- [ ] Bouton "⚠️ Ignorer"

**Validation #3 (classification) :**
- [ ] Bouton "✅ Accepter le code"
- [ ] Expander "✏️ Corriger" avec champs code + libellé

---

#### T6.5 — Implémenter l'affichage de l'écriture comptable
Section "Écriture Comptable" :
- [ ] Tableau Débit/Crédit avec `st.dataframe`
- [ ] Indicateur d'équilibre (✅ ou ❌)
- [ ] Avertissement "SUGGESTION — À valider par comptable" en orange
- [ ] Bouton "Générer le Rapport Final"

---

#### T6.6 — Implémenter la section rapport
Section "Rapport Final" :
- [ ] `st.markdown(rapport)` pour affichage formaté
- [ ] `st.download_button` pour téléchargement .md
- [ ] Sauvegarde automatique dans `data/outputs/`
- [ ] Bouton "Nouvelle Analyse" dans sidebar

---

#### T6.7 — CSS et UX
- [ ] CSS `status-ok`, `status-warn`, `status-error`
- [ ] CSS `avertissement-critique`, `avertissement-majeur`, `avertissement-mineur`
- [ ] En-têtes de section colorés
- [ ] Spinner pendant les appels LLM
- [ ] Messages d'erreur clairs avec `st.error()`

---

#### T6.8 — Test manuel de l'interface
```bash
streamlit run app.py
```
Vérifier le golden path :
1. Téléverser `data/sample_invoices/facture_test_01.txt`
2. Lancer l'analyse
3. Accepter l'extraction
4. Confirmer la conformité
5. Accepter la classification
6. Générer le rapport
7. Vérifier le fichier dans `data/outputs/`

---

**LIVRABLE PHASE 6 :** Application Streamlit fonctionnelle, démontrable, entièrement en français.

---

## PHASE 7 — Tests & Validation

**Objectif :** Couverture >= 80%, tous les tests passent en vert.

### Tâches

#### T7.1 — Compléter tests/test_extractor_agent.py
- [ ] `TestInvoiceDataSchema` : création, valeurs par défaut, validation
- [ ] `TestExtractorAgent` : mock AgentExecutor, vérifier InvoiceData retournée
- [ ] Test champs manquants → score confiance < 0.8
- [ ] Couverture ciblée : `schemas/invoice_schema.py`, `agents/extractor_agent.py`

**Run :** `pytest tests/test_extractor_agent.py -v --cov=agents/extractor_agent`

---

#### T7.2 — Compléter tests/test_compliance_agent.py
- [ ] `TestComplianceSchema` : conforme et non conforme
- [ ] `TestTVACoherence` : calcul TVA correct, incorrect, taux valides
- [ ] Mock de `run_compliance_agent` pour tester la logique métier

---

#### T7.3 — Compléter tests/test_accounting_classifier.py
- [ ] `TestAccountingCodeSchema` : haute et faible confiance
- [ ] `TestJournalEntry` : équilibre, 3 lignes, comptes obligatoires
- [ ] Test pattern immuable : `model_copy(update=...)`

---

#### T7.4 — Compléter tests/test_rag_retrievers.py
- [ ] Mock FAISS pour éviter dépendance à l'index réel
- [ ] Tester format de sortie `[N] Source\nContenu`
- [ ] Tester cas "aucun résultat" → message clair

---

#### T7.5 — Compléter tests/test_invoice_graph.py
- [ ] `TestSupervisorAgent` : tous les statuts couverts
- [ ] `TestInvoiceState` : initialisation, pattern immuable `{**state, ...}`
- [ ] Test transition validation_1 : accepté → check_compliance, rejeté → END

---

#### T7.6 — Mesurer la couverture
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
# Objectif : coverage >= 80%
open htmlcov/index.html
```

---

#### T7.7 — Test d'intégration end-to-end
Tester le workflow complet avec les fichiers de test :
```bash
python -c "
from graph.invoice_graph import invoice_graph
from graph.invoice_state import InvoiceState

state = {
    'fichier_path': 'data/sample_invoices/facture_test_01.txt',
    'fichier_type': 'pdf',
    'fichier_nom': 'facture_test_01.txt',
    'statut': 'fichier_reçu',
    # ... autres champs à None
}
# Exécuter jusqu'au premier point de validation humaine
"
```

---

**LIVRABLE PHASE 7 :** Rapport de couverture HTML avec >= 80%, tous les tests en vert.

---

## PHASE 8 — Documentation & Rapport PDF

**Objectif :** README complet + rapport académique en PDF.

### Tâches

#### T8.1 — Finaliser README.md
- [ ] Titre et description claire
- [ ] Architecture ASCII art (déjà présente)
- [ ] Instructions d'installation complètes avec uv
- [ ] Section `.env` avec toutes les variables
- [ ] Structure du projet
- [ ] Section tests avec commandes
- [ ] Lien GitHub public
- [ ] Badge de couverture des tests

---

#### T8.2 — Créer le rapport final PDF

**Structure requise (30-40 pages) :**

```
Page de garde
  - Titre, nom étudiant, module, date

Table des matières

1. Introduction (2-3 pages)
   1.1 Contexte et problématique
   1.2 Objectifs du projet
   1.3 Périmètre et limitations

2. Revue de Littérature (2-3 pages)
   2.1 Systèmes multi-agents : concepts clés
   2.2 LangChain et LangGraph
   2.3 RAG (Retrieval-Augmented Generation)
   2.4 Human-in-the-Loop en IA

3. Analyse et Conception (6-8 pages)
   3.1 Architecture globale (schéma)
   3.2 Justification de l'orchestration hiérarchique
   3.3 Design du RAG multi-corpus
   3.4 Définition de InvoiceState
   3.5 Workflow LangGraph (diagramme)

4. Implémentation (8-10 pages)
   4.1 Configuration et environnement
   4.2 Agents LangChain (code commenté)
   4.3 Pipeline RAG (ingestion + retrieval)
   4.4 Orchestration LangGraph
   4.5 Interface Streamlit
   4.6 Gestion des prompts

5. Tests et Validation (4-5 pages)
   5.1 Stratégie de test
   5.2 Tests unitaires
   5.3 Tests d'intégration
   5.4 Résultats de couverture

6. Démonstration (3-4 pages)
   6.1 Cas d'usage 1 : facture conforme
   6.2 Cas d'usage 2 : facture non conforme
   6.3 Captures d'écran de l'interface

7. Analyse Critique (2-3 pages)
   7.1 Résultats obtenus
   7.2 Limitations identifiées
   7.3 Pistes d'amélioration

8. Conclusion (1 page)

Références bibliographiques
Annexes (code source complet)
```

---

#### T8.3 — Pousser sur GitHub
```bash
git add .
git commit -m "feat: projet complet smart-einvoice-agent"
git remote add origin https://github.com/<username>/smart-einvoice-agent.git
git push -u origin main
```
- [ ] Repository public sur GitHub
- [ ] README affiché correctement sur la page GitHub
- [ ] Lien GitHub inclus dans le rapport PDF

---

#### T8.4 — Préparer la démo (optionnel)
- [ ] Vidéo démo de 5 minutes (OBS Studio)
- [ ] Slides de présentation (10 slides max)

---

**LIVRABLE PHASE 8 :** Rapport PDF académique + code sur GitHub public.

---

## CHECKLIST FINALE AVANT RENDU

### Consignes du Professeur

- [ ] Système multi-agent autonome/semi-autonome ✓ (6 agents)
- [ ] LangChain pour agents et tools ✓
- [ ] LangGraph pour orchestration ✓
- [ ] Justification de l'orchestration dans le rapport ✓
- [ ] RAG agentique multi-corpus (3 corpus) ✓
- [ ] Human-in-the-Loop (3 points de validation) ✓
- [ ] Interface web fonctionnelle Streamlit ✓
- [ ] Structure projet claire (8 dossiers) ✓
- [ ] Gestion des prompts dans prompts/ ✓
- [ ] LangChain et LangGraph avec logique claire ✓
- [ ] uv pour reproductibilité ✓
- [ ] README.md complet ✓
- [ ] Rapport PDF en français avec lien GitHub ✓

### Qualité Technique

- [ ] Tests passent : `pytest tests/ -v` → vert
- [ ] Couverture >= 80% : `pytest --cov`
- [ ] Application démarre : `streamlit run app.py`
- [ ] Ingestion RAG fonctionne : `python rag/ingest.py`
- [ ] Environnement reproductible : `uv sync`
- [ ] `.env.example` sans secrets réels
- [ ] `.gitignore` exclut `.env`, `.venv/`, `rag/indexes/`

### Interface Utilisateur

- [ ] Tous les textes visibles en français
- [ ] 3 points de validation humaine fonctionnels
- [ ] Indicateurs de confiance affichés
- [ ] Rapport téléchargeable
- [ ] Avertissement "ce n'est pas un expert-comptable" visible

---

## ESTIMATION DU TEMPS PAR PHASE

| Phase | Tâches | Heures Estimées | Priorité |
|---|---|---|---|
| 0 — Setup | T0.1 à T0.6 | 2h | CRITIQUE |
| 1 — Schémas | T1.1 à T1.6 | 3h | CRITIQUE |
| 2 — Tools | T2.1 à T2.5 | 4h | CRITIQUE |
| 3 — RAG | T3.1 à T3.6 | 6h | CRITIQUE |
| 4 — Agents | T4.1 à T4.7 | 8h | CRITIQUE |
| 5 — LangGraph | T5.1 à T5.4 | 4h | CRITIQUE |
| 6 — Streamlit | T6.1 à T6.8 | 6h | ÉLEVÉ |
| 7 — Tests | T7.1 à T7.7 | 4h | ÉLEVÉ |
| 8 — Docs/Rapport | T8.1 à T8.4 | 8h | ÉLEVÉ |
| **TOTAL** | | **~45h** | |

---

## CONSEILS D'IMPLÉMENTATION

### Ordre recommandé pour progresser rapidement

1. Commencer par Phase 0 + 1 + 2 (le socle technique)
2. Créer des corpus RAG minimaux (Phase 3) avant les agents
3. Implémenter les agents un par un, tester chacun indépendamment
4. Assembler le graphe uniquement quand les agents fonctionnent
5. Interface Streamlit en dernier (après que le backend fonctionne)

### Pièges à éviter

- Ne pas appeler les vrais agents LLM dans les tests unitaires (mocker)
- Toujours initialiser les champs optionnels à None dans InvoiceState
- Le graphe LangGraph attend le TypedDict exact — pas un dict Python normal
- Les tools LangChain doivent avoir une docstring claire (utilisée par le LLM)
- Encoder tous les fichiers .txt en UTF-8 (important pour le français)

### Gestion des coûts OpenAI

- Utiliser `gpt-4o-mini` pendant le développement, `gpt-4o` pour la démo finale
- Activer `verbose=False` sur AgentExecutor pour réduire les logs
- Les tests unitaires doivent mocker le LLM (0 appel API = 0 coût)
