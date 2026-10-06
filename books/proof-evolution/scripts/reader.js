(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('book-data').textContent);
  document.documentElement.classList.add('enhanced');
  const storageKey = `${data.id}:reading-progress`;
  const chapters = Array.from(document.querySelectorAll('.chapter'));
  const navLinks = Array.from(document.querySelectorAll('.nav-link'));
  const searchInput = document.getElementById('book-search');
  const searchStatus = document.getElementById('search-status');
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('book-navigation');
  const progress = document.getElementById('reading-progress');
  const progressLabel = document.getElementById('progress-label');
  const previousLink = document.getElementById('previous-chapter');
  const nextLink = document.getElementById('next-chapter');
  const mobile = window.matchMedia('(max-width: 900px)');
  let currentIndex = 0;
  let scrollPending = false;
  let saveTimer;

  function readProgress() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      if (saved && data.documents.some(item => item.id === saved.chapter) && Number.isFinite(saved.ratio)) return saved;
    } catch { /* Reading remains usable when storage is unavailable. */ }
    return null;
  }

  function chapterRatio() {
    const range = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    return range === 0 ? 1 : Math.max(0, Math.min(1, window.scrollY / range));
  }

  function saveProgress() {
    if (document.body.classList.contains('nav-open')) return;
    try { localStorage.setItem(storageKey, JSON.stringify({ chapter: data.documents[currentIndex].id, ratio: chapterRatio() })); }
    catch { /* Private browsing or file URL restrictions must not block reading. */ }
  }

  function updateProgress() {
    const percent = Math.round(chapterRatio() * 100);
    progress.value = percent;
    progressLabel.textContent = `本篇 ${percent}%`;
    scrollPending = false;
  }

  function setMenu(open) {
    document.body.classList.toggle('nav-open', open && mobile.matches);
    menuToggle.setAttribute('aria-expanded', String(open && mobile.matches));
    sidebar.inert = mobile.matches && !open;
  }

  function setPager(link, index, label) {
    const target = data.documents[index];
    link.hidden = !target;
    if (target) {
      link.href = `#${target.id}`;
      link.replaceChildren();
      const direction = document.createElement('span');
      direction.className = 'direction';
      direction.textContent = label;
      link.append(direction, document.createTextNode(target.title));
    }
  }

  function currentFragment() {
    try { return decodeURIComponent(location.hash.slice(1)); }
    catch { return ''; }
  }

  function activate(fragment, { restoreRatio = null, focus = false } = {}) {
    const documentId = fragment.split('--')[0];
    const index = data.documents.findIndex(item => item.id === documentId);
    currentIndex = index < 0 ? 0 : index;
    chapters.forEach((chapter, i) => { chapter.hidden = i !== currentIndex; });
    navLinks.forEach(link => {
      if (link.dataset.document === data.documents[currentIndex].id) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    setPager(previousLink, currentIndex - 1, '← 上一篇');
    setPager(nextLink, currentIndex + 1, '下一篇 →');
    document.title = `${data.documents[currentIndex].title}｜${data.title}`;
    setMenu(false);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (restoreRatio !== null) {
        const range = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        window.scrollTo(0, range * Math.max(0, Math.min(1, restoreRatio)));
      } else if (fragment.includes('--')) {
        const target = document.getElementById(fragment);
        if (target) target.scrollIntoView();
        else window.scrollTo(0, 0);
      } else window.scrollTo(0, 0);
      if (focus) {
        const target = fragment.includes('--') ? document.getElementById(fragment) : chapters[currentIndex].querySelector('h1');
        if (target) {
          if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
          target.focus({ preventScroll: true });
        }
      }
      updateProgress();
      saveProgress();
    }));
  }

  function search() {
    const query = searchInput.value.normalize('NFKC').toLocaleLowerCase('zh-TW').trim();
    let count = 0;
    navLinks.forEach((link, index) => {
      const entry = data.documents[index];
      const content = `${entry.title} ${entry.text}`.normalize('NFKC').toLocaleLowerCase('zh-TW');
      const position = content.indexOf(query);
      const matches = !query || position >= 0;
      link.parentElement.hidden = !matches;
      link.querySelector('.snippet')?.remove();
      if (matches) count++;
      if (query && matches) {
        const snippet = document.createElement('span');
        snippet.className = 'snippet';
        const start = Math.max(0, position - 22);
        snippet.textContent = `${start ? '…' : ''}${content.slice(start, position + query.length + 46)}…`;
        link.append(snippet);
      }
    });
    document.querySelectorAll('.nav-group').forEach(group => { group.hidden = !Array.from(group.querySelectorAll('li')).some(item => !item.hidden); });
    searchStatus.textContent = query ? `找到 ${count} 篇包含「${searchInput.value.trim()}」的文章` : '';
  }

  searchInput.addEventListener('input', search);
  menuToggle.addEventListener('click', () => {
    const open = menuToggle.getAttribute('aria-expanded') !== 'true';
    setMenu(open);
    if (open) searchInput.focus();
  });
  mobile.addEventListener('change', () => setMenu(false));
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const fragment = decodeURIComponent(link.getAttribute('href').slice(1));
    if (fragment === currentFragment() && data.documents.some(item => item.id === fragment.split('--')[0])) {
      event.preventDefault();
      activate(fragment, { focus: true });
    }
  });
  window.addEventListener('hashchange', () => {
    const fragment = currentFragment();
    if (data.documents.some(item => item.id === fragment.split('--')[0])) activate(fragment, { focus: true });
    else document.getElementById(fragment)?.focus({ preventScroll: true });
  });
  window.addEventListener('scroll', () => {
    if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateProgress); }
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveProgress, 180);
  }, { passive: true });
  window.addEventListener('resize', updateProgress);
  window.addEventListener('pagehide', saveProgress);
  document.addEventListener('keydown', event => {
    const editing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (event.key === '/' && !editing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      setMenu(true);
      searchInput.focus();
    } else if (event.key === 'Escape') {
      if (document.body.classList.contains('nav-open')) { setMenu(false); menuToggle.focus(); }
      else if (document.activeElement === searchInput && searchInput.value) { searchInput.value = ''; search(); }
    }
  });
  document.getElementById('print-book').addEventListener('click', () => window.print());
  const saved = readProgress();
  const fragment = currentFragment();
  activate(fragment || saved?.chapter || data.documents[0].id, { restoreRatio: saved && (!fragment || fragment === saved.chapter) ? saved.ratio : null });
})();
