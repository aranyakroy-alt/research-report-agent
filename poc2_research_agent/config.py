import os
from dotenv import load_dotenv

load_dotenv()

# Read API keys from environment (or .env)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

MAX_TOOL_CALLS = 20
MAX_LOOP_ITERATIONS = 5
MIN_DIMENSIONS = 5
MAX_BRIEF_WORDS = 650
TOOL_TIMEOUT_SECONDS = 10

MODEL_PRICING = {
    "claude-sonnet-4-6":         {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 1.00,  "output": 5.00},
    "gpt-4o":                    {"input": 5.00,  "output": 15.00},
    "gpt-4o-mini":               {"input": 0.15,  "output": 0.60},
}

SCENARIOS = {
    "S-A": {"C2": "claude-sonnet-4-6",         "C3": "claude-sonnet-4-6",         "C4": "claude-sonnet-4-6",         "C5": "claude-sonnet-4-6"},
    "S-B": {"C2": "claude-haiku-4-5-20251001", "C3": "claude-haiku-4-5-20251001", "C4": "claude-haiku-4-5-20251001", "C5": "claude-haiku-4-5-20251001"},
    "S-C": {"C2": "gpt-4o",                    "C3": "gpt-4o",                    "C4": "gpt-4o",                    "C5": "gpt-4o"},
    "S-D": {"C2": "gpt-4o-mini",               "C3": "gpt-4o-mini",               "C4": "gpt-4o-mini",               "C5": "gpt-4o-mini"},
    "S-E": {"C2": "claude-haiku-4-5-20251001", "C3": "claude-haiku-4-5-20251001", "C4": "claude-sonnet-4-6",         "C5": "claude-sonnet-4-6"},
    "S-F": {"C2": "claude-sonnet-4-6",         "C3": "claude-haiku-4-5-20251001", "C4": "claude-sonnet-4-6",         "C5": "gpt-4o"},
}
