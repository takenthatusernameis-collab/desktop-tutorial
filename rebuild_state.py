#!/usr/bin/env python3
"""Rebuild research_state.md from its emitted (corrupted) frontmatter + intact body.

Current file layout:
  line 0: leading '---' (added by earlier repair attempts)
  lines 1..N: emitted frontmatter content (with digit-prefix / duplicate-key bugs)
  line N+1: '# Research State' (body intro, start of the real body)
  lines after: original body sections + appended A8 section (intact)

Goal:
  ---
  <emitted fm, formatting-repaired>
  ---
  <body verbatim>
"""
import re, sys
sys.path.insert(0, 'scripts')

def needs_quote(v):
    if v.startswith('"'):
        return False
    return bool(re.search(r'[ \t]|\s|[#,{}[\]|>&`@$%\n]', v))

def quote(s):
    if not s:
        return '""'
    if s.startswith('"'):
        return s
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

def repair_frontmatter_text(fm_lines):
    """Apply the three formatting fixes: digit indent -> spaces, drop duplicate keys,
    normalize nested list indents, quote unquoted scalars."""
    out = []
    item_props = []
    in_item = False

    for ln in fm_lines:
        if ln and not ln[0].isspace():
            in_item = False
            item_props = []
            out.append(ln)
            continue
        if ln.startswith('  - '):
            in_item = True
            item_props = []
            out.append(ln)
            continue
        if not in_item:
            out.append(ln)
            continue

        m = re.match(r'^  (\d) (.*)$', ln)
        if m:
            d = int(m.group(1))
            key, rest = m.group(2).split(':', 1)
            item_props.append(key.strip())
            indent = ' ' * d
            val = rest.strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"{indent}{key.strip()}: {val}")
            continue

        m = re.match(r'^(\s*)- (.*)$', ln)
        if m and not ln.startswith('  - '):
            val = m.group(2).strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"    - {val}")
            continue

        m = re.match(r'^(\s+)([^:]+):(.*)$', ln)
        if m and len(m.group(1)) == 6:
            key = m.group(2).strip()
            if key in item_props:
                continue  # duplicate key line: drop
            val = m.group(3).strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"    {key}: {val}")
            continue

        out.append(ln)  # safety: keep other indented lines as-is

    return out

def main():
    t = open('research_state.md', encoding='utf-8').read()
    lines = t.split('\n')

    # The body begins at the first line exactly equal to '# Research State'
    body_start = None
    for i, ln in enumerate(lines):
        if ln.strip() == '# Research State':
            body_start = i
            break
    assert body_start is not None, "body intro not found"

    fm_raw = lines[1:body_start]   # emitted fm content (excludes leading '---' and the body)
    body = lines[body_start:]

    repaired = repair_frontmatter_text(fm_raw)

    bad = [ln for ln in repaired if re.match(r'^  \d ', ln)]
    if bad:
        print("WARN: digit-prefix lines remain:", bad[:5], file=sys.stderr)
    dupes = [ln for ln in repaired if re.match(r'^      (evidence_refs|linked_evidence|false_positive_checks):$', ln)]
    if dupes:
        print("WARN: duplicate key lines remain:", dupes[:5], file=sys.stderr)

    final = ['---'] + repaired + ['---'] + body
    new_text = '\n'.join(final) + '\n'
    open('research_state.md', 'w', encoding='utf-8').write(new_text)
    print(f"rebuilt: fm {len(fm_raw)} -> {len(repaired)} lines, body {len(body)} lines, total {len(final)} lines")

if __name__ == '__main__':
    main()
