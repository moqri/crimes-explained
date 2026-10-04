"""Generate one static page per section from the same rendering code the list page uses.

Federal (default): 18/<section>.html, after build_data.py. Massachusetts (--jur ma): first writes ma/index.html from
index.html with the Massachusetts header, about text and footer, then ma/<chapter>/<section>.html, after ma/build_ma.py.
Steps: copy index.html's styles to assets/site.css; render every section's body with the list page's own functions in
headless Chrome; write the pages, plus sitemap.xml and robots.txt (covering both jurisdictions).
"""
import glob, html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://moqri.github.io/us-crimes-explained/"   # used for canonical links and the sitemap
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SERVER = "http://localhost:8000/"                         # a local server must be serving this folder

index = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
MA = "--jur" in sys.argv and sys.argv[sys.argv.index("--jur") + 1] == "ma"

# Massachusetts list page: index.html with its own header, about text and footer (the regions marked <!-- jur:… -->).
# The header names the chapters included so far, e.g. "Chapters 265 (Crimes Against the Person) and 266 (Crimes Against Property)".
ma_chapters = {}
if MA:
    for c in json.load(open(os.path.join(HERE, "ma", "crimes.json"), encoding="utf-8"))["crimes"]:
        ma_chapters.setdefault(c["chapter"], c["chapterTitle"])
chap_link = lambda n, t: f'<a href="https://malegislature.gov/Laws/GeneralLaws/PartIV/TitleI/Chapter{n}" target="_blank" rel="noopener" title="Chapter {n}: official text on malegislature.gov">{"Chapter" if len(ma_chapters) == 1 else ""} {n} ({t})</a>'.replace("> ", ">")
chap_list = (lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1])([chap_link(n, t) for n, t in ma_chapters.items()]) if ma_chapters else ""
MA_REGIONS = {
    "nav": '<nav class="jurnav" aria-label="Jurisdiction"><a href="../">Federal</a><a href="./" aria-current="page">MA</a></nav>',
    "lede": f'<p class="lede">Every crime in {"" if len(ma_chapters) == 1 else "chapters "}{chap_list} of the <a href="https://malegislature.gov/Laws/GeneralLaws" target="_blank" rel="noopener" title="The General Laws on malegislature.gov">Massachusetts General Laws</a><span id="crimecount"></span></p>',
    "about": """
          <p>Massachusetts criminal law in its official text, annotated. Each section is color-coded to show the prohibited act, the knowledge and intent the law requires, and the penalty, and references to other sections link to them. <span id="edition"></span> More chapters of the criminal code will follow.</p>
          <ul>
      <li><b>Select any section</b> to open its own page with the official text beside a breakdown of each crime in it: the act, who can commit it when the law limits that, the knowledge and intent required, conditions, exceptions and defenses, the penalty with any conditions that change it, and other consequences. Breakdowns use only the text of that section.</li>
      <li>In the official text, <span class="act">the prohibited act</span> is highlighted in orange, the <span class="know">knowledge</span> the law requires in teal, the <span class="intent">intent</span> or purpose required (such as <i>wilfully</i> or <i>with intent to</i>) in purple, conditions by their <span class="condw">if</span> or <span class="condw">unless</span> in slate-blue italics, and <span class="pen">penalties</span> in red.</li>
      <li><span class="term" tabindex="0" style="cursor:default">Dotted-underlined words</span> are legal terms. Tap or hover to see what they mean.</li>
      <li>The colored bar on each card shows the <b>maximum</b> prison time stated in that section. Many sentences are lower, and some crimes are punished under other sections.</li>
      <li><b>State prison or house of correction:</b> a crime that can be punished in the state prison is a <b>felony</b>; one punishable only in a house of correction (county jail, usually up to 2½ years) is a <b>misdemeanor</b>.</li>
    </ul>
        """,
    "footer": """
    <p>Section headings and statutory text are the official text of the Massachusetts General Laws from the <a id="srclink" href="https://malegislature.gov/Laws/GeneralLaws" target="_blank" rel="noopener">Massachusetts Legislature</a>, current as of the download date shown under About. Summaries, crime types, maximum-penalty labels, crime breakdowns, and highlighting were prepared with AI assistance from that text and may contain errors, so rely on the official text.</p>
    <p>Not included: repealed sections and sections that do not themselves create a crime (definitions, procedure, sentencing administration). Many Massachusetts crimes are defined in chapters not yet included, for example chapters 268 (crimes against public justice), 269 (public peace and weapons), 272 (public order), 90 (motor vehicles), and 94C (drugs).</p>
    <p><b>This is general information, not legal advice.</b> If you are facing a legal issue, talk to a lawyer. If you are charged with a crime that can lead to jail and cannot afford a lawyer, you have the right to a court-appointed attorney.</p>
  """,
}
if MA:
    page_src = index.replace('<html lang="en">', '<html lang="en" data-jur="ma">', 1).replace("<title>Crimes Explained: Federal</title>", "<title>Crimes Explained: MA</title>", 1).replace("<h1>Crimes Explained: Federal</h1>", "<h1>Crimes Explained: MA</h1>", 1)
    page_src = page_src.replace('placeholder="Search, e.g. “identity theft”, “firearm”, or “§ 1001”"', 'placeholder="Search, e.g. “dangerous weapon”, “strangulation”, or “13A”"', 1)
    for name, body in MA_REGIONS.items():
        page_src, n = re.subn(rf"<!-- jur:{name} -->.*?<!-- /jur:{name} -->", lambda m: f"<!-- jur:{name} -->{body}<!-- /jur:{name} -->", page_src, flags=re.S)
        assert n == 1, name
    open(os.path.join(HERE, "ma", "index.html"), "w", encoding="utf-8").write(page_src)
