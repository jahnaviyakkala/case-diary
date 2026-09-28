"""
LLM access with the failure handling a demo (and a courtroom morning) needs.

- Several API keys rotate round-robin, so their per-minute limits add up.
- A key that hits a rate limit cools down for exactly as long as the provider says,
  while the other keys keep serving. Bad keys and missing models are skipped for good.
- If every key is cooling, the call waits for the first one to free up (bounded),
  and only then falls through to the next model.
- Tolerant JSON parsing, and a clear LLMUnavailable so callers drop to a template answer.
"""

import itertools
import json
import logging
import re
import threading
import time

from openai import (APIConnectionError, APIStatusError, AuthenticationError, BadRequestError, NotFoundError, OpenAI,
                    PermissionDeniedError, RateLimitError)

from app.config import LLM_API_KEYS, LLM_BASE_URL, LLM_FALLBACK_MODEL, LLM_MODEL

log = logging.getLogger("case-diary.llm")
MAX_WAIT = 40  # seconds a single call may spend waiting for a key to come off cooldown


class LLMUnavailable(Exception):
    pass


_clients = [OpenAI(base_url=LLM_BASE_URL, api_key=k, timeout=60.0, max_retries=0) for k in LLM_API_KEYS]
_turn = itertools.count()
_lock = threading.Lock()
_cooling = {}        # (key index, model) -> time when usable again
_dead_keys = set()   # rejected with 401/403
_dead_models = set() # 404 on this account
last_model_used = None
last_error = None


def configured():
    return bool(_clients)


def key_status():
    now = time.time()
    return {"keys": len(_clients), "usable": len([i for i in range(len(_clients)) if i not in _dead_keys]),
            "cooling": sorted({i for (i, _), t in _cooling.items() if t > now})}


def _retry_after(exc):
    """Seconds until the provider will accept this key again (Groq sends retry-after / reset headers)."""
    headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
    for name in ("retry-after", "x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
        raw = headers.get(name)
        if not raw:
            continue
        try:
            return float(raw)
        except ValueError:
            m = re.fullmatch(r"(?:(\d+)m)?(?:([\d.]+)s)?(?:([\d.]+)ms)?", raw.strip())
            if m and any(m.groups()):
                return int(m.group(1) or 0) * 60 + float(m.group(2) or 0) + float(m.group(3) or 0) / 1000
    return 20.0


def _extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _complete(client, model, messages, json_mode, max_tokens, reasoning="low"):
    kwargs = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens}
    if "gpt-oss" in model:
        # gpt-oss spends completion tokens on hidden reasoning; without this a long prompt
        # can use the whole budget thinking and return an empty answer.
        kwargs["reasoning_effort"] = reasoning
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = client.chat.completions.create(**kwargs)
    except BadRequestError:
        if not json_mode:
            raise
        kwargs.pop("response_format")  # some models reject JSON mode; ask plainly and parse
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _order(model):
    """Live keys for this model, starting from the next key in the rotation."""
    n = len(_clients)
    with _lock:
        first = next(_turn) % n
    now = time.time()
    return [i for i in (list(range(first, n)) + list(range(first))) if i not in _dead_keys and _cooling.get((i, model), 0) <= now]


def chat(system, user, *, json_mode=False, max_tokens=2500, reasoning="low"):
    """Return text (or a dict when json_mode) from the first key and model that answer sensibly."""
    global last_model_used, last_error
    if not configured():
        last_error = "LLM_API_KEY is not set"
        raise LLMUnavailable(last_error)
    base = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    strict = base[:1] + [{"role": "user", "content": user + "\n\nReturn ONLY valid JSON."}]
    models = [m for m in dict.fromkeys([LLM_MODEL, LLM_FALLBACK_MODEL, "openai/gpt-oss-20b"]) if m]
    deadline = time.time() + MAX_WAIT

    while True:
        for model in [m for m in models if m not in _dead_models]:
            for i in _order(model):
                for messages in (base, strict):  # one re-ask if the output is not parseable
                    try:
                        text = _complete(_clients[i], model, messages, json_mode, max_tokens, reasoning)
                        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
                        result = _extract_json(text) if json_mode else text
                        if not result:
                            raise ValueError("empty response")
                        last_model_used, last_error = model, None
                        return result
                    except RateLimitError as exc:
                        wait = _retry_after(exc)
                        _cooling[(i, model)] = time.time() + wait
                        last_error = f"rate limited on {model} (key {i + 1}, {wait:.0f}s)"
                        log.info(last_error)
                        break  # next key
                    except (json.JSONDecodeError, ValueError) as exc:
                        last_error = f"{model} returned unparseable output ({exc})"
                        log.warning(last_error)
                    except (AuthenticationError, PermissionDeniedError):
                        _dead_keys.add(i)
                        last_error = f"key {i + 1} was rejected; skipping it"
                        log.warning(last_error)
                        break
                    except NotFoundError:
                        _dead_models.add(model)
                        last_error = f"model {model} is not available on this account; skipping it"
                        log.warning(last_error)
                        break
                    except (APIConnectionError, APIStatusError) as exc:
                        _cooling[(i, model)] = time.time() + 5
                        last_error = f"{model} (key {i + 1}): {type(exc).__name__} {str(exc)[:120]}"
                        log.warning(last_error)
                        break
                if model in _dead_models:
                    break

        # Every live key is cooling for every live model: wait for the first to free up, within budget.
        now = time.time()
        live = [t for (i, m), t in _cooling.items() if i not in _dead_keys and m not in _dead_models and m in models]
        if not live or len(_dead_keys) == len(_clients):
            break
        soonest = min(live)
        if soonest > deadline:
            break
        time.sleep(max(0.5, soonest - now))
    raise LLMUnavailable(last_error or "all models failed")
