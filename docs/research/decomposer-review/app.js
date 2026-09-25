(function () {
  const clientSession = (() => {
    const k = 'sos0011_client_session';
    let v = localStorage.getItem(k);
    if (!v) { v = 'cs_' + Math.random().toString(36).slice(2,10) + Date.now().toString(36); localStorage.setItem(k,v); }
    return v;
  })();
  const draftKey = 'sos0011_review_draft_v1';
  let variantsIndex = [];
  let cache = {};
  let ratings = loadDraft();

  mermaid.initialize({ startOnLoad:false, theme:'neutral', securityLevel:'strict' });

  function loadDraft() {
    try { return JSON.parse(localStorage.getItem(draftKey) || '{}'); } catch { return {}; }
  }
  function saveDraft() { localStorage.setItem(draftKey, JSON.stringify(ratings)); }

  function setStatus(msg, cls) {
    const el = document.getElementById('status');
    el.textContent = msg || '';
    el.className = 'status' + (cls ? ' ' + cls : '');
  }

  async function loadIndex() {
    // Prefer static index.json; fall back to API
    try {
      const r = await fetch('/review/decomposer/data/index.json', { cache:'no-cache' });
      if (r.ok) {
        const j = await r.json();
        variantsIndex = j.variants || [];
        return;
      }
    } catch {}
    try {
      const r = await fetch('/api/review/decomposer/variants');
      if (r.ok) {
        const j = await r.json();
        variantsIndex = j.variants || [];
      }
    } catch (e) {
      setStatus('Could not load variants index', 'err');
    }
  }

  async function loadVariant(fileOrId) {
    if (!fileOrId) return null;
    if (cache[fileOrId]) return cache[fileOrId];
    const meta = variantsIndex.find(v => v.variant_id === fileOrId || v.file === fileOrId);
    const file = (meta && meta.file) || (fileOrId.endsWith('.json') ? fileOrId : fileOrId + '.json');
    const r = await fetch('/review/decomposer/data/' + file, { cache:'no-cache' });
    if (!r.ok) throw new Error('load failed ' + file);
    const j = await r.json();
    cache[fileOrId] = j;
    cache[file] = j;
    return j;
  }

  function problems() {
    const map = new Map();
    for (const v of variantsIndex) {
      if (!v.problem_id) continue;
      if (!map.has(v.problem_id)) map.set(v.problem_id, v.problem_title || v.problem_id);
    }
    return [...map.entries()];
  }

  function variantsFor(problemId) {
    return variantsIndex.filter(v => v.problem_id === problemId);
  }

  function fillSelects() {
    const ps = document.getElementById('problemSelect');
    ps.innerHTML = '';
    for (const [id, title] of problems()) {
      const o = document.createElement('option');
      o.value = id; o.textContent = title || id; ps.appendChild(o);
    }
    ps.onchange = () => { refreshVariantOptions(); render(); };
    refreshVariantOptions();
    document.getElementById('variantA').onchange = render;
    document.getElementById('variantB').onchange = render;
  }

  function refreshVariantOptions() {
    const pid = document.getElementById('problemSelect').value;
    const list = variantsFor(pid);
    for (const selId of ['variantA','variantB']) {
      const sel = document.getElementById(selId);
      const keepEmpty = selId === 'variantB';
      const prev = sel.value;
      sel.innerHTML = keepEmpty ? '<option value="">— none —</option>' : '';
      for (const v of list) {
        const o = document.createElement('option');
        o.value = v.variant_id;
        o.textContent = (v.variant_kind || '?') + ' · ' + (v.model || '?');
        sel.appendChild(o);
      }
      if ([...sel.options].some(o => o.value === prev)) sel.value = prev;
      else if (!keepEmpty && list[0]) sel.value = list[0].variant_id;
    }
  }

  function rateKey(variantId, stepId) { return variantId + '::' + stepId; }

  function getRating(variantId, stepId) {
    return ratings[rateKey(variantId, stepId)] || { rating:null, note:'' };
  }

  function setRating(variantId, stepId, patch) {
    const k = rateKey(variantId, stepId);
    ratings[k] = Object.assign({ rating:null, note:'', variant_id:variantId, step_id:stepId }, ratings[k] || {}, patch);
    saveDraft();
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderArtifact(step, mount) {
    const fmt = (step.artifact_format || 'ascii').toLowerCase();
    const raw = step.artifact || '';
    mount.innerHTML = '';
    if (fmt === 'svg' || raw.trim().startsWith('<svg')) {
      const wrap = document.createElement('div');
      // trust curated/generator SVG only from our static files
      wrap.innerHTML = raw;
      mount.appendChild(wrap);
      return;
    }
    if (fmt === 'mermaid') {
      const id = 'mmd_' + Math.random().toString(36).slice(2);
      const div = document.createElement('div');
      div.className = 'mermaid';
      div.id = id;
      div.textContent = raw;
      mount.appendChild(div);
      mermaid.run({ nodes:[div] }).catch(() => {
        mount.innerHTML = '<pre>' + escapeHtml(raw) + '</pre>';
      });
      return;
    }
    if (fmt === 'katex' || fmt === 'algebra') {
      const div = document.createElement('div');
      try {
        // try katex; fall back to pre
        katex.render(raw.replace(/^\$+|\$+$/g,'').replace(/\\\\/g,'\\'), div, { throwOnError:false, displayMode:true });
      } catch {
        div.innerHTML = '<pre>' + escapeHtml(raw) + '</pre>';
      }
      // If katex produced empty, show pre
      if (!div.textContent.trim()) div.innerHTML = '<pre>' + escapeHtml(raw) + '</pre>';
      mount.appendChild(div);
      return;
    }
    if (fmt === 'code') {
      mount.innerHTML = '<pre>' + escapeHtml(raw) + '</pre>';
      return;
    }
    mount.innerHTML = '<pre>' + escapeHtml(raw) + '</pre>';
  }

  function stepCard(variant, step) {
    const vid = variant._meta.variant_id;
    const el = document.createElement('section');
    el.className = 'step';
    el.dataset.stepId = step.step_id;
    const cur = getRating(vid, step.step_id);
    el.innerHTML = `
      <div class="step-head">
        <span class="chip">Step ${step.step_index ?? ''}</span>
        <span class="chip">${escapeHtml(step.representation || '')}</span>
        <span class="chip">${escapeHtml(step.artifact_format || '')}</span>
        <span class="chip">${escapeHtml(step.concept || '')}</span>
        <span class="goal">${escapeHtml(step.goal || '')}</span>
      </div>
      <div class="artifact" data-art></div>
      <div class="prompt"><strong>Tutor prompt:</strong> ${escapeHtml(step.tutor_prompt || '')}</div>
      <div class="flow"><strong>on_correct:</strong> ${escapeHtml(step.on_correct || '')}<br/>
        <strong>on_wrong:</strong> ${escapeHtml(step.on_wrong || '')}</div>
      <div class="rate-row">
        <button type="button" data-r="good" class="good${cur.rating==='good'?' active':''}">Good</button>
        <button type="button" data-r="prefer" class="prefer${cur.rating==='prefer'?' active':''}">Prefer</button>
        <button type="button" data-r="bad" class="bad${cur.rating==='bad'?' active':''}">Bad</button>
        <textarea placeholder="Optional comment on this step + artifact" data-note>${escapeHtml(cur.note||'')}</textarea>
      </div>`;
    renderArtifact(step, el.querySelector('[data-art]'));
    el.querySelectorAll('button[data-r]').forEach(btn => {
      btn.addEventListener('click', () => {
        setRating(vid, step.step_id, {
          rating: btn.dataset.r,
          step_index: step.step_index,
          artifact_format: step.artifact_format,
          concept: step.concept,
        });
        el.querySelectorAll('button[data-r]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
    el.querySelector('[data-note]').addEventListener('input', (e) => {
      setRating(vid, step.step_id, { note: e.target.value, step_index: step.step_index, artifact_format: step.artifact_format });
    });
    return el;
  }

  function panel(variant) {
    const wrap = document.createElement('article');
    wrap.className = 'variant-panel';
    const m = variant._meta || {};
    wrap.innerHTML = `
      <h2>${escapeHtml(m.problem_title || m.problem_id || '')}</h2>
      <div class="meta">${escapeHtml(m.variant_kind||'')} · route <code>${escapeHtml(m.route||m.model||'')}</code> · ${escapeHtml(m.variant_id||'')}</div>
      <p class="strategy">${escapeHtml(variant.strategy || '')}</p>
      <p class="meta">${escapeHtml(m.problem_statement||'')}</p>
      <div class="steps"></div>
      <div class="overall">
        <div class="goal">Overall note for this variant</div>
        <div class="rate-row">
          <button type="button" data-or="good" class="good">Good</button>
          <button type="button" data-or="prefer" class="prefer">Prefer</button>
          <button type="button" data-or="bad" class="bad">Bad</button>
          <textarea data-overall placeholder="Optional overall comment"></textarea>
        </div>
      </div>`;
    const stepsMount = wrap.querySelector('.steps');
    for (const s of (variant.steps || [])) stepsMount.appendChild(stepCard(variant, s));
    const okey = rateKey(m.variant_id, '__overall__');
    const ocur = ratings[okey] || {};
    const ota = wrap.querySelector('[data-overall]');
    ota.value = ocur.note || '';
    if (ocur.rating) {
      const b = wrap.querySelector(`button[data-or="${ocur.rating}"]`);
      if (b) b.classList.add('active');
    }
    wrap.querySelectorAll('button[data-or]').forEach(btn => {
      btn.addEventListener('click', () => {
        ratings[okey] = Object.assign({}, ratings[okey]||{}, { rating: btn.dataset.or, note: ota.value, variant_id:m.variant_id, step_id:null, artifact_format:'overall' });
        saveDraft();
        wrap.querySelectorAll('button[data-or]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
    ota.addEventListener('input', () => {
      ratings[okey] = Object.assign({}, ratings[okey]||{}, { note: ota.value, variant_id:m.variant_id, artifact_format:'overall' });
      saveDraft();
    });
    return wrap;
  }

  async function render() {
    const layout = document.getElementById('layout');
    layout.innerHTML = '';
    const aId = document.getElementById('variantA').value;
    const bId = document.getElementById('variantB').value;
    try {
      const a = await loadVariant(aId);
      layout.appendChild(panel(a));
      if (bId) {
        const b = await loadVariant(bId);
        layout.appendChild(panel(b));
        layout.classList.add('compare');
      } else {
        layout.classList.remove('compare');
      }
      document.getElementById('headerMeta').textContent =
        `Client ${clientSession}. Draft autosaved locally. Showing full proposal(s) — scroll and rate artifacts.`;
    } catch (e) {
      setStatus(String(e), 'err');
    }
  }

  function collectForVariant(variantId) {
    const out = { ratings:[], overall:null };
    for (const [k,v] of Object.entries(ratings)) {
      if (!k.startsWith(variantId + '::')) continue;
      if (k.endsWith('::__overall__')) {
        out.overall = { rating: v.rating || 'ok', note: v.note || '' };
        continue;
      }
      if (!v.rating && !(v.note||'').trim()) continue;
      out.ratings.push({
        step_id: v.step_id,
        step_index: v.step_index,
        artifact_format: v.artifact_format,
        rating: v.rating || 'ok',
        note: v.note || null,
        payload: { concept: v.concept || null },
      });
    }
    return out;
  }

  async function submit() {
    const aId = document.getElementById('variantA').value;
    const variant = await loadVariant(aId);
    const m = variant._meta;
    const collected = collectForVariant(m.variant_id);
    if (!collected.ratings.length && !collected.overall) {
      setStatus('No ratings to submit', 'err'); return;
    }
    const batch = 'rb_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6);
    const body = {
      review_batch_id: batch,
      client_session: clientSession,
      problem_id: m.problem_id,
      variant_id: m.variant_id,
      ratings: collected.ratings,
      overall: collected.overall,
      client_ts: new Date().toISOString(),
    };
    setStatus('Submitting…');
    try {
      const r = await fetch('/api/review/decomposer', {
        method:'POST',
        headers: { 'Content-Type':'application/json', 'x-study-os':'1' },
        body: JSON.stringify(body),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || ('HTTP '+r.status));
      setStatus(`Stored ${j.stored} row(s) · batch ${j.review_batch_id}`, 'ok');
    } catch (e) {
      setStatus('Submit failed: ' + e + ' — use Export JSON', 'err');
    }
  }

  function exportJson() {
    const aId = document.getElementById('variantA').value;
    const blob = new Blob([JSON.stringify({ client_session: clientSession, exported_at: new Date().toISOString(), ratings }, null, 2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sos0011-decomposer-review-' + aId + '.json';
    a.click();
  }

  document.getElementById('btnSubmit').onclick = submit;
  document.getElementById('btnExport').onclick = exportJson;
  document.getElementById('btnCompare').onclick = () => {
    document.getElementById('layout').classList.toggle('compare');
  };

  loadIndex().then(() => { fillSelects(); return render(); });
})();
