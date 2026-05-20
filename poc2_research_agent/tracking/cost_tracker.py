"""Cost tracking wrapper for all LLM calls.

All LLM usage must go through CostTracker.call_llm which records tokens,
cost and latency, writes entries to a JSON append-only log and keeps an
in-memory session log.
"""
import json
import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from poc2_research_agent.config import MODEL_PRICING

# Resolve the outputs directory relative to this file (package root/outputs/)
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_LOG_PATH = os.path.join(_PKG_ROOT, "outputs", "cost_log.json")

# Process-level lock to prevent concurrent writes corrupting the JSON log
_LOG_LOCK = threading.Lock()


class LLMCallError(Exception):
    pass


class CostTracker:
    def __init__(self, scenario: str, company: str, log_path: str = _DEFAULT_LOG_PATH):
        self.scenario = scenario
        self.company = company
        self.log_path = log_path
        self.session_calls: List[Dict[str, Any]] = []

    def call_llm(self, component: str, model: str, messages: List[Dict[str, Any]], system: Optional[str] = None, max_tokens: int = 1000) -> str:
        """Unified LLM call wrapper for Anthropic and OpenAI.

        Returns the response text on success. On failure logs the error and
        raises LLMCallError.
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        # naive token estimate: characters/4
        prompt_text = "\n".join([str(m) for m in messages])
        input_tokens = max(1, len(prompt_text) // 4)

        start = time.time()
        try:
            if model.startswith("claude-"):
                resp_text, out_tokens = self._call_anthropic(model, messages, system, max_tokens)
            elif model.startswith("gpt-"):
                resp_text, out_tokens = self._call_openai(model, messages, system, max_tokens)
            else:
                raise LLMCallError(f"Unknown model prefix for model '{model}'")

            latency_ms = int((time.time() - start) * 1000)
            output_tokens = int(out_tokens)
            cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

            entry = {
                "timestamp": timestamp,
                "scenario": self.scenario,
                "company": self.company,
                "component": component,
                "model": model,
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
            }

            self.session_calls.append(entry)
            self._write_to_log(entry)
            return resp_text

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            # Log failure entry
            failure_entry = {
                "timestamp": timestamp,
                "scenario": self.scenario,
                "company": self.company,
                "component": component,
                "model": model,
                "input_tokens": int(input_tokens),
                "output_tokens": 0,
                "cost_usd": 0.0,
                "latency_ms": latency_ms,
                "error": str(e),
            }
            # Always record the failure (in-memory and on disk)
            try:
                self.session_calls.append(failure_entry)
                self._write_to_log(failure_entry)
            except Exception:
                # _write_to_log must be silent on failure; swallow all
                pass
            raise LLMCallError(str(e))

    def get_session_summary(self) -> Dict[str, Any]:
        total_cost = sum(c.get("cost_usd", 0.0) for c in self.session_calls)
        total_latency = sum(c.get("latency_ms", 0) for c in self.session_calls)
        total_input = sum(c.get("input_tokens", 0) for c in self.session_calls)
        total_output = sum(c.get("output_tokens", 0) for c in self.session_calls)

        calls_by_component: Dict[str, Dict[str, Any]] = {}
        for c in self.session_calls:
            comp = c.get("component")
            if comp not in calls_by_component:
                calls_by_component[comp] = {"cost": 0.0, "latency_ms": 0, "calls": 0}
            calls_by_component[comp]["cost"] += c.get("cost_usd", 0.0)
            calls_by_component[comp]["latency_ms"] += c.get("latency_ms", 0)
            calls_by_component[comp]["calls"] += 1

        return {
            "scenario": self.scenario,
            "company": self.company,
            "total_cost_usd": total_cost,
            "total_latency_ms": total_latency,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "calls_by_component": calls_by_component,
        }

    def _write_to_log(self, entry: Dict[str, Any]):
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with _LOG_LOCK:
                try:
                    with open(self.log_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                except (FileNotFoundError, json.JSONDecodeError):
                    data = []

                data.append(entry)
                with open(self.log_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: failed to write cost log: {e}")

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            # Default to zero if unknown model
            return 0.0
        input_price = pricing["input"]
        output_price = pricing["output"]
        cost = (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price
        return cost

    # The following helper methods encapsulate SDK calls so tests can mock the SDKs.
    def _call_anthropic(self, model: str, messages: List[Dict[str, Any]], system: Optional[str], max_tokens: int):
        import anthropic

        Client = getattr(anthropic, "Anthropic", None)
        if Client is None:
            raise RuntimeError("Anthropic SDK not available")

        # ── Tests mock client.create (dict return) ──────────────────────────────
        # When tests monkeypatch `client.create` we honour that shape first.
        client = Client()
        if hasattr(client, "create"):
            result = client.create(model=model, messages=messages, system=system, max_tokens=max_tokens)
            if isinstance(result, dict):
                text = result.get("text") or result.get("completion") or result.get("output") or ""
                out_tokens = result.get("output_tokens", 0)
            else:
                text = getattr(result, "text", getattr(result, "completion", ""))
                out_tokens = getattr(result, "output_tokens", 0)
            return text, out_tokens

        # ── Live SDK path: client.messages.create ───────────────────────────────
        # Anthropic Messages API requires system to be a top-level param, NOT
        # a message with role="system". Strip any such messages and merge them.
        clean_messages = []
        extracted_system_parts = []
        for m in messages:
            if m.get("role") == "system":
                extracted_system_parts.append(m.get("content", ""))
            else:
                clean_messages.append(m)

        # Build final system string (explicit arg wins, else extracted)
        final_system: Optional[str] = system
        if extracted_system_parts:
            extracted = "\n".join(extracted_system_parts)
            final_system = (final_system + "\n" + extracted) if final_system else extracted

        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": clean_messages,
        }
        if final_system:
            kwargs["system"] = final_system
        result = client.messages.create(**kwargs)
        # result is an anthropic.types.Message
        if hasattr(result, "content") and result.content:
            text = result.content[0].text
        else:
            text = ""
        out_tokens = getattr(getattr(result, "usage", None), "output_tokens", 0)
        return text, out_tokens

    def _call_openai(self, model: str, messages: List[Dict[str, Any]], system: Optional[str], max_tokens: int):
        import openai

        Client = getattr(openai, "OpenAI", None)
        if Client is None:
            raise RuntimeError("OpenAI SDK not available")
        client = Client()

        # ── Tests mock client.create (dict return) ──────────────────────────────
        if hasattr(client, "create"):
            result = client.create(model=model, messages=messages, system=system, max_tokens=max_tokens)
            if isinstance(result, dict):
                text = result.get("text") or result.get("output") or ""
                out_tokens = result.get("output_tokens", 0)
            else:
                text = getattr(result, "text", getattr(result, "output", ""))
                out_tokens = getattr(result, "output_tokens", 0)
            return text, out_tokens

        # ── Live SDK path: client.chat.completions.create ───────────────────────
        # Inject system prompt as first message if provided
        all_messages = list(messages)
        if system:
            all_messages = [{"role": "system", "content": system}] + all_messages
        result = client.chat.completions.create(
            model=model,
            messages=all_messages,
            max_tokens=max_tokens,
        )
        text = result.choices[0].message.content or ""
        out_tokens = getattr(getattr(result, "usage", None), "completion_tokens", 0)
        return text, out_tokens
"""Cost Tracker placeholder."""

# No logic yet; placeholder to be implemented later.
