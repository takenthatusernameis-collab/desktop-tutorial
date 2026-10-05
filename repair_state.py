#!/usr/bin/env python3
"""Repair the emitted frontmatter in research_state.md.

The emitted frontmatter has three formatting bugs:
  1. Item-property lines use a digit prefix for indent: `  4 title:` -> `    title:`.
  2. Some items (F1-F8, A1-A5, H1-H5, E1-E10) have duplicate key lines (`      evidence_refs:`) that must be dropped.
  3. Unquoted multi-word scalar values must be quoted; nested list items at 6/8 spaces must be normalized to 4.

Rules (applied to YAML inside the opening --- and the first following ---):
 - item marker `  - ` (2-space) kept as-is; begins a new item context.
 - digit-prop `  <d> key: value` -> d spaces + key + value.
 - plain 6-space prop `      key: value` -> real prop if key not seen as digit-prop in this item -> 4 spaces; if duplicate -> drop.
 - nested list items `      - ` or `        - ` -> `    - `.
 - quote any scalar value (prop or list item) that is unquoted and contains spaces or YAML-special chars.
 - top-level keys (`enterprise:`, `hypotheses:`, ...) kept as-is.
 - the body starts at the first `## ` heading; everything from there is copied verbatim.
 - a closing `---` is emitted after the repaired frontmatter.
"""
import re, sys
sys.path.insert(0, 'scripts')

def quote(s):
    """YAML-quote a scalar like the original format."""
    if not s:
        return '""'
    if s.startswith('"'):
        return s
    if '"' in s or '\n' in s or '\\' in s:
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    low = s.lower()
    if low in ('true', 'false', 'null', 'yes', 'no', 'on', 'off'):
        return '"' + s + '"'
    if any(ch in s for ch in '#&*{}[]|><`@$%!,;:\\') or ':' in s:
        return '"' + s + '"'
    if s and s[0] in ' \t' or (s and s[0].isdigit() and len(s) > 1 and s[1] in ' \t'):
        return '"' + s + '"'
    return s

def needs_quote(v):
    if v.startswith('"'):
        return False
    # unquoted scalars must not contain unescaped special YAML chars
    return bool(re.search(r'[ \t]|\s|[#,{}[\]|>&`@$%\n]', v))

def repair_frontmatter_text(fm_lines):
    out = []
    item_props = []  # keys seen as digit-props in the current item
    in_item = False

    for ln in fm_lines:
        # top-level key (no leading space): end of any item
        if ln and not ln[0].isspace():
            in_item = False
            item_props = []
            out.append(ln)
            continue

        # item marker `  - ` (2-space indent, starts a new item)
        if ln.startswith('  - '):
            in_item = True
            item_props = []
            out.append(ln)
            continue

        if not in_item:
            out.append(ln)
            continue

        # item property with digit prefix: `  <d> key: value`
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

        # nested list item: `      - ` (6) or `        - ` (8) -> `    - `
        m = re.match(r'^(\s*)- (.*)$', ln)
        if m and not ln.startswith('  - '):
            val = m.group(2).strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"    - {val}")
            continue

        # plain 6-space line: `      key: value` (duplicate key or real prop)
        m = re.match(r'^(\s+)([^:]+):(.*)$', ln)
        if m and len(m.group(1)) == 6:
            key = m.group(2).strip()
            if key in item_props:
                # duplicate key -> drop
                continue
            # real prop -> 4 spaces
            val = m.group(3).strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"    {key}: {val}")
            continue

        # any other indented line inside an item -> keep as-is (safety)
        out.append(ln)

    return out

def main():
    t = open('research_state.md', encoding='utf-8').read()
    lines = t.split('\n')

    # body starts at first line matching `## <number>. `
    body_start = 0
    for i, ln in enumerate(lines):
        if re.match(r'^## [0-9]+\. ', ln):
            body_start = i
            break
    assert body_start > 1, "body section not found"

    fm_lines = lines[:body_start]
    body_lines = lines[body_start:]

    repaired = repair_frontmatter_text(fm_lines)

    # sanity: no digit prefixes remain inside the repaired frontmatter
    bad = [ln for ln in repaired if re.match(r'^  \d ', ln)]
    if bad:
        print("WARN: unrepaired digit-prefix lines remain:", bad[:5], file=sys.stderr)

    # ensure no duplicate-key 6-space lines remain (they should have been dropped)
    dupes = [ln for ln in repaired if re.match(r'^      (evidence_refs|linked_evidence|false_positive_checks):$', ln)]
    if dupes:
        print("WARN: duplicate key lines remain:", dupes[:5], file=sys.stderr)

    if repaired and repaired[0] == '---':
        front = repaired + ['---']
    else:
        front = ['---'] + repaired + ['---']
    new_text = '\n'.join(front) + '\n' + '\n'.join(body_lines)
    open('research_state.md', 'w', encoding='utf-8').write(new_text)
    print(f"rewrote: {len(lines)} -> {len(new_text.splitlines())} lines, body at line {len(front)+1}")

if __name__ == '__main__':
    main()
