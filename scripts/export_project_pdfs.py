#!/usr/bin/env python3
"""Export the four project reports and check their Chinese text and page bounds.

Dependencies: markdown-it-py, weasyprint, pymupdf, Pillow. Supply a local CJK
font with --font-file when no system Noto Sans CJK/SC font is available.
"""

import argparse
import hashlib
import html
import json
import logging
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from PIL import Image
import pymupdf
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration


SOURCES = (
    "PROJECT_OVERVIEW.md",
    "PROJECT_CHALLENGES.md",
    "PROJECT_PRESENTATION_30MIN.md",
    "PROJECT_ISSUE_REPORT.md",
)
STYLE = """
@font-face {
  font-family: ProjectCJK;
  src: url("FONT_URL");
  font-weight: 100 900;
}
@page {
  size: A4;
  margin: 19mm 16mm 20mm;
  @top-left {
    content: "DOCUMENT_LABEL";
    font-family: ProjectCJK; font-size: 8pt; color: #697277;
  }
  @bottom-right {
    content: counter(page) " / " counter(pages);
    font-family: ProjectCJK; font-size: 8pt; color: #697277;
  }
}
body {
  font-family: ProjectCJK, sans-serif;
  font-size: 10pt; line-height: 1.7; color: #22292d;
  overflow-wrap: anywhere;
}
h1, h2, h3, h4 { line-height: 1.45; break-after: avoid; font-weight: 700; }
h1 { font-size: 20pt; margin: 0 0 7mm; }
h2 {
  font-size: 14pt; margin: 7mm 0 3mm; padding-bottom: 1.5mm;
  border-bottom: 0.5pt solid #d8dfe2;
}
h3 { font-size: 11.5pt; margin: 4mm 0 2mm; }
p { margin: 0 0 3mm; orphans: 3; widows: 3; }
li { margin-bottom: 1.8mm; }
ul, ol { padding-left: 6mm; margin: 2mm 0 4mm; }
a { color: #236256; text-decoration: none; overflow-wrap: anywhere; }
strong { font-weight: 700; }
code {
  font-family: "DejaVu Sans Mono", ProjectCJK, monospace;
  font-size: 8.4pt; overflow-wrap: anywhere;
}
p code, li code, td code { white-space: normal; }
pre {
  background: #f1f4f5; border-left: 2pt solid #75878f;
  padding: 3mm; margin: 3mm 0 4mm; white-space: pre-wrap;
  overflow-wrap: anywhere; line-height: 1.55; break-inside: avoid;
}
pre code { font-size: 8pt; white-space: pre-wrap; }
table {
  border-collapse: collapse; table-layout: fixed; width: 100%;
  font-size: 8.2pt; line-height: 1.6; margin: 3mm 0 5mm;
}
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td {
  border: 0.5pt solid #d6dfe2; padding: 1.7mm 2mm;
  vertical-align: top; overflow-wrap: anywhere;
}
th { background: #eaf0f1; font-weight: 700; text-align: left; }
figure { margin: 4mm 0 5mm; break-inside: avoid; }
figure img { display: block; max-width: 100%; max-height: 210mm; margin: auto; }
figcaption { text-align: center; font-size: 8.5pt; color: #68767d; margin-top: 2mm; }
blockquote { margin: 3mm 0; padding-left: 3mm; border-left: 2pt solid #75878f; }
.source-note { font-size: 8pt; color: #697277; }
nav { break-after: page; margin-top: 8mm; }
nav h2 { border: 0; }
nav ul { list-style: none; padding: 0; }
nav a::after { content: leader('.') target-counter(attr(href), page); }
"""


