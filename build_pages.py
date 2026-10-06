"""Generate one static page per section from the same rendering code the list page uses.

Federal (default): 18/<section>.html, after build_data.py. Massachusetts (--jur ma): first writes ma/index.html from
index.html with the Massachusetts header, about text and footer, then ma/<chapter>/<section>.html, after ma/build_ma.py.
California (--jur ca): the same for ca/index.html and ca/<section>.html, after ca/build_ca.py.
New York (--jur ny): ny/index.html and ny/<section>.html, after ny/build_ny.py.
Steps: copy index.html's styles to assets/site.css; render every section's body with the list page's own functions in
headless Chrome; write the pages, plus sitemap.xml and robots.txt (covering both jurisdictions).
"""
import glob, html, json, os, re, subprocess, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://crimes.wiki/"   # used for canonical links and the sitemap
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SERVER = "http://localhost:8000/"                         # a local server must be serving this folder

index = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
JURSEL = sys.argv[sys.argv.index("--jur") + 1] if "--jur" in sys.argv else "us"
MA, CA, NY = JURSEL == "ma", JURSEL == "ca", JURSEL == "ny"
CON, MACON = JURSEL in ("con", "macon"), JURSEL == "macon"      # a constitution: the U.S. ("con") or Massachusetts ("macon")
STATE = MA or CA or NY or CON                                   # a list page generated from index.html (a state, or a constitution)
DIR = "ma/constitution" if MACON else "constitution" if CON else JURSEL   # the folder its pages go in

# Massachusetts list page: index.html with its own header, about text and footer (the regions marked <!-- jur:… -->).
# The header names the chapters included so far, e.g. "Chapters 265 (Crimes Against the Person) and 266 (Crimes Against Property)".
ma_chapters = {}
if MA:
    for c in json.load(open(os.path.join(HERE, "ma", "crimes.json"), encoding="utf-8"))["crimes"]:
        ma_chapters.setdefault(c["chapter"], c["chapterTitle"])
