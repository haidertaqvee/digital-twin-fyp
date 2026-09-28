"""
export_proposal_docs.py
Exports docs/FYP_Proposal.md into publication-quality Word (.docx) and PDF (.pdf) documents
using Microsoft Word COM Automation on Windows.
"""

import os
import re
import html
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"E:\digital-twin-fyp").resolve()
DOCS_DIR = PROJECT_ROOT / "docs"
MD_PATH = DOCS_DIR / "FYP_Proposal.md"
HTML_PATH = DOCS_DIR / "FYP_Proposal.html"
DOCX_PATH = DOCS_DIR / "FYP_Proposal.docx"
PDF_PATH = DOCS_DIR / "FYP_Proposal.pdf"


def format_math_latex(formula: str) -> str:
    """Converts common LaTeX math syntax into clean unicode/HTML representation."""
    s = formula.strip()
    
    # Common replacements
    replacements = [
        (r"\\text\{([^}]+)\}", r"<b>\1</b>"),
        (r"\\mathbf\{([^}]+)\}", r"<b>\1</b>"),
        (r"\\mathcal\{([^}]+)\}", r"<i>\1</i>"),
        (r"\\bm\{([^}]+)\}", r"<b>\1</b>"),
        (r"\\cdot", " · "),
        (r"\\times", " × "),
        (r"\\approx", " ≈ "),
        (r"\\le\b", " ≤ "),
        (r"\\leq\b", " ≤ "),
        (r"\\ge\b", " ≥ "),
        (r"\\geq\b", " ≥ "),
        (r"\\neq\b", " ≠ "),
        (r"\\in\b", " ∈ "),
        (r"\\notin\b", " ∉ "),
        (r"\\subset\b", " ⊂ "),
        (r"\\cap\b", " ∩ "),
        (r"\\cup\b", " ∪ "),
        (r"\\rightarrow\b", " → "),
        (r"\\leftarrow\b", " ← "),
        (r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"∑<sub>\1</sub><sup>\2</sup>"),
        (r"\\sum_\{([^}]+)\}", r"∑<sub>\1</sub>"),
        (r"\\sum\b", "∑"),
        (r"\\prod\b", "∏"),
        (r"\\int_\{([^}]+)\}\^\{([^}]+)\}", r"∫<sub>\1</sub><sup>\2</sup>"),
        (r"\\int\b", "∫"),
        (r"\\sqrt\{([^}]+)\}", r"√(\1)"),
        (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1) / (\2)"),
        (r"\\theta", "θ"),
        (r"\\alpha", "α"),
        (r"\\beta", "β"),
        (r"\\gamma", "γ"),
        (r"\\delta", "δ"),
        (r"\\Delta", "Δ"),
        (r"\\lambda", "λ"),
        (r"\\mu", "μ"),
        (r"\\pi", "π"),
        (r"\\rho", "ρ"),
        (r"\\sigma", "σ"),
        (r"\\tau", "τ"),
        (r"\\phi", "φ"),
        (r"\\omega", "ω"),
        (r"\\Omega", "Ω"),
        (r"\\nabla", "∇"),
        (r"\\infty", "∞"),
        (r"\\partial", "∂"),
        (r"\\left\(", "("),
        (r"\\right\)", ")"),
        (r"\\left\[", "["),
        (r"\\right\]", "]"),
        (r"\\left\|", "‖"),
        (r"\\right\|", "‖"),
        (r"\\|", "‖"),
        (r"\\quad", " &nbsp; "),
        (r"\\qquad", " &nbsp;&nbsp; "),
    ]
    for pattern, repl in replacements:
        s = re.sub(pattern, repl, s)
        
    # Subscripts and superscripts
    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"_([a-zA-Z0-9])", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([a-zA-Z0-9])", r"<sup>\1</sup>", s)
    
    return s


def parse_inline(text: str) -> str:
    """Parses inline Markdown formatting into HTML."""
    # Inline math: $formula$
    def replace_math(m):
        raw = m.group(1)
        formatted = format_math_latex(raw)
        return f'<span class="math-inline">{formatted}</span>'
    text = re.sub(r"(?<!\$)\$([^$]+)\$(?!\$)", replace_math, text)
    
    # Bold italic: ***text*** or ___text___
    text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold: **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text*
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # Inline code: `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    
    return text


