"""Generate one static page per section (18/<section>.html) from the same rendering code the list page uses.

Steps: copy index.html's styles to assets/site.css; render every section's body with index.html's own functions in
headless Chrome; write the pages, plus sitemap.xml and robots.txt. Run after build_data.py.
"""
import html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://moqri.github.io/federal-crimes-explained/"   # used for canonical links and the sitemap
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SERVER = "http://localhost:8000/usc18/"                         # a local server must be serving this folder

index = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
os.makedirs(os.path.join(HERE, "18"), exist_ok=True)

# 1. Shared stylesheet: exactly the list page's styles.
css = re.search(r"<style>(.*?)</style>", index, re.S).group(1)
open(os.path.join(HERE, "assets", "site.css"), "w", encoding="utf-8").write(css.strip() + "\n")
legend = re.search(r'<span class="legend" aria-label="Color key">.*?</span></span>', index, re.S).group(0)

# 2. Small script for section pages: legal-term popups and the copy-link button.
open(os.path.join(HERE, "assets", "page.js"), "w", encoding="utf-8").write(r"""// Section pages: show a legal term's definition on hover/tap, and copy the page link.
(() => {
  const pop = document.getElementById('pop');
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function show(btn) {
    if (!btn.dataset.def) return;
    pop.innerHTML = `<b>${esc(btn.dataset.label)}</b>${esc(btn.dataset.def)}`;
    pop.style.display = 'block';
    const r = btn.getBoundingClientRect(), w = pop.offsetWidth;
    pop.style.left = Math.max(16, Math.min(scrollX + r.left, scrollX + document.documentElement.clientWidth - w - 16)) + 'px';
    pop.style.top = (scrollY + r.bottom + 6) + 'px';
  }
  const hide = () => { pop.style.display = 'none'; };
  const hover = () => matchMedia('(hover: hover)').matches;
  document.addEventListener('click', e => {
    const t = e.target.closest('.term[data-def]');
    if (t) { e.preventDefault(); show(t); return; }
    hide();
    const cp = e.target.closest('[data-copy]');
    if (cp) {
      const url = location.href.split('#')[0];
      navigator.clipboard?.writeText(url).then(() => { cp.textContent = 'Copied!'; setTimeout(() => cp.textContent = 'Copy link', 1500); },
        () => { cp.textContent = 'Copy failed'; cp.title = url; });
    }
  });
  document.addEventListener('mouseover', e => { const t = e.target.closest('.term[data-def]'); if (t && hover()) show(t); });
  document.addEventListener('mouseout', e => { if (e.target.closest('.term[data-def]') && hover()) hide(); });
  document.addEventListener('focusin', e => { const t = e.target.closest('.term[data-def]'); t ? show(t) : hide(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') hide(); });

  // Crimes ↔ text: a crime's "(b)(1)" reference highlights that part of the official text, and a label in the text
  // highlights the crimes it holds. Click also scrolls the other side into view.
  const paras = [...document.querySelectorAll('.stat p[data-path]')];
  const crimes = [...document.querySelectorAll('.offenses li[data-where]')];
  const clear = () => document.querySelectorAll('.hl').forEach(el => el.classList.remove('hl'));
  const textFor = w => { let hits = paras.filter(p => p.dataset.path.startsWith(w));
    while (!hits.length && w.includes(')(')) { w = w.slice(0, w.lastIndexOf('(')); hits = paras.filter(p => p.dataset.path.startsWith(w)); }
    return hits; };
  const crimesFor = path => crimes.filter(c => path.startsWith(c.dataset.where) || c.dataset.where.startsWith(path));
  const mark = (els, scroll) => { els.forEach(el => el.classList.add('hl')); if (scroll && els[0]) els[0].scrollIntoView({ behavior: 'smooth', block: 'center' }); };
  for (const c of crimes) {
    c.addEventListener('mouseenter', () => { if (hover()) { clear(); mark(textFor(c.dataset.where)); c.classList.add('hl'); } });
    c.addEventListener('mouseleave', () => { if (hover()) clear(); });
    c.addEventListener('click', e => { if (e.target.closest('a, button')) return; clear(); c.classList.add('hl'); mark(textFor(c.dataset.where), true); });
  }
  for (const p of paras) p.querySelector('.lbl')?.addEventListener('click', () => {
    clear(); p.classList.add('hl');
    const hits = crimesFor(p.dataset.path);
    hits.forEach(c => c.classList.add('hl'));
    if (hits[0]) hits[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();
""")

