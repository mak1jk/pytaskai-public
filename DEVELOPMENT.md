# PyTaskAI - Guida allo Sviluppo

## 🔄 Sistema di Hot Reload e Restart

PyTaskAI include un sistema avanzato di hot reload e restart per semplificare lo sviluppo del server MCP.

### 🛠️ Tool MCP Disponibili

#### `hot_reload_modules_tool`
Ricarica i moduli Python senza riavviare il server MCP.

```python
# Esempio di utilizzo
mcp__pytaskai__hot_reload_modules_tool(
    project_root="/path/to/pytaskai",
    clear_cache=True  # Opzionale: pulisce la cache dei moduli
)
```

**Vantaggi:**
- ✅ Mantiene la connessione MCP attiva
- ✅ Applica le modifiche al codice istantaneamente
- ✅ Non interrompe le sessioni client
- ❌ Non funziona per cambiamenti strutturali profondi

#### `restart_mcp_server_tool` 
Riavvia completamente il server MCP.

```python
# Richiede conferma per sicurezza
mcp__pytaskai__restart_mcp_server_tool(
    project_root="/path/to/pytaskai",
    confirm=True,      # RICHIESTO per procedere
    graceful=True      # Shutdown graceful vs forzato
)
```

**Vantaggi:**
- ✅ Applica TUTTI i cambiamenti al codice
- ✅ Ricarica configurazioni e nuovi tool
- ❌ Interrompe la connessione client (riconnessione necessaria)

#### `get_module_status_tool`
Diagnostics dettagliati sui moduli caricati e stato server.

```python
mcp__pytaskai__get_module_status_tool(
    project_root="/path/to/pytaskai"
)
```

**Informazioni fornite:**
- 📊 Moduli caricati e loro percorsi
- 🏷️ Versioni PyTaskAI attive  
- 🗄️ Stato database SQLite
- 🐍 Informazioni processo Python

### 🐕 Development Server con Watchdog

Per sviluppo automatizzato, usa il development server:

```bash
# Server con auto-restart su modifiche file
python dev_server.py

# Opzioni avanzate
python dev_server.py --verbose --watch-dir custom_dir

# Solo server senza file watching
python dev_server.py --no-watchdog

# Server senza auto-restart (solo notifiche)
python dev_server.py --no-restart
```

**Caratteristiche:**
- 🐕 Monitoring automatico file Python
- 🔄 Restart automatico su modifiche
- 📝 Logging dettagliato delle operazioni
- ⏱️ Cooldown per evitare restart multipli
- 🛑 Graceful shutdown su Ctrl+C

### 📋 Workflow di Sviluppo Raccomandato

#### 1. **Modifiche Minori** (hot reload)
Per fix di bug o piccole modifiche logiche:

```bash
# 1. Modifica il codice
vim mcp_server/task_manager.py

# 2. Applica hot reload via MCP tool
mcp__pytaskai__hot_reload_modules_tool(clear_cache=True)

# 3. Testa immediatamente
```

#### 2. **Modifiche Strutturali** (restart completo)
Per nuovi tool, cambi configurazione, o modifiche architetturali:

```bash
# 1. Modifica il codice
vim mcp_server/task_manager.py

# 2. Restart server via MCP tool  
mcp__pytaskai__restart_mcp_server_tool(confirm=True)

# 3. Client MCP deve riconnettersi
# 4. Testa i nuovi tool
```

#### 3. **Sviluppo Continuo** (development server)
Per sessioni di sviluppo lunghe:

```bash
# Terminal 1: Development server
python dev_server.py --verbose

# Terminal 2: Modifica codice
# - Il server si riavvia automaticamente ad ogni modifica
# - I client MCP devono riconnettersi dopo ogni restart

# Terminal 3: Test MCP tools
# - Testa i tool dopo ogni riavvio automatico
```

### 🔧 Risoluzione Problemi Comuni

#### **Tool non disponibili dopo modifiche**
**Sintomo:** `Error: No such tool available: mcp__pytaskai__new_tool`

**Causa:** Server MCP usa versione cached del codice

**Soluzione:**
1. Usa `restart_mcp_server_tool(confirm=True)` 
2. Oppure riavvia manualmente il server MCP
3. Oppure usa il development server

#### **Hot reload non applica modifiche**
**Sintomo:** Modifiche al codice non si riflettono nel comportamento

**Causa:** 
- Modifica di configurazioni globali
- Nuovi import o dipendenze
- Modifiche a decoratori o metaclassi

**Soluzione:**
1. Usa restart completo invece di hot reload
2. Verifica con `get_module_status_tool` i moduli ricaricati

#### **Errori durante hot reload**
**Sintomo:** Hot reload fallisce con errori di import

**Causa:** Dipendenze circolari o moduli non compatibili con reload

**Soluzione:**
1. Usa `clear_cache=True` nell'hot reload
2. Se persiste, usa restart completo
3. Controlla logs per dettagli specifici

### 📊 Monitoring e Diagnostics

#### Verifica Stato Server
```python
# Controlla versioni e stato moduli
status = mcp__pytaskai__get_module_status_tool(project_root="/path/to/pytaskai")

print(f"Versione MCP Server: {status['version_info']['mcp_server_version']}")
print(f"Database: {status['database_status']['database_exists']}")
print(f"Moduli caricati: {len(status['module_info']['modules'])}")
```

#### Verifica Hot Reload Success
```python
# Esegui hot reload e controlla risultati
result = mcp__pytaskai__hot_reload_modules_tool(
    project_root="/path/to/pytaskai",
    clear_cache=True
)

print(f"Status: {result['status']}")
print(f"Moduli ricaricati: {result['operations'][1]['result']['summary']['successfully_reloaded']}")
print(f"Falliti: {result['operations'][1]['result']['summary']['failed']}")
```

### 🔄 Integrazione con IDE

#### Claude Code / Cursor
1. **Configura MCP server** nel `mcp.json`
2. **Usa hot reload tool** per applicare modifiche
3. **Restart server tool** per modifiche strutturali
4. **Module status tool** per diagnostics

#### VS Code
1. **Development server** in terminal integrato
2. **Auto-save** + **auto-restart** workflow
3. **Debugging** con logs dettagliati

### ⚡ Prestazioni e Ottimizzazioni

- **Hot reload**: ~1-2 secondi per applicare modifiche
- **Restart completo**: ~3-5 secondi + riconnessione client
- **Development server**: ~2-3 secondi per restart automatico

### 🚨 Limitazioni

1. **Hot reload non supporta:**
   - Nuovi tool MCP (richiede restart)
   - Modifiche a configurazioni globali
   - Cambi di dipendenze esterne

2. **Restart tool:**
   - Interrompe connessione client
   - Perde stato in-memory non persistito

3. **Development server:**
   - Richiede watchdog (`pip install watchdog`)
   - Client devono riconnettersi ad ogni restart

### 📚 Riferimenti

- **FastMCP Documentation**: [FastMCP Docs](https://fastmcp.dev)
- **MCP Protocol**: [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)
- **Watchdog**: [Python File Monitoring](https://pythonhosted.org/watchdog/)