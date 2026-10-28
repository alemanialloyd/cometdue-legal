"""Build GitHub Pages from the legal content also bundled with CometDue."""

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from shutil import copyfile
from urllib.parse import urlsplit


DOCUMENT_IDS = {"privacy", "terms", "refunds", "data-deletion", "support", "licenses"}
BASE_URL = "https://alemanialloyd.github.io/cometdue-legal/"

CSS = """\
:root{color-scheme:dark;--bg:#090d1b;--panel:#11182b;--line:#28314c;--text:#eeeefa;--muted:#b0bbd3;--accent:#c6b6ff;--gold:#ffd698}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:2rem}
body{margin:0;background:radial-gradient(ellipse at 0 0,#201c3e,transparent 55rem),var(--bg);color:var(--text);font:17px/1.75 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--accent);text-underline-offset:.2em}a:hover{color:#fff}a:focus-visible{outline:3px solid var(--gold);outline-offset:5px;border-radius:3px}
.skip{position:absolute;top:-5rem;left:1rem;z-index:3;padding:.6rem 1rem;background:var(--panel)}.skip:focus{top:1rem}
.shell{max-width:1160px;margin:auto;padding:0 32px}.top{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:28px 0;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;color:var(--text);text-decoration:none;font-weight:800;font-size:22px;letter-spacing:-.04em}
.mark{display:grid;place-items:center;width:42px;height:42px;border:1px solid #665b94;border-radius:14px;background:linear-gradient(140deg,#50407d,#192341);color:var(--gold);font-size:25px;letter-spacing:0}
.top-note,.meta,.eyebrow{color:var(--muted);font-size:13px}.eyebrow{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-weight:700}
h1,h2,h3{line-height:1.2;letter-spacing:-.035em}h1{font-size:clamp(2.25rem,5vw,3.9rem);margin:.5rem 0 1.25rem}h2{font-size:1.5rem;margin:2.4rem 0 1rem}h3{font-size:1.2rem;margin:0 0 .6rem}p{margin:0 0 1.2rem}ul{padding-left:1.4rem}li{margin-bottom:.65rem}
.hero{max-width:780px;padding:62px 0 38px}.lead{color:var(--muted);font-size:1.15rem}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:0 0 48px}
.card{display:block;background:linear-gradient(130deg,#171e34,#101728);border:1px solid var(--line);border-radius:18px;padding:25px;color:var(--text);text-decoration:none;transition:border-color .15s}.card:hover{border-color:#8b78bf}.card h2{margin:0 0 12px;font-size:1.3rem}.card p{color:var(--muted);font-size:15px;margin:0}.card .arrow{display:inline-block;color:var(--gold);margin-top:16px;font-size:14px;font-weight:650}
.contact{border-top:1px solid var(--line);padding:28px 0}.contact p{color:var(--muted)}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:56px;padding:40px 0 64px}.side{align-self:start;position:sticky;top:28px}.side nav{display:flex;flex-direction:column;gap:4px}.side a{display:block;text-decoration:none;font-size:14px;color:var(--muted);padding:9px 12px;border-left:2px solid transparent}.side a[aria-current=page]{color:var(--text);background:#c6b6ff0b;border-color:var(--accent);border-radius:0 8px 8px 0}
article{min-width:0;max-width:780px}article header{padding-bottom:18px;border-bottom:1px solid var(--line)}article h1{font-size:clamp(2rem,4vw,3rem)}article p,article li{overflow-wrap:anywhere;white-space:pre-line}.toc{padding:20px 24px;margin:28px 0;background:var(--panel);border:1px solid var(--line);border-radius:14px}.toc p{font-size:13px;font-weight:700;color:var(--muted);margin:0 0 .5rem}.toc ol{padding-left:1.2rem;font-size:14px;margin:0}.toc li{margin:.2rem 0}.links{display:flex;flex-direction:column;align-items:start;gap:.55rem;margin:1rem 0 1.5rem}.links a{font-size:15px;overflow-wrap:anywhere}.footer{border-top:1px solid var(--line);padding:24px 0 40px;color:var(--muted);font-size:13px}.footer p{margin:0 0 .6rem}.footer a{margin-right:18px}.back{font-size:14px;display:inline-block;margin-bottom:22px}
@media(max-width:760px){.shell{padding:0 20px}.top{padding:20px 0}.top-note{display:none}.hero{padding:42px 0 24px}.cards{grid-template-columns:1fr}.layout{grid-template-columns:1fr;gap:28px;padding-top:24px}.side{position:static}.side nav{flex-direction:row;flex-wrap:wrap;gap:5px}.side a{padding:5px 9px;border-left:0;font-size:13px;border:1px solid var(--line);border-radius:7px}.side a[aria-current=page]{border:1px solid var(--accent);border-radius:7px}.toc{padding:16px 20px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card{transition:none}}
@media print{:root{color-scheme:light}body{background:#fff;color:#111;font-size:11pt}.shell{max-width:none;padding:0}.top,.side,.toc,.back,.footer{display:none}.layout{display:block;padding:0}article{max-width:none}a{color:#111}h2{break-after:avoid}.links a:after{content:" (" attr(href) ")";font-size:9pt}.meta,.lead{color:#444}}
"""