# 3. Render every section with index.html's own functions (bodyHTML, chipsHTML) in headless Chrome.
harness = os.path.join(HERE, "_prerender.html")
open(harness, "w").write("""<!doctype html><body><iframe id="f" src="index.html" style="width:1100px;height:600px"></iframe><pre id="out"></pre>
<script>
f.onload = () => {
  const w = f.contentWindow;
  const wait = setInterval(() => {
    let crimes; try { crimes = w.eval('crimes'); } catch { return; }
    if (!crimes || !crimes.length) return;
    clearInterval(wait);
    const res = crimes.map(c => ({ section: c.section, title: c.title, chips: w.chipsHTML(c), body: w.bodyHTML(c), color: c.tier.color,
      plain: c.plain || '', chapter: c.chapter, chapterTitle: c.chapterTitle, n: (c.elements?.crimes || []).length }));
    out.textContent = JSON.stringify(res);
  }, 200);
};
</script></body>""")
try:
    dom = subprocess.run(["perl", "-e", "alarm 240; exec @ARGV", CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=60000",
                          "--dump-dom", SERVER + "_prerender.html"], capture_output=True, text=True).stdout
finally:
    os.remove(harness)
m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
if not m or not m.group(1).strip():
    sys.exit("Rendering failed: is the local server running at " + SERVER + "?")
pages = json.loads(html.unescape(m.group(1)))

# 4. Write the pages.
def page(i, p):
    prev_p, next_p = (pages[i - 1] if i else None), (pages[i + 1] if i + 1 < len(pages) else None)
    nav = lambda q, label: f'<a href="{q["section"]}.html" rel="{label}">{"‹ § " + q["section"] if label == "prev" else "§ " + q["section"] + " ›"}</a>' if q else ""
    desc = p["plain"] or f'18 U.S.C. § {p["section"]}, {p["title"]}: official text, color-coded, with each crime broken into its elements.'
    desc = (desc[:157] + "…") if len(desc) > 160 else desc
    title = f'18 U.S.C. § {p["section"]}: {p["title"]} · Crime Code'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{BASE_URL}18/{p["section"]}.html">
  <link rel="stylesheet" href="../assets/site.css">
</head>
<body>
<main class="page">
  <nav class="page-nav" aria-label="Sections">
    <a href="../index.html">← Crime Code: all {len(pages)} sections</a>
    <span class="pn">{nav(prev_p, "prev")}{nav(next_p, "next")}</span>
  </nav>
  <article class="card" style="--sev:{p["color"]}">
    <div class="card-row" style="cursor:default">
      <div class="page-head">
        <span class="sec">§ {html.escape(p["section"])}</span>
        <h1>{html.escape(p["title"])}</h1>
        <div class="chips">{p["chips"]}</div>
      </div>
    </div>
    <div class="body">
      {p["body"]}
    </div>
  </article>
  <nav class="page-nav page-foot-nav" aria-label="Sections">
    <a href="../index.html">← All sections</a>
    <span class="pn">{nav(prev_p, "prev")}{nav(next_p, "next")}</span>
  </nav>
  <footer><p>Official text from the United States Code, 2024 edition (current through Jan. 6, 2025), via GovInfo. Highlighting, crime breakdowns, and labels were prepared with AI assistance and may contain errors; rely on the official text. <b>This is general information, not legal advice.</b></p></footer>
</main>
<div id="pop" role="tooltip"></div>
<script src="../assets/page.js"></script>
</body>
</html>
"""

for i, p in enumerate(pages):
    open(os.path.join(HERE, "18", f'{p["section"]}.html'), "w", encoding="utf-8").write(page(i, p))

# 5. Sitemap and robots.txt for search engines.
urls = [BASE_URL] + [f'{BASE_URL}18/{p["section"]}.html' for p in pages]
open(os.path.join(HERE, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                                   + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
print(f"wrote {len(pages)} section pages, assets/site.css, assets/page.js, sitemap.xml, robots.txt")
