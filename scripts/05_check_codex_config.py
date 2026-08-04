#!/usr/bin/env python3
"""CodexTune - 05_check_codex_config.py

Read-only safety checker for ~/.codex/config.toml (or a given config path).
It flags the known failure modes collected from two Windows machines:

  - TOML parse errors
  - wire_api = "chat" (removed upstream, see openai/codex#7782)
  - model_provider that does not exist in [model_providers]
  - base_url pointing at a localhost port that is not listening
  - model_catalog_json missing or unreadable
  - double-encoded UTF-8 mojibake in paths
  - localhost MCP endpoints that are not listening
  - named pipe references in MCP env (stale pipe candidates)
  - local marketplace sources that no longer exist

Does not modify anything. Sensitive values are never printed.

Usage:
  python scripts/05_check_codex_config.py
  python scripts/05_check_codex_config.py --config C:/path/to/config.toml
  python scripts/05_check_codex_config.py --json
"""

import argparse
import json
import pathlib
import socket
import sys
import urllib.parse

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for Python < 3.11
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

# Double-encoded UTF-8 fragments seen in real configs (mojibake from Windows
# PowerShell 5.1-era writes). Example-only; real paths are never committed.
MOJIBAKE_FRAGMENTS = [

    "ä¸­å›½",
    "è¿è¥",
    "å…¬ä¼—",
    "å­¦æœ¯",
    "ä¼ é€",
    "éœ€æ±",
    "å†²å‡»",
]

NAMED_PIPE_PREFIX = "\\\\.\\pipe\\"

LOCALHOSTS = {"127.0.0.1", "localhost", "::1"}


def check_listen(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Codex config safety checker")
    parser.add_argument("--config", default=str(pathlib.Path.home() / ".codex" / "config.toml"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = pathlib.Path(args.config)
    findings = []

    def add(level: str, code: str, message: str) -> None:
        findings.append({"level": level, "code": code, "message": message})

    if not path.exists():
        add("error", "missing", f"config not found: {path}")
        return _emit(findings, args.json)

    if tomllib is None:
        add("error", "toml-lib", "tomllib/tomli not available; cannot parse config")
        return _emit(findings, args.json)

    raw = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(raw.splitlines(), 1):
        for frag in MOJIBAKE_FRAGMENTS:
            if frag in line:
                add("error", "mojibake", f"line {line_no}: double-encoded UTF-8 path entry")
                break

    try:
        config = tomllib.loads(raw)
    except Exception as exc:
        add("error", "toml-parse", f"TOML parse failed: {exc}")
        return _emit(findings, args.json)

    provider_id = config.get("model_provider", "openai")
    providers = config.get("model_providers", {}) or {}
    if provider_id not in providers and provider_id not in {
        "openai", "ollama", "lmstudio", "amazon-bedrock",
    }:
        add("error", "unknown-provider", f"model_provider={provider_id!r} has no [model_providers.{provider_id}] table")

    for pid, pconf in providers.items():
        if not isinstance(pconf, dict):
            continue
        wire = pconf.get("wire_api")
        if wire == "chat":
            add("error", "wire-api-chat", f"model_providers.{pid}: wire_api='chat' is no longer supported; use 'responses'")
        base = pconf.get("base_url")
        if isinstance(base, str):
            url = urllib.parse.urlsplit(base)
            if url.hostname in LOCALHOSTS and url.port:
                if not check_listen(url.hostname, url.port):
                    add("warning", "base-url-not-listening", f"model_providers.{pid}: base_url {base} but port {url.port} is not listening")

    catalog = config.get("model_catalog_json")
    if catalog:
        cat_path = pathlib.Path(catalog)
        if not cat_path.is_absolute():
            cat_path = path.parent / cat_path
        if not cat_path.exists():
            add("error", "catalog-missing", f"model_catalog_json points to missing file: {catalog}")
        else:
            try:
                cat = json.loads(cat_path.read_text(encoding="utf-8"))
                models = cat.get("models", [])
                has_image = False
                for m in models:
                    modalities = m.get("input_modalities") or []
                    if "image" in modalities:
                        has_image = True
                if models and not has_image:
                    add("info", "catalog-text-only", f"catalog {catalog}: all models are text-only (no image modality)")
            except Exception as exc:
                add("error", "catalog-invalid", f"model_catalog_json unreadable: {exc}")

    mcp_servers = config.get("mcp_servers", {}) or {}
    for sid, spec in mcp_servers.items():
        if not isinstance(spec, dict):
            continue
        stype = spec.get("type", "")
        url_text = spec.get("url", "")
        if stype == "http" or url_text:
            url = urllib.parse.urlsplit(str(url_text))
            if url.hostname in LOCALHOSTS and url.port:
                if not check_listen(url.hostname, url.port):
                    add("warning", "mcp-not-listening", f"mcp_servers.{sid}: localhost endpoint not listening: {url_text}")

    for sid, spec in mcp_servers.items():
        if not isinstance(spec, dict):
            continue
        env = spec.get("env")
        if isinstance(env, dict):
            for key, value in env.items():
                if isinstance(value, str) and NAMED_PIPE_PREFIX in value:
                    add("warning", "named-pipe-env", f"mcp_servers.{sid}.env.{key}: named pipe reference (stale pipe candidate): {value}")

    for mid, mconf in (config.get("marketplaces", {}) or {}).items():
        if not isinstance(mconf, dict):
            continue
        if mconf.get("source_type") == "local":
            src = mconf.get("source")
            if isinstance(src, str):
                p_text = src
                if p_text.startswith("\\\\?\\"):
                    p_text = p_text[4:]
                elif p_text.startswith("\\?\\"):
                    p_text = p_text[3:]
                if not pathlib.Path(p_text).exists():
                    add("warning", "marketplace-source-missing", f"marketplaces.{mid}: local source does not exist: {src}")

    return _emit(findings, args.json)


def _emit(findings, as_json) -> int:
    errors = [f for f in findings if f["level"] == "error"]
    if as_json:
        print(json.dumps({"errors": errors, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"[{f['level'].upper()}] {f['code']}: {f['message']}")
        if errors:
            print(f"FAIL: {len(errors)} error(s)")
        else:
            print("OK: no config errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