def font_path(value):
    candidates = [value, os.environ.get("PROJECT_PDF_FONT")]
    candidates += [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
        "/mnt/c/Windows/Fonts/NotoSansSC-VF.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError("Supply a Chinese font with --font-file or PROJECT_PDF_FONT")


def local_path(target, root):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    path = (root / unquote(parts.path)).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def image_rule(tokens, index, options, env):
    token = tokens[index]
    path = local_path(token.attrGet("src"), env["base"])
    if path is None or not path.is_file():
        raise ValueError("Report images must be existing local files")
    with Image.open(path) as source:
        width, height = source.size
    scale = min(673 / width, 793 / height, 1)
    return (f'<img src="{path.as_uri()}" alt="{html.escape(token.content)}" '
            f'width="{round(width * scale)}" height="{round(height * scale)}">')


def paragraph_rule(tokens, index, options, env):
    opening = tokens[index].type == "paragraph_open"
    content = tokens[index + 1 if opening else index - 1]
    children = content.children or []
    if content.type == "inline" and len(children) == 1 and children[0].type == "image":
        if opening:
            return "<figure>"
        return f"<figcaption>{html.escape(children[0].content)}</figcaption></figure>\n"
    return "<p>" if opening else "</p>\n"


def render_markdown(source, original):
    parser = MarkdownIt("commonmark").enable("table")
    parser.renderer.rules["image"] = image_rule
    parser.renderer.rules["paragraph_open"] = paragraph_rule
    parser.renderer.rules["paragraph_close"] = paragraph_rule
    tokens = parser.parse(original.decode("utf-8"))
    sections = []
    for index, block in enumerate(tokens):
        if block.type == "heading_open" and block.tag == "h2":
            anchor = f"section-{len(sections) + 1}"
            block.attrSet("id", anchor)
            sections.append((anchor, tokens[index + 1].content))
        for token in block.children or []:
            if token.type == "link_open":
                local_path(token.attrGet("href"), source.parent)
    body = parser.renderer.render(tokens, parser.options, {"base": source.parent})
    sha = hashlib.sha256(original).hexdigest()
    toc = '<nav aria-label="目录"><h2>目录</h2><ul>'
    toc += "".join(f'<li><a href="#{anchor}">{html.escape(label)}</a></li>'
                   for anchor, label in sections)
    toc += "</ul></nav>"
    note = (f'<p class="source-note">源文件：{source.name}；SHA256：{sha[:16]}。'
            '正文、表格与链接来自同名 Markdown；本地证据链接需与仓库一起使用。</p>')
    body = body.replace("</h1>", f"</h1>{note}{toc}", 1)
    title = next(line[2:] for line in original.decode("utf-8").splitlines()
                 if line.startswith("# "))
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<title>{html.escape(title)}</title></head><body>{body}</body></html>')


def make_local_links_portable(output, root):
    with pymupdf.open(output) as pdf:
        changed = False
        for page in pdf:
            for link in page.get_links():
                if link["kind"] == pymupdf.LINK_LAUNCH and Path(link["file"]).is_absolute():
                    target = Path(link["file"]).resolve().relative_to(root)
                    page.update_link({**link, "file": target.as_posix()})
                    changed = True
        if changed:
            pdf.saveIncr()


def validate_pdf(source, original, output, preview):
    with pymupdf.open(output) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        source_cjk = len(re.findall(r"[\u4e00-\u9fff]", original.decode("utf-8")))
        pdf_cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        if "\ufffd" in text or pdf_cjk < source_cjk * .97:
            raise ValueError(f"Possible missing Chinese text: {source.name}")
        outside = []
        image_pages = []
        for index, page in enumerate(pdf):
            if not page.get_text().strip():
                raise ValueError(f"Blank page {index + 1}: {source.name}")
            for word in page.get_text("words"):
                if not page.rect.contains(pymupdf.Rect(word[:4])):
                    outside.append({"page": index + 1, "text": word[4]})
            if page.get_image_info():
                image_pages.append(index + 1)
            if preview:
                page.get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2)).save(
                    preview / f"{source.stem}_page_{index + 1:02d}.png")
        if outside:
            raise ValueError(f"Text outside pages: {outside}")
        return {
            "source": source.name, "source_sha256": hashlib.sha256(original).hexdigest(),
            "pdf": output.name, "pdf_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "pages": len(pdf), "bytes": output.stat().st_size,
            "chinese_source": source_cjk, "chinese_pdf": pdf_cjk,
            "image_pages": image_pages,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--font-file")
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    font = font_path(args.font_file)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
    fonts = FontConfiguration()
    logging.getLogger("weasyprint").setLevel(logging.WARNING)
    results = []
    for name in SOURCES:
        source = root / name
        original = source.read_bytes()
        document = render_markdown(source, original)
        style = STYLE.replace("FONT_URL", font.as_uri()).replace("DOCUMENT_LABEL", source.stem)
        output = source.with_suffix(".pdf")
        HTML(string=document, base_url=str(root)).write_pdf(
            str(output), stylesheets=[CSS(string=style, font_config=fonts)], font_config=fonts)
        make_local_links_portable(output, root)
        if source.read_bytes() != original:
            raise RuntimeError(f"Markdown changed during export: {source}")
        results.append(validate_pdf(source, original, output, args.preview_dir))
    manifest = {"font": str(font), "documents": results}
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
