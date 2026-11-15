"""Connector records for models. Keys stay in the environment. Nothing here runs a sample."""

import ipaddress
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

_ENV_NAME = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")
_FORBIDDEN = {"api_key", "apikey", "key", "token", "secret", "password", "authorization"}


class ConnectorError(ValueError):
    pass


class ModelCallError(RuntimeError):
    pass


def validate_llm_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ConnectorError("Provider configuration must be an object")
    extra = _FORBIDDEN.intersection(key.casefold() for key in config)
    if extra:
        raise ConnectorError("Provider configuration must not contain a key or token")
    provider = config.get("provider")
    model = config.get("model")
    if provider not in ("local", "hosted"):
        raise ConnectorError("Provider type must be local or hosted")
    if not isinstance(model, str) or not model.strip() or len(model.strip()) > 200:
        raise ConnectorError("Model name is required")
    base_url = _base_url(provider, config.get("base_url"))
    cleaned = {"provider": provider, "model": model.strip(), "base_url": base_url}
    if provider == "hosted":
        env_name = config.get("api_key_env")
        if not isinstance(env_name, str) or not _env_var_name(env_name):
            raise ConnectorError("Hosted providers name an environment variable, not a key")
        cleaned["api_key_env"] = env_name
    elif "api_key_env" in config:
        raise ConnectorError("Local providers do not take a key")
    allowed = set(cleaned)
    if set(config) - allowed:
        raise ConnectorError("Provider configuration has an unknown field")
    return cleaned


def chat(config: dict, prompt: str) -> str:
    cleaned = validate_llm_config(config)
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
        raise ConnectorError("The test prompt must be 1 to 2000 characters")
    url = _chat_url(cleaned)
    _same_host(cleaned["base_url"], url)
    if cleaned["provider"] == "local":
        payload = {"model": cleaned["model"], "messages": [{"role": "user", "content": prompt}], "stream": False}
    else:
        payload = {"model": cleaned["model"], "messages": [{"role": "user", "content": prompt}]}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    if cleaned["provider"] == "hosted":
        key = os.environ.get(cleaned["api_key_env"], "").strip()
        if not key:
            raise ModelCallError("The named environment variable is not set")
        request.add_header("Authorization", "Bearer " + key)
    opener = urllib.request.build_opener(_RefuseRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            raw = response.read(1_000_000)
    except urllib.error.HTTPError as exc:
        raise ModelCallError(f"The model provider returned {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ModelCallError("The model provider is unreachable") from exc
    return _reply(cleaned["provider"], raw)


def _env_var_name(value: str) -> bool:
    return 1 <= len(value) <= 80 and value[0].isalpha() and all(character in _ENV_NAME for character in value)


def _base_url(provider: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise ConnectorError("Base URL is required")
    parts = urlsplit(value.strip())
    host = parts.hostname
    if parts.username or parts.password or not host or parts.scheme not in ("http", "https"):
        raise ConnectorError("Base URL is not allowed")
    if provider == "local":
        if not _loopback(host):
            raise ConnectorError("A local model must use a loopback address")
    elif parts.scheme != "https":
        raise ConnectorError("A hosted model must use https")
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _chat_url(config: dict) -> str:
    base = config["base_url"]
    if config["provider"] == "local":
        return base + "/api/chat"
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def _same_host(base_url: str, target: str) -> None:
    base = urlsplit(base_url)
    goal = urlsplit(target)
    if (base.scheme, base.hostname, base.port) != (goal.scheme, goal.hostname, goal.port):
        raise ConnectorError("The test call does not match the configured host")


def _reply(provider: str, raw: bytes) -> str:
    try:
        body = json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelCallError("The model provider returned an unreadable reply") from exc
    if provider == "local":
        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
    else:
        choices = body.get("choices") if isinstance(body, dict) else None
        message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ModelCallError("The model provider returned an empty reply")
    return content


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelCallError("The model provider redirected the request")
