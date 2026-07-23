/* SpeedSlope.net — portal interactions: lazy iframe player, fullscreen,
   theater mode, favorites, local rating, client search, sorting. */
(function () {
  'use strict';

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- mobile nav ---------- */
  var toggle = $('#menuToggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      $('#mobileNav').classList.toggle('open');
    });
  }

  /* ---------- search submit (header + mobile + search page) ---------- */
  $$('form[data-search]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = $('input', f).value.trim();
      var base = f.getAttribute('data-search') || '/';
      if (q) location.href = base + 'search/?q=' + encodeURIComponent(q);
    });
  });

  /* ---------- favorites (localStorage) ---------- */
  var FAV_KEY = 'po_favorites';
  function getFavs() { try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; } catch (e) { return []; } }
  function setFavs(v) { localStorage.setItem(FAV_KEY, JSON.stringify(v)); }

  var favBtn = $('#favBtn');
  if (favBtn) {
    var slug = favBtn.getAttribute('data-slug');
    var render = function () {
      var on = getFavs().indexOf(slug) !== -1;
      favBtn.classList.toggle('active', on);
      $('span', favBtn).textContent = on ? 'Saved' : 'Save';
    };
    favBtn.addEventListener('click', function () {
      var f = getFavs(), i = f.indexOf(slug);
      if (i === -1) f.push(slug); else f.splice(i, 1);
      setFavs(f); render();
    });
    render();
  }

  /* ---------- rating widget ---------- */
  var rateBox = $('#rateBox');
  if (rateBox) {
    var rSlug = rateBox.getAttribute('data-slug');
    var base = parseFloat(rateBox.getAttribute('data-rating'));
    var count = parseInt(rateBox.getAttribute('data-count'), 10);
    var key = 'po_rate_' + rSlug;
    var mine = parseInt(localStorage.getItem(key) || '0', 10);
    var stars = $$('.rate-stars button', rateBox);

    function paint(val) {
      stars.forEach(function (b, i) { b.classList.toggle('on', i < Math.round(val)); });
    }
    function showNum() {
      var avg = mine ? (base * count + mine) / (count + 1) : base;
      $('#rateNum').textContent = avg.toFixed(1);
      $('#rateCount').textContent = (count + (mine ? 1 : 0)).toLocaleString('en-US') + ' votes';
      paint(mine || avg);
    }
    stars.forEach(function (b, i) {
      b.addEventListener('click', function () {
        mine = i + 1;
        localStorage.setItem(key, String(mine));
        showNum();
      });
    });
    showNum();
  }

  /* ---------- iframe player ---------- */
  var playBtn = $('#playNow');
  if (playBtn) {
    var stage = $('#stage');
    var cover = $('#stageCover');
    var loading = $('#stageLoading');
    var errorBox = $('#stageError');
    var src = stage.getAttribute('data-src');
    var title = stage.getAttribute('data-title');
    var timer = null;

    playBtn.addEventListener('click', function () {
      cover.style.display = 'none';
      loading.classList.add('show');
      var ifr = document.createElement('iframe');
      ifr.setAttribute('allow', 'autoplay; fullscreen; gamepad; keyboard-map; xr-spatial-tracking; cross-origin-isolated');
      ifr.setAttribute('allowfullscreen', '');
      ifr.setAttribute('title', title);
      ifr.src = src;
      var done = false;
      ifr.addEventListener('load', function () {
        done = true;
        clearTimeout(timer);
        loading.classList.remove('show');
      });
      // if the game host blocks embedding or is unreachable, offer a way out
      timer = setTimeout(function () {
        if (!done) {
          loading.classList.remove('show');
          errorBox.classList.add('show');
        }
      }, 20000);
      stage.appendChild(ifr);
    });

    $('#openExternal').addEventListener('click', function () {
      window.open(src, '_blank', 'noopener');
    });
    $('#retryLoad').addEventListener('click', function () {
      errorBox.classList.remove('show');
      cover.style.display = '';
    });
  }

  /* ---------- fullscreen ---------- */
  var fsBtn = $('#fsBtn');
  if (fsBtn) {
    fsBtn.addEventListener('click', function () {
      var st = $('#stage');
      if (document.fullscreenElement) document.exitFullscreen();
      else if (st.requestFullscreen) st.requestFullscreen();
    });
  }

  /* ---------- theater mode ---------- */
  var thBtn = $('#theaterBtn');
  if (thBtn) {
    thBtn.addEventListener('click', function () {
      document.body.classList.toggle('theater');
      thBtn.classList.toggle('active');
    });
  }

  /* ---------- search page ---------- */
  var resultsBox = $('#searchResults');
  if (resultsBox) {
    var q = new URLSearchParams(location.search).get('q') || '';
    var input = $('#searchInput');
    if (input) input.value = q;
    var dataUrl = resultsBox.getAttribute('data-json');
    var basePath = dataUrl.replace(/games\.json$/, '');
    fetch(dataUrl).then(function (r) { return r.json(); }).then(function (games) {
      games.forEach(function (g) { g.url = basePath + g.url; g.thumb = basePath + g.thumb; });
      var ql = q.toLowerCase();
      var hits = !ql ? [] : games.filter(function (g) {
        return (g.title + ' ' + g.tags.join(' ') + ' ' + g.categories.join(' ')).toLowerCase().indexOf(ql) !== -1;
      });
      $('#searchTitle').textContent = ql ? 'Results for “' + q + '”' : 'Search games';
      $('#searchCount').textContent = ql ? hits.length + (hits.length === 1 ? ' game' : ' games') + ' found' : '';
      if (!ql || !hits.length) {
        $('#searchEmpty').style.display = 'block';
        var pop = games.slice().sort(function (a, b) { return b.plays - a.plays; }).slice(0, 12);
        $('#searchPopular').innerHTML = pop.map(cardHTML).join('');
      } else {
        resultsBox.innerHTML = hits.map(cardHTML).join('');
        $('#searchPopularWrap').style.display = 'none';
      }
    });
  }

  function cardHTML(g) {
    var badge = g.isHot ? '<span class="badge">Hot</span>' : (g.isNew ? '<span class="badge new">New</span>' : '');
    return '<a class="game-card" href="' + g.url + '">' +
      '<div class="thumb">' + badge +
      '<img loading="lazy" src="' + g.thumb + '" alt="' + g.title + '">' +
      '<div class="play-hint"><span><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span></div>' +
      '</div><div class="meta"><div class="title">' + g.title + '</div>' +
      '<div class="sub"><span class="star"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z"/></svg>' +
      g.rating.toFixed(1) + '</span><span>' + fmtPlays(g.plays) + ' plays</span></div></div></a>';
  }

  function fmtPlays(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '') + 'K';
    return String(n);
  }

  /* ---------- sortable game grids (category / hot / new pages) ---------- */
  var sortBar = $('#sortBar');
  if (sortBar) {
    var grid = $('#sortGrid');
    var cards = $$('.game-card', grid);
    var moreWrap = $('#loadMoreWrap');
    var PAGE = 18, shown = PAGE;

    function applySort(mode) {
      cards.sort(function (a, b) {
        if (mode === 'rating') return parseFloat(b.dataset.rating) - parseFloat(a.dataset.rating);
        if (mode === 'new') return (b.dataset.added || '').localeCompare(a.dataset.added || '');
        return parseInt(b.dataset.plays, 10) - parseInt(a.dataset.plays, 10);
      });
      cards.forEach(function (c) { grid.appendChild(c); });
      shown = PAGE;
      paintVisible();
    }
    function paintVisible() {
      cards.forEach(function (c, i) { c.style.display = i < shown ? '' : 'none'; });
      if (moreWrap) moreWrap.style.display = shown >= cards.length ? 'none' : '';
    }
    $$('.sort-btn', sortBar).forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.sort-btn', sortBar).forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        applySort(b.dataset.sort);
      });
    });
    if (moreWrap) $('#loadMore').addEventListener('click', function () {
      shown += PAGE; paintVisible();
    });
    paintVisible();
    $('#gridCount') && ($('#gridCount').textContent = cards.length + (cards.length === 1 ? ' game' : ' games'));
  }
})();
