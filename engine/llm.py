"""engine/llm.py — four providers, one interface.

bedrock | anthropic | openai | mock. mock is not a stub: it replays recorded
responses from mock/llm_cassettes/*.json keyed by a stable hash of
(system + messages). Every LIVE provider call is recorded to the cassette dir
when RECORD_CASSETTES=1 — that recording is the demo's life insurance.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Protocol

CASSETTE_DIR = Path(__file__).resolve().parents[1] / "mock" / "llm_cassettes"


class LLM(Protocol):
    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str: ...


# ---------------------------------------------------------------- cassettes


def _cassette_key(system: str, messages: list[dict]) -> str:
    payload = json.dumps({"system": system, "messages": messages},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def record_cassette(system: str, messages: list[dict], response: str) -> None:
    CASSETTE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cassette_key(system, messages)
    (CASSETTE_DIR / f"{key}.json").write_text(json.dumps(
        {"key": key, "system": system, "messages": messages, "response": response},
        indent=2, ensure_ascii=False))


class MockLLM:
    """Replays cassettes. Zero network. If the venue wifi dies, nobody knows."""

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        key = _cassette_key(system, messages)
        path = CASSETTE_DIR / f"{key}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"no cassette for key {key} — run once with a live provider and "
                f"RECORD_CASSETTES=1 (dir: {CASSETTE_DIR})")
        return json.loads(path.read_text())["response"]


# ---------------------------------------------------------------- live providers


class OpenAILLM:
    """OpenAI chat.completions. Reads OPENAI_API_KEY / OPENAI_MODEL from env."""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()  # picks up OPENAI_API_KEY
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        msgs = [{"role": "system", "content": system}] + messages
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=msgs, max_completion_tokens=max_tokens)
        except Exception as exc:
            # older models reject max_completion_tokens; newer reject max_tokens
            if "max_completion_tokens" in str(exc) or "unsupported" in str(exc).lower():
                resp = self.client.chat.completions.create(
                    model=self.model, messages=msgs, max_tokens=max_tokens)
            else:
                raise
        return resp.choices[0].message.content or ""


class AnthropicLLM:
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        resp = self.client.messages.create(
            model=self.model, system=system, messages=messages, max_tokens=max_tokens)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


class BedrockLLM:
    def __init__(self):
        import boto3
        self.client = boto3.client("bedrock-runtime",
                                   region_name=os.environ.get("AWS_REGION", "us-west-2"))
        self.model = os.environ.get(
            "BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        resp = self.client.converse(
            modelId=self.model,
            system=[{"text": system}],
            messages=[{"role": m["role"], "content": [{"text": m["content"]}]}
                      for m in messages],
            inferenceConfig={"maxTokens": max_tokens},
        )
        return "".join(c.get("text", "")
                       for c in resp["output"]["message"]["content"])


class RecordingLLM:
    """Wraps a live provider; every call lands in the cassette dir."""

    def __init__(self, inner: LLM):
        self.inner = inner

    def complete(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        response = self.inner.complete(system, messages, max_tokens)
        record_cassette(system, messages, response)
        return response


# ---------------------------------------------------------------- factory + JSON


def get_llm(provider: str | None = None) -> LLM:
    provider = (provider or os.environ.get("LLM_PROVIDER", "bedrock")).lower()
    if provider == "mock":
        return MockLLM()
    llm: LLM
    if provider == "openai":
        llm = OpenAILLM()
    elif provider == "anthropic":
        llm = AnthropicLLM()
    elif provider == "bedrock":
        llm = BedrockLLM()
    else:
        raise ValueError(f"unknown LLM_PROVIDER: {provider}")
    if os.environ.get("RECORD_CASSETTES") == "1":
        llm = RecordingLLM(llm)
    return llm


_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$", re.MULTILINE)


def parse_json_response(text: str) -> dict:
    """Prompts request JSON-only; strip markdown fences defensively anyway."""
    t = text.strip()
    if t.startswith("```"):
        t = _FENCE_RE.sub("", t).strip()
    # last resort: slice from first '{' to last '}'
    if not t.startswith("{"):
        start, end = t.find("{"), t.rfind("}")
        if start != -1 and end > start:
            t = t[start:end + 1]
    return json.loads(t)
