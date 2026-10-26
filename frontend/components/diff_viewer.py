from difflib import SequenceMatcher
from html import escape

import streamlit.components.v1 as components
from pygments import format as format_tokens
from pygments import lex
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.util import ClassNotFound


def _lexer_for(filename):
    try:
        return get_lexer_for_filename(filename)
    except ClassNotFound:
        return TextLexer()


def _tokenized_lines(text, lexer):
    lines = [[]]
    for token_type, value in lex(text, lexer):
        parts = value.split("\n")
        for index, part in enumerate(parts):
            if part:
                lines[-1].append((token_type, part.rstrip("\r")))
            if index < len(parts) - 1:
                lines.append([])

    if text.endswith("\n") and len(lines) > 1 and not lines[-1]:
        lines.pop()
    return lines if text else [[]]


def _changed_ranges(source_line, target_line):
    source_ranges = []
    target_ranges = []
    matcher = SequenceMatcher(None, source_line, target_line, autojunk=False)
    for tag, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if tag != "equal":
            if source_start < source_end:
                source_ranges.append((source_start, source_end))
            if target_start < target_end:
                target_ranges.append((target_start, target_end))
    return source_ranges, target_ranges


def _render_line(tokens, changed_ranges, formatter):
    if not tokens:
        return "&nbsp;"

    rendered = []
    position = 0
    for token_type, value in tokens:
        token_end = position + len(value)
        boundaries = {position, token_end}
        for start, end in changed_ranges:
            if start < token_end and end > position:
                boundaries.add(max(position, start))
                boundaries.add(min(token_end, end))

        sorted_boundaries = sorted(boundaries)
        for start, end in zip(sorted_boundaries, sorted_boundaries[1:]):
            segment = value[start - position:end - position]
            if not segment:
                continue
            segment_html = format_tokens([(token_type, segment)], formatter).rstrip("\n")
            if any(diff_start < end and diff_end > start for diff_start, diff_end in changed_ranges):
                segment_html = f'<span class="inline-change">{segment_html}</span>'
            rendered.append(segment_html)
        position = token_end

    return "".join(rendered) or "&nbsp;"


def _aligned_rows(source_lines, target_lines):
    rows = []
    matcher = SequenceMatcher(None, source_lines, target_lines)
    for tag, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if tag == "equal":
            rows.extend(
                (source_index, target_index, tag)
                for source_index, target_index in zip(
                    range(source_start, source_end),
                    range(target_start, target_end)
                )
            )
        elif tag == "replace":
            count = max(source_end - source_start, target_end - target_start)
            for offset in range(count):
                source_index = source_start + offset
                target_index = target_start + offset
                rows.append((
                    source_index if source_index < source_end else None,
                    target_index if target_index < target_end else None,
                    tag
                ))
        elif tag == "delete":
            rows.extend((source_index, None, tag) for source_index in range(source_start, source_end))
        else:
            rows.extend((None, target_index, tag) for target_index in range(target_start, target_end))
    return rows


def render_diff_viewer(
    source_filename: str,
    source_code: str,
    matched_filename: str,
    matched_code: str,
    matched_source_lines: set,
    matched_target_lines: set | None = None
):
    if matched_target_lines is None:
        matched_target_lines = matched_source_lines

    source_lines = source_code.splitlines() or [""]
    target_lines = matched_code.splitlines() or [""]
    source_lexer = _lexer_for(source_filename)
    target_lexer = _lexer_for(matched_filename)
    source_tokens = _tokenized_lines(source_code, source_lexer)
    target_tokens = _tokenized_lines(matched_code, target_lexer)
    formatter = HtmlFormatter(nowrap=True)

    rows = _aligned_rows(source_lines, target_lines)
    source_rendered_lines = []
    target_rendered_lines = []

    for source_index, target_index, tag in rows:
        source_line = source_lines[source_index] if source_index is not None else ""
        target_line = target_lines[target_index] if target_index is not None else ""
        source_ranges, target_ranges = (
            _changed_ranges(source_line, target_line) if tag == "replace" else ([], [])
        )

        source_number = source_index + 1 if source_index is not None else None
        target_number = target_index + 1 if target_index is not None else None
        source_is_match = source_number in matched_source_lines if source_number else False
        target_is_match = target_number in matched_target_lines if target_number else False

        if source_index is None:
            source_class, target_class = "empty", "added"
        elif target_index is None:
            source_class, target_class = "removed", "empty"
        elif tag == "delete":
            source_class, target_class = "removed", "empty"
        elif tag == "insert":
            source_class, target_class = "empty", "added"
        elif tag == "replace":
            source_class, target_class = "changed", "changed"
        else:
            source_class = "similar" if source_is_match else "unchanged"
            target_class = "similar" if target_is_match else "unchanged"

        if source_is_match and tag != "delete":
            source_class = "similar"
        if target_is_match and tag != "insert":
            target_class = "similar"

        source_html = (
            _render_line(source_tokens[source_index], source_ranges, formatter)
            if source_index is not None else "&nbsp;"
        )
        target_html = (
            _render_line(target_tokens[target_index], target_ranges, formatter)
            if target_index is not None else "&nbsp;"
        )
        source_rendered_lines.append(
            f"<div class='editor-line {source_class}'>"
            f"<span class='line-number'>{source_number or ''}</span><code>{source_html}</code>"
            "</div>"
        )
        target_rendered_lines.append(
            f"<div class='editor-line {target_class}'>"
            f"<span class='line-number'>{target_number or ''}</span><code>{target_html}</code>"
            "</div>"
        )

    escaped_source = escape(source_filename)
    escaped_target = escape(matched_filename)
    page = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
