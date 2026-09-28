/**
 * render_proposal.js
 * Parses docs/FYP_Proposal.md, renders all mathematical formulas using KaTeX,
 * generates a publication-grade HTML document, and exports:
 * 1. docs/FYP_Proposal.pdf via Headless Edge with full vector math
 * 2. docs/FYP_Proposal.docx via Word COM automation
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const katex = require('katex');

const PROJECT_ROOT = path.resolve('E:/digital-twin-fyp');
const DOCS_DIR = path.join(PROJECT_ROOT, 'docs');
const MD_PATH = path.join(DOCS_DIR, 'FYP_Proposal.md');
const HTML_PATH = path.join(DOCS_DIR, 'FYP_Proposal.html');
const PDF_PATH = path.join(DOCS_DIR, 'FYP_Proposal.pdf');
const DOCX_PATH = path.join(DOCS_DIR, 'FYP_Proposal.docx');

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function renderMathSafe(tex, displayMode) {
  try {
    return katex.renderToString(tex.trim(), {
      displayMode: displayMode,
      throwOnError: false,
      output: 'htmlAndMathml'
    });
  } catch (e) {
    console.error(`KaTeX error for [${tex}]:`, e.message);
    return `<code class="math-fallback">${escapeHtml(tex)}</code>`;
  }
}

function parseInline(text) {
  // 1. Inline math: $...$
  text = text.replace(/(?<!\$)\$([^$\n]+?)\$(?!\$)/g, (match, formula) => {
    return renderMathSafe(formula, false);
  });

  // 2. Bold Italic: ***text***
  text = text.replace(/\*\*\*([^*]+?)\*\*\*/g, '<strong><em>$1</em></strong>');

  // 3. Bold: **text**
  text = text.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');

  // 4. Italic: *text*
  text = text.replace(/\*([^*]+?)\*/g, '<em>$1</em>');

  // 5. Inline code: `code`
  text = text.replace(/`([^`]+?)`/g, '<code>$1</code>');

  // 6. Markdown links: [text](url)
  text = text.replace(/\[([^\]]+?)\]\(([^)]+?)\)/g, '<a href="$2">$1</a>');

  return text;
}

function splitTableRow(rowStr) {
  let trimmed = rowStr.trim();
  if (trimmed.startsWith('|')) trimmed = trimmed.slice(1);
  if (trimmed.endsWith('|')) trimmed = trimmed.slice(0, -1);

  const cells = [];
  let current = '';
  let inMath = false;

  for (let i = 0; i < trimmed.length; i++) {
    const char = trimmed[i];
    const prev = i > 0 ? trimmed[i - 1] : '';

    if (char === '$' && prev !== '\\') {
      inMath = !inMath;
      current += char;
    } else if (char === '|' && !inMath && prev !== '\\') {
      cells.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  cells.push(current.trim());
  return cells;
}

function convertMarkdownToHtml(md) {
  const lines = md.split(/\r?\n/);
  const out = [];

  let inCode = false;
  let codeLang = '';
  let codeLines = [];

  let inTable = false;
  let tableRows = [];

  let inList = false;
  let listType = 'ul';

  let inBlockquote = false;
  let bqLines = [];

  let inBlockMath = false;
  let blockMathLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const stripped = line.trim();

    // Check Block Code fence
    if (stripped.startsWith('```')) {
      if (!inCode) {
        if (inList) { out.push(`</${listType}>`); inList = false; }
        if (inBlockquote) { out.push(`<blockquote>${parseInline(bqLines.join(' '))}</blockquote>`); inBlockquote = false; bqLines = []; }
        inCode = true;
        codeLang = stripped.slice(3).trim();
        codeLines = [];
        continue;
      } else {
        inCode = false;
        out.push(`<pre class="code-box"><code class="language-${codeLang}">${escapeHtml(codeLines.join('\n'))}</code></pre>`);
        codeLines = [];
        continue;
      }
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }

    // Check Block Math $$ ... $$
    if (stripped.startsWith('$$')) {
      if (inList) { out.push(`</${listType}>`); inList = false; }
      if (inBlockquote) { out.push(`<blockquote>${parseInline(bqLines.join(' '))}</blockquote>`); inBlockquote = false; bqLines = []; }
      
      if (stripped === '$$') {
        if (!inBlockMath) {
          inBlockMath = true;
          blockMathLines = [];
          continue;
        } else {
          inBlockMath = false;
          out.push(`<div class="math-display">${renderMathSafe(blockMathLines.join(' '), true)}</div>`);
          blockMathLines = [];
          continue;
        }
      } else {
        // Single line $$ formula $$
        const singleMatch = stripped.match(/^\$\$([\s\S]+?)\$\$$/);
        if (singleMatch) {
          out.push(`<div class="math-display">${renderMathSafe(singleMatch[1], true)}</div>`);
          continue;
        } else {
          // Starts with $$ but ends later
          inBlockMath = true;
          blockMathLines = [stripped.slice(2)];
          continue;
        }
      }
    }
    if (inBlockMath) {
      if (stripped.endsWith('$$')) {
        inBlockMath = false;
        blockMathLines.push(stripped.slice(0, -2));
        out.push(`<div class="math-display">${renderMathSafe(blockMathLines.join(' '), true)}</div>`);
        blockMathLines = [];
      } else {
        blockMathLines.push(stripped);
      }
      continue;
    }

    // Check Tables
    if (stripped.startsWith('|') && stripped.endsWith('|')) {
      if (inList) { out.push(`</${listType}>`); inList = false; }
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      tableRows.push(stripped);
      continue;
    } else if (inTable) {
      inTable = false;
      if (tableRows.length >= 2) {
        const headerCols = splitTableRow(tableRows[0]);
        const bodyRows = tableRows.slice(2).map(r => splitTableRow(r));
        
        let tHtml = '<div class="table-wrap"><table class="academic-table"><thead><tr>';
        for (const h of headerCols) {
          tHtml += `<th>${parseInline(h)}</th>`;
        }
        tHtml += '</tr></thead><tbody>';
        for (const row of bodyRows) {
          tHtml += '<tr>';
          for (const cell of row) {
            tHtml += `<td>${parseInline(cell)}</td>`;
          }
          tHtml += '</tr>';
        }
        tHtml += '</tbody></table></div>';
        out.push(tHtml);
      }
      tableRows = [];
    }

    // Check Blockquote
    if (stripped.startsWith('>')) {
      if (!inBlockquote) {
        inBlockquote = true;
        bqLines = [];
      }
      let bqText = stripped.slice(1).trim();
      bqText = bqText.replace(/^\[!(NOTE|IMPORTANT|TIP|WARNING|CAUTION)\]\s*/, '<strong>[$1]</strong> ');
      bqLines.push(bqText);
      continue;
    } else if (inBlockquote) {
      inBlockquote = false;
      out.push(`<blockquote>${parseInline(bqLines.join(' '))}</blockquote>`);
      bqLines = [];
    }

    // Check Horizontal Rule
    if (/^(\*\*\*|---|___)$/.test(stripped)) {
      if (inList) { out.push(`</${listType}>`); inList = false; }
      out.push('<hr class="section-divider" />');
      continue;
    }

    // Check Headings (# Heading)
    const headingMatch = stripped.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      if (inList) { out.push(`</${listType}>`); inList = false; }
      const level = headingMatch[1].length;
      const text = parseInline(headingMatch[2]);
      out.push(`<h${level} class="heading-${level}">${text}</h${level}>`);
      continue;
    }

    // Check Lists
    const ulMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
    const olMatch = line.match(/^(\s*)\d+\.\s+(.*)$/);
    if (ulMatch || olMatch) {
      const curType = olMatch ? 'ol' : 'ul';
      const itemText = (olMatch || ulMatch)[2];
      if (!inList) {
        inList = true;
        listType = curType;
        out.push(`<${listType}>`);
      } else if (listType !== curType) {
        out.push(`</${listType}>`);
        listType = curType;
        out.push(`<${listType}>`);
      }
      out.push(`<li>${parseInline(itemText)}</li>`);
      continue;
    } else if (inList && stripped === '') {
      if (i + 1 < lines.length && /^(\s*)([-*+]|\d+\.)\s+/.test(lines[i + 1])) {
        continue;
      } else {
        out.push(`</${listType}>`);
        inList = false;
        continue;
      }
    } else if (inList) {
      out.push(`</${listType}>`);
      inList = false;
    }

    // Empty lines
    if (!stripped) continue;

    // Normal paragraph
    out.push(`<p>${parseInline(line)}</p>`);
  }

  // Cleanup lingering tags
  if (inTable && tableRows.length >= 2) {
    const headerCols = splitTableRow(tableRows[0]);
    const bodyRows = tableRows.slice(2).map(r => splitTableRow(r));
    let tHtml = '<div class="table-wrap"><table class="academic-table"><thead><tr>';
    for (const h of headerCols) tHtml += `<th>${parseInline(h)}</th>`;
    tHtml += '</tr></thead><tbody>';
    for (const row of bodyRows) {
      tHtml += '<tr>';
      for (const cell of row) tHtml += `<td>${parseInline(cell)}</td>`;
      tHtml += '</tr>';
    }
    tHtml += '</tbody></table></div>';
    out.push(tHtml);
  }
  if (inList) out.push(`</${listType}>`);
  if (inBlockquote) out.push(`<blockquote>${parseInline(bqLines.join(' '))}</blockquote>`);

  return out.join('\n');
}

