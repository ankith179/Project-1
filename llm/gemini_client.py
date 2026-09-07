"""
llm/gemini_client.py
--------------------
Gemini API client for VIGILANT LLM layer.
Uses google-genai SDK (google.genai).
Falls back to deterministic mock output when GEMINI_API_KEY is absent,
ensuring all tests pass without an API key.
"""
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Lazy SDK import — don't crash if package is missing
# ---------------------------------------------------------------------------
def _try_import_genai():
    try:
        from google import genai
        from google.genai import types as genai_types
        return genai, genai_types
    except ImportError:
        return None, None


class GeminiClient:
    """
    Thin wrapper around Gemini 1.5 Flash for structured JSON generation.

    If GEMINI_API_KEY is not set, the client runs in MOCK mode:
    all methods return deterministic placeholder responses so that
    the agent pipeline and test suite can run without a real API key.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model or self.DEFAULT_MODEL
        self._client = None
        self._mock_mode = False
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            self._mock_mode = True
            return
        genai, _ = _try_import_genai()
        if genai is None:
            self._mock_mode = True
            return
        try:
            self._client = genai.Client(api_key=self.api_key)
            self._mock_mode = False
        except Exception:
            self._mock_mode = True

    @property
    def is_mock(self) -> bool:
        return self._mock_mode

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """Raw text generation. Returns mock if no API key."""
        if self._mock_mode:
            return self._mock_text(prompt)

        _, genai_types = _try_import_genai()
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"temperature": temperature},
            )
            return response.text or ""
        except Exception as exc:
            return f"[LLM ERROR: {exc}]"

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Generate and parse a JSON response from Gemini.
        Returns parsed dict. Falls back gracefully on parse errors.
        """
        json_prompt = (
            prompt
            + "\n\nRespond ONLY with a valid JSON object. No markdown, no explanation."
        )
        raw = self.generate(json_prompt, temperature=temperature)
        return self._parse_json(raw, schema)

    # ------------------------------------------------------------------
    # High-level task methods
    # ------------------------------------------------------------------

    def rerank_candidates(
        self,
        requirement: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ask Gemini to re-rank traceability candidates and explain each.
        Returns candidates list with added 'llm_score' and 'llm_reason'.
        """
        if self._mock_mode:
            # Mock: assign descending scores, no reordering
            for i, c in enumerate(candidates):
                c["llm_score"] = round(0.9 - i * 0.05, 2)
                c["llm_reason"] = f"[MOCK] Candidate ranked {i+1} by placeholder LLM."
            return candidates

        from llm.prompts import PromptBuilder
        prompt = PromptBuilder.build_reranking_prompt(requirement, candidates)
        result = self.generate_json(prompt)

        ranked = result.get("ranked_candidates", [])
        # Merge LLM scores back into candidates by index / target id
        target_map = {c.get("target"): c for c in candidates}
        for item in ranked:
            tid = item.get("target") or item.get("artifact_id")
            if tid in target_map:
                target_map[tid]["llm_score"] = item.get("score", 0.5)
                target_map[tid]["llm_reason"] = item.get("reason", "")

        # Fill missing
        for c in candidates:
            c.setdefault("llm_score", 0.0)
            c.setdefault("llm_reason", "")

        candidates.sort(key=lambda x: x.get("llm_score", 0.0), reverse=True)
        return candidates

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json(
        self, raw: str, schema: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        try:
            data = json.loads(raw)
            if schema:
                return schema.model_validate(data).model_dump()
            return data
        except (json.JSONDecodeError, Exception):
            return {"raw_response": raw, "parse_error": True}

    def _mock_text(self, prompt: str) -> str:
        """Deterministic mock for testing without an API key."""
        if "rerank" in prompt.lower() or "rank" in prompt.lower():
            return json.dumps({
                "ranked_candidates": [],
                "reasoning": "MOCK MODE — no API key provided."
            })
        if "consist" in prompt.lower():
            return json.dumps({
                "status": "CONSISTENT",
                "confidence": 0.8,
                "issues": [],
                "evidence": ["MOCK MODE — no API key provided."]
            })
        return json.dumps({
            "result": "MOCK",
            "explanation": "No GEMINI_API_KEY set — running in mock mode.",
            "links": []
        })