OUT = os.path.join(HERE, "ma") if MA else os.path.join(HERE, "18")
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
os.makedirs(OUT, exist_ok=True)

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
harness = os.path.join(OUT if MA else HERE, "_prerender.html")
open(harness, "w").write("""<!doctype html><body><iframe id="f" src="index.html" style="width:1100px;height:600px"></iframe><pre id="out"></pre>
<script>
f.onload = () => {
  const w = f.contentWindow;
  const wait = setInterval(() => {
    let crimes; try { crimes = w.eval('crimes'); } catch { return; }
    if (!crimes || !crimes.length) return;
    clearInterval(wait);
    const res = crimes.map(c => ({ section: c.section, label: w.eval('secLabel')(c), url: c.url, title: c.title, chips: w.chipsHTML(c), body: w.bodyHTML(c), color: c.tier.color,
      plain: c.plain || '', chapter: c.chapter, chapterTitle: c.chapterTitle, n: (c.elements?.crimes || []).length }));
    out.textContent = JSON.stringify(res);
  }, 200);
};
</script></body>""")
try:
    dom = subprocess.run(["perl", "-e", "alarm 240; exec @ARGV", CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=60000",
                          "--dump-dom", SERVER + ("ma/" if MA else "") + "_prerender.html"], capture_output=True, text=True).stdout
finally:
    os.remove(harness)
m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
if not m or not m.group(1).strip():
    sys.exit("Rendering failed: is the local server running at " + SERVER + "?")
pages = json.loads(html.unescape(m.group(1)))

# 4. Write the pages.
UP = "../../" if MA else "../"                 # from a section page to the site root
def page(i, p):
    prev_p, next_p = (pages[i - 1] if i else None), (pages[i + 1] if i + 1 < len(pages) else None)
    href = lambda q: f'../{q["section"]}.html' if MA else f'{q["section"]}.html'
    short = lambda q: q["label"].split(", ")[-1] if MA else "§ " + q["section"]
    nav = lambda q, label: f'<a href="{href(q)}" rel="{label}">{"‹ " + short(q) if label == "prev" else short(q) + " ›"}</a>' if q else ""
    law = "M.G.L. " + p["label"] if MA else f'18 U.S.C. § {p["section"]}'
    desc = p["plain"] or f'{law}, {p["title"]}: official text, color-coded, with each crime broken into its elements.'
    desc = (desc[:157] + "…") if len(desc) > 160 else desc
    title = f'{law}: {p["title"]} · Crimes Explained'
    back = "Crimes Explained: MA, all" if MA else "Crimes Explained: Federal, all"
    source = (f'Official text of the Massachusetts General Laws from the Massachusetts Legislature (<a href="{html.escape(p["url"])}">malegislature.gov</a>), downloaded {EDITION_DATE}.'
              if MA else "Official text from the United States Code, 2024 edition (current through Jan. 6, 2025), via GovInfo.")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{BASE_URL}{"ma/" if MA else "18/"}{p["section"]}.html">
  <link rel="stylesheet" href="{UP}assets/site.css">
</head>
<body>
<main class="page">
  <nav class="page-nav" aria-label="Sections">
    <a href="{"../index.html"}">← {back} {len(pages)} sections</a>
    <span class="pn">{nav(prev_p, "prev")}{nav(next_p, "next")}</span>
  </nav>
  <article class="card" style="--sev:{p["color"]}">
    <div class="card-row" style="cursor:default">
      <div class="page-head">
        <span class="sec">{html.escape(p["label"])}</span>
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
  <footer><p>{source} Highlighting, crime breakdowns, and labels were prepared with AI assistance and may contain errors; rely on the official text. <b>This is general information, not legal advice.</b></p></footer>
</main>
<div id="pop" role="tooltip"></div>
<script src="{UP}assets/page.js"></script>
</body>
</html>
"""

EDITION_DATE = re.search(r"downloaded ([\d-]+)", json.load(open(os.path.join(OUT, "crimes.json")))["edition"]).group(1) if MA else ""
for i, p in enumerate(pages):
    path = os.path.join(OUT, f'{p["section"]}.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(page(i, p))

# 5. Sitemap (every section page of both jurisdictions) and robots.txt for search engines.
rel = sorted(os.path.relpath(f, HERE) for f in glob.glob(os.path.join(HERE, "18", "*.html")) + glob.glob(os.path.join(HERE, "ma", "*", "*.html")))
urls = [BASE_URL, BASE_URL + "ma/"] + [BASE_URL + r for r in rel]
open(os.path.join(HERE, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                                   + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
print(f"wrote {len(pages)} section pages{' and ma/index.html' if MA else ''}, assets/site.css, assets/page.js, sitemap.xml ({len(urls)} URLs), robots.txt")
