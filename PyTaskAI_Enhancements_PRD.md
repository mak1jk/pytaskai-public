# Product Requirements Document: PyTaskAI Enhancements

## 1. Introduzione e Obiettivi Generali

Questo documento delinea i requisiti per le nuove funzionalità e i miglioramenti pianificati per PyTaskAI. L'obiettivo è rendere PyTaskAI uno strumento più robusto, completo e integrato per la gestione dei progetti di sviluppo software, con un focus sulla qualità del codice e sulla tracciabilità dei problemi.

Le principali aree di miglioramento includono:
- Introduzione di un sistema di Bug Tracking dedicato.
- Implementazione del tracciamento della copertura dei test del codice.
- Integrazione flessibile con Jira.
- Risoluzione di problemi tecnici negli strumenti MCP esistenti.

## 2. Funzionalità 1: Bug Tracking Avanzato

### 2.1. Problema
Attualmente, PyTaskAI non distingue formalmente tra task generici e bug. Questo limita la capacità di tracciare, prioritizzare e gestire efficacemente i difetti del software all'interno del sistema.

### 2.2. Proposta di Soluzione

#### 2.2.1. Modifiche al Modello Dati (`shared/models.py`)
- Aggiungere un campo `type: str` al modello `Task` (valori possibili: "task", "bug", "feature", ecc., default "task").
- Per i task di tipo "bug", includere campi opzionali specifici:
    - `severity: Optional[str]` (es. "critical", "high", "medium", "low")
    - `steps_to_reproduce: Optional[str]`
    - `expected_result: Optional[str]`
    - `actual_result: Optional[str]`
    - `environment: Optional[str]`
    - `attachments: Optional[List[str]]` (se non già generalizzato)

#### 2.2.2. Aggiornamenti agli Strumenti MCP (`mcp_server/task_manager.py`)
- **`add_task_tool`**: Deve accettare il parametro `type` e i campi specifici per i bug.
- **`list_tasks_tool`**: Aggiungere filtro per `type`; visualizzare campi specifici dei bug.
- **`get_task_tool`**: Restituire tutti i campi, inclusi quelli dei bug.
- **`update_task_tool`**: Permettere la modifica dei campi dei bug.
- Valutare un nuovo `report_bug_tool` per la segnalazione rapida.

#### 2.2.3. Workflow dei Bug
- Inizialmente, utilizzare gli stati esistenti (`pending`, `in-progress`, `done`, ecc.).
- Valutare in futuro l'introduzione di stati specifici per i bug (es. `open`, `resolved`, `verified`, `reopened`) se necessario.

### 2.3. Criteri di Successo
- Gli utenti possono creare, visualizzare, filtrare e aggiornare bug distintamente dai task.
- I bug possono essere arricchiti con informazioni specifiche (severità, passi per riprodurre, ecc.).
- La distinzione tra task e bug è chiara nell'interfaccia utente (tramite strumenti MCP).

## 3. Funzionalità 2: Tracciamento della Copertura dei Test

### 3.1. Problema
PyTaskAI non offre attualmente un modo per tracciare la copertura dei test del codice associata ai task di sviluppo. Questo rende difficile valutare la qualità e la robustezza del software prodotto e garantire che i task siano completati con un'adeguata base di test.

### 3.2. Proposta di Soluzione

#### 3.2.1. Integrazione con Strumenti di Testing
- Integrare PyTaskAI con strumenti comuni di testing e code coverage Python (es. `pytest`, `coverage.py`).

#### 3.2.2. Modifiche al Modello Dati (`shared/models.py`)
- Estendere il modello `Task` per includere:
    - `target_test_coverage: Optional[float]` (es. 80.0 per 80%)
    - `achieved_test_coverage: Optional[float]`
    - `test_report_url: Optional[str]` (link al report di coverage HTML)
    - `related_tests: Optional[List[str]]` (nomi o percorsi dei file di test associati)

#### 3.2.3. Aggiornamenti agli Strumenti MCP (`mcp_server/task_manager.py`)
- **`add_task_tool`**: Permettere di specificare `target_test_coverage` e `related_tests` alla creazione del task.
- **Nuovo `run_tests_and_update_coverage_tool`**: 
    - Esegue i test (possibilmente filtrati per `related_tests` del task).
    - Analizza l'output di `coverage.py`.
    - Aggiorna i campi `achieved_test_coverage` e `test_report_url` del task.
- **`list_tasks_tool` / `get_task_tool`**: Visualizzare le informazioni sulla copertura.

#### 3.2.4. Promuovere lo Sviluppo Test-Driven
- Incoraggiare la creazione di subtask specifici per la scrittura di test.
- I criteri di accettazione dei task di sviluppo dovrebbero includere il raggiungimento della `target_test_coverage`.

### 3.3. Criteri di Successo
- Gli utenti possono definire obiettivi di copertura dei test per i task.
- PyTaskAI può eseguire test e aggiornare automaticamente la copertura raggiunta per un task.
- Le informazioni sulla copertura sono visibili e tracciabili a livello di task.
- Il sistema facilita un approccio orientato ai test nello sviluppo.

## 4. Funzionalità 3: Integrazione con Jira (Riepilogo)

### 4.1. Obiettivo
Fornire un'integrazione bidirezionale opzionale e flessibile tra PyTaskAI e Jira per team che utilizzano entrambe le piattaforme.

