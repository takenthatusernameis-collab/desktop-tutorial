#!/usr/bin/env python3
"""Minimal YAML emitter (write-only, no dependencies).

Handles dict, list, str, int, float, bool, None and nested combinations.
Emits with 2-space indentation.
"""


def _scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return quote(value)


def quote(s):
    if not isinstance(s, str):
        return str(s)
    needs_quote = (
        not s
        or s[0] in "'\"&*#!|>:,%}][{"
        or s[-1] in ": \t"
        or "\n" in s
        or " " in s
        or s.lower() in ("true", "false", "null", "yes", "no", "~", "on", "off")
        or (s and s.replace(".", "").isdigit())
    )
    if needs_quote:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + escaped + '"'
    return s


def _emit(data, indent):
    if isinstance(data, list):
        if not data:
            return "[]"
        items = []
        for item in data:
            if isinstance(item, (dict, list)) and item:
                child = _emit(item, indent)
                parts = [p.lstrip() for p in child.split("\n")]
                items.append("  " * indent + "- " + parts[0])
                for p in parts[1:]:
                    items.append("  " * (indent + 1) + p)
            else:
                items.append("  " * indent + "- " + _emit(item, indent + 1))
        return "\n".join(items)
    if isinstance(data, dict):
        if not data:
            return "{}"
        items = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and v:
                child = _emit(v, indent + 1)
                parts = child.split("\n")
                items.append("  " * indent + quote(str(k)) + ":")
                items.extend(parts)
            elif isinstance(v, list) and not v:
                items.append("  " * indent + quote(str(k)) + ": []")
            elif isinstance(v, dict) and not v:
                items.append("  " * indent + quote(str(k)) + ": {}")
            else:
                items.append("  " * indent + quote(str(k)) + ": " + _scalar(v))
        return "\n".join(items)
    return _scalar(data)


def dump_frontmatter(data):
    return "---\n" + _emit(data, 0) + "\n---\n"
