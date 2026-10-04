// Section pages: show a legal term's definition on hover/tap, and copy the page link.
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
