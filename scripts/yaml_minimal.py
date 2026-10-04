#!/usr/bin/env python3
"""Minimal YAML frontmatter parser for RESEARCH_STATE.md documents.

Handles the specific structure used by the research-state format:
- scalar key: value
- quoted strings ('"...')
- inline lists [ item, item ] (strings, ints)
- nested objects
- block lists (items starting with '- ')
- lists of objects (2-space indented key: value)
- lists of plain strings

Pure-Python, zero external dependencies. Used by validate_research_state.py.
"""

import re


def extract_frontmatter(text):
    """Split YAML frontmatter from markdown body. Returns (parsed dict, body)."""
    match = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.S)
    if not match:
        return None, None
    return parse_yaml_block(match.group(1)), text[match.end():]


def _indent(line):
    return len(line) - len(line.lstrip())


def _skip_empty(lines, i):
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return i


def _parse_value(val):
    val = val.strip()
    if not val:
        return None
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        items = []
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            if (part.startswith('"') and part.endswith('"')) or \
               (part.startswith("'") and part.endswith("'")):
                items.append(part[1:-1])
            else:
                try:
                    if "." in part and part.replace(".", "").isdigit():
                        items.append(float(part))
                    else:
                        items.append(int(part))
                except ValueError:
                    items.append(part)
        return items
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    low = val.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~"):
        return None
    try:
        if "." in val and val.replace(".", "").isdigit():
            return float(val)
        return int(val)
    except ValueError:
        return val


def _parse_block(lines, i, base_indent):
    """Parse a block starting at index i.

    base_indent: lines with indent >= this are part of the block.
    Returns (node, next_index). base_indent of -1 matches any indentation.
    """
    i = _skip_empty(lines, i)
    if i >= len(lines):
        return None, i

    first = lines[i]
    ii = _indent(first)

    # If this position starts a list, parse as a list.
    if first.lstrip().startswith("-"):
        return _parse_list(lines, i, ii)

    # Otherwise parse as a mapping.
    return _parse_map(lines, i, ii, base_indent)


def _parse_list(lines, i, item_indent):
    """Parse a block list. item_indent is the indent of '- ' markers."""
    items = []
    while i < len(lines):
        i = _skip_empty(lines, i)
        if i >= len(lines):
            break
        line = lines[i]
        cur = _indent(line)
        if cur < item_indent:
            break
        if cur == item_indent and not line.lstrip().startswith("-"):
            break
        if cur > item_indent:
            # More-indented line after a completed item => belongs to previous.
            i += 1
            continue

        content = line.lstrip()[1:]
        if content.strip() == "":
            nested, i = _parse_block(lines, i + 1, cur + 2)
            items.append(nested)
            continue

        kv = re.match(r"^([^:]+):\s*(.*)$", content)
        if kv and kv.group(2).strip() == "":
            nested, i = _parse_block(lines, i + 1, cur + 2)
            items.append({kv.group(1).strip(): nested})
        elif kv:
            key = kv.group(1).strip()
            val = kv.group(2).strip()
            j = _skip_empty(lines, i + 1)
            if j < len(lines) and _indent(lines[j]) > cur \
                    and not lines[j].lstrip().startswith("-"):
                obj = {key: _parse_value(val)}
                while j < len(lines):
                    sj = lines[j]
                    if sj.strip() == "":
                        j += 1
                        continue
                    ji = _indent(sj)
                    if ji <= cur or sj.lstrip().startswith("-"):
                        break
                    mk = re.match(r"^([^:]+):\s*(.*)$", sj)
                    if not mk:
                        j += 1
                        continue
                    kkey = mk.group(1).strip()
                    kv2 = mk.group(2).strip()
                    if kv2 == "":
                        nb, nj = _parse_block(lines, j, ji)
                        obj[kkey] = nb
                        j = nj
                    else:
                        obj[kkey] = _parse_value(kv2)
                        j += 1
                items.append(obj)
                i = j
                continue
            else:
                items.append({key: _parse_value(val)})
                i += 1
        else:
            items.append(content.strip())
            i += 1
    return items, i


def _parse_map(lines, i, map_indent, base_indent):
    """Parse a mapping (dict). map_indent is the indent of this block's keys."""
    d = {}
    while i < len(lines):
        i = _skip_empty(lines, i)
        if i >= len(lines):
            break
        line = lines[i]
        cur = _indent(line)
        if cur < map_indent:
            break
        # A list at this indent belonging to a preceding incomplete key
        # would have been handled by the caller; treat stray list as item.
        if cur == map_indent and line.lstrip().startswith("-"):
            break
        if cur > map_indent:
            i += 1
            continue
        mk = re.match(r"^([^:]+):\s*(.*)$", line)
        if not mk:
            i += 1
            continue
        key = mk.group(1).strip()
        val = mk.group(2).strip()
        i += 1
        if val == "":
            nested, i = _parse_block(lines, i, cur + 2)
            d[key] = nested
        else:
            d[key] = _parse_value(val)
    return d, i


def parse_yaml_block(text):
    lines = text.split("\n")
    result, _ = _parse_block(lines, 0, -1)
    return result


# Compatibility aliases for validate_research_state.py
def safe_load(text):
    return parse_yaml_block(text)


class YAMLError(Exception):
    """Dummy YAML parse error (parse-only mode)."""
    pass
