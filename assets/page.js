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
})();