chap_link = lambda n, t: f'<a href="https://malegislature.gov/Laws/GeneralLaws/PartIV/TitleI/Chapter{n}" target="_blank" rel="noopener" title="Chapter {n}: official text on malegislature.gov">{"Chapter" if len(ma_chapters) == 1 else ""} {n} ({t})</a>'.replace("> ", ">")
chap_list = (lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1])([chap_link(n, t) for n, t in ma_chapters.items()]) if ma_chapters else ""
MA_REGIONS = {
    "nav": '<nav class="jurnav docnav" aria-label="Law"><a href="./" aria-current="page">Crimes</a><a href="constitution/">Constitution</a></nav><nav class="jurnav" aria-label="Jurisdiction"><a href="../">Federal</a><a href="./" aria-current="page">Massachusetts</a><a href="../ny/">New York</a><a href="../ca/">California</a></nav>',
    "lede": f'<p class="lede">Every crime in {"" if len(ma_chapters) == 1 else "chapters "}{chap_list} of the <a href="https://malegislature.gov/Laws/GeneralLaws" target="_blank" rel="noopener" title="The General Laws on malegislature.gov">Massachusetts General Laws</a><span id="crimecount"></span></p>',
    "about": """
          <p>Massachusetts criminal law in its official text, annotated. Each section is color-coded to show the prohibited act, the mental state the law requires, and the penalty, and references to other sections link to them. <span id="edition"></span> More chapters of the criminal code will follow.</p>
          <ul>
      <li><b>Select any section</b> to open its own page with the official text beside a breakdown of each crime in it: the act, who can commit it when the law limits that, the mental state required, conditions, exceptions and defenses, the penalty with any conditions that change it, and other consequences. Breakdowns use only the text of that section.</li>
      <li>In the official text, <span class="act">the prohibited act</span> is highlighted in orange, the <span class="intent">mental state</span> the law requires (knowledge, intent, recklessness or negligence, such as <i>wilfully</i> or <i>with intent to</i>) in teal, conditions by their <span class="condw">if</span> or <span class="condw">unless</span> in purple italics, and <span class="pen">penalties</span> in red.</li>
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

# California list page: the same regions, for Titles 8 and 13 of Part 1 of the Penal Code.
CA_TITLE_URL = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=PEN&division=&title={}.&part=1.&chapter=&article="
CA_REGIONS = {
    "nav": '<nav class="jurnav docnav" aria-label="Law"><a href="./" aria-current="page">Crimes</a><a href="../constitution/">U.S. Constitution</a></nav><nav class="jurnav" aria-label="Jurisdiction"><a href="../">Federal</a><a href="../ma/">Massachusetts</a><a href="../ny/">New York</a><a href="./" aria-current="page">California</a></nav>',
    "lede": f'<p class="lede">Every crime in <a href="{CA_TITLE_URL.format(8)}" target="_blank" rel="noopener" title="Title 8 (Of Crimes Against the Person): official text on leginfo.legislature.ca.gov">Title 8 (Of Crimes Against the Person)</a> and <a href="{CA_TITLE_URL.format(13)}" target="_blank" rel="noopener" title="Title 13 (Of Crimes Against Property): official text on leginfo.legislature.ca.gov">Title 13 (Of Crimes Against Property)</a> of the <a href="https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=PEN" target="_blank" rel="noopener" title="The Penal Code on leginfo.legislature.ca.gov">California Penal Code</a><span id="crimecount"></span></p>',
    "about": """
          <p>California criminal law in its official text, annotated. Each section is color-coded to show the prohibited act, the mental state the law requires, and the penalty, and references to other sections link to them. <span id="edition"></span> More of the Penal Code may follow.</p>
          <ul>
      <li><b>Select any section</b> to open its own page with the official text beside a breakdown of each crime in it: the act, who can commit it when the law limits that, the mental state required, conditions, exceptions and defenses, the penalty with any conditions that change it, and other consequences. Breakdowns use only the text of that section. The Penal Code has no official section headings, so each section's name here is a short description written for this site.</li>
      <li>In the official text, <span class="act">the prohibited act</span> is highlighted in orange, the <span class="intent">mental state</span> the law requires (knowledge, intent, recklessness or negligence, such as <i>willfully</i> or <i>with intent to</i>) in teal, conditions by their <span class="condw">if</span> or <span class="condw">unless</span> in purple italics, and <span class="pen">penalties</span> in red.</li>
      <li><span class="term" tabindex="0" style="cursor:default">Dotted-underlined words</span> are legal terms. Tap or hover to see what they mean.</li>
      <li>The colored bar on each card shows the <b>maximum</b> prison time stated in that section. Many sentences are lower, enhancements and punishments set in other sections can add to them, and some crimes are punished under other sections.</li>
      <li><b>Felony or misdemeanor:</b> a crime punishable by death, in state prison, or in county jail under Penal Code Section 1170(h) is a <b>felony</b>; every other crime is a <b>misdemeanor</b> (usually up to one year in county jail) or an infraction. A <b>wobbler</b> can be punished either way.</li>
    </ul>
        """,
    "footer": """
    <p>Section text is the official text of the California Penal Code from the <a id="srclink" href="https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=PEN" target="_blank" rel="noopener">California Legislative Information</a> site, current as of the download date shown under About. Section names, summaries, crime types, maximum-penalty labels, crime breakdowns, and highlighting were prepared with AI assistance from that text and may contain errors, so rely on the official text.</p>
    <p>Not included: repealed sections and sections that do not themselves create a crime (definitions, procedure, venue, civil remedies). Many California crimes are defined outside Titles 8 and 13, for example sex crimes (Penal Code Title 9), weapons (Part 6), drug crimes (Health and Safety Code), and driving offenses (Vehicle Code). Sentence enhancements set in other sections, such as Sections 12022 to 12022.9, are not included.</p>
    <p><b>This is general information, not legal advice.</b> If you are facing a legal issue, talk to a lawyer. If you are charged with a crime that can lead to jail and cannot afford a lawyer, you have the right to a court-appointed attorney.</p>
  """,
}
# New York list page: the same regions, for Titles H, I and J of Part 3 of the Penal Law.
NY_URL = "https://www.nysenate.gov/legislation/laws/PEN/"
NY_REGIONS = {
    "nav": '<nav class="jurnav docnav" aria-label="Law"><a href="./" aria-current="page">Crimes</a><a href="../constitution/">U.S. Constitution</a></nav><nav class="jurnav" aria-label="Jurisdiction"><a href="../">Federal</a><a href="../ma/">Massachusetts</a><a href="./" aria-current="page">New York</a><a href="../ca/">California</a></nav>',
    "lede": f'<p class="lede">Every crime in <a href="{NY_URL}P3TH" target="_blank" rel="noopener" title="Title H, Offenses Against the Person Involving Physical Injury, Sexual Conduct, Restraint and Intimidation: official text on nysenate.gov">Title H (Offenses Against the Person)</a>, <a href="{NY_URL}P3TI" target="_blank" rel="noopener" title="Title I, Offenses Involving Damage to and Intrusion Upon Property: official text on nysenate.gov">Title I (Property Damage and Intrusion)</a> and <a href="{NY_URL}P3TJ" target="_blank" rel="noopener" title="Title J, Offenses Involving Theft: official text on nysenate.gov">Title J (Theft)</a> of the <a href="https://www.nysenate.gov/legislation/laws/PEN" target="_blank" rel="noopener" title="The Penal Law on nysenate.gov">New York Penal Law</a><span id="crimecount"></span></p>',
    "about": """
          <p>New York criminal law in its official text, annotated. Each section is color-coded to show the prohibited act, the mental state the law requires, and the penalty, and references to other sections link to them. <span id="edition"></span> More of the Penal Law may follow.</p>
          <ul>
      <li><b>Select any section</b> to open its own page with the official text beside a breakdown of each crime in it: the act, who can commit it when the law limits that, the mental state required, conditions, exceptions and defenses, the penalty with any conditions that change it, and other consequences. Breakdowns use only the text of that section. Section names are the official titles.</li>
      <li>In the official text, <span class="act">the prohibited act</span> is highlighted in orange, the <span class="intent">mental state</span> the law requires (knowledge, intent, recklessness or negligence, such as <i>intentionally</i> or <i>with intent to</i>) in teal, conditions by their <span class="condw">if</span> or <span class="condw">unless</span> in purple italics, and the <span class="pen">class of the offense</span> in red.</li>
      <li><span class="term" tabindex="0" style="cursor:default">Dotted-underlined words</span> are legal terms. Tap or hover to see what they mean.</li>
      <li>The colored bar on each card shows the <b>class</b> of the offense stated in that section (class A to E felony, class A or B misdemeanor, or violation). The sentence for each class is set in Penal Law Articles 70 and 80, which are not part of this set, so no prison term is shown here.</li>
      <li><b>Felony, misdemeanor or violation:</b> a <b>felony</b> can be punished by more than one year in prison; a <b>misdemeanor</b> by up to one year; a <b>violation</b> by no more than fifteen days (general definitions from Penal Law section 10.00).</li>
    </ul>
        """,
    "footer": """
    <p>Section names are the official titles, and section text is the official text of the New York Penal Law from the <a id="srclink" href="https://www.nysenate.gov/legislation/laws/PEN" target="_blank" rel="noopener">New York State Senate Open Legislation API</a>, downloaded on the date shown under About. Summaries, crime types, class labels, crime breakdowns, and highlighting were prepared with AI assistance and may contain errors; the official text is what counts. Each breakdown uses only the text of its own section.</p>
    <p>Not included: sections that do not themselves create a crime (definitions, rules of consent, defenses, procedure). Many New York crimes are defined outside Titles H, I and J, for example forgery and fraud (Title K), drug crimes (Article 220), weapons (Article 265), and driving offenses (Vehicle and Traffic Law). Sentences are set in Penal Law Articles 70 and 80.</p>
    <p><b>This is general information, not legal advice.</b> If you are facing a legal issue, talk to a lawyer. If you are charged with a crime that can lead to jail and cannot afford a lawyer, you have the right to a court-appointed attorney.</p>
  """,
}
# The Constitution of the United States (--jur con): constitution/index.html and constitution/<provision>.html.
CON_SRC = "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm"
CON_REGIONS = {
    "nav": '<nav class="jurnav docnav" aria-label="Law"><a href="../">Crimes</a><a href="./" aria-current="page">U.S. Constitution</a></nav><nav class="jurnav" aria-label="Jurisdiction"><a href="./" aria-current="page">United States</a><a href="../ma/constitution/">Massachusetts</a></nav>',
    "lede": f'<p class="lede">Every provision of the <a href="{CON_SRC}" target="_blank" rel="noopener" title="The Constitution of the United States of America, As Amended (House Document 110-50): official text on GovInfo">Constitution of the United States</a> and its 27 amendments<span id="crimecount"></span></p>',
    "about": """
          <p>The Constitution of the United States in its official text, annotated. Each provision is color-coded to show the rights it guarantees, the powers it grants and the limits it sets, and broken into its parts. <span id="edition"></span></p>
          <ul>
      <li><b>Select any provision</b> to open its own page with the official text beside a breakdown: each right, power, limit or duty in it, who holds it, who is bound, what it requires or forbids, its conditions and exceptions, and any official note that it was changed by a later amendment. Breakdowns use only the provision's own text.</li>
      <li>In the official text, <span class="right">rights</span> are green, <span class="power">grants of power</span> are highlighted in orange, <span class="limit">limits</span> on government are red, and conditions by their <span class="condw">if</span> or <span class="condw">unless</span> are purple italics. The small numbers are the clause numbers of the official print.</li>
      <li><span class="term" tabindex="0" style="cursor:default">Dotted-underlined words</span> are legal terms. Tap or hover to see what they mean.</li>
      <li>The colored bar on each card shows the provision's main kind: a right, a power, a limit, a duty, or structure (offices, terms, elections and procedures).</li>
      <li>The text keeps the original spelling and capitals of 1787 ("chuse", "defence"). Clauses changed by later amendments stay in the text, with the official note saying so.</li>
    </ul>
        """,
    "footer": f"""
    <p>Text of the Constitution and its amendments, clause numbers and notes are from <a id="srclink" href="{CON_SRC}" target="_blank" rel="noopener">The Constitution of the United States of America, As Amended</a> (House Document 110-50, Government Printing Office, 2007) on GovInfo; no amendment has been ratified since. Captions, summaries, topics, highlighting and breakdowns were prepared with AI assistance and may contain errors, and they describe only the text itself, not how courts have interpreted it; the official text is what counts.</p>
    <p><b>This is general information, not legal advice.</b> If you are facing a legal issue, talk to a lawyer.</p>
  """,
}
# The Constitution of the Commonwealth of Massachusetts (--jur macon): ma/constitution/index.html and ma/constitution/<provision>.html.
MACON_SRC = "https://malegislature.gov/Laws/Constitution"
MACON_REGIONS = {
    "nav": '<nav class="jurnav docnav" aria-label="Law"><a href="../">Crimes</a><a href="./" aria-current="page">Constitution</a></nav><nav class="jurnav" aria-label="Jurisdiction"><a href="../../constitution/">United States</a><a href="./" aria-current="page">Massachusetts</a></nav>',
    "lede": f'<p class="lede">Every provision of the <a href="{MACON_SRC}" target="_blank" rel="noopener" title="The Constitution of the Commonwealth of Massachusetts: official text on malegislature.gov">Constitution of the Commonwealth of Massachusetts</a>: the Declaration of Rights, the Frame of Government and the Articles of Amendment<span id="crimecount"></span></p>',
    "about": """
          <p>The Massachusetts Constitution of 1780, the oldest written constitution still in use, in its official text and annotated. Each provision is color-coded to show the rights it guarantees, the powers it grants and the limits it sets, and broken into its parts. <span id="edition"></span></p>
          <ul>
      <li><b>Select any provision</b> to open its own page with the official text beside a breakdown: each right, power, limit or duty in it, who holds it, who is bound, what it requires or forbids, its conditions and exceptions, and any note of the Legislature that it was annulled, superseded or amended. Breakdowns use only the provision's own text.</li>
      <li>In the official text, <span class="right">rights</span> are green, <span class="power">grants of power</span> are highlighted in orange, <span class="limit">limits</span> on government are red, and conditions by their <span class="condw">if</span> or <span class="condw">unless</span> are purple italics.</li>
      <li>Words in [square brackets] are printed that way by the Legislature to show wording that was later superseded; the Legislature's own notes ("Annulled by Amendments, Art. CVI", "See Amendments, Arts. XLVI and XLVIII") appear under the text and link to the articles they name. Provisions marked <b>Annulled</b> or <b>Partly superseded</b> say so on their cards.</li>
      <li><span class="term" tabindex="0" style="cursor:default">Dotted-underlined words</span> are legal terms. Tap or hover to see what they mean.</li>
      <li>The colored bar on each card shows the provision's main kind: a right, a power, a limit, a duty, or structure (offices, terms, elections and procedures).</li>
    </ul>
        """,
    "footer": f"""
    <p>Text of the Constitution and the bracketed notes are from the <a id="srclink" href="{MACON_SRC}" target="_blank" rel="noopener">Massachusetts Legislature</a> (malegislature.gov), downloaded on the date shown under About. Captions, summaries, topics, statuses, highlighting and breakdowns were prepared with AI assistance and may contain errors, and they describe only the text itself, not how courts have interpreted it; the official text is what counts.</p>
    <p><b>This is general information, not legal advice.</b> If you are facing a legal issue, talk to a lawyer.</p>
  """,
}
if STATE:
    NAME, REGIONS = ("Massachusetts", MA_REGIONS) if MA else ("California", CA_REGIONS) if CA else ("Massachusetts Constitution", MACON_REGIONS) if MACON else ("U.S. Constitution", CON_REGIONS) if CON else ("New York", NY_REGIONS)
    page_src = index.replace('<html lang="en">', f'<html lang="en" data-jur="{"ma" if MACON else "us"}" data-doc="con">' if CON else f'<html lang="en" data-jur="{JURSEL}">', 1).replace("<title>Crimes Explained: Federal</title>", f"<title>Crimes Explained: {NAME}</title>", 1).replace("<h1>Crimes Explained: Federal</h1>", f"<h1>Crimes Explained: {NAME}</h1>", 1)
    page_src = page_src.replace('placeholder="Search, e.g. “identity theft”, “firearm”, or “§ 1001”"', 'placeholder="Search, e.g. “religion”, “general court”, or “decl14”"' if MACON else 'placeholder="Search, e.g. “speech”, “jury”, or “amend14-s1”"' if CON else 'placeholder="Search, e.g. “dangerous weapon”, “strangulation”, or “13A”"' if MA else 'placeholder="Search, e.g. “great bodily injury”, “kidnapping”, or “245”"' if CA else 'placeholder="Search, e.g. “strangulation”, “serious physical injury”, or “125.25”"', 1)
    for name, body in REGIONS.items():
        page_src, n = re.subn(rf"<!-- jur:{name} -->.*?<!-- /jur:{name} -->", lambda m: f"<!-- jur:{name} -->{body}<!-- /jur:{name} -->", page_src, flags=re.S)
        assert n == 1, name
    page_src = page_src.replace('href="feedback.html"', 'href="../../feedback.html"' if MACON else 'href="../feedback.html"')
    os.makedirs(os.path.join(HERE, DIR), exist_ok=True)
    open(os.path.join(HERE, DIR, "index.html"), "w", encoding="utf-8").write(page_src)
OUT = os.path.join(HERE, DIR) if STATE else os.path.join(HERE, "18")
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
harness = os.path.join(OUT if STATE else HERE, "_prerender.html")
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
                          "--dump-dom", SERVER + (DIR + "/" if STATE else "") + "_prerender.html"], capture_output=True, text=True).stdout
finally:
    os.remove(harness)
m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
if not m or not m.group(1).strip():
    sys.exit("Rendering failed: is the local server running at " + SERVER + "?")
pages = json.loads(html.unescape(m.group(1)))

# 4. Write the pages.
UP = "../../" if MA or MACON else "../"                 # from a section page to the site root
LIST = "index.html" if (CA or NY or CON) else "../index.html"  # from a section page to its list page
# Related crimes (related.py): titles, labels and addresses of every section in every jurisdiction.
RELATED = json.load(open(os.path.join(HERE, "related.json"))) if os.path.exists(os.path.join(HERE, "related.json")) else {}
JUR_NAMES = {"us": "Federal", "ma": "Massachusetts", "ca": "California", "ny": "New York"}
INFO = {}
for _jur, _f in (("us", "crimes.json"), ("ma", "ma/crimes.json"), ("ca", "ca/crimes.json"), ("ny", "ny/crimes.json")):
    if os.path.exists(os.path.join(HERE, _f)):
        for _c in json.load(open(os.path.join(HERE, _f), encoding="utf-8"))["crimes"]:
            INFO[(_jur, _c["section"])] = (_c["title"], _c.get("cite") or "§ " + _c["section"], ("18/" if _jur == "us" else _jur + "/") + _c["section"] + ".html")

def related_html(key):
    r = RELATED.get(key)
    if not r or not (r["same"] or r["other"]): return ""
    def item(j, s, show_jur):
        t, label, path = INFO[(j, s)]
        jur = f'<span class="rel-jur">{JUR_NAMES[j]}</span> ' if show_jur else ""
        return f'<li>{jur}<a href="{UP}{path}"><span class="rel-sec">{html.escape(label)}</span> {html.escape(t)}</a></li>'
    cols = ""
    if r["same"]: cols += f'<div><h3>In {JUR_NAMES[JURSEL]}</h3><ul>{"".join(item(j, s, False) for j, s in r["same"])}</ul></div>'
    if r["other"]: cols += f'<div><h3>In other jurisdictions</h3><ul>{"".join(item(j, s, True) for j, s in r["other"])}</ul></div>'
    return f'<section class="related" aria-label="Related crimes"><h2>Related crimes</h2><div class="rel-cols">{cols}</div></section>'

def page(i, p):
    prev_p, next_p = (pages[i - 1] if i else None), (pages[i + 1] if i + 1 < len(pages) else None)
    href = lambda q: f'../{q["section"]}.html' if MA else f'{q["section"]}.html'
    short = lambda q: q["label"].split(", ")[-1] if MA else q["label"] if CON else "§ " + q["section"]
    nav = lambda q, label: f'<a href="{href(q)}" rel="{label}">{"‹ " + short(q) if label == "prev" else short(q) + " ›"}</a>' if q else ""
    law = "Mass. Const. " + p["label"] if MACON else "U.S. Const. " + p["label"] if CON else "M.G.L. " + p["label"] if MA else f'Cal. Penal Code § {p["section"]}' if CA else f'N.Y. Penal Law § {p["section"]}' if NY else f'18 U.S.C. § {p["section"]}'
    desc = p["plain"] or (f'{law}, {p["title"]}: official text, color-coded, with each right, power and limit broken out.' if CON else f'{law}, {p["title"]}: official text, color-coded, with each crime broken into its elements.')
    desc = (desc[:157] + "…") if len(desc) > 160 else desc
    title = f'{law}: {p["title"]} · Crimes Explained'
    back = "Crimes Explained: Massachusetts Constitution, all" if MACON else "Crimes Explained: U.S. Constitution, all" if CON else "Crimes Explained: Massachusetts, all" if MA else "Crimes Explained: California, all" if CA else "Crimes Explained: New York, all" if NY else "Crimes Explained: Federal, all"
    source = (f'Official text of the Constitution of the Commonwealth of Massachusetts from the Massachusetts Legislature (<a href="{html.escape(p["url"])}">malegislature.gov</a>), downloaded {EDITION_DATE}. Captions are descriptions written for this site, and the breakdowns describe only the text, not court interpretations.' if MACON else
              "Official text from The Constitution of the United States of America, As Amended (House Document 110-50), via GovInfo. Captions are descriptions written for this site; the Constitution has no section headings, and the breakdowns describe only the text, not court interpretations." if CON else
              f'Official text of the Massachusetts General Laws from the Massachusetts Legislature (<a href="{html.escape(p["url"])}">malegislature.gov</a>), downloaded {EDITION_DATE}.'
              if MA else f'Official text of the California Penal Code from the California Legislative Information site (<a href="{html.escape(p["url"])}">leginfo.legislature.ca.gov</a>), downloaded {EDITION_DATE}. Section names are descriptions written for this site; the Penal Code has no official section headings.'
              if CA else f'Official text of the New York Penal Law from the New York State Senate Open Legislation API (<a href="{html.escape(p["url"])}">nysenate.gov</a>), downloaded {EDITION_DATE}. Section names are the official titles.' if NY else "Official text from the United States Code, 2024 edition (current through Jan. 6, 2025), via GovInfo.")
    related = related_html(f'{JURSEL}:{p["section"]}')
    page_url = f'{BASE_URL}{DIR + "/" if STATE else "18/"}{p["section"]}.html'
    report = "https://github.com/moqri/crimes-explained/issues/new?" + urllib.parse.urlencode(
        {"title": f"Error in {law}", "body": f"Section: {law}, {p['title']}\nPage: {page_url}\n\nWhat is wrong:\n\nWhat the official text says:\n"}, quote_via=urllib.parse.quote)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{page_url}">
  <link rel="stylesheet" href="{UP}assets/site.css">
</head>
<body>
<main class="page">
  <nav class="page-nav" aria-label="Sections">
    <a href="{LIST}">← {back} {len(pages)} {"provisions" if CON else "sections"}</a>
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
  {related}
  <nav class="page-nav page-foot-nav" aria-label="Sections">
    <a href="{LIST}">← All {"provisions" if CON else "sections"}</a>
    <span class="pn">{nav(prev_p, "prev")}{nav(next_p, "next")}</span>
  </nav>
  <footer><p>{source} Highlighting, {"breakdowns" if CON else "crime breakdowns"}, and labels were prepared with AI assistance and may contain errors; rely on the official text. <b>This is general information, not legal advice.</b></p>
  <p>Found a mistake? <a href="{html.escape(report)}" target="_blank" rel="noopener">Report an error on this section</a> · <a href="{UP}feedback.html">Other feedback</a></p></footer>
</main>
<div id="pop" role="tooltip"></div>
<script src="{UP}assets/page.js"></script>
</body>
</html>
"""

EDITION_DATE = re.search(r"downloaded ([\d-]+)", json.load(open(os.path.join(OUT, "crimes.json")))["edition"]).group(1) if STATE and JURSEL != "con" else ""
for i, p in enumerate(pages):
    path = os.path.join(OUT, f'{p["section"]}.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(page(i, p))

# 5. Sitemap (every section page of both jurisdictions) and robots.txt for search engines.
rel = sorted(os.path.relpath(f, HERE) for f in glob.glob(os.path.join(HERE, "18", "*.html")) + [f for f in glob.glob(os.path.join(HERE, "ma", "*", "*.html")) if os.sep + "constitution" + os.sep not in f]
             + [f for f in glob.glob(os.path.join(HERE, "ca", "*.html")) if not f.endswith("index.html")]
             + [f for f in glob.glob(os.path.join(HERE, "ny", "*.html")) if not f.endswith("index.html")]
             + [f for f in glob.glob(os.path.join(HERE, "constitution", "*.html")) + glob.glob(os.path.join(HERE, "ma", "constitution", "*.html")) if not f.endswith("index.html")])
urls = [BASE_URL, BASE_URL + "feedback.html", BASE_URL + "ma/"] + ([BASE_URL + "ca/"] if os.path.exists(os.path.join(HERE, "ca", "index.html")) else []) + ([BASE_URL + "ny/"] if os.path.exists(os.path.join(HERE, "ny", "index.html")) else []) + ([BASE_URL + "constitution/"] if os.path.exists(os.path.join(HERE, "constitution", "index.html")) else []) + ([BASE_URL + "ma/constitution/"] if os.path.exists(os.path.join(HERE, "ma", "constitution", "index.html")) else []) + [BASE_URL + r for r in rel]
open(os.path.join(HERE, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                                   + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
print(f"wrote {len(pages)} section pages{f' and {DIR}/index.html' if STATE else ''}, assets/site.css, assets/page.js, sitemap.xml ({len(urls)} URLs), robots.txt")
