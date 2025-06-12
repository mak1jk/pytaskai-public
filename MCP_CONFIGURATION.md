# PyTaskAI MCP Server Configuration

## JSON Configuration for Claude Code / MCP Clients

Add this configuration to your MCP client (Claude Code, Cline, etc.):

```json
{
  "servers": {
    "pytaskai": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/your/pytaskai/project/root", // Crucial: Set to your project's root directory
      "env": {
        // === AI Model API Keys (Required) ===
        "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
        "PERPLEXITY_API_KEY": "YOUR_PERPLEXITY_API_KEY_HERE", 
        "OPENAI_API_KEY": "YOUR_OPENAI_KEY_HERE",
        "GOOGLE_API_KEY": "YOUR_GOOGLE_KEY_HERE",
        "MISTRAL_API_KEY": "YOUR_MISTRAL_KEY_HERE",
        "OPENROUTER_API_KEY": "YOUR_OPENROUTER_KEY_HERE",
        "XAI_API_KEY": "YOUR_XAI_KEY_HERE",
        "AZURE_OPENAI_API_KEY": "YOUR_AZURE_KEY_HERE",
        
        // === AI Model Selection (Optional) ===
        "PYTASKAI_DEFAULT_MODEL": "gpt-4o-mini",
        "PYTASKAI_RESEARCH_MODEL": "anthropic/claude-3-haiku-20240307",
        "PYTASKAI_LTS_MODEL": "perplexity/llama-3-sonar-large-32k-online",
        "PYTASKAI_BEST_PRACTICES_MODEL": "perplexity/llama-3-sonar-large-32k-online",
        "PYTASKAI_FALLBACK_MODEL": "gpt-3.5-turbo",
        
        // === AI Model Parameters (Optional) ===
        "PYTASKAI_DEFAULT_TEMPERATURE": "0.7",
        "PYTASKAI_RESEARCH_TEMPERATURE": "0.3",
        "PYTASKAI_SEARCH_TEMPERATURE": "0.1",
        "PYTASKAI_MAX_TOKENS": "4096",
        
        // === PyTaskAI Configuration (Optional) ===
        "PYTASKAI_PROJECT_ROOT": "/path/to/your/project",
        "PYTASKAI_CACHE_TTL": "3600",
        "PYTASKAI_LOG_LEVEL": "INFO"
      },
      "type": "stdio"
    }
  }
}
```

## Environment Variables Reference

### AI Model API Keys (Required)

