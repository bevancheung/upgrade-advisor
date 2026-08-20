#!/usr/bin/env node
/* Render a dossier markdown (written by `upgrade-advisor dossier`) to .docx.
   Usage: node scripts/render_dossier_docx.js <dossier.md> <out.docx>
   Requires: npm i docx  (the only dependency).
   Handles the dossier's markdown subset: #/## headings, | tables |,
   - lists, **bold**, 【banner】lines, ``` fenced technical appendix. */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, LevelFormat, ShadingType, BorderStyle,
} = require("docx");
const fs = require("fs");

const [src, out] = process.argv.slice(2);
if (!src || !out) {
  console.error("usage: node render_dossier_docx.js <dossier.md> <out.docx>");
  process.exit(1);
}
const md = fs.readFileSync(src, "utf-8");
const F = "Microsoft YaHei";
const t = (s, o = {}) => new TextRun({ text: String(s), font: F, size: 21, ...o });
const runsMd = (text, base = {}) =>
  String(text).split(/\*\*/).map((seg, i) => t(seg, { bold: i % 2 === 1, ...base }));

function table(rows) {
  const ncol = rows[0].length;
  const total = 9200;
  const w = Math.floor(total / ncol);
  const widths = rows[0].map((_, i) =>
    ncol === 3 ? [2900, 3300, 3000][i] : w);
  const cell = (s, hdr, cw) => new TableCell({
    width: { size: cw, type: WidthType.DXA },
    shading: hdr ? { type: ShadingType.CLEAR, fill: "1F3864" } : undefined,
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ children: runsMd(s, { size: 18, bold: hdr, color: hdr ? "FFFFFF" : undefined }) })],
  });
  return new Table({
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      children: rows[0].map((_, i) => cell(r[i] == null ? "—" : r[i], ri === 0, widths[i])),
    })),
  });
}

const kids = [];
const lines = md.split(/\r?\n/);
let i = 0;
let inCode = false;
while (i < lines.length) {
  const ln = lines[i];
  const s = ln.trim();
  if (s.startsWith("```")) { inCode = !inCode; i++; continue; }
  if (inCode) {
    kids.push(new Paragraph({ spacing: { after: 20 },
      children: [new TextRun({ text: ln.length ? ln : " ", font: "Consolas", size: 15, color: "333333" })] }));
    i++; continue;
  }
  if (!s) { i++; continue; }
  if (s.startsWith("| ") || s.startsWith("|")) {
    const rows = [];
    while (i < lines.length && lines[i].trim().startsWith("|")) {
      const cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map(x => x.trim());
      if (!cells.every(c => /^-+$/.test(c))) rows.push(cells);
      i++;
    }
    kids.push(table(rows));
    kids.push(new Paragraph({ children: [t(" ", { size: 8 })] }));
    continue;
  }
  if (s.startsWith("# ")) {
    kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: [t(s.slice(2), { bold: true, size: 32 })] }));
  } else if (s.startsWith("## ")) {
    kids.push(new Paragraph({ spacing: { before: 220, after: 110 },
      children: [t(s.slice(3), { bold: true, size: 26, color: "1F3864" })] }));
  } else if (s.startsWith("【")) {
    kids.push(new Paragraph({
      shading: { type: ShadingType.CLEAR, fill: "FFF2CC" },
      border: { left: { style: BorderStyle.SINGLE, size: 24, color: "BF8F00" } },
      spacing: { before: 60, after: 140 }, children: runsMd(s) }));
  } else if (s.startsWith("- ")) {
    kids.push(new Paragraph({ numbering: { reference: "b", level: 0 },
      spacing: { after: 70 }, children: runsMd(s.slice(2), { size: 20 }) }));
  } else if (/^\d+\. /.test(s)) {
    kids.push(new Paragraph({ numbering: { reference: "b", level: 0 },
      spacing: { after: 70 }, children: runsMd(s.replace(/^\d+\. /, ""), { size: 20 }) }));
  } else {
    kids.push(new Paragraph({ spacing: { after: 100 }, children: runsMd(s, { size: 20 }) }));
  }
  i++;
}

const doc = new Document({
  numbering: { config: [{ reference: "b",
    levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
               style: { paragraph: { indent: { left: 340, hanging: 200 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 },
    margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } } }, children: kids }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log("wrote", out); });