def markdown_to_html(md_text: str) -> str:
    """Converts the full markdown text to a structured, styled HTML page."""
    lines = md_text.splitlines()
    html_out = []
    
    in_code_block = False
    code_block_lang = ""
    code_block_lines = []
    
    in_table = False
    table_rows = []
    
    in_list = False
    list_type = "ul"
    
    in_blockquote = False
    blockquote_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check code fence
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_lang = stripped[3:].strip()
                code_block_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                code_content = html.escape("\n".join(code_block_lines))
                html_out.append(f'<pre class="code-block"><code class="language-{code_block_lang}">{code_content}</code></pre>')
                i += 1
                continue
                
        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue
            
        # Check block math $$...$$
        if stripped.startswith("$$"):
            math_lines = []
            if stripped == "$$":
                i += 1
                while i < len(lines) and lines[i].strip() != "$$":
                    math_lines.append(lines[i].strip())
                    i += 1
                if i < len(lines) and lines[i].strip() == "$$":
                    i += 1
            else:
                # Single line $$...$$
                m = re.match(r"^\$\$(.+)\$\$$", stripped)
                if m:
                    math_lines.append(m.group(1))
                    i += 1
                else:
                    math_lines.append(stripped[2:])
                    i += 1
                    while i < len(lines) and not lines[i].strip().endswith("$$"):
                        math_lines.append(lines[i].strip())
                        i += 1
                    if i < len(lines):
                        math_lines.append(lines[i].strip()[:-2])
                        i += 1
            raw_math = " ".join(math_lines)
            fmt_math = format_math_latex(raw_math)
            html_out.append(f'<div class="math-block">{fmt_math}</div>')
            continue
            
        # Check tables
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            in_table = False
            # Render table
            if len(table_rows) >= 2:
                header_row = [c.strip() for c in table_rows[0].split("|")[1:-1]]
                separator_row = table_rows[1]
                body_rows = [[c.strip() for c in r.split("|")[1:-1]] for r in table_rows[2:]]
                
                tbl_html = ['<table class="academic-table">', '<thead><tr>']
                for th in header_row:
                    tbl_html.append(f'<th>{parse_inline(th)}</th>')
                tbl_html.append('</tr></thead><tbody>')
                for row in body_rows:
                    tbl_html.append('<tr>')
                    for td in row:
                        tbl_html.append(f'<td>{parse_inline(td)}</td>')
                    tbl_html.append('</tr>')
                tbl_html.append('</tbody></table>')
                html_out.append("".join(tbl_html))
            table_rows = []
            # do not increment i, let next logic process current line
            
        # Check blockquote
        if stripped.startswith(">"):
            if not in_blockquote:
                in_blockquote = True
                blockquote_lines = []
            bq_content = stripped[1:].strip()
            # Clean alert syntax like [!NOTE], [!IMPORTANT]
            bq_content = re.sub(r"^\[!(NOTE|IMPORTANT|TIP|WARNING|CAUTION)\]\s*", r"<strong>[\1]</strong> ", bq_content)
            blockquote_lines.append(bq_content)
            i += 1
            continue
        elif in_blockquote:
            in_blockquote = False
            bq_text = " ".join(blockquote_lines)
            html_out.append(f'<blockquote>{parse_inline(bq_text)}</blockquote>')
            blockquote_lines = []
            # do not increment i, let next logic process current line
            
        # Check horizontal rule
        if stripped in ["---", "***", "___"]:
            if in_list:
                html_out.append(f"</{list_type}>")
                in_list = False
            html_out.append('<hr class="divider" />')
            i += 1
            continue
            
        # Check headings
        if stripped.startswith("#"):
            if in_list:
                html_out.append(f"</{list_type}>")
                in_list = False
            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                h_text = parse_inline(m.group(2))
                html_out.append(f'<h{level} class="heading-{level}">{h_text}</h{level}>')
                i += 1
                continue
                
        # Check lists
        ul_match = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        ol_match = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if ul_match or ol_match:
            current_type = "ol" if ol_match else "ul"
            item_text = (ol_match or ul_match).group(2)
            
            if not in_list:
                in_list = True
                list_type = current_type
                html_out.append(f"<{list_type}>")
            elif list_type != current_type:
                html_out.append(f"</{list_type}>")
                list_type = current_type
                html_out.append(f"<{list_type}>")
                
            html_out.append(f"<li>{parse_inline(item_text)}</li>")
            i += 1
            continue
        elif in_list and stripped == "":
            # Check if next line is also a list item
            if i + 1 < len(lines) and re.match(r"^(\s*)([-*+]|\d+\.)\s+", lines[i+1]):
                i += 1
                continue
            else:
                html_out.append(f"</{list_type}>")
                in_list = False
                i += 1
                continue
        elif in_list:
            html_out.append(f"</{list_type}>")
            in_list = False
            
        # Blank line
        if not stripped:
            i += 1
            continue
            
        # Regular paragraph
        html_out.append(f'<p>{parse_inline(line)}</p>')
        i += 1

    # Close any open structures
    if in_table and len(table_rows) >= 2:
        header_row = [c.strip() for c in table_rows[0].split("|")[1:-1]]
        body_rows = [[c.strip() for c in r.split("|")[1:-1]] for r in table_rows[2:]]
        tbl_html = ['<table class="academic-table">', '<thead><tr>']
        for th in header_row:
            tbl_html.append(f'<th>{parse_inline(th)}</th>')
        tbl_html.append('</tr></thead><tbody>')
        for row in body_rows:
            tbl_html.append('<tr>')
            for td in row:
                tbl_html.append(f'<td>{parse_inline(td)}</td>')
            tbl_html.append('</tr>')
        tbl_html.append('</tbody></table>')
        html_out.append("".join(tbl_html))

    if in_list:
        html_out.append(f"</{list_type}>")
    if in_blockquote:
        html_out.append(f'<blockquote>{parse_inline(" ".join(blockquote_lines))}</blockquote>')

    body_html = "\n".join(html_out)

    # Wrap in complete HTML document with rich academic CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BS Space Science Final Year Project Proposal — IST Islamabad</title>
