# ============================================
# Rate Limiting Configuration (to avoid 429 errors)
# ============================================

# Which LLM providers to use (disable some to reduce API calls)
ENABLE_OPENAI=true      # OpenAI GPT-4
ENABLE_GEMINI=true      # Google Gemini
ENABLE_GROK=false       # Grok (disabled by default)

# Concurrent request limits (reduce if hitting rate limits)
MAX_CONCURRENT_LLM_CALLS=3  # Max parallel LLM calls at once (default: 3)
                            # Lower this to 1-2 if you have tight rate limits
                            # With 3 agents, setting this to 1 means sequential processing

# Retry configuration
RETRY_DELAY_SECONDS=2       # Initial delay between retries
EXPONENTIAL_BACKOFF=true    # Use exponential backoff (2s, 4s, 8s...)
MAX_RETRIES=3              # Number of retry attempts

# Tips to avoid 429 errors:
# 1. Set ENABLE_GROK=false (reduces from 9 to 6 LLM calls per review)
# 2. Set MAX_CONCURRENT_LLM_CALLS=1 (sequential instead of parallel)
# 3. Increase RETRY_DELAY_SECONDS to 5 or 10
# 4. For free tier APIs, consider using only ONE provider (fastest, cheapest)
#    Example: ENABLE_OPENAI=true, ENABLE_GEMINI=false, ENABLE_GROK=false
