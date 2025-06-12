# 🚀 PyTaskAI Quick Start Guide

## 📋 Prerequisiti

- Python 3.8+ installato
- Una API key per almeno un provider AI (OpenAI raccomandato)

## ⚡ Avvio Rapido (5 minuti)

### 1. **Configurazione API Key**
```bash
# Copia il template di configurazione
cp .env.example .env

# Modifica .env con la tua API key
nano .env
# o
code .env
```

**Minimo richiesto:** aggiungi la tua OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. **Test di Base**
```bash
# Test rapido che il sistema funzioni
python3 pytaskai_minimal.py --help
```

### 3. **Primo Utilizzo**
Scegli una delle opzioni qui sotto:

---

## 🎯 Modi di Utilizzo

### **A) CLI Interattivo** (Raccomandato per iniziare)
```bash
# Avvia il CLI principale con tutti i comandi
python3 pytaskai_cli.py

# Oppure con comando specifico
python3 pytaskai_cli.py list-tasks
python3 pytaskai_cli.py add-task "Implementare login utente"
```

### **B) Interfaccia Web Streamlit** (Più user-friendly)
```bash
# Avvia il frontend web
python3 -m streamlit run frontend/streamlit_app.py

# Oppure usa lo script helper
python3 run_streamlit.py
```

Poi apri http://localhost:8501 nel browser.

### **C) Server MCP per Claude Code**
```bash
# Per integrare con Claude Code/IDE
python3 -m mcp_server.task_manager
```

### **D) Setup Guidato** (Prima configurazione)
```bash
# Wizard per configurazione completa
python3 setup_cli.py
```

---

## 📝 Primi Passi

### 1. **Crea il tuo primo progetto**

**Opzione A - Da PRD:**
```bash
# Se hai un documento di requisiti
echo "Creare un'app mobile per gestione spese personali" > my_prd.txt
python3 pytaskai_cli.py parse-prd my_prd.txt
```

**Opzione B - Task manuale:**
```bash
# Aggiungi task singoli
python3 pytaskai_cli.py add-task "Setup ambiente di sviluppo"
python3 pytaskai_cli.py add-task "Creare database schema"
```

### 2. **Gestisci i task**
```bash
# Vedi tutti i task
python3 pytaskai_cli.py list-tasks

# Prendi il prossimo task da fare
python3 pytaskai_cli.py next-task

# Cambia stato di un task
python3 pytaskai_cli.py set-status 1 in-progress

# Espandi un task in subtask dettagliati
python3 pytaskai_cli.py expand-task 1
```

### 3. **Analisi AI avanzata**
```bash
# Analizza complessità dei task
python3 pytaskai_cli.py analyze-complexity

# Aggiorna un subtask con AI
python3 pytaskai_cli.py update-subtask 1.2 "Aggiungere validazione email"
```

---

## 🎨 Interfaccia Web (Streamlit)

L'interfaccia web offre:

- 📊 **Dashboard visuale** con progress charts
- 🎯 **Gestione drag-and-drop** dei task
- 🤖 **AI integration** con progress tracking
- 💰 **Cost monitoring** in tempo reale
- 🔍 **Ricerca avanzata** e filtri

**Per avviarla:**
```bash
python3 -m streamlit run frontend/streamlit_app.py
```

---

## ⚙️ Configurazione Avanzata

### **Modelli AI supportati:**
- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet`, `claude-3-haiku`
- Google: `gemini-pro`, `gemini-pro-vision`
- Perplexity: `llama-3.1-sonar-small`, `llama-3.1-sonar-large`

### **Comandi CLI principali:**
```bash
# Gestione task
pytaskai_cli.py list-tasks
pytaskai_cli.py add-task "Descrizione task"
pytaskai_cli.py expand-task <id>
pytaskai_cli.py set-status <id> <status>
pytaskai_cli.py next-task

# Analisi AI
pytaskai_cli.py analyze-complexity
pytaskai_cli.py update-subtask <id> "Modifica"

# Gestione dipendenze
pytaskai_cli.py add-dependency <task_id> <depends_on>
pytaskai_cli.py validate-dependencies

# Utility
pytaskai_cli.py init-claude-support
pytaskai_cli.py cost-report
```

---

## 🆘 Troubleshooting

### **Errore "No module named ..."**
```bash
# Installa dipendenze mancanti
pip install fastmcp pydantic litellm streamlit rich click
```

### **Errore API Key**
```bash
# Verifica che .env contenga le chiavi corrette
cat .env | grep API_KEY
```

### **Errore permessi**
```bash
# Dai permessi di esecuzione
chmod +x pytaskai_cli.py pytaskai_minimal.py setup_cli.py
```

### **Porta Streamlit occupata**
```bash
# Usa una porta diversa
python3 -m streamlit run frontend/streamlit_app.py --server.port 8502
```

---

## 🎯 Prossimi Passi

1. **Esplora la documentazione completa** in `docs/`
2. **Integra con Claude Code** usando il server MCP
3. **Personalizza i prompt** in `mcp_server/prompts/`
4. **Contribuisci** al progetto su GitHub

Buon task management con PyTaskAI! 🚀