You need API keys for the providers you want to use:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | For Claude models | Get from [Anthropic Console](https://console.anthropic.com/) |
| `PERPLEXITY_API_KEY` | For research/LTS search | Get from [Perplexity API](https://www.perplexity.ai/settings/api) |
| `OPENAI_API_KEY` | For GPT models | Get from [OpenAI Platform](https://platform.openai.com/api-keys) |
| `GOOGLE_API_KEY` | For Gemini models | Get from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `XAI_API_KEY` | For Grok models | Get from [xAI Console](https://console.x.ai/) |
| `OPENROUTER_API_KEY` | For OpenRouter | Get from [OpenRouter](https://openrouter.ai/keys) |

### AI Model Selection (Optional)

Configure which models to use for different operations:

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTASKAI_DEFAULT_MODEL` | `gpt-4o-mini` | Main model for task generation |
| `PYTASKAI_RESEARCH_MODEL` | `anthropic/claude-3-haiku-20240307` | Model for research-enhanced generation |
| `PYTASKAI_LTS_MODEL` | `perplexity/llama-3-sonar-large-32k-online` | Model for LTS version research |
| `PYTASKAI_BEST_PRACTICES_MODEL` | `perplexity/llama-3-sonar-large-32k-online` | Model for best practices research |
| `PYTASKAI_FALLBACK_MODEL` | `gpt-3.5-turbo` | Fallback model when primary fails |

### Supported Model Names

#### OpenAI Models
- `gpt-4o` - Latest GPT-4 Omni (expensive, high quality)
- `gpt-4o-mini` - **Recommended default** (fast, cheap, good quality)
- `gpt-4-turbo` - GPT-4 Turbo (high quality)
- `gpt-3.5-turbo` - GPT-3.5 (cheap fallback)

#### Anthropic Models  
- `anthropic/claude-3-opus-20240229` - Highest quality (expensive)
- `anthropic/claude-3-sonnet-20240229` - Balanced quality/cost
- `anthropic/claude-3-haiku-20240307` - **Recommended for research** (fast, cheap)

#### Perplexity Models (for web research)
- `perplexity/llama-3-sonar-large-32k-online` - **Recommended for LTS/best practices**
- `perplexity/llama-3-sonar-small-32k-online` - Cheaper alternative

#### Google Models
- `google/gemini-pro` - Google's flagship model
- `google/gemini-pro-vision` - With vision capabilities

#### xAI Models
- `xai/grok-beta` - xAI's Grok model

### AI Model Parameters (Optional)

Fine-tune model behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTASKAI_DEFAULT_TEMPERATURE` | `0.7` | Creativity for task generation (0.0-1.0) |
| `PYTASKAI_RESEARCH_TEMPERATURE` | `0.3` | Lower for factual research |
| `PYTASKAI_SEARCH_TEMPERATURE` | `0.1` | Very low for precise search |
| `PYTASKAI_MAX_TOKENS` | `4096` | Maximum response length |

### PyTaskAI Configuration (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTASKAI_PROJECT_ROOT` | Current directory | Default project root for operations |
| `PYTASKAI_CACHE_TTL` | `3600` | AI response cache time (seconds) |
| `PYTASKAI_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Example Configurations

### Budget-Friendly Setup
```json
"env": {
  "OPENAI_API_KEY": "your-key",
  "PYTASKAI_DEFAULT_MODEL": "gpt-3.5-turbo",
  "PYTASKAI_RESEARCH_MODEL": "gpt-3.5-turbo",
  "PYTASKAI_LTS_MODEL": "gpt-3.5-turbo",
  "PYTASKAI_BEST_PRACTICES_MODEL": "gpt-3.5-turbo"
}
```

### High-Quality Setup
```json
"env": {
  "OPENAI_API_KEY": "your-openai-key",
  "ANTHROPIC_API_KEY": "your-anthropic-key", 
  "PERPLEXITY_API_KEY": "your-perplexity-key",
  "PYTASKAI_DEFAULT_MODEL": "gpt-4o",
  "PYTASKAI_RESEARCH_MODEL": "anthropic/claude-3-sonnet-20240229",
  "PYTASKAI_LTS_MODEL": "perplexity/llama-3-sonar-large-32k-online",
  "PYTASKAI_BEST_PRACTICES_MODEL": "perplexity/llama-3-sonar-large-32k-online"
}
```

### Claude-Focused Setup
```json
"env": {
  "ANTHROPIC_API_KEY": "your-anthropic-key",
  "PERPLEXITY_API_KEY": "your-perplexity-key",
  "PYTASKAI_DEFAULT_MODEL": "anthropic/claude-3-haiku-20240307",
  "PYTASKAI_RESEARCH_MODEL": "anthropic/claude-3-sonnet-20240229",
  "PYTASKAI_LTS_MODEL": "perplexity/llama-3-sonar-large-32k-online"
}
```

## Local Development Setup

When running the `pytaskai` MCP server locally for development, especially if you haven't installed it as a system-wide package, ensure the following in your MCP client configuration for the `pytaskai` server:

1.  **`command`**: Set to `"python"`.
2.  **`args`**: Set to `["-m", "mcp_server"]`. This instructs Python to run the `mcp_server` package located within your project.
3.  **`cwd` (Current Working Directory)**: This **must** be set to the absolute path of your `pytaskai` project's root directory (e.g., `/Users/marcomacri/Desktop/cartella progetti github/pytaskai`). This is crucial for Python to correctly locate the `mcp_server` package when using the `-m` flag.
4.  **`PYTHONPATH` Environment Variable (Recommended)**: While `cwd` is key for the `-m` flag, also setting `PYTHONPATH` in the `env` block to your project's root directory is good practice. It ensures that any internal imports within your `mcp_server` code (e.g., `from shared import models`) are resolved correctly.

   Example `pytaskai` server configuration snippet:
   ```json
   {
     // ... other servers ...
     "pytaskai": {
       "command": "python",
       "args": ["-m", "mcp_server"],
       "cwd": "/path/to/your/pytaskai/project/root", // Crucial: Set to your project's root
       "env": {
         // ... your API keys and other PyTaskAI specific env vars ...
         "PYTHONPATH": "/path/to/your/pytaskai/project/root" // Recommended for local dev
       },
       "type": "stdio" // Or other type if applicable
     }
     // ...
   }
   ```
This setup ensures that Python can find and execute the `mcp_server` module correctly.

## Usage Notes

1. **Minimum Required**: You need at least one API key. PyTaskAI will use available models and fallback as needed.

2. **Cost Optimization**: 
   - Use `gpt-4o-mini` for default generation (very cheap)
   - Use Perplexity for research (web access required)
   - Use `gpt-3.5-turbo` as fallback

3. **Research Features**: LTS search and best practices require web-enabled models (Perplexity recommended).

4. **Model Auto-Detection**: PyTaskAI automatically detects provider from model name.

5. **Rate Limiting**: Automatic rate limiting per provider to prevent API errors.

6. **Caching**: AI responses are cached to reduce costs and improve performance.

## Troubleshooting

- **Model not found**: Check model name spelling and ensure API key is set
- **Rate limits**: PyTaskAI handles this automatically with delays
- **High costs**: Use cheaper models like `gpt-4o-mini` or `gpt-3.5-turbo`
- **Research not working**: Ensure Perplexity API key is set for web research