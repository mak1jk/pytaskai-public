# 🤖 PyTaskAI

![](https://img.shields.io/badge/Python-3.8%2B-brightgreen?style=flat-square) ![](https://img.shields.io/badge/AI-Powered-blue?style=flat-square) ![](https://img.shields.io/badge/MCP-FastMCP-orange?style=flat-square) ![](https://img.shields.io/badge/UI-Streamlit-red?style=flat-square) ![](https://img.shields.io/badge/Version-0.0.1-success?style=flat-square)

**PyTaskAI** è un sistema avanzato di gestione task AI-powered che combina intelligenza artificiale, ricerca attiva e interfacce moderne per la gestione progetti professionale con integrazione MCP (Model Context Protocol).

## ✨ Caratteristiche Principali

- **🤖 AI-Powered Task Generation**: Genera task dettagliati da PRD usando LiteLLM multi-provider
- **🔍 Ricerca Attiva LTS**: Trova automaticamente versioni LTS e best practices aggiornate
- **🌐 Frontend Streamlit**: Interfaccia web moderna per gestione completa dei task
- **💰 Token & Cost Tracking**: Monitoring completo usage e costi AI con controlli budget
- **🔧 Claude Code Integration**: Setup automatico per Claude Code con supporto MCP
- **📊 MCP Server Tools**: Server FastMCP con tool completi per integrazione IDE
- **🚀 Workflow Agentico**: Processo AI intelligente con ricerca e generazione ottimizzata

## 🎯 Workflow Intelligente

1. **📋 PRD Analysis**: Analizza Product Requirements Document
2. **🔍 Research Phase**: Ricerca attiva di versioni LTS e best practices via Perplexity
3. **🤖 AI Generation**: Genera task dettagliati integrando ricerca e context
4. **📝 Task Management**: Gestisce task con UI web completa e tool MCP
5. **💸 Cost Optimization**: Traccia e ottimizza costi AI con cache intelligente

## 🚀 Quick Start

### 1. Installazione

```bash
# Clona il repository
git clone https://github.com/mak1jk/pytaskai-public.git
cd pytaskai

# Installa dipendenze
pip install -e .

# Oppure installa dalla PyPI (quando pubblicato)
pip install pytaskai
```

### 2. Configurazione API Keys

PyTaskAI supporta multiple provider AI. Configura almeno uno di questi:

```bash
# Crea file .env per API keys
cat > .env << EOF
# OpenAI (Raccomandato per iniziare)
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic (Per Claude models)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Perplexity (Per ricerca web e LTS research)
PERPLEXITY_API_KEY=your-perplexity-api-key-here

# Google AI (Opzionale)
GOOGLE_API_KEY=your-google-api-key-here

# xAI (Opzionale)
XAI_API_KEY=your-xai-api-key-here
EOF
```

**API Key Setup:**
- **OpenAI**: Vai su [platform.openai.com](https://platform.openai.com/api-keys)
- **Anthropic**: Vai su [console.anthropic.com](https://console.anthropic.com/keys)
- **Perplexity**: Vai su [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)

### 3. Configurazione MCP (Per Claude Code)

Aggiungi PyTaskAI al tuo MCP configuration file:

```json
{
  "servers": {
    "pytaskai": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/your/pytaskai-project",
      "env": {
        "OPENAI_API_KEY": "your-openai-key-here",
        "ANTHROPIC_API_KEY": "your-anthropic-key-here",
        "PERPLEXITY_API_KEY": "your-perplexity-key-here",
        "PYTASKAI_DEFAULT_MODEL": "gpt-4o-mini",
        "PYTASKAI_RESEARCH_MODEL": "perplexity/llama-3.1-sonar-small-128k-online",
        "PYTHONPATH": "/path/to/your/pytaskai-project"
      }
    }
  }
}
```

**Oppure usa il comando Claude Code:**

```bash
claude mcp add pytaskai -s user -- python -m mcp_server \
  --cwd "/path/to/your/pytaskai-project" \
  --env PYTASKAI_DEFAULT_MODEL="your-preferred-model" \
  PYTHONPATH="/path/to/your/pytaskai-project"
```

Vedi [MCP_CONFIGURATION.md](MCP_CONFIGURATION.md) per configurazione completa.

### 4. Primo Task da PRD

```bash
# Crea un nuovo progetto
mkdir my-project && cd my-project

# Inizializza PyTaskAI
pytaskai init

# Crea un PRD (o usa l'esempio)
cp scripts/example_prd.txt .pytaskai/docs/prd.txt

# Genera task automaticamente dal PRD
pytaskai parse-prd --research --target-tasks 10
```

### 5. Avvia UI Streamlit

```bash
# Avvia l'interfaccia web
python3 run_streamlit.py

# Oppure direttamente con streamlit
streamlit run frontend/streamlit_app.py
```

Apri **http://localhost:8501** per accedere alla UI!

## 📚 Utilizzo

### Frontend Streamlit

Il frontend offre 4 sezioni principali:

#### 📋 PRD Parser
- **Input PRD**: Incolla testo o carica file .txt/.md
- **Configurazione AI**: 
  - Target task count (1-50)
  - Enable AI research (più lento ma dettagliato)
  - Prefer LTS dependencies (raccomandato)
  - Overwrite existing tasks
- **Generazione**: Automatica con AI e validazione

#### 📝 Task Management  
- **Lista Task**: Visualizzazione completa con filtri
- **Filtri**: Status (pending/in-progress/done) e Priority (high/medium/low)
- **Statistiche**: Metrics real-time del progetto
- **Selezione**: Click per visualizzare dettagli

#### 🤖 AI Assistant
- **Chat Custom**: Descrivi cosa vuoi accomplire
- **Configurazione**: Research, LTS deps, priority
- **Generazione**: Task custom via AI conversation
- **Preview**: Visualizzazione dettagliata del task generato

#### 🔍 Task Details
- **Vista Completa**: Descrizione, details, test strategy
- **Dipendenze**: Relazioni tra task
- **Subtask**: Lista subtask con status
- **Metadata**: Date, complessità, stime ore

### Tool MCP Disponibili

PyTaskAI fornisce i seguenti tool MCP per integrazione IDE:

- `list_tasks_tool`: Lista tutti i task del progetto
- `get_task_tool`: Ottieni dettagli task specifico  
- `get_next_task_tool`: Trova prossimo task da fare
- `parse_prd_tool`: Genera task da PRD
- `validate_tasks_tool`: Valida struttura task
- `init_claude_support_tool`: Setup Claude Code integration

### Command Line Interface

```bash
# Inizializza nuovo progetto
pytaskai init [directory]

# Genera task da PRD  
pytaskai parse-prd [--research] [--target-tasks N]

# Lista task
pytaskai list [--status STATUS] [--priority PRIORITY]

# Ottieni prossimo task
pytaskai next

# Valida task structure
pytaskai validate

# Setup Claude Code integration
pytaskai init-claude
```

## 🔧 Configurazione Avanzata

### Modelli AI

Configura modelli specifici per diversi use case:

```bash
# Configurazione modelli via environment variables
export PYTASKAI_DEFAULT_MODEL="gpt-4o-mini"           # Task generation standard
export PYTASKAI_RESEARCH_MODEL="perplexity/llama-3.1-sonar-small-128k-online"  # Research web
export PYTASKAI_LTS_MODEL="anthropic/claude-3-haiku-20240307"  # LTS research
export PYTASKAI_FALLBACK_MODEL="gpt-3.5-turbo"       # Fallback model
```

### Configurazioni Preset

#### Budget-Friendly Setup
```bash
export PYTASKAI_DEFAULT_MODEL="gpt-4o-mini"
export PYTASKAI_RESEARCH_MODEL="gpt-4o-mini" 
export PYTASKAI_LTS_MODEL="gpt-4o-mini"
```

#### High-Quality Setup
```bash
export PYTASKAI_DEFAULT_MODEL="gpt-4o"
export PYTASKAI_RESEARCH_MODEL="perplexity/llama-3.1-sonar-large-128k-online"
export PYTASKAI_LTS_MODEL="anthropic/claude-3-sonnet-20240229"
```

#### Claude-Focused Setup
```bash
export PYTASKAI_DEFAULT_MODEL="anthropic/claude-3-haiku-20240307"
export PYTASKAI_RESEARCH_MODEL="anthropic/claude-3-sonnet-20240229"
export PYTASKAI_LTS_MODEL="anthropic/claude-3-haiku-20240307"
```

## 🏗️ Architettura

### Core Components

```
PyTaskAI/
├── mcp_server/              # MCP Server e AI Service
│   ├── ai_service.py        # LiteLLM multi-provider AI
│   ├── task_manager.py      # FastMCP tools
│   ├── prompts/             # Sistema prompt centralizzati  
│   └── utils.py             # Utilities shared
├── frontend/                # Streamlit UI
│   ├── streamlit_app.py     # Main UI application
│   └── components/          # UI components
├── shared/                  # Modelli e schemas
│   ├── models.py            # Pydantic models
│   └── schemas.py           # JSON schemas
└── tasks/                   # Task storage
    └── tasks.json           # Task database
```

### AI Service Architecture

Il sistema AI utilizza un approccio agentico sofisticato:

1. **Research Phase** (Opzionale):
   - Estrae tecnologie dal prompt utente
   - Ricerca versioni LTS correnti via Perplexity
   - Identifica best practices pertinenti

2. **Generation Phase**:
   - Integra research findings nel context
   - Genera task dettagliati con prompt engineering
   - Valida output con JSON schema

3. **Cost Optimization**:
   - Cache intelligente per research results
   - Model selection basata su use case
   - Token usage tracking e budgeting

## 🧪 Testing

### Test Streamlit App
```bash
# Test logica app (senza dipendenze)
python3 test_streamlit_logic.py

# Test completo (richiede dipendenze)
python3 test_streamlit_basic.py
```

### Test MCP Tools
```bash
# Test tool MCP individuali
python3 test_task7.py

# Test integrazione completa
python3 test_task18_simple.py
```

### Test AI Service
```bash
# Test AI service e prompts
python3 test_task5_aiservice.py

# Test modelli Pydantic
python3 tests/test_models.py
```

## 🐛 Troubleshooting

### Problemi Comuni

**Errore "No module named 'streamlit'":**
```bash
pip install streamlit>=1.28.0
```

**Errore "No module named 'fastmcp'":**
```bash
pip install fastmcp>=0.4.0
```

**Errore API Key:**
```bash
# Verifica API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Tasks non si caricano:**
```bash
# Verifica struttura progetto
ls -la .pytaskai/
ls -la tasks/tasks.json

# Reinizializza se necessario  
pytaskai init --force
```

**MCP Server non risponde:**
```bash
# Test connessione MCP
python -m pytaskai.mcp_server --test

# Verifica configurazione Claude Code
cat ~/.config/claude-code/mcp_settings.json
```

### Debug Mode

Abilita logging dettagliato:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

O via environment variable:
```bash
export PYTASKAI_LOG_LEVEL=DEBUG
```

## 📖 Documentazione Completa

- **[MCP Configuration Guide](MCP_CONFIGURATION.md)**: Setup completo MCP server
- **[Streamlit Frontend Guide](README_STREAMLIT.md)**: Guida dettagliata UI
- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)**: Dettagli tecnici implementazione
- **[API Documentation](docs/api.md)**: Reference completa API

## 🤝 Contribuire

### Setup Sviluppo

```bash
# Clone e setup
git clone https://github.com/mak1jk/pytaskai-public.git
cd pytaskai

# Install in development mode
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

### Linee Guida

1. **Code Style**: Usa `black` e `isort` per formatting
2. **Testing**: Aggiungi test per nuove funzionalità
3. **Documentation**: Aggiorna documentazione per modifiche API
4. **Type Hints**: Usa typing completo per tutto il codice
5. **MCP Tools**: Nuovi tool devono seguire pattern FastMCP

### Aree di Contribuzione

- 🧪 **Testing**: Aggiungi test cases e edge cases
- 📚 **Documentation**: Migliora guide e tutorials  
- 🎨 **UI/UX**: Enhance Streamlit interface
- 🤖 **AI Integration**: Nuovi provider AI e prompt optimization
- 🔧 **MCP Tools**: Nuovi tool per workflow specifici
- 📊 **Analytics**: Metrics e monitoring avanzati

## 📄 License

PyTaskAI is licensed under the **MIT License with Commons Clause**. This means you can:

✅ **Allowed:**
- Use PyTaskAI for any purpose (personal, commercial, academic)
- Modify the code
- Distribute copies
- Create and sell products built using PyTaskAI

❌ **Not Allowed:**
- Sell PyTaskAI itself
- Offer PyTaskAI as a hosted service
- Create competing products based on PyTaskAI

See the [LICENSE.md](LICENSE.md) file for the complete license text and licensing details.

## 🙏 Ringraziamenti

- **Anthropic** per Claude AI e MCP protocol
- **OpenAI** per GPT models e API
- **Perplexity** per ricerca web real-time
- **Streamlit** per framework UI
- **LiteLLM** per multi-provider AI integration
- **FastMCP** per MCP server implementation
- **[Claude Task Master](https://github.com/eyaltoledano/claude-task-master)** per l'ispirazione iniziale

---

**Costruito con ❤️ per automatizzare la gestione progetti con AI**

🚀 **[Get Started Now](#-quick-start)** | 📚 **[Frontend Guide](README_STREAMLIT.md)** | 🐛 **[Report Bug](https://github.com/mak1jk/pytaskai-public/issues)** | 💬 **[Discussions](https://github.com/mak1jk/pytaskai-public/discussions)**
