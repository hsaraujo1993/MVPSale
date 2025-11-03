// Basic HTTP helper with CSRF + optional JWT and error handling
(function(){
  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split('; ') : [];
    for (const c of cookies) {
      const [k, v] = c.split('=');
      if (k === name) return decodeURIComponent(v);
    }
    return null;
  }

  async function fetchJson(url, options={}){
    const headers = new Headers(options.headers || {});
    headers.set('Accept', 'application/json');
    const token = window.localStorage.getItem('accessToken');
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const isFormData = (options.body && typeof FormData !== 'undefined' && options.body instanceof FormData);
    if (!isFormData && (options.body && !headers.has('Content-Type'))) {
      headers.set('Content-Type', 'application/json');
    }
    const csrf = getCookie('csrftoken');
    if (csrf && !headers.has('X-CSRFToken')) headers.set('X-CSRFToken', csrf);
    // Normalize URL to absolute and ensure trailing slash for non-GET to satisfy Django APPEND_SLASH
    let effectiveUrl = url || '';
    let finalMethod = String(options.method || 'GET').toUpperCase();
    try {
      const origin = (window.location && window.location.protocol && window.location.host)
        ? (window.location.protocol + '//' + window.location.host)
        : '';
      // Fix scheme without slashes (e.g., 'http:localhost:8000...')
      if (/^https?:[^\/]/i.test(effectiveUrl)) {
        effectiveUrl = effectiveUrl.replace(/^(https?):(?!\/\/)/i, '$1://');
      }
      if (!/^https?:\/\//i.test(effectiveUrl)) {
        const path = effectiveUrl.startsWith('/') ? effectiveUrl : '/' + effectiveUrl;
        effectiveUrl = origin ? (new URL(path, origin).toString()) : path;
      }
      // Force PATCH for sale order item updates (defensive against legacy PUT callers)
      try {
        const u = new URL(effectiveUrl, origin || undefined);
        const p = u.pathname || '';
        if (/^\/api\/sale\/orders\/.+\/items\/.+\/?$/i.test(p)) {
          finalMethod = 'PATCH';
        }
      } catch(e) {}
      if (finalMethod !== 'GET' && /\/api\//.test(effectiveUrl) && !effectiveUrl.endsWith('/')) {
        effectiveUrl = effectiveUrl + '/';
      }
    } catch(e) { /* keep original if normalization fails */ }
    const method = finalMethod;
    // Debug aid for FrontendTest mapping
    try { console.debug('fetchJson', { url, effectiveUrl, method }); } catch(e) {}
    // Visual logs (Sales page only): show non-GET requests
    const onSales = (window.location && typeof window.location.pathname === 'string' && window.location.pathname.indexOf('/sales') === 0);
    if (onSales && method !== 'GET') { try { toast(`➡ ${method} ${effectiveUrl}`,'info'); } catch(e) {} }

    const resp = await fetch(effectiveUrl, { credentials: 'same-origin', ...options, headers, method });
    const text = await resp.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch(e) { /* ignore */ }
    if (!resp.ok) {
      if (onSales) {
        try {
          const msg = (data && (data.detail || data.non_field_errors)) ? (typeof (data.detail||data.non_field_errors) === 'string' ? (data.detail||data.non_field_errors) : JSON.stringify(data.detail||data.non_field_errors)) : resp.statusText;
          toast(`⛔ ${resp.status} ${method} ${effectiveUrl}\n${msg}`,'error');
        } catch(e) {}
      }
      const detail = data && (data.detail || data.non_field_errors || data.errors) || text || resp.statusText;
      const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      err.status = resp.status; err.data = data; throw err;
    }
    if (onSales && method !== 'GET') { try { toast(`✓ ${resp.status} ${method} ${effectiveUrl}`,'success'); } catch(e) {} }
    return data;
  }

  function toast(message, type='info'){
    window.dispatchEvent(new CustomEvent('show-toast', { detail: { message, type } }));
  }

  window.Http = { fetchJson, toast };
})();
