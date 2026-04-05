(function(){
  const qs = (s)=>document.querySelector(s);
  const appendForm = qs('#appendForm');
  const updateForm = qs('#updateForm');
  const appendMsg = qs('#appendMsg');
  const updateMsg = qs('#updateMsg');
  const csvFile = qs('#csvFile');
  const importBtn = qs('#importCsv');
  const downloadBtn = qs('#downloadCsv');
  const pushToSheetsBtn = qs('#pushToSheets');
  const pullFromSheetsBtn = qs('#pullFromSheets');
  const clearBtn = qs('#clearAll');
  const csvMsg = qs('#csvMsg');
  const entriesCount = qs('#entriesCount');
  const entriesTableBody = qs('#entriesTable tbody');
  const galleryBoatId = qs('#galleryBoatId');
  const galleryBoatSelect = qs('#galleryBoatSelect');
  const galleryLoadBtn = qs('#galleryLoad');
  const galleryNewFile = qs('#galleryNewFile');
  const galleryNewAlt = qs('#galleryNewAlt');
  const galleryAddBtn = qs('#galleryAddPhoto');
  const galleryList = qs('#galleryList');
  const gallerySaveBtn = qs('#gallerySaveBoat');
  const galleryMsg = qs('#galleryMsg');
  const galleryImportInput = qs('#galleryImport');
  const galleryImportBtn = qs('#galleryImportBtn');
  const galleryDownloadBtn = qs('#galleryDownload');
  const galleryResetBtn = qs('#galleryReset');

  // csv/local entries store
  const STORAGE_KEY = 'adminEntriesCsv';
  const GALLERY_STORAGE_KEY = 'photoManifestDraft';
  const HEADERS = [
    'id','title','category','status','price','price_display','year','make','model',
    'length_ft','hours','engine','hull','color','location','description',
    'primary_image_url','gallery_urls','contact_phone','contact_email','created_at',
    'published','condition','trailer_included','propulsion','beam_ft','draft_ft',
    'fuel_capacity','seating_capacity','features','history','maintenance_notes'
  ];

  function getEntries(){
    try{
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    }catch(_){ return []; }
  }
  function setEntries(list){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    renderEntries(list);
  }
  function renderEntries(list){
    entriesCount.textContent = String(list.length);
    entriesTableBody.innerHTML = '';
    list.forEach(item => {
      const tr = document.createElement('tr');
      const cells = [item.id, item.title, item.status, item.price, item.year, item.make, item.model];
      cells.forEach(val => {
        const td = document.createElement('td');
        td.style.padding = '.25rem .5rem';
        td.textContent = val || '';
        tr.appendChild(td);
      });
      // share column
      const shareTd = document.createElement('td');
      shareTd.style.padding = '.25rem .5rem';
      shareTd.appendChild(makeShareButtons(item));
      tr.appendChild(shareTd);
      entriesTableBody.appendChild(tr);
    });
  }

  function makeShareButtons(item){
    const wrap = document.createElement('div');
    wrap.className = 'row';
    const btn = (label)=>{ const b=document.createElement('button'); b.type='button'; b.className='pill secondary'; b.textContent=label; return b; };
    const webShareBtn = btn('Share');
    const twBtn = btn('Tweet');
    const fbBtn = btn('Facebook');

    const caption = buildCaption(item);
    const url = buildPublicUrl(item);

    webShareBtn.addEventListener('click', async ()=>{
      if (navigator.share){
        try{ await navigator.share({ title: item.title||'Listing', text: caption, url }); }catch(_){ /* canceled */ }
      } else {
        window.open(url, '_blank');
      }
    });
    twBtn.addEventListener('click', ()=>{
      const t = encodeURIComponent(caption);
      const u = encodeURIComponent(url||'');
      window.open(`https://twitter.com/intent/tweet?text=${t}&url=${u}`, '_blank');
    });
    fbBtn.addEventListener('click', ()=>{
      const u = encodeURIComponent(url||'');
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${u}`, '_blank');
    });

    wrap.appendChild(webShareBtn);
    wrap.appendChild(twBtn);
    wrap.appendChild(fbBtn);
    return wrap;
  }

  function buildCaption(item){
    const bits = [];
    const line1 = [item.year, item.make, item.model].filter(Boolean).join(' ');
    if (line1) bits.push(line1);
    if (item.length_ft) bits.push(`${item.length_ft} ft`);
    if (item.hours) bits.push(`${item.hours} hrs`);
    const price = item.price_display || (item.price ? `$${Number(item.price).toLocaleString()}` : 'Call for price');
    bits.push(price);
    const title = item.title && item.title !== line1 ? `— ${item.title}` : '';
    const caption = `${bits.join(' • ')}${title}`.trim();
    return caption;
  }

  function buildPublicUrl(item){
    try{
      const base = new URL(location.origin + location.pathname).origin; // site origin
      // site home is at ../index.html relative to admin/
      // use hash routing to boat id (see app.js)
      return `${base}${location.pathname.replace(/\/admin\/.*/, '/') }#${encodeURIComponent(item.id||'')}`;
    } catch(_){
      return '';
    }
  }
  function parseCsv(text){
    const rows = [];
    let cur = '', row = [], inQ = false;
    for (let i=0;i<text.length;i++){
      const c = text[i];
      if (inQ){
        if (c==='"'){
          if (text[i+1]==='"'){ cur+='"'; i++; }
          else { inQ=false; }
        } else { cur+=c; }
      } else {
        if (c==='"') inQ=true;
        else if (c===','){ row.push(cur); cur=''; }
        else if (c==='\n'){ row.push(cur); rows.push(row); row=[]; cur=''; }
        else if (c==='\r'){ /* ignore */ }
        else { cur+=c; }
      }
    }
    if (cur.length || row.length){ row.push(cur); rows.push(row); }
    return rows;
  }
  function toCsv(list){
    const esc = (v)=>{
      const s = (v==null? '': String(v));
      if (/[",\n]/.test(s)) return '"' + s.replace(/"/g,'""') + '"';
      return s;
    };
    const lines = [HEADERS.join(',')];
    list.forEach(obj => {
      const row = HEADERS.map(h => esc(obj[h]));
      lines.push(row.join(','));
    });
    return lines.join('\n');
  }
  function upsertEntry(obj){
    const list = getEntries();
    const idx = list.findIndex(x => (x.id||'') === (obj.id||''));
    if (idx >= 0) list[idx] = { ...list[idx], ...obj };
    else list.push(obj);
    setEntries(list);
  }

  const galleryState = {
    manifest: { updated_at: '', boats: {} },
    boatId: '',
    draft: []
  };

  const escapeHtml = (str='')=>{
    return String(str).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  };

  // Google Sheets API integration
  const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':5001/api';
  
  async function pushToGoogleSheets(){
    csvMsg.textContent = 'Pushing to Google Sheets...';
    csvMsg.className = 'note';
    pushToSheetsBtn.disabled = true;
    pushToSheetsBtn.textContent = 'Pushing...';
    
    try {
      const entries = getEntries();
      if (!entries.length) {
        throw new Error('No data to push');
      }
      
      // Check API health first
      const healthResponse = await fetch(`${API_BASE_URL}/health`);
      if (!healthResponse.ok) {
        throw new Error('API server not available. Make sure the Flask API server is running.');
      }
      
      const healthData = await healthResponse.json();
      if (!healthData.sheets_connected) {
        throw new Error('Google Sheets service not connected. Check your credentials.');
      }
      
      // Push boats data
      const response = await fetch(`${API_BASE_URL}/boats`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ boats: entries })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to push to Google Sheets');
      }
      
      const result = await response.json();
      csvMsg.textContent = result.message || 'Successfully pushed to Google Sheets!';
      csvMsg.className = 'note success';
      
    } catch (err) {
      csvMsg.textContent = `Error: ${err.message}`;
      csvMsg.className = 'note error';
      console.error('Push to Google Sheets failed:', err);
    } finally {
      pushToSheetsBtn.disabled = false;
      pushToSheetsBtn.textContent = 'Push to Google Sheets';
    }
  }

  async function pullFromGoogleSheets(){
    csvMsg.textContent = 'Pulling from Google Sheets...';
    csvMsg.className = 'note';
    
    try {
      // Check API health first
      const healthResponse = await fetch(`${API_BASE_URL}/health`);
      if (!healthResponse.ok) {
        throw new Error('API server not available. Make sure the Flask API server is running.');
      }
      
      const healthData = await healthResponse.json();
      if (!healthData.sheets_connected) {
        throw new Error('Google Sheets service not connected. Check your credentials.');
      }
      
      // Pull boats data
      const response = await fetch(`${API_BASE_URL}/boats`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to pull from Google Sheets');
      }
      
      const result = await response.json();
      const boats = result.boats || [];
      
      if (boats.length > 0) {
        setEntries(boats);
        csvMsg.textContent = `Pulled ${boats.length} entries from Google Sheets`;
        csvMsg.className = 'note success';
      } else {
        csvMsg.textContent = 'No data found in Google Sheets';
        csvMsg.className = 'note';
      }
      
    } catch (err) {
      csvMsg.textContent = `Error: ${err.message}`;
      csvMsg.className = 'note error';
      console.error('Pull from Google Sheets failed:', err);
    }
  }

  // Wire up
  document.addEventListener('DOMContentLoaded', ()=>{
    appendForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      appendMsg.textContent = 'Saving...';
      appendMsg.className = 'note';
      try{
        const fd = new FormData(appendForm);
        const obj = {};
        for (const [k,v] of fd.entries()) obj[k] = v;
        obj.created_at = obj.created_at || new Date().toISOString();
        upsertEntry(obj);
        appendMsg.textContent = 'Row added locally';
        appendMsg.className = 'note success';
        appendForm.reset();
      } catch(err){
        appendMsg.textContent = String(err.message || err);
        appendMsg.className = 'note error';
      }
    });

    updateForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      updateMsg.textContent = 'Saving...';
      updateMsg.className = 'note';
      try{
        const fd = new FormData(updateForm);
        const id = fd.get('id');
        const field = fd.get('field');
        const value = fd.get('value');
        const list = getEntries();
        const idx = list.findIndex(x => (x.id||'') === String(id||''));
        if (idx === -1) throw new Error('ID not found locally');
        list[idx][field] = value;
        setEntries(list);
        updateMsg.textContent = 'Row updated locally';
        updateMsg.className = 'note success';
      } catch(err){
        updateMsg.textContent = String(err.message || err);
        updateMsg.className = 'note error';
      }
    });

    importBtn.addEventListener('click', async ()=>{
      csvMsg.textContent = '';
      const file = csvFile.files && csvFile.files[0];
      if (!file){ csvMsg.textContent = 'Choose a CSV file first'; csvMsg.className='note error'; return; }
      const text = await file.text();
      try{
        const rows = parseCsv(text);
        if (!rows.length) throw new Error('Empty CSV');
        const header = rows[0].map(h => String(h||'').trim().toLowerCase());
        const items = rows.slice(1).filter(r => r.some(c => String(c||'').trim().length>0)).map(r => {
          const obj = {};
          header.forEach((h,i)=> obj[h] = r[i]);
          return obj;
        });
        setEntries(items);
        csvMsg.textContent = `Imported ${items.length} rows`;
        csvMsg.className = 'note success';
      } catch(err){
        csvMsg.textContent = String(err.message||err);
        csvMsg.className = 'note error';
      }
    });

    downloadBtn.addEventListener('click', ()=>{
      const list = getEntries();
      const csv = toCsv(list);
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'boats-admin-export.csv';
      document.body.appendChild(a);
      a.click();
      setTimeout(()=>{ URL.revokeObjectURL(url); a.remove(); }, 0);
    });

    pushToSheetsBtn.addEventListener('click', pushToGoogleSheets);
    pullFromSheetsBtn.addEventListener('click', pullFromGoogleSheets);

    clearBtn.addEventListener('click', ()=>{
      if (confirm('Clear all local entries?')){
        setEntries([]);
        csvMsg.textContent = 'Cleared';
        csvMsg.className = 'note';
      }
    });

    // initial render
    renderEntries(getEntries());
    initGalleryManager();
  });

  function initGalleryManager(){
    if (!galleryList) return;
    loadGalleryManifest();
    galleryLoadBtn?.addEventListener('click', ()=>{
      const id = (galleryBoatId.value || '').trim();
      if (!id){
        galleryMsg.textContent = 'type a boat id first';
        galleryMsg.className = 'note error';
        return;
      }
      loadBoatGallery(id);
    });
    galleryBoatSelect?.addEventListener('change', (e)=>{
      const val = e.target.value;
      if (val){
        galleryBoatId.value = val;
        loadBoatGallery(val);
      }
    });
    galleryAddBtn?.addEventListener('click', addGalleryPhoto);
    galleryList?.addEventListener('click', handleGalleryListClick);
    galleryList?.addEventListener('input', handleGalleryInputChange);
    gallerySaveBtn?.addEventListener('click', saveBoatGallery);
    galleryDownloadBtn?.addEventListener('click', downloadGalleryManifest);
    galleryImportBtn?.addEventListener('click', importGalleryManifest);
    galleryResetBtn?.addEventListener('click', resetGalleryManifest);
  }

  async function loadGalleryManifest(){
    try{
      const localDraft = localStorage.getItem(GALLERY_STORAGE_KEY);
      if (localDraft){
        galleryState.manifest = normalizeManifestShape(JSON.parse(localDraft));
      } else {
        const res = await fetch('../data/photo-manifest.json', { cache: 'no-store' });
        if (res.ok){
          galleryState.manifest = normalizeManifestShape(await res.json());
        } else {
          galleryState.manifest = { updated_at: '', boats: {} };
        }
      }
    } catch(err){
      console.warn('photo manifest load failed', err);
      galleryState.manifest = { updated_at: '', boats: {} };
    }
    renderGallerySelect();
    if (galleryState.boatId){
      loadBoatGallery(galleryState.boatId);
    }
  }

  function normalizeManifestShape(manifest){
    if (!manifest || typeof manifest !== 'object'){
      return { updated_at: '', boats: {} };
    }
    if (!manifest.boats || typeof manifest.boats !== 'object'){
      manifest.boats = {};
    }
    return manifest;
  }

  function renderGallerySelect(){
    if (!galleryBoatSelect) return;
    const ids = Object.keys(galleryState.manifest.boats || {}).sort();
    const options = ['<option value="">load existing...</option>'].concat(
      ids.map(id => `<option value="${id}">${escapeHtml(id)} (${(galleryState.manifest.boats[id]||[]).length})</option>`)
    );
    galleryBoatSelect.innerHTML = options.join('');
  }

  function loadBoatGallery(boatId){
    galleryState.boatId = boatId.trim();
    if (!galleryState.boatId){
      galleryMsg.textContent = 'boat id missing';
      galleryMsg.className = 'note error';
      return;
    }
    galleryBoatId.value = galleryState.boatId;
    const photos = galleryState.manifest.boats[galleryState.boatId] || [];
    galleryState.draft = photos.map(photo => ({ ...photo }));
    renderGalleryList();
    galleryMsg.textContent = `editing ${galleryState.boatId}`;
    galleryMsg.className = 'note';
  }

  function renderGalleryList(){
    if (!galleryList) return;
    if (!galleryState.draft.length){
      galleryList.innerHTML = '<p class="note">no photos yet. drop in filenames above to add them.</p>';
      return;
    }
    galleryList.innerHTML = galleryState.draft.map((photo, index) => {
      return `
        <div class="gallery-item" data-index="${index}">
          <label>file</label>
          <input data-field="file" data-index="${index}" value="${escapeHtml(photo.file || '')}">
          <label>alt text</label>
          <input data-field="photo_alt" data-index="${index}" value="${escapeHtml(photo.photo_alt || '')}">
          <div class="gallery-controls">
            <button type="button" class="pill secondary" data-action="up" data-index="${index}">up</button>
            <button type="button" class="pill secondary" data-action="down" data-index="${index}">down</button>
            <button type="button" class="pill secondary" data-action="delete" data-index="${index}">remove</button>
            <button type="button" class="pill ${photo.is_primary ? 'gallery-primary' : 'secondary'}" data-action="primary" data-index="${index}">${photo.is_primary ? 'primary' : 'make primary'}</button>
          </div>
        </div>
      `;
    }).join('');
  }

  function handleGalleryListClick(e){
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const idx = Number(btn.dataset.index);
    if (Number.isNaN(idx) || !galleryState.draft[idx]) return;
    const action = btn.dataset.action;
    if (action === 'delete'){
      galleryState.draft.splice(idx, 1);
    } else if (action === 'up' && idx > 0){
      [galleryState.draft[idx-1], galleryState.draft[idx]] = [galleryState.draft[idx], galleryState.draft[idx-1]];
    } else if (action === 'down' && idx < galleryState.draft.length - 1){
      [galleryState.draft[idx+1], galleryState.draft[idx]] = [galleryState.draft[idx], galleryState.draft[idx+1]];
    } else if (action === 'primary'){
      galleryState.draft.forEach((photo, position) => {
        photo.is_primary = position === idx;
      });
    }
    renderGalleryList();
  }

  function handleGalleryInputChange(e){
    const input = e.target;
    if (!input.dataset || input.dataset.field == null) return;
    const idx = Number(input.dataset.index);
    if (Number.isNaN(idx) || !galleryState.draft[idx]) return;
    const field = input.dataset.field;
    galleryState.draft[idx][field] = input.value;
  }

  function addGalleryPhoto(){
    if (!galleryState.boatId){
      const id = (galleryBoatId.value || '').trim();
      if (!id){
        galleryMsg.textContent = 'load a boat before adding photos';
        galleryMsg.className = 'note error';
        return;
      }
      galleryState.boatId = id;
    }
    const rawFile = (galleryNewFile.value || '').trim();
    if (!rawFile){
      galleryMsg.textContent = 'add a filename first';
      galleryMsg.className = 'note error';
      return;
    }
    galleryState.draft.push({
      file: normalizeGalleryPath(rawFile, galleryState.boatId),
      photo_alt: (galleryNewAlt.value || '').trim(),
      photo_order: galleryState.draft.length + 1,
      is_primary: galleryState.draft.length === 0 && !galleryState.draft.some(p => p.is_primary)
    });
    galleryNewFile.value = '';
    galleryNewAlt.value = '';
    renderGalleryList();
  }

  function saveBoatGallery(){
    if (!galleryState.boatId){
      galleryMsg.textContent = 'load a boat before saving';
      galleryMsg.className = 'note error';
      return;
    }
    const cleaned = galleryState.draft
      .filter(photo => (photo.file || '').trim().length > 0)
      .map((photo, idx) => ({
        file: normalizeGalleryPath(photo.file, galleryState.boatId),
        photo_alt: (photo.photo_alt || '').trim(),
        photo_order: idx + 1,
        is_primary: !!photo.is_primary
      }));
    if (cleaned.length && !cleaned.some(p => p.is_primary)){
      cleaned[0].is_primary = true;
    }
    if (cleaned.length){
      galleryState.manifest.boats[galleryState.boatId] = cleaned;
    } else {
      delete galleryState.manifest.boats[galleryState.boatId];
    }
    galleryState.manifest.updated_at = new Date().toISOString();
    persistGalleryManifest();
    renderGallerySelect();
    galleryMsg.textContent = 'saved locally. download the json when ready.';
    galleryMsg.className = 'note success';
  }

  function normalizeGalleryPath(path, boatId){
    let safe = (path || '').trim();
    if (!safe) return '';
    safe = safe.replace(/\\/g, '/');
    if (safe.startsWith('http://') || safe.startsWith('https://')){
      return safe;
    }
    if (safe.startsWith('/')){
      return safe;
    }
    if (safe.startsWith('photos-optimized')){
      return `/${safe.replace(/^\/+/, '')}`;
    }
    const prefix = boatId ? `/photos-optimized/${boatId}/` : '/photos-optimized/';
    return `${prefix}${safe}`.replace(/\/{2,}/g, '/');
  }

  function persistGalleryManifest(){
    try{
      localStorage.setItem(GALLERY_STORAGE_KEY, JSON.stringify(galleryState.manifest));
    } catch(err){
      console.warn('could not persist photo manifest', err);
    }
  }

  function downloadGalleryManifest(){
    galleryState.manifest.updated_at = new Date().toISOString();
    const blob = new Blob([JSON.stringify(galleryState.manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'photo-manifest.json';
    document.body.appendChild(a);
    a.click();
    setTimeout(()=>{ URL.revokeObjectURL(url); a.remove(); }, 0);
  }

  async function importGalleryManifest(){
    const file = galleryImportInput?.files && galleryImportInput.files[0];
    if (!file){
      galleryMsg.textContent = 'choose a json file first';
      galleryMsg.className = 'note error';
      return;
    }
    try{
      const text = await file.text();
      const parsed = JSON.parse(text);
      galleryState.manifest = normalizeManifestShape(parsed);
      persistGalleryManifest();
      renderGallerySelect();
      if (galleryState.boatId){
        loadBoatGallery(galleryState.boatId);
      } else {
        galleryList.innerHTML = '<p class="note">manifest loaded. pick a boat above.</p>';
      }
      galleryMsg.textContent = 'manifest imported (remember to download before deploying)';
      galleryMsg.className = 'note success';
    } catch(err){
      galleryMsg.textContent = 'import failed. check the json format.';
      galleryMsg.className = 'note error';
      console.error('manifest import failed', err);
    }
  }

  async function resetGalleryManifest(){
    try{
      localStorage.removeItem(GALLERY_STORAGE_KEY);
      const res = await fetch('../data/photo-manifest.json', { cache: 'no-store' });
      if (res.ok){
        galleryState.manifest = normalizeManifestShape(await res.json());
        renderGallerySelect();
        if (galleryState.boatId){
          loadBoatGallery(galleryState.boatId);
        } else {
          galleryList.innerHTML = '<p class="note">loaded from disk. pick a boat above.</p>';
        }
        galleryMsg.textContent = 'reloaded manifest from disk';
        galleryMsg.className = 'note success';
      } else {
        throw new Error('request failed');
      }
    } catch(err){
      galleryMsg.textContent = 'could not reload from disk';
      galleryMsg.className = 'note error';
      console.error('reset failed', err);
    }
  }
})();


