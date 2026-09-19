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
    function tryBrowserBookmark() {
      if (window.sidebar && window.sidebar.addPanel) {
        window.sidebar.addPanel(document.title, location.href, '');
        return true;
      }
      if (window.external && typeof window.external.AddFavorite === 'function') {
        window.external.AddFavorite(location.href, document.title);
        return true;
      }
      return false;
    }
    favBtn.addEventListener('click', function () {
      var f = getFavs();
      if (f.indexOf(slug) === -1) {
        f.push(slug);
        setFavs(f);
      }
      render();
      if (!tryBrowserBookmark()) {
        alert((/Mac|iPhone|iPad|iPod/.test(navigator.platform) ? 'Press Command+D' : 'Press Ctrl+D') + ' to bookmark this game.');
      }
    });
    render();
  }

  /* ---------- align side game rails ---------- */
  var playLayout = $('.play-layout');
  if (playLayout) {
    var sideResizeTimer = null;
    function syncSideRails() {
      var stageWrap = $('.stage-wrap', playLayout);
      if (!stageWrap) return;
      var h = stageWrap.offsetHeight;
      $$('.play-side', playLayout).forEach(function (side) { side.style.setProperty('--play-side-max', h + 'px'); });
    }
    window.addEventListener('load', syncSideRails);
    window.addEventListener('resize', function () {
      clearTimeout(sideResizeTimer);
      sideResizeTimer = setTimeout(syncSideRails, 120);
    });
    syncSideRails();
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
  var stage = $('#stage');
  if (stage) {
    var cover = $('#stageCover');
    var playBtn = $('#playNow');
    var loading = $('#stageLoading');
    var errorBox = $('#stageError');
    var src = stage.getAttribute('data-src');
    var title = stage.getAttribute('data-title');
    var timer = null;
    var started = false;

    function watch(ifr) {
      var done = false;
      function finish() {
        if (done) return;
        done = true;
        clearTimeout(timer);
        loading.classList.remove('show');
      }
      ifr.addEventListener('load', finish);
      // window load also waits for iframes — covers the case where the
      // iframe finished before this script attached its listener
      window.addEventListener('load', finish);
      // if the game host blocks embedding or is unreachable, offer a way out
      timer = setTimeout(function () {
        if (!done) {
          loading.classList.remove('show');
          errorBox.classList.add('show');
        }
      }, 20000);
    }

    function loadGame() {
      if (started) return;
      started = true;
      if (cover) cover.style.display = 'none';
      loading.classList.add('show');
      var ifr = document.createElement('iframe');
      ifr.setAttribute('allow', 'autoplay; fullscreen; gamepad; keyboard-map; xr-spatial-tracking; cross-origin-isolated');
      ifr.setAttribute('allowfullscreen', '');
      ifr.setAttribute('title', title);
      ifr.src = src;
      watch(ifr);
      stage.appendChild(ifr);
    }

    var existing = $('iframe', stage);
    if (existing) {
      // autoplay pages render the iframe directly into the HTML
      started = true;
      watch(existing);
    } else if (stage.getAttribute('data-autoplay') === '1') {
      loadGame();
    }
    if (playBtn) playBtn.addEventListener('click', loadGame);

    $('#openExternal').addEventListener('click', function () {
      window.open(src, '_blank', 'noopener');
    });
    $('#retryLoad').addEventListener('click', function () {
      errorBox.classList.remove('show');
      // drop the failed iframe and allow a fresh attempt
      var old = $('iframe', stage);
      if (old) old.parentNode.removeChild(old);
      started = false;
      if (cover) cover.style.display = '';   // click-to-play pages: back to the cover
      else loadGame();                       // autoplay pages: retry immediately
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

  /* ---------- share and broken-game reports ---------- */
  var shareBtn = $('#shareBtn');
  if (shareBtn) {
    var shareLabel = $('span', shareBtn);
    shareBtn.addEventListener('click', function () {
      var payload = { title: document.title, url: location.href };
      if (navigator.share) {
        navigator.share(payload).catch(function () {});
        return;
      }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(location.href).then(function () {
          shareLabel.textContent = 'Copied';
          setTimeout(function () { shareLabel.textContent = 'Share'; }, 1800);
        }).catch(function () {
          prompt('Copy this game link', location.href);
        });
        return;
      }
      prompt('Copy this game link', location.href);
    });
  }

  var reportModal = $('#reportModal');
  if (reportModal) {
    var reportBtn = $('#reportBtn');
    var reportForm = $('#reportForm');
    var reportStatus = $('#reportStatus');
    reportBtn.addEventListener('click', function () {
      reportStatus.textContent = '';
      reportModal.showModal();
    });
    $('[data-close-report]', reportModal).addEventListener('click', function () {
      reportModal.close();
    });
    reportForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var submit = $('button[type="submit"]', reportForm);
      var fd = new FormData(reportForm);
      reportStatus.textContent = 'Sending...';
      submit.disabled = true;
      fetch(reportForm.getAttribute('data-report-api'), {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          slug: reportForm.getAttribute('data-slug'),
          issue: fd.get('issue'),
          details: fd.get('details'),
          website: fd.get('website')
        })
      }).then(function (r) {
        return r.json().then(function (data) { return { ok: r.ok, data: data }; });
      }).then(function (res) {
        if (!res.ok || !res.data.ok) throw new Error(res.data.error || 'Could not send report.');
        reportForm.reset();
        reportStatus.textContent = res.data.message || 'Thanks. We will check this game.';
        setTimeout(function () { reportModal.close(); }, 1200);
      }).catch(function (err) {
        reportStatus.textContent = err.message;
      }).finally(function () {
        submit.disabled = false;
      });
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

  /* ---------- comments ---------- */
  var commentsBox = $('[data-comments]');
  if (commentsBox) {
    var commentsSlug = commentsBox.getAttribute('data-slug');
    var commentsList = $('#commentsList');
    var commentsCount = $('#commentsCount');
    var commentForm = $('#commentForm');
    var commentStatus = $('#commentStatus');

    function commentDate(value) {
      var d = new Date(value);
      return isNaN(d.getTime()) ? '' : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    }
    function renderComments(items) {
      commentsList.innerHTML = '';
      commentsCount.textContent = items.length + (items.length === 1 ? ' comment' : ' comments');
      if (!items.length) {
        var empty = document.createElement('p');
        empty.className = 'comment-note';
        empty.textContent = 'No comments yet. Be the first to leave one.';
        commentsList.appendChild(empty);
        return;
      }
      items.forEach(function (item) {
        var wrap = document.createElement('article');
        wrap.className = 'comment-item';
        var meta = document.createElement('div');
        meta.className = 'comment-meta';
        var name = document.createElement('span');
        name.className = 'comment-name';
        name.textContent = item.displayName || 'Anonymous';
        var date = document.createElement('span');
        date.className = 'comment-date';
        date.textContent = commentDate(item.createdAt);
        var body = document.createElement('div');
        body.className = 'comment-body';
        body.textContent = item.body || '';
        meta.appendChild(name);
        if (date.textContent) meta.appendChild(date);
        wrap.appendChild(meta);
        wrap.appendChild(body);
        commentsList.appendChild(wrap);
      });
    }
    function loadComments() {
      fetch('/api/comments?slug=' + encodeURIComponent(commentsSlug))
        .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok || !res.data.ok) throw new Error(res.data.error || 'Comments unavailable');
          renderComments(res.data.comments || []);
        })
        .catch(function () {
          commentsList.innerHTML = '<p class="comment-note">Comments are not available right now.</p>';
        });
    }
    loadComments();

    if (commentForm) {
      commentForm.addEventListener('submit', function (e) {
        e.preventDefault();
        commentStatus.textContent = 'Posting...';
        var fd = new FormData(commentForm);
        fetch('/api/comments', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            slug: commentsSlug,
            displayName: fd.get('displayName'),
            email: fd.get('email'),
            body: fd.get('body'),
            website: fd.get('website'),
            turnstileToken: fd.get('cf-turnstile-response')
          })
        }).then(function (r) {
          return r.json().then(function (data) { return { ok: r.ok, data: data }; });
        }).then(function (res) {
          if (!res.ok || !res.data.ok) throw new Error(res.data.error || 'Could not post comment.');
          commentForm.reset();
          if (window.turnstile) window.turnstile.reset();
          commentStatus.textContent = res.data.message || 'Thanks. Your comment is waiting for review.';
          loadComments();
        }).catch(function (err) {
          commentStatus.textContent = err.message;
          if (window.turnstile) window.turnstile.reset();
        });
      });
    }
  }

  /* ---------- admin comments ---------- */
  var adminComments = $('#adminComments');
  if (adminComments) {
    var adminList = $('#adminCommentList');
    var adminCount = $('#adminCommentCount');
    var adminStatus = 'pending';
    var adminToken = sessionStorage.getItem('ss_admin_token') || '';

    function promptAdminToken() {
      adminToken = prompt('Admin token') || '';
      if (adminToken) sessionStorage.setItem('ss_admin_token', adminToken);
      return adminToken;
    }
    function adminHeaders(extra) {
      var headers = extra || {};
      if (adminToken) headers.authorization = 'Bearer ' + adminToken;
      return headers;
    }
    function adminFetch(url, options) {
      options = options || {};
      options.headers = adminHeaders(options.headers);
      return fetch(url, options).then(function (r) {
        if (r.status !== 403 || adminToken) return r;
        sessionStorage.removeItem('ss_admin_token');
        if (!promptAdminToken()) return r;
        options.headers = adminHeaders(options.headers);
        return fetch(url, options);
      });
    }

    function button(label, status, id) {
      var b = document.createElement('button');
      b.className = status === 'approved' ? 'btn btn-primary' : 'btn btn-ghost';
      b.type = 'button';
      b.textContent = label;
      b.addEventListener('click', function () {
        adminFetch('/api/admin/comments/' + id, {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ status: status })
        }).then(function (r) {
          if (!r.ok) throw new Error('Moderation failed');
          loadAdminComments();
        }).catch(function (err) { alert(err.message); });
      });
      return b;
    }
    function renderAdmin(items) {
      adminList.innerHTML = '';
      adminCount.textContent = items.length + (items.length === 1 ? ' comment' : ' comments');
      if (!items.length) {
        adminList.innerHTML = '<p class="comment-note">No comments in this queue.</p>';
        return;
      }
      items.forEach(function (item) {
        var wrap = document.createElement('article');
        wrap.className = 'comment-item';
        var meta = document.createElement('div');
        meta.className = 'comment-meta';
        var name = document.createElement('span');
        name.className = 'comment-name';
        name.textContent = item.displayName || 'Anonymous';
        var game = document.createElement('span');
        game.className = 'comment-date';
        game.textContent = item.gameSlug || '';
        var email = document.createElement('span');
        email.className = 'admin-comment-email';
        email.textContent = item.email || 'no email';
        var body = document.createElement('div');
        body.className = 'comment-body';
        body.textContent = item.body || '';
        var actions = document.createElement('div');
        actions.className = 'admin-comment-actions';
        actions.appendChild(button('Approve', 'approved', item.id));
        actions.appendChild(button('Reject', 'rejected', item.id));
        actions.appendChild(button('Hide', 'hidden', item.id));
        meta.appendChild(name);
        meta.appendChild(game);
        meta.appendChild(email);
        wrap.appendChild(meta);
        wrap.appendChild(body);
        wrap.appendChild(actions);
        adminList.appendChild(wrap);
      });
    }
    function loadAdminComments() {
      adminList.innerHTML = '<p class="comment-note">Loading comments...</p>';
      adminFetch('/api/admin/comments?status=' + encodeURIComponent(adminStatus))
        .then(function (r) { if (r.status === 403) sessionStorage.removeItem('ss_admin_token'); return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
        .then(function (res) {
          if (!res.ok || !res.data.ok) throw new Error(res.data.error || 'Could not load comments.');
          renderAdmin(res.data.comments || []);
        })
        .catch(function (err) { adminList.innerHTML = '<p class="comment-note">' + err.message + '</p>'; });
    }
    $$('[data-status]', adminComments).forEach(function (b) {
      b.addEventListener('click', function () {
        $$('[data-status]', adminComments).forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        adminStatus = b.getAttribute('data-status');
        loadAdminComments();
      });
    });
    loadAdminComments();
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