function buildFullHtml(bodyHtml) {
  // Read local KaTeX CSS
  const katexCssPath = path.join(PROJECT_ROOT, 'node_modules/katex/dist/katex.min.css');
  let katexCss = '';
  if (fs.existsSync(katexCssPath)) {
    katexCss = fs.readFileSync(katexCssPath, 'utf8');
    // Ensure font paths in CSS point to local file or cdn fallback
    katexCss = katexCss.replace(/url\(fonts\//g, 'url(https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/fonts/');
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BS Space Science FYP Proposal — IST Islamabad</title>
<style>
${katexCss}

@page {
  size: A4;
  margin: 2.2cm 2.0cm 2.4cm 2.0cm;
  @top-center {
    content: "BS Space Science Final Year Project Thesis Proposal — IST Islamabad";
    font-family: 'Calibri', 'Segoe UI', sans-serif;
    font-size: 8.5pt;
    color: #64748b;
    border-bottom: 0.5pt solid #cbd5e1;
    padding-bottom: 4pt;
  }
  @bottom-right {
    content: "Page " counter(page);
    font-family: 'Calibri', 'Segoe UI', sans-serif;
    font-size: 8.5pt;
    color: #64748b;
  }
  @bottom-left {
    content: "Haider Taqveen (230601020) · Mashaf Majeed (230601017)";
    font-family: 'Calibri', 'Segoe UI', sans-serif;
    font-size: 8.5pt;
    color: #64748b;
  }
}

body {
  font-family: 'Calibri', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}

/* Formal Academic Header */
.academic-banner {
  border-bottom: 3px double #1e3a8a;
  padding-bottom: 14pt;
  margin-bottom: 22pt;
  text-align: center;
}
.inst-title {
  font-size: 14.5pt;
  font-weight: 800;
  color: #1e3a8a;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-bottom: 3pt;
}
.dept-title {
  font-size: 11.5pt;
  font-weight: 600;
  color: #2563eb;
  margin-bottom: 12pt;
}
.thesis-title {
  font-size: 18pt;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.3;
  margin-bottom: 14pt;
}
.metadata-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  margin: 10pt 0 4pt 0;
  font-size: 10.5pt;
}
.metadata-table td {
  padding: 6pt 10pt;
  border-bottom: 1px solid #e2e8f0;
}
.metadata-table tr:last-child td {
  border-bottom: none;
}
.meta-lbl {
  font-weight: 700;
  color: #1e3a8a;
  width: 22%;
  white-space: nowrap;
}
.meta-val {
  color: #334155;
}

/* Headings */
h1.heading-1 {
  font-family: 'Georgia', 'Cambria', serif;
  font-size: 17pt;
  color: #1e3a8a;
  font-weight: 700;
  border-bottom: 1.75pt solid #1e3a8a;
  padding-bottom: 5pt;
  margin-top: 26pt;
  margin-bottom: 12pt;
  page-break-after: avoid;
}
h2.heading-2 {
  font-family: 'Georgia', 'Cambria', serif;
  font-size: 13.5pt;
  color: #1d4ed8;
  font-weight: 700;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 3pt;
  margin-top: 20pt;
  margin-bottom: 8pt;
  page-break-after: avoid;
}
h3.heading-3 {
  font-size: 11.5pt;
  color: #2563eb;
  font-weight: 700;
  margin-top: 15pt;
  margin-bottom: 6pt;
  page-break-after: avoid;
}
h4.heading-4 {
  font-size: 11pt;
  color: #475569;
  font-weight: 700;
  font-style: italic;
  margin-top: 12pt;
  margin-bottom: 4pt;
  page-break-after: avoid;
}

/* Paragraphs & Text */
p {
  margin-top: 0;
  margin-bottom: 8pt;
  text-align: justify;
  text-justify: inter-word;
}
strong {
  font-weight: 700;
  color: #0f172a;
}
em {
  font-style: italic;
}

/* Section Dividers */
hr.section-divider {
  border: 0;
  height: 1px;
  background: #cbd5e1;
  margin: 20pt 0;
}

/* Tables */
.table-wrap {
  margin: 12pt 0;
  page-break-inside: avoid;
}
table.academic-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
  line-height: 1.4;
}
table.academic-table th {
  background-color: #1e3a8a;
  color: #ffffff;
  font-weight: 700;
  padding: 8pt 10pt;
  border: 1px solid #1e3a8a;
  text-align: left;
}
table.academic-table td {
  padding: 8pt 10pt;
  border: 1px solid #cbd5e1;
  vertical-align: middle;
  color: #1e293b;
}
table.academic-table td .katex {
  font-size: 1.05em !important;
  line-height: 1.25;
}
table.academic-table tr:nth-child(even) {
  background-color: #f8fafc;
}

/* KaTeX Math Blocks */
.math-display {
  display: block;
  text-align: center;
  margin: 14pt 0;
  padding: 10pt 16pt;
  background-color: #f8fafc;
  border-left: 3.5pt solid #3b82f6;
  border-radius: 4px;
  overflow-x: auto;
  page-break-inside: avoid;
}
.katex-display {
  margin: 0 !important;
}
.katex {
  font-size: 1.05em !important;
}

/* Code Blocks */
pre.code-box {
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 3.5pt solid #64748b;
  border-radius: 4px;
  padding: 9pt 12pt;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 9.5pt;
  color: #0f172a;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 12pt 0;
  page-break-inside: avoid;
}
code {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 9.5pt;
  background-color: #f1f5f9;
  padding: 1.5pt 4pt;
  border-radius: 3px;
  color: #0f172a;
}

/* Blockquotes / Callouts */
blockquote {
  border-left: 3.5pt solid #2563eb;
  background-color: #f8fafc;
  padding: 8pt 14pt;
  margin: 12pt 0;
  color: #334155;
  font-style: italic;
  border-radius: 0 4px 4px 0;
}

/* Lists */
ul, ol {
  margin-top: 3pt;
  margin-bottom: 9pt;
  padding-left: 24pt;
}
li {
  margin-bottom: 4pt;
}

a {
  color: #2563eb;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
</head>
<body>

<div class="academic-banner">
  <div class="inst-title">Institute of Space Technology (IST), Islamabad</div>
  <div class="dept-title">Department of Space Science · BS Space Science Final Year Project</div>
  <div class="thesis-title">Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin</div>

  <table class="metadata-table">
    <tr>
      <td class="meta-lbl">Project Title:</td>
      <td class="meta-val">Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin</td>
    </tr>
    <tr>
      <td class="meta-lbl">Authors / Team:</td>
      <td class="meta-val"><strong>Haider Taqveen</strong> (Reg. No. 230601020) &nbsp;|&nbsp; <strong>Mashaf Majeed</strong> (Reg. No. 230601017)</td>
    </tr>
    <tr>
      <td class="meta-lbl">Supervisor:</td>
      <td class="meta-val"><strong>Dr. Munawar Ali Shah</strong>, Department of Space Science, IST Islamabad</td>
    </tr>
    <tr>
      <td class="meta-lbl">Academic Year:</td>
      <td class="meta-val">2026–2027 &nbsp;·&nbsp; Version 2.0 (Engineering Architecture Revision)</td>
    </tr>
    <tr>
      <td class="meta-lbl">Target Simulators:</td>
      <td class="meta-val">Blender 4.x / Unreal Engine 5.4 (Chaos Physics)</td>
    </tr>
    <tr>
      <td class="meta-lbl">Repository:</td>
      <td class="meta-val"><code>E:\\digital-twin-fyp</code></td>
    </tr>
  </table>
</div>

${bodyHtml}

</body>
</html>`;
}

async function main() {
  console.log(`Reading Markdown from: ${MD_PATH}`);
  const md = fs.readFileSync(MD_PATH, 'utf8');

  console.log('Converting Markdown with KaTeX math rendering...');
  const bodyHtml = convertMarkdownToHtml(md);
  const fullHtml = buildFullHtml(bodyHtml);

  fs.writeFileSync(HTML_PATH, fullHtml, 'utf8');
  console.log(`Generated HTML with KaTeX (${fullHtml.length} bytes): ${HTML_PATH}`);

  // 1. Export PDF using Headless Edge (Chromium rendering vector math)
  console.log('Generating PDF via Headless Edge...');
  const edgePs = `
$edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
$htmlUrl = "file:///" + "${HTML_PATH.replace(/\\/g, '/')}"
$pdfTarget = "${PDF_PATH.replace(/\\/g, '\\\\')}"

Start-Process $edgePath -ArgumentList "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=\`"$pdfTarget\`"", "\`"$htmlUrl\`"" -Wait -PassThru
`;
  const edgePsFile = path.join(DOCS_DIR, 'convert_pdf.ps1');
  fs.writeFileSync(edgePsFile, edgePs, 'utf8');

  try {
    execSync(`powershell -ExecutionPolicy Bypass -File "${edgePsFile}"`, { stdio: 'inherit' });
    if (fs.existsSync(PDF_PATH)) {
      const pdfSize = fs.statSync(PDF_PATH).size;
      console.log(`SUCCESS: PDF generated: ${PDF_PATH} (${pdfSize.toLocaleString()} bytes)`);
    } else {
      console.error('PDF was not found after Edge command.');
    }
  } catch (err) {
    console.error('Error running Edge for PDF generation:', err.message);
  } finally {
    if (fs.existsSync(edgePsFile)) fs.unlinkSync(edgePsFile);
  }

  // 2. Export DOCX via Word COM
  console.log('Generating Word DOCX via Word COM Automation...');
  const wordPs = `
$htmlPath = "${HTML_PATH}"
$docxPath = "${DOCX_PATH}"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    $doc = $word.Documents.Open($htmlPath)
    $doc.PageSetup.TopMargin = 54
    $doc.PageSetup.BottomMargin = 54
    $doc.PageSetup.LeftMargin = 54
    $doc.PageSetup.RightMargin = 54
    $doc.SaveAs2($docxPath, 16)
    $doc.Close()
    Write-Host "DOCX generated successfully via Word."
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
`;
  const psFile = path.join(DOCS_DIR, 'convert_docx.ps1');
  fs.writeFileSync(psFile, wordPs, 'utf8');

  try {
    execSync(`powershell -ExecutionPolicy Bypass -File "${psFile}"`, { stdio: 'inherit' });
    if (fs.existsSync(DOCX_PATH)) {
      const docxSize = fs.statSync(DOCX_PATH).size;
      console.log(`SUCCESS: DOCX generated: ${DOCX_PATH} (${docxSize.toLocaleString()} bytes)`);
    }
  } catch (err) {
    console.error('Error running Word COM:', err.message);
  } finally {
    if (fs.existsSync(psFile)) fs.unlinkSync(psFile);
  }
}

main().catch(err => {
  console.error('Fatal execution error:', err);
  process.exit(1);
});
