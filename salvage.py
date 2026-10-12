#!/usr/bin/env python3
"""json-output-salvage — repair common LLM-output JSON breakages with an audit trail.

Repairs (in deterministic order): markdown-fence/prose stripping, truncation
completion (string + bracket closing), trailing-comma removal, single-quote
normalization, smart-quote normalization. Pure stdlib.
"""
import argparse
import json
import re
import sys

MAX_PASSES = 8


def _scan(text):
    """Scan JSON-ish text; return (stack, in_string, ended_with_escape)."""
    stack = []
    in_string = False
    escape = False
    quote = ""
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in "\"'":
            in_string = True
            quote = ch
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack and (stack[-1] == "{" and ch == "}" or stack[-1] == "[" and ch == "]"):
                stack.pop()
            else:
                stack.append(ch)  # mismatch marker
    return stack, in_string, escape


def _complete_truncation(text):
    stack, in_string, escape = _scan(text)
    repaired = text
    applied = []
    if in_string:
        if escape:
            repaired = repaired[:-1]
            applied.append("drop-dangling-escape")
        repaired += '"'
        applied.append("close-string")
    if stack:
        closers = []
        for ch in reversed(stack):
            closers.append("}" if ch == "{" else "]")
        repaired += "".join(closers)
        applied.append("close-brackets(%s)" % "".join(closers))
    return repaired, applied


def _strip_prose(text):
    t = text.strip()
    applied = []
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl != -1:
            t = t[first_nl + 1:]
        end = t.rfind("```")
        if end != -1:
            t = t[:end]
        applied.append("strip-code-fence")
    starts = [t.find(c) for c in "{[" if t.find(c) != -1]
    if starts and not t.startswith(("{", "[")):
        t = t[min(starts):]
        applied.append("strip-leading-prose")
    ends = [t.rfind(c) for c in "}]" if t.rfind(c) != -1]
    if ends and not t.endswith(("}", "]")):
        t = t[:max(ends) + 1]
        applied.append("strip-trailing-prose")
    return t, applied


def _strip_trailing_comma(text):
    """Remove trailing commas before } or ] anywhere (regex), and at end of text."""
    out = re.sub(r",(\s*[}\]])", r"\1", text)
    t = out.rstrip()
    if t.endswith(","):
        out = t[:-1].rstrip()
    return out, ["strip-trailing-comma"] if out != text else []


def _normalize_quotes(text):
    if '"' in text:
        return text, []
    swapped = text.replace("\\'", "\x00").replace("'", '"').replace("\x00", "'")
    return swapped, ["single-to-double-quotes"] if swapped != text else []


SMART_OPEN, SMART_CLOSE = "\u201c", "\u201d"


def _fix_smart_quotes(text):
    """Convert curly double quotes to ASCII only at structural delimiter
    positions (after ':' / before , } ]), never inside string contents."""
    out = text
    out = re.sub("(:\\s*)" + SMART_OPEN, '\\1"', out)
    out = re.sub("([{,:\\[]\\s*)" + SMART_OPEN, '\\1"', out)
    out = re.sub(SMART_CLOSE + "(\\s*:)", '"\\1', out)
    out = re.sub(SMART_CLOSE + "(\\s*[,}\\]])", '\\1"', out)
    if out.startswith(SMART_OPEN):
        out = '"' + out[1:]
    if out.endswith(SMART_CLOSE):
        out = out[:-1] + '"'
    return out, ["smart-quotes-to-ascii"] if out != text else []


REPAIRS = [_strip_prose, _fix_smart_quotes, _normalize_quotes, _strip_trailing_comma, _complete_truncation]


def salvage(text, max_passes=MAX_PASSES):
    """Attempt to repair `text` into parseable JSON.

    Returns dict: {ok, value, repairs, error}. Never raises on bad input text.
    """
    if not isinstance(text, str):
        return {"ok": False, "value": None, "repairs": [], "error": "input must be a string"}
    audit = []
    current = text
    try:
        value = json.loads(current)
        return {"ok": True, "value": value, "repairs": [], "error": None}
    except ValueError as e:
        err = str(e)
    for _ in range(max_passes):
        progressed = False
        for repair in REPAIRS:
            candidate, applied = repair(current)
            if applied:
                audit.extend(applied)
                current = candidate
                progressed = True
                try:
                    value = json.loads(current)
                    return {"ok": True, "value": value, "repairs": audit, "error": None}
                except ValueError as e:
                    err = str(e)
        if not progressed:
            break
    return {"ok": False, "value": None, "repairs": audit, "error": err}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="json-output-salvage", description="Repair common LLM-output JSON breakages (truncation, trailing commas, quote issues) with an audit trail.")
    ap.add_argument("file", nargs="?", help="file containing raw LLM output (JSON-ish); omit to read stdin")
    ap.add_argument("--text", help="repair this literal text instead")
    ap.add_argument("--json", action="store_true", help="emit full JSON report including audit trail")
    args = ap.parse_args(argv)
    try:
        if args.text is not None:
            raw = args.text
        elif args.file:
            with open(args.file, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
        else:
            raw = sys.stdin.read()
    except OSError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    result = salvage(raw)
    if result["ok"] and not args.json:
        print(json.dumps(result["value"], ensure_ascii=False))
        if result["repairs"]:
            print("repairs: %s" % "; ".join(result["repairs"]), file=sys.stderr)
        return 0
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    print("error: unparseable even after repairs: %s" % result["error"], file=sys.stderr)
    print("repairs tried: %s" % "; ".join(result["repairs"]), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
