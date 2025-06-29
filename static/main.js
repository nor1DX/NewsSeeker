document.addEventListener('DOMContentLoaded', () => {
  const loadBtn = document.getElementById('loadMore');
  const list = document.getElementById('newsList');
  const sourceFilter = document.getElementById('sourceFilter');
  const themeToggle = document.getElementById('themeToggle');
  let offset = parseInt(loadBtn?.dataset.offset || '0', 10);
  const limit = 5;

  // фильтр по источнику
  sourceFilter?.addEventListener('change', () => {
    const s = sourceFilter.value;
    const params = new URLSearchParams();
    if (s) params.set('source', s);
    window.location = '/?' + params.toString();
  });

  // переключатель темы
  themeToggle?.addEventListener('click', () => {
    const html = document.documentElement;
    html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
  });

  // загрузка ещё новостей
  loadBtn?.addEventListener('click', async () => {
    const params = new URLSearchParams({offset, limit});
    if (CURRENT_SOURCE) params.set('source', CURRENT_SOURCE);
    const res = await fetch('/api/posts?' + params.toString());
    const posts = await res.json();
    posts.forEach(p => {
      const article = document.createElement('article');
      article.innerHTML = `
        <header>
          <h2>${p.title}</h2>
          <p class="source-label">${p.source.toUpperCase()}</p>
        </header>
        <p>${p.summary}</p>
        <footer><a href="${p.link}" target="_blank">Читать оригинал</a></footer>
      `;
      list.appendChild(article);
    });
    offset += posts.length;
    if (posts.length < limit) loadBtn.disabled = true;
  });
});