### 4.2. Aspetti Chiave della Proposta
- **Mappatura Gerarchica**: PyTaskAI (Epic, Task, Subtask) ↔ Jira (Epic, Story/Task, Subtask).
- **Mappatura Intelligente**: Tipo di issue Jira determinato da complessità/priorità del task PyTaskAI.
- **Configurazione Flessibile**: Strategie di mapping personalizzabili (per complessità, priorità, regole custom).
- **Sincronizzazione Bidirezionale**: Creazione/aggiornamento automatico, sync di stati, commenti, allegati.
- **Risoluzione Conflitti**: Basata su timestamp.
- **Opzioni di Sync**: Completa, selettiva (per tag), unidirezionale, manuale.
- **Autenticazione**: OAuth 2.0 raccomandato.

### 4.3. Criteri di Successo
- L'integrazione permette una sincronizzazione fluida dei dati tra PyTaskAI e Jira.
- Gli utenti possono configurare la mappatura e il comportamento della sincronizzazione secondo le proprie esigenze.
- L'integrazione migliora la visibilità e la collaborazione per i team che usano Jira.

## 5. Prerequisito Tecnico: Risoluzione Bug Strumenti MCP

### 5.1. Problema
Attualmente, gli strumenti MCP di PyTaskAI (es. `mcp4_add_task_tool`) falliscono con un errore `[Errno 30] Read-only file system: '/.taskmaster'`. Questo indica un tentativo di scrittura nella directory root del file system, bloccando la creazione e la gestione dei task tramite MCP.

### 5.2. Azione Richiesta
- Investigare il codice sorgente degli strumenti MCP di PyTaskAI per identificare la causa della gestione errata dei percorsi.
- Correggere il bug per assicurare che gli strumenti utilizzino percorsi relativi al `project_root` o directory utente appropriate per i file di lavoro interni.

### 5.3. Criteri di Successo
- Gli strumenti MCP di PyTaskAI (in particolare `mcp4_add_task_tool`, `mcp4_list_tasks_tool`, ecc.) funzionano correttamente senza errori di file system.
- È possibile creare, elencare e gestire task nel progetto utilizzando gli strumenti MCP.

## 6. Funzionalità 4: Integrazione LiteLLM Completa

### 6.1. Problema
Il sistema attualmente utilizza implementazioni mock per LiteLLM, limitando la capacità di utilizzare servizi AI reali per la generazione di task e analisi. Manca una configurazione robusta per gestire API keys, fallback e cost tracking.

### 6.2. Proposta di Soluzione

#### 6.2.1. Integrazione LiteLLM Reale
- Sostituire tutte le implementazioni mock con LiteLLM autentico
- Supporto per multipli provider AI (OpenAI, Anthropic, Perplexity, Google, xAI)
- Configurazione dinamica dei modelli tramite environment variables

#### 6.2.2. Environment Variable Management
- `OPENAI_API_KEY` - Chiave API OpenAI (modello principale)
- `ANTHROPIC_API_KEY` - Chiave API Claude (ricerca e analisi)
- `PERPLEXITY_API_KEY` - Chiave API Perplexity (web research)
- `GOOGLE_API_KEY`, `XAI_API_KEY` - Provider aggiuntivi
- `PYTASKAI_DEFAULT_MODEL`, `PYTASKAI_RESEARCH_MODEL` - Configurazione modelli

#### 6.2.3. Fallback Strategy e Error Handling
- Cascata automatica tra provider in caso di fallimento
- Rate limiting intelligente per evitare throttling
- Cache sistema per ridurre costi e latenza
- Graceful degradation quando AI non disponibile

#### 6.2.4. Cost Tracking e Budget Management
- Monitoraggio costi in tempo reale per provider
- Budget limits configurabili
- Report utilizzo dettagliati
- Ottimizzazione automatica modelli per ridurre costi

### 6.3. Criteri di Successo
- LiteLLM funziona con provider AI reali senza mock
- Sistema gestisce automaticamente fallback e rate limiting
- Costi sono tracciati e ottimizzati
- Configurazione flessibile tramite environment variables

## 7. Release 0.0.2 - Bugfix e Integrazione AI

### 7.1. Obiettivo
Rilasciare una versione stabile 0.0.2 che risolve i bug critici e introduce l'integrazione LiteLLM completa.

### 7.2. Componenti Release
- **Bugfixes MCP**: Risoluzione errori path e async compatibility
- **LiteLLM Integration**: Provider AI reali con fallback strategy
- **Enhanced Task Management**: Supporto migliorato per creation e management
- **Documentation Updates**: Guide aggiornate per nuove funzionalità

### 7.3. Validation Requirements
- Tutti i MCP tools devono funzionare senza errori
- Integrazione AI testata con almeno 2 provider
- Backward compatibility mantenuta
- Performance testing completato

### 7.4. Criteri di Successo
- Version 0.0.2 pubblicata su PyPI
- CHANGELOG.md aggiornato con tutte le modifiche
- MCP tools completamente funzionali
- User feedback positivo su stabilità

## 8. Considerazioni Future
- Interfaccia utente per la configurazione delle integrazioni (es. Jira).
- Meccanismi avanzati di gestione degli errori di sincronizzazione.
- Ottimizzazione delle performance per sincronizzazioni su larga scala.
