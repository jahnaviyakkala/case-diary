"""
LLM access with the failure handling a demo (and a courtroom morning) needs:
retries with backoff on rate limits, a fallback model, tolerant JSON parsing,
and a clear LLMUnavailable so callers can drop to a template answer.
"""

import json
import logging
import re
import time

from openai import APIConnectionError, APIStatusError, BadRequestError, OpenAI, RateLimitError

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_FALLBACK_MODEL, LLM_MODEL

log = logging.getLogger("case-diary.llm")


class LLMUnavailable(Exception):
    pass


_client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY or "missing", timeout=60.0, max_retries=0)
last_model_used = None
last_error = None


def configured():
    return bool(LLM_API_KEY)


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


def _complete(model, messages, json_mode, max_tokens):
    kwargs = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = _client.chat.completions.create(**kwargs)
    except BadRequestError:
        if not json_mode:
            raise
        kwargs.pop("response_format")  # some models reject JSON mode; ask plainly and parse
        resp = _client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def chat(system, user, *, json_mode=False, max_tokens=2500):
    """Return text (or a dict when json_mode) from the first model that answers sensibly."""
    global last_model_used, last_error
    if not configured():
        last_error = "LLM_API_KEY is not set"
        raise LLMUnavailable(last_error)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for model in [LLM_MODEL, LLM_FALLBACK_MODEL]:
        for attempt in range(2):
            try:
                text = _complete(model, messages, json_mode, max_tokens)
                result = _extract_json(text) if json_mode else re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
                if not result:
                    raise ValueError("empty response")
                last_model_used, last_error = model, None
                return result
            except RateLimitError as exc:
                last_error = f"rate limited on {model}"
                wait = 2 + attempt * 3
                log.warning("%s; retrying in %ss", last_error, wait)
                time.sleep(wait)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = f"{model} returned unparseable output ({exc})"
                messages = messages[:2] + [{"role": "user", "content": user + "\n\nReturn ONLY valid JSON."}]
            except (APIConnectionError, APIStatusError) as exc:
                last_error = f"{model}: {type(exc).__name__} {str(exc)[:160]}"
                log.warning(last_error)
                break  # move to the fallback model
    raise LLMUnavailable(last_error or "all models failed")