:root {{
  color-scheme: dark;
  --base: #1e1e2e; --mantle: #181825; --crust: #11111b; --surface: #313244;
  --overlay: #45475a; --text: #cdd6f4; --subtext: #a6adc8; --green: #a6e3a1;
  --red: #f38ba8; --mauve: #cba6f7; --blue: #89b4fa; --yellow: #f9e2af;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--base); color: var(--text); font-family: Inter, system-ui, sans-serif; }}
.toolbar {{ display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center; padding: 10px 14px; border-bottom: 1px solid var(--surface); background: var(--mantle); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 12px; color: var(--subtext); font-size: 12px; }}
.legend span {{ display: inline-flex; gap: 6px; align-items: center; }}
.swatch {{ width: 11px; height: 11px; border-radius: 3px; display: inline-block; }}
.similar-swatch {{ background: var(--green); }} .changed-swatch {{ background: var(--red); }} .added-swatch {{ background: #313f35; }}
.editors {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1px; background: var(--surface); }}
.editor {{ min-width: 0; background: var(--crust); }}
.editor-header {{ position: sticky; top: 0; z-index: 2; display: flex; gap: 8px; align-items: center; min-height: 42px; padding: 8px 12px; border-bottom: 1px solid var(--surface); background: var(--mantle); color: var(--text); font: 600 12px/1.4 Inter, system-ui, sans-serif; overflow: hidden; }}
.file-icon {{ color: var(--mauve); }} .filename {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.editor-scroll {{ height: 630px; overflow: auto; overscroll-behavior: contain; }}
.editor-line {{ display: flex; min-height: 22px; width: max-content; min-width: 100%; padding-right: 18px; color: var(--text); font: 13px/1.7 'Cascadia Code', 'Fira Code', Consolas, monospace; white-space: pre; }}
.editor-line code {{ display: block; min-width: 0; padding-left: 12px; font: inherit; }}
.line-number {{ flex: 0 0 48px; padding: 0 10px 0 4px; color: #6c7086; text-align: right; user-select: none; border-right: 1px solid #242436; }}
.unchanged {{ background: var(--crust); }} .similar {{ background: #25332f; box-shadow: inset 3px 0 var(--green); }}
.changed {{ background: #382832; box-shadow: inset 3px 0 var(--red); }}
.removed {{ background: #3c2630; box-shadow: inset 3px 0 var(--red); }}
.added {{ background: #25332f; box-shadow: inset 3px 0 var(--green); }}
.empty {{ background: #181825; opacity: .45; }}
.inline-change {{ background: rgba(243, 139, 168, .3); border-radius: 2px; text-decoration: underline; text-decoration-color: var(--red); }}
.editor-line:hover {{ filter: brightness(1.12); }}
.token, span {{ font-family: inherit; }}
.c {{ color: #6c7086; font-style: italic; }} .k, .kd, .kn, .ow {{ color: #cba6f7; }}
.s, .s1, .s2, .sb {{ color: #a6e3a1; }} .nf, .fm {{ color: #89b4fa; }}
.nc, .kt, .nn {{ color: #f9e2af; }} .mi, .mf, .m {{ color: #fab387; }}
.bp, .nb, .na {{ color: #f5c2e7; }} .o, .p {{ color: #89dceb; }}
.err {{ color: var(--red); }}
@media (max-width: 760px) {{
  .editors {{ grid-template-columns: minmax(0, 1fr); }}
  .editor-scroll {{ height: 38vh; }}
}}
</style>
</head>
<body>
  <div class="toolbar">
    <strong>Side-by-side comparison</strong>
    <div class="legend">
      <span><i class="swatch similar-swatch"></i>Matched content</span>
      <span><i class="swatch changed-swatch"></i>Changed or removed</span>
      <span><i class="swatch added-swatch"></i>Added</span>
    </div>
  </div>
  <div class="editors">
    <section class="editor">
      <header class="editor-header"><span class="file-icon">●</span><span class="filename">{escaped_source}</span></header>
      <div class="editor-scroll" aria-label="Source document code"></div>
    </section>
    <section class="editor">
      <header class="editor-header"><span class="file-icon">●</span><span class="filename">{escaped_target}</span></header>
      <div class="editor-scroll" aria-label="Matched document code"></div>
    </section>
  </div>
  <template id="source-lines">{''.join(source_rendered_lines)}</template>
  <template id="target-lines">{''.join(target_rendered_lines)}</template>
  <script>
    const panes = document.querySelectorAll(".editor-scroll");
    panes[0].innerHTML = document.getElementById("source-lines").innerHTML;
    panes[1].innerHTML = document.getElementById("target-lines").innerHTML;
    let syncing = false;
    panes[0].addEventListener("scroll", () => {{
      if (syncing) return;
      syncing = true;
      panes[1].scrollTop = panes[0].scrollTop;
      panes[1].scrollLeft = panes[0].scrollLeft;
      syncing = false;
    }});
    panes[1].addEventListener("scroll", () => {{
      if (syncing) return;
      syncing = true;
      panes[0].scrollTop = panes[1].scrollTop;
      panes[0].scrollLeft = panes[1].scrollLeft;
      syncing = false;
    }});
  </script>
</body>
</html>"""
    components.html(page, height=730, scrolling=True)
