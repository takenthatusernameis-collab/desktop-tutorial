#!/usr/bin/env python3
"""Final repair: the file now has the correct scaffolding,
  line 0: spurious leading '---'
  line 1: spurious second '---' (original frontmatter closing)
  lines 2-1028: emitted fm content (corrupted: digit-prefix, duplicate keys, unquoted scalars)
  line 1029: original closing '---' (correct place)
  lines 1030+: body verbatim

Emit: '---' + repaired(fm 2:1029) + body(1029:).
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
            val = rest.strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"{' ' * d}{key.strip()}: {val}")
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
                continue
            val = m.group(3).strip()
            if needs_quote(val):
                val = quote(val)
            out.append(f"    {key}: {val}")
            continue
        out.append(ln)
    return out

def main():
    lines = open('research_state.md', encoding='utf-8').read().split('\n')
    assert lines[0] == '---' and lines[1] == '---' and lines[1029] == '---'
    fm = lines[2:1029]
    body = lines[1029:]
    repaired = repair_frontmatter_text(fm)

    bad = [ln for ln in repaired if re.match(r'^  \d ', ln)]
    if bad:
        print("WARN digit-prefix:", bad[:5], file=sys.stderr)
    dupes = [ln for ln in repaired if re.match(r'^      (evidence_refs|linked_evidence|false_positive_checks):$', ln)]
    if dupes:
        print("WARN duplicates:", dupes[:5], file=sys.stderr)

    final = ['---'] + repaired + body
    new_text = '\n'.join(final) + '\n'
    open('research_state.md', 'w', encoding='utf-8').write(new_text)
    print(f"wrote: {len(lines)} -> {len(final)} lines; body {'# Research State' in new_text}")

if __name__ == '__main__':
    main()