<style>
  @page {{
    size: A4;
    margin: 2.2cm 2.0cm 2.2cm 2.0cm;
    mso-header-margin: 35.4pt;
    mso-footer-margin: 35.4pt;
    mso-paper-source: 0;
  }}

  body {{
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a202c;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
  }}

  /* Academic Cover Banner */
  .proposal-header {{
    border-bottom: 3px double #1e3a8a;
    padding-bottom: 14pt;
    margin-bottom: 20pt;
    text-align: center;
  }}
  .inst-name {{
    font-size: 14pt;
    font-weight: bold;
    color: #1e3a8a;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4pt;
  }}
  .dept-name {{
    font-size: 11.5pt;
    font-weight: 600;
    color: #3b82f6;
    margin-bottom: 12pt;
  }}
  .doc-title {{
    font-size: 18pt;
    font-weight: bold;
    color: #0f172a;
    line-height: 1.3;
    margin-bottom: 14pt;
  }}
  .meta-box {{
    display: table;
    width: 100%;
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 10pt 14pt;
    margin: 10pt auto;
    font-size: 10.5pt;
    text-align: left;
  }}
  .meta-row {{
    display: table-row;
  }}
  .meta-label {{
    display: table-cell;
    font-weight: bold;
    color: #1e3a8a;
    width: 22%;
    padding: 3pt 6pt 3pt 0;
  }}
  .meta-val {{
    display: table-cell;
    color: #334155;
    padding: 3pt 0;
  }}

  /* Headings */
  h1.heading-1 {{
    font-family: 'Georgia', 'Cambria', serif;
    font-size: 17pt;
    color: #1e3a8a;
    font-weight: bold;
    border-bottom: 1.5pt solid #1e3a8a;
    padding-bottom: 4pt;
    margin-top: 24pt;
    margin-bottom: 10pt;
    page-break-after: avoid;
  }}
  h2.heading-2 {{
    font-family: 'Georgia', 'Cambria', serif;
    font-size: 13.5pt;
    color: #1e40af;
    font-weight: bold;
    border-bottom: 0.75pt solid #cbd5e1;
    padding-bottom: 3pt;
    margin-top: 18pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
  }}
  h3.heading-3 {{
    font-size: 11.5pt;
    color: #2563eb;
    font-weight: bold;
    margin-top: 14pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
  }}
  h4.heading-4 {{
    font-size: 11pt;
    color: #334155;
    font-weight: bold;
    font-style: italic;
    margin-top: 10pt;
    margin-bottom: 4pt;
    page-break-after: avoid;
  }}

  /* Paragraphs & Text */
  p {{
    margin-top: 0;
    margin-bottom: 8pt;
    text-align: justify;
    text-justify: inter-word;
  }}

  strong {{
    font-weight: bold;
    color: #0f172a;
  }}
  em {{
    font-style: italic;
  }}

  /* Dividers */
  hr.divider {{
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 18pt 0;
  }}

  /* Tables */
  table.academic-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}
  table.academic-table th {{
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: bold;
    padding: 6pt 8pt;
    border: 1px solid #1e3a8a;
    text-align: left;
  }}
  table.academic-table td {{
    padding: 5pt 8pt;
    border: 1px solid #cbd5e1;
    vertical-align: top;
    color: #1e293b;
  }}
  table.academic-table tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  /* Math Blocks */
  .math-block {{
    display: block;
    text-align: center;
    margin: 10pt 0;
    padding: 8pt 14pt;
    background-color: #f8fafc;
    border-left: 3pt solid #3b82f6;
    border-radius: 2px;
    font-family: 'Cambria Math', 'Cambria', serif;
    font-size: 11.5pt;
    color: #0f172a;
  }}
  .math-inline {{
    font-family: 'Cambria Math', 'Cambria', serif;
    font-size: 11pt;
    color: #1e3a8a;
    padding: 0 2pt;
  }}

  /* Code Blocks */
  pre.code-block {{
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 8pt 12pt;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
    color: #0f172a;
    line-height: 1.4;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 10pt 0;
    page-break-inside: avoid;
  }}
  code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
    background-color: #f1f5f9;
    padding: 1pt 4pt;
    border-radius: 3px;
    color: #0f172a;
  }}

  /* Blockquotes / Callouts */
  blockquote {{
    border-left: 3.5pt solid #2563eb;
    background-color: #f8fafc;
    padding: 6pt 12pt;
    margin: 10pt 0;
    color: #334155;
    font-style: italic;
  }}

  /* Lists */
  ul, ol {{
    margin-top: 2pt;
    margin-bottom: 8pt;
    padding-left: 22pt;
  }}
  li {{
    margin-bottom: 4pt;
  }}

  a {{
    color: #2563eb;
    text-decoration: none;
  }}
  a:hover {{
    text-decoration: underline;
  }}