def esc(value):
    return html.escape(str(value), quote=True)


def load_catalog(source):
    catalog = json.loads(Path(source).read_text(encoding="utf-8"))
    if catalog.get("version") != 1:
        raise ValueError("Unsupported legal catalog version")
    date.fromisoformat(catalog["updatedAt"])
    publisher = catalog["publisher"]
    if not publisher.get("name") or not publisher.get("email"):
        raise ValueError("Publisher name and email are required")
    documents = catalog["documents"]
    if len(documents) != len(DOCUMENT_IDS) or {d["id"] for d in documents} != DOCUMENT_IDS:
        raise ValueError("Exactly the six legal documents are required")
    for document in documents:
        if not document["title"] or not document["description"] or not document["sections"]:
            raise ValueError("Empty legal document")
        for section in document["sections"]:
            if not section["heading"]:
                raise ValueError("Empty section heading")
            for link in section.get("links", []):
                parts = urlsplit(link["url"])
                supported = (parts.scheme == "https" and bool(parts.netloc)) or (
                    parts.scheme == "mailto" and bool(parts.path)
                )
                if not supported or not link["label"]:
                    raise ValueError("Unsupported legal link")
    return catalog


def section_id(index, heading):
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return f"section-{index + 1}-{slug}"


def frame(catalog, title, description, body, prefix, canonical):
    identity = catalog["publisher"].get("legalName", catalog["publisher"]["name"])
    email = catalog["publisher"]["email"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#090d1b"><meta name="description" content="{esc(description)}">
<title>{esc(title)} · CometDue</title><link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{prefix}assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a><div class="shell">
<header class="top"><a class="brand" href="{prefix}"><span class="mark" aria-hidden="true">☄</span>CometDue</a><span class="top-note">Legal &amp; support</span></header>
{body}
<footer class="footer"><p>{esc(identity)} · Philippines</p><p><a href="mailto:{esc(email)}">{esc(email)}</a></p><a href="{prefix}privacy/">Privacy</a><a href="{prefix}terms/">Terms</a><a href="{prefix}support/">Support</a></footer>
</div></body></html>
"""


def render_index(catalog, base_url):
    cards = "".join(
        f'<a class="card" href="{esc(d["id"])}/"><h2>{esc(d["title"])}</h2>'
        f'<p>{esc(d["description"])}</p><span class="arrow">Read document →</span></a>'
        for d in catalog["documents"]
    )
    email = catalog["publisher"]["email"]
    body = f"""<main id="main"><section class="hero"><p class="eyebrow">Clear information. Your control.</p>
<h1>Legal &amp; support</h1><p class="lead">How CometDue works, how your data is handled, and where to get help.</p><p class="meta">Documents updated {esc(catalog["updatedAt"])}</p></section>
<div class="cards">{cards}</div><section class="contact"><h2>Need a hand?</h2><p>Questions about your data, a purchase, or the app? Contact <a href="mailto:{esc(email)}">{esc(email)}</a>. Please keep passwords, payment card details, and full financial backups out of your initial support request.</p></section></main>"""
    return frame(catalog, "Legal & support", "CometDue policies and support from Sensei IT Solutions.", body, "./", base_url)


def render_document(catalog, document, base_url):
    nav = "".join(
        f'<a href="../{esc(d["id"])}/"' + (' aria-current="page"' if d["id"] == document["id"] else "")
        + f'>{esc(d["title"])}</a>' for d in catalog["documents"]
    )
    toc, sections = [], []
    for index, section in enumerate(document["sections"]):
        anchor = section_id(index, section["heading"])
        toc.append(f'<li><a href="#{anchor}">{esc(section["heading"])}</a></li>')
        content = "".join(f"<p>{esc(p)}</p>" for p in section.get("paragraphs", []))
        if section.get("bullets"):
            content += "<ul>" + "".join(f"<li>{esc(b)}</li>" for b in section["bullets"]) + "</ul>"
        if section.get("links"):
            content += '<div class="links">' + "".join(
                f'<a href="{esc(link["url"])}" rel="external">{esc(link["label"])}</a>' for link in section["links"]
            ) + "</div>"
        sections.append(f'<section aria-labelledby="{anchor}"><h2 id="{anchor}">{esc(section["heading"])}</h2>{content}</section>')
    identity = catalog["publisher"].get("legalName", catalog["publisher"]["name"])
    body = f"""<main class="layout" id="main"><aside class="side"><nav aria-label="Legal documents">{nav}</nav></aside>
<article><a class="back" href="../">← Legal &amp; support</a><header><p class="eyebrow">CometDue</p><h1>{esc(document["title"])}</h1><p class="lead">{esc(document["description"])}</p><p class="meta">Effective date: {esc(catalog["updatedAt"])}<br>{esc(identity)}</p></header>
<nav class="toc" aria-label="On this page"><p>ON THIS PAGE</p><ol>{"".join(toc)}</ol></nav>{"".join(sections)}</article></main>"""
    return frame(catalog, document["title"], document["description"], body, "../", base_url + document["id"] + "/")


def generate(source, output, base_url=BASE_URL):
    catalog = load_catalog(source)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    base_url = base_url.rstrip("/") + "/"
    (output / "assets").mkdir(exist_ok=True)
    (output / "assets/site.css").write_text(CSS, encoding="utf-8")
    (output / "index.html").write_text(render_index(catalog, base_url), encoding="utf-8")
    for document in catalog["documents"]:
        directory = output / document["id"]
        directory.mkdir(exist_ok=True)
        (directory / "index.html").write_text(render_document(catalog, document, base_url), encoding="utf-8")
    for directory in ("content", "tools"):
        (output / directory).mkdir(exist_ok=True)
    for original, target in ((Path(source), output / "content/en.json"), (Path(__file__), output / "tools/generate_site.py")):
        if original.resolve() != target.resolve():
            copyfile(original, target)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base_url}sitemap.xml\n", encoding="utf-8")
    urls = [base_url] + [base_url + d["id"] + "/" for d in catalog["documents"]]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    sitemap += "".join(f"<url><loc>{esc(url)}</loc><lastmod>{catalog['updatedAt']}</lastmod></url>" for url in urls)
    (output / "sitemap.xml").write_text(sitemap + "</urlset>\n", encoding="utf-8")
    missing_body = f'<main id="main" class="hero"><h1>Page not found</h1><p>Find the document you need in <a href="{esc(base_url)}">CometDue Legal &amp; Support</a>.</p></main>'
    (output / "404.html").write_text(frame(catalog, "Page not found", "Find CometDue legal documents and support.", missing_body, base_url, base_url), encoding="utf-8")
    links = "\n".join(f'- [{d["title"]}]({base_url}{d["id"]}/)' for d in catalog["documents"])
    readme = f"""# CometDue Legal & Support

Public legal documents and support information for CometDue.

**Website:** {base_url}

**Publisher:** {catalog['publisher'].get('legalName', catalog['publisher']['name'])}  
**Support and privacy:** {catalog['publisher']['email']}  
**Audience:** ages 13 and older  
**Effective date:** {catalog['updatedAt']}

## Documents

{links}

## Publishing

GitHub Pages serves **main / (root)**. This repository includes `index.html`
and `.nojekyll`; no theme, custom domain, or paid plan is needed.
After updating main, inspect the **pages build and deployment** run in Actions.

## Updating content

`content/en.json` is the public copy of the content bundled by the app at
`assets/legal/en.json`. Update the app source first, then generate this site:

```powershell
python tool/legal/generate_site.py --output build/legal-site
```

Publish only that generated folder to this repository. It includes policy
content, HTML, styling and the generator. Keep the installed app's bundled
policy version in step with releases.

For a site-only checkout, regenerate with:

```powershell
python tools/generate_site.py --source content/en.json --output .
```

Update the app's canonical copy with those same changes before its next release.
Use the public Privacy Policy and Support URLs above in store listings.
Store privacy disclosures, trader verification, purchases and submission are
configured separately in the store consoles.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="assets/legal/en.json")
    parser.add_argument("--output", default="build/legal-site")
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    catalog = generate(args.source, args.output, args.base_url)
    print(f"Generated {len(catalog['documents'])} legal pages and index in {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
