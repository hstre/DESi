"""DESi task classifier — autonomous routing.

Given a free-text query (and optional context hints), classifies into one of
the known DESi task classes, OR returns 'other' for inputs outside the
empirically-grounded routing table.

Implementation: a single cheap LLM call (Llama 3B by default — fast, cheap).
The prompt is bounded to a closed enumeration so the output is parseable.

Usage:
    from desi_router.classifier import TaskClassifier
    c = TaskClassifier()
    res = c.classify("How long did I wait for my asylum decision?")
    # res = ClassificationResult(task_class='memory_recall', confidence=0.92, ...)
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal


TaskClass = Literal["memory_recall", "code_audit", "scientific_claim", "other"]


SYSTEM = (
    "You are a task classifier for an LLM routing system. Read the query and "
    "classify it into exactly ONE of these task classes:\n\n"
    "memory_recall — Question about a fact, event, or update from a multi-turn "
    "  conversation history (user's own past statements, sessions, prior chat). "
    "  Examples:\n"
    "    'When did I move to Berlin?'\n"
    "    'How many properties did I view?'\n"
    "    'What kind of car did I tell you about?'\n\n"
    "code_audit — Audit/review of Python code for bugs, security issues, "
    "  correctness problems. The query usually contains code or asks for a code review.\n"
    "  Examples:\n"
    "    'Find any bugs in this function: def foo(): ...'\n"
    "    'Audit this Python code for issues.'\n"
    "    'Is the operator precedence correct in <expression>?'\n\n"
    "scientific_claim — Verify a scientific or biomedical claim against published "
    "  evidence (abstracts, papers). The query may be a QUESTION about a claim, "
    "  OR it may be a STATEMENT followed by an instruction to verify it "
    "  (often: 'Respond with VERDICT: SUPPORT | CONTRADICT | NEI'). "
    "  Either way, if the input is a factual scientific/medical assertion + "
    "  request to evaluate against evidence, classify as scientific_claim.\n"
    "  Examples:\n"
    "    'Does aspirin reduce cardiovascular risk?'\n"
    "    'Alirocumab treatment reduces apo(a) fractional clearance rate. "
    "       Respond with VERDICT: SUPPORT | CONTRADICT | NEI.'\n"
    "    'Verify the claim that statins cause memory loss against the abstracts.'\n"
    "    'There is a positive correlation between hip fractures and statin use.'\n"
    "    Any bare-statement claim that looks like a thesis or finding (BRCA1, "
    "    folic acid, vitamin D, RCT outcomes, etc.) — classify as scientific_claim.\n\n"
    "other — Anything else: open-ended creative writing, trip planning, math "
    "  problems, translation, weather lookup, etc.\n\n"
    "Your entire response must be exactly two lines:\n"
    "CLASS: <one of: memory_recall | code_audit | scientific_claim | other>\n"
    "CONFIDENCE: <high|medium|low>\n\n"
    "Do not explain, do not output anything else."
)


@dataclass
class ClassificationResult:
    task_class: TaskClass
    confidence: Literal["high", "medium", "low"]
    raw_response: str
    classifier_model: str
    latency_ms: int
    cost_usd: float
    error: str | None = None


def _http_post(url, headers, body, timeout=60, retries=2):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:200]
            if e.code in (400, 401, 403, 404):
                return {"_http_error": e.code, "_body": text}
            last = f"HTTP {e.code}: {text}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(2 ** i)
    return {"_http_error": "retry_exhausted", "_body": last}


_CLASS_RE = re.compile(r"CLASS:\s*(memory_recall|code_audit|scientific_claim|other)",
                       re.IGNORECASE)
_CONF_RE = re.compile(r"CONFIDENCE:\s*(high|medium|low)", re.IGNORECASE)

_DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct"
_DEFAULT_PRICE_IN = 0.051
_DEFAULT_PRICE_OUT = 0.335


class TaskClassifier:
    def __init__(self, model: str = _DEFAULT_MODEL,
                 price_in_per_m: float = _DEFAULT_PRICE_IN,
                 price_out_per_m: float = _DEFAULT_PRICE_OUT):
        self.model = model
        self.price_in = price_in_per_m
        self.price_out = price_out_per_m

    def classify(self, query: str, context_hint: str | None = None) -> ClassificationResult:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            return ClassificationResult(
                task_class="other", confidence="low", raw_response="",
                classifier_model=self.model, latency_ms=0, cost_usd=0.0,
                error="no OPENROUTER_API_KEY",
            )

        user = f"QUERY:\n{query}"
        if context_hint:
            user += f"\n\nCONTEXT HINT:\n{context_hint[:500]}"
        user += "\n\nClassify:"

        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": user}],
            "max_tokens": 30,
        }).encode()
        t0 = time.time()
        d = _http_post(
            "https://openrouter.ai/api/v1/chat/completions",
            {"Authorization": f"Bearer {key}",
             "Content-Type": "application/json",
             "HTTP-Referer": "https://github.com/hstre/DESi",
             "X-Title": "DESi TaskClassifier"}, body)
        lat = int((time.time() - t0) * 1000)
        if "_http_error" in d:
            return ClassificationResult(
                task_class="other", confidence="low", raw_response="",
                classifier_model=self.model, latency_ms=lat, cost_usd=0.0,
                error=f"{d['_http_error']}: {d.get('_body','')[:200]}",
            )

        try:
            text = d["choices"][0]["message"]["content"] or ""
            u = d.get("usage", {}) or {}
            in_t = u.get("prompt_tokens", 0) or 0
            out_t = u.get("completion_tokens", 0) or 0
            cost = in_t / 1e6 * self.price_in + out_t / 1e6 * self.price_out

            cm = _CLASS_RE.search(text)
            tc: TaskClass = cm.group(1).lower() if cm else "other"  # type: ignore
            confm = _CONF_RE.search(text)
            conf = confm.group(1).lower() if confm else "medium"
            return ClassificationResult(
                task_class=tc, confidence=conf, raw_response=text,
                classifier_model=self.model, latency_ms=lat, cost_usd=cost,
            )
        except Exception as e:
            return ClassificationResult(
                task_class="other", confidence="low", raw_response="",
                classifier_model=self.model, latency_ms=lat, cost_usd=0.0,
                error=f"parse: {e}",
            )


if __name__ == "__main__":
    # Quick smoke test
    c = TaskClassifier()
    examples = [
        "How long did I wait for the decision on my asylum application?",
        "Audit this Python function for bugs: def fenced_sum(values): ...",
        "Does the evidence support the claim that 1 in 5 million people in UK have abnormal PrP positivity?",
        "Write me a poem about autumn leaves.",
        "Plan a trip to Berlin including hotels and restaurants.",
    ]
    for ex in examples:
        r = c.classify(ex)
        print(f"  [{r.task_class:<18} conf={r.confidence:<6} lat={r.latency_ms}ms ${r.cost_usd:.6f}]  {ex[:80]}")