</style>
</head>
<body>

<div class="proposal-header">
  <div class="inst-name">Institute of Space Technology (IST), Islamabad</div>
  <div class="dept-name">Department of Space Science · BS Space Science Final Year Project</div>
  <div class="doc-title">Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin</div>
  
  <div class="meta-box">
    <div class="meta-row">
      <div class="meta-label">Project Title:</div>
      <div class="meta-val">Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin</div>
    </div>
    <div class="meta-row">
      <div class="meta-label">Authors / Team:</div>
      <div class="meta-val"><strong>Haider Taqveen</strong> (Reg. No. 230601020) &nbsp;|&nbsp; <strong>Mashaf Majeed</strong> (Reg. No. 230601017)</div>
    </div>
    <div class="meta-row">
      <div class="meta-label">Supervisor:</div>
      <div class="meta-val"><strong>Dr. Munawar Ali Shah</strong>, Department of Space Science, IST</div>
    </div>
    <div class="meta-row">
      <div class="meta-label">Academic Session:</div>
      <div class="meta-val">2026–2027 &nbsp;·&nbsp; Version 2.0 (Engineering Architecture Revision)</div>
    </div>
    <div class="meta-row">
      <div class="meta-label">Target Simulators:</div>
      <div class="meta-val">Blender 4.x / Unreal Engine 5.4 (Chaos Physics)</div>
    </div>
    <div class="meta-row">
      <div class="meta-label">Repository:</div>
      <div class="meta-val"><code>E:\digital-twin-fyp</code></div>
    </div>
  </div>
</div>

{body_html}

</body>
</html>
"""
    return full_html


def build_documents():
    print(f"Reading Markdown from: {MD_PATH}")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("Generating styled academic HTML...")
    html_content = markdown_to_html(md_text)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Wrote HTML ({len(html_content)} bytes) to: {HTML_PATH}")

    # Invoke PowerShell script with Word COM automation
    ps_script = f"""
$htmlPath = "{HTML_PATH}"
$docxPath = "{DOCX_PATH}"
$pdfPath = "{PDF_PATH}"

Write-Host "Starting Microsoft Word COM Automation..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {{
    Write-Host "Opening HTML in Word: $htmlPath"
    $doc = $word.Documents.Open($htmlPath)

    # Page setup
    $doc.PageSetup.TopMargin = 54      # ~0.75 in
    $doc.PageSetup.BottomMargin = 54   # ~0.75 in
    $doc.PageSetup.LeftMargin = 54     # ~0.75 in
    $doc.PageSetup.RightMargin = 54    # ~0.75 in

    # Save as native Word .docx (16 = wdFormatXMLDocument)
    Write-Host "Exporting to DOCX: $docxPath"
    $doc.SaveAs2($docxPath, 16)

    # Save as native PDF (17 = wdFormatPDF)
    Write-Host "Exporting to PDF: $pdfPath"
    $doc.SaveAs2($pdfPath, 17)

    $doc.Close()
    Write-Host "Documents generated successfully!"
}}
finally {{
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}}
"""

    ps_file = DOCS_DIR / "convert_word.ps1"
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_script)

    print("Running PowerShell conversion with Word COM...")
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("PowerShell Output:")
    print(res.stdout)
    if res.stderr:
        print("PowerShell Stderr:")
        print(res.stderr)

    if ps_file.exists():
        ps_file.unlink()

    if DOCX_PATH.exists() and PDF_PATH.exists():
        print(f"SUCCESS: Generated DOCX: {DOCX_PATH} ({DOCX_PATH.stat().st_size:,} bytes)")
        print(f"SUCCESS: Generated PDF: {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes)")
    else:
        print("WARNING: One or more target document files were not generated.")


if __name__ == "__main__":
    build_documents()
