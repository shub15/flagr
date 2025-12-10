# LLM Provider Changes

## New Configuration (as of 2025-12-10)

### Council Members (for Agents)
- **OpenAI GPT-4** - Primary reasoning
- **Mistral Large** - Fast, cost-effective alternative
- **Groq (Llama 3.1 70B)** - Ultra-fast inference (optional)

### Referee
- **Gemini 1.5 Flash** - Single LLM (no council) for fast, reliable aggregation

## Previous Configuration
- Council: OpenAI + Gemini + Grok
- Referee: Council-based consensus

## Why the Change?

### 1. **Gemini → Referee (Single LLM)**
**Before:** Gemini was in council with consensus voting
**After:** Gemini is dedicated Referee
**Benefits:**
- Faster aggregation (no council overhead)
- More reliable (no consensus conflicts)
- Better for deterministic scoring

### 2. **Grok → Groq**
**Before:** Grok (xAI) - slower, limited availability
**After:** Groq - ultra-fast inference platform
**Benefits:**
- 10x faster response times
- Better rate limits
- Cheaper API costs
- Supports open models (Llama, Mixtral)

### 3. **Added Mistral**
**Why:** Cost-effective alternative to GPT-4
**Benefits:**
- Cheaper than OpenAI
- Good legal reasoning
- European data privacy if needed

## API Keys Needed

```bash
# Required
OPENAI_API_KEY=sk-...          # Get from platform.openai.com
GOOGLE_API_KEY=AI...           # Get from ai.google.dev
MISTRAL_API_KEY=...            # Get from console.mistral.ai

# Optional (enable in .env)
GROQ_API_KEY=gsk_...           # Get from console.groq.com
```

## Configuration Options

### Budget-Conscious
```bash
# Use only Mistral (cheapest)
ENABLE_OPENAI=false
ENABLE_MISTRAL=true
ENABLE_GROQ=false
```

### Speed-Focused
```bash
# Use Groq for ultra-fast inference
ENABLE_OPENAI=false
ENABLE_MISTRAL=false
ENABLE_GROQ=true
```

### Quality-Focused
```bash
# Use OpenAI + Mistral
ENABLE_OPENAI=true
ENABLE_MISTRAL=true
ENABLE_GROQ=false
```

### Maximum Reliability
```bash
# All three providers
ENABLE_OPENAI=true
ENABLE_MISTRAL=true
ENABLE_GROQ=true
```

## Architecture Diagram

```
Contract Upload
      ↓
   RAG Retrieval (3 calls)
      ↓
   ┌──────────────┬──────────────┬──────────────┐
   │   Skeptic    │  Strategist  │   Auditor    │
   │              │              │              │
   │  ┌────────┐  │  ┌────────┐  │  ┌────────┐  │
   │  │ OpenAI │  │  │ OpenAI │  │  │ OpenAI │  │
   │  │Mistral │  │  │Mistral │  │  │Mistral │  │
   │  │  Groq  │  │  │  Groq  │  │  │  Groq  │  │
   │  └────────┘  │  └────────┘  │  └────────┘  │
   │   Council    │   Council    │   Council    │
   │  Consensus   │  Consensus   │  Consensus   │
   └──────────────┴──────────────┴──────────────┘
                  ↓
              Referee
         (Gemini 1.5 Flash)
          Algorithmic +
         AI Aggregation
                  ↓
          Final Result
```

## Performance Impact

**Before (Grok + Gemini in council):**
- 9 LLM calls per review (3 agents × 3 LLMs)
- ~30-45 seconds total
- Higher rate limit pressure

**After (Groq + Mistral in council, Gemini for Referee):**
- 6-9 LLM calls (depending on enabled providers)
- ~10-20 seconds with Groq
- Lower costs with Mistral
- More flexible configuration

## Migration Guide

1. **Get new API keys:**
   ```bash
   # Mistral (required)
   https://console.mistral.ai
   
   # Groq (optional, but recommended)
   https://console.groq.com
   ```

2. **Update .env:**
   ```bash
   # Remove
   # GROK_API_KEY=...
   
   # Add
   MISTRAL_API_KEY=your_mistral_key
   GROQ_API_KEY=your_groq_key
   
   # Update flags
   ENABLE_MISTRAL=true
   ENABLE_GROQ=false  # or true for max speed
   ```

3. **Restart server:**
   ```bash
   # Will auto-detect new configuration
   uvicorn app.main:app --reload
   ```

## Cost Comparison (per 1M tokens)

| Provider | Input | Output | Notes |
|----------|-------|--------|-------|
| OpenAI GPT-4 Turbo | $10 | $30 | Highest quality |
| Mistral Large | $4 | $12 | Best value |
| Groq (Llama 3.1 70B) | $0.59 | $0.79 | Ultra fast, cheapest |
| Gemini 1.5 Flash | Free tier | Free tier | Referee only |

**Estimated cost per review:**
- **All enabled:** ~$0.05-0.08
- **OpenAI + Mistral:** ~$0.03-0.05
- **Mistral only:** ~$0.01-0.02
- **Groq only:** ~$0.003-0.005

## Troubleshooting

**Q: I get "No LLM providers enabled!" error**
A: Add API keys and set ENABLE_OPENAI=true or ENABLE_MISTRAL=true

**Q: Groq is fast but quality seems lower**
A: Groq runs open models. Use for speed, not maximum quality.

**Q: Should I use all three providers?**
A: For best quality: OpenAI + Mistral. For speed: Groq. For cost: Mistral only.

**Q: What happened to Gemini in the council?**
A: Moved to Referee for better aggregation performance.
