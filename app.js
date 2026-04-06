/* the boat dude — mvp inventory
 * CSV paths are relative to the site root (serve this folder with any static host).
 * Regenerate files with scripts/pull_marketplace.py (defaults match paths below).
 */

const SHEET_CSV_URL = "/data/exports/boats-sheet.csv";
const PHOTO_GALLERY_CSV_URL = "/data/exports/photos-sheet.csv";
const GLOBAL_PHONE = "+704.957.0900";
const GLOBAL_EMAIL = "info@boatdudedeals.com";

// cache setup
const CACHE_DURATION = 30000; // 30 seconds cache for development, longer for production

const state = {
  boats: [],
  filtered: [],
  lightbox: { index: 0, images: [], title: "", phone: GLOBAL_PHONE, email: GLOBAL_EMAIL },
  detail: { boat: null, currentImage: 0 },
  photoGalleries: {}, // boat_id -> array of photos
};

// cache management
const cache = {
  boats: { data: null, timestamp: 0 },
  photos: { data: null, timestamp: 0 },
  lastUpdate: 0
};

// Cache management only


document.addEventListener("DOMContentLoaded", () => {
  // Check if we're on the inventory page
  const searchElement = document.getElementById("search");
  if (!searchElement) {
    return;
  }
  
  document.getElementById("year").textContent = new Date().getFullYear();
  applyHeaderVariantFromQuery();
  
  // Load initial data
  loadBoats().then(() => {
    loadPhotoGalleries().then(() => {
      initUI();
      handleRouting();
      // Listen for browser navigation
      window.addEventListener('popstate', handleRouting);
    });
  });
});

function applyHeaderVariantFromQuery(){
  try {
    const params = new URLSearchParams(window.location.search);
    const variant = (params.get('header') || '').toLowerCase();
    document.body.classList.remove('variant-a','variant-b');
    if (variant === 'a') {
      document.body.classList.add('variant-a');
    } else if (variant === 'b') {
      document.body.classList.add('variant-b');
    } else {
      // Default to Variant A when no explicit choice is provided
      document.body.classList.add('variant-a');
    }
  } catch (_) { /* noop */ }
}

// data loading with simple cache
function isCacheValid(cacheKey) {
  const now = Date.now();
  return cache[cacheKey].data && (now - cache[cacheKey].timestamp) < CACHE_DURATION;
}

function getCacheBustingURL(url) {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}_t=${Date.now()}`;
}

async function loadBoats(){
  try{
  // check cache first
    if (isCacheValid('boats')) {
      state.boats = cache.boats.data;
      updateFilteredBoats();
      renderCards(state.filtered);
      return;
    }

    // fetch boats CSV (static file under /data/exports/)
    const response = await fetch(getCacheBustingURL(SHEET_CSV_URL), { 
      cache: "no-store",
      redirect: "follow",
      mode: "cors"
    });
    
    if (!response.ok) {
      throw new Error(`Failed to load boats CSV: ${response.status} ${response.statusText}`);
    }
    
    const csv = await response.text();
    const boats = parseBoatsCSV(csv);
    state.boats = await normalizeBoats(boats);
    
    // save to cache
    cache.boats.data = state.boats;
    cache.boats.timestamp = Date.now();
    
    updateFilteredBoats();
    renderCards(state.filtered);
    
  } catch (e){
    console.error("Failed to load boats:", e);
    document.getElementById("inventory").innerHTML = `<p style="opacity:.8">Could not load inventory. Please check your data source.</p>`;
  }
}

function updateFilteredBoats() {
  state.filtered = state.boats.filter(b => {
    // Always show only published boats
    return b.published;
  });
}

async function loadPhotoGalleries(){
  if (PHOTO_GALLERY_CSV_URL && PHOTO_GALLERY_CSV_URL.trim().length > 0) {
    try {
      const csv = await fetch(getCacheBustingURL(PHOTO_GALLERY_CSV_URL), { 
        cache: "no-store",
        redirect: "follow",
        mode: "cors"
      }).then(r => r.text());
      const photos = parsePhotoGalleryCSV(csv);
      
      // Group photos by boat_id
      state.photoGalleries = {};
      photos.forEach(photo => {
        if (!state.photoGalleries[photo.boat_id]) {
          state.photoGalleries[photo.boat_id] = [];
        }
        state.photoGalleries[photo.boat_id].push(photo);
      });
      
      // Sort photos by order within each boat
      Object.keys(state.photoGalleries).forEach(boatId => {
        state.photoGalleries[boatId].sort((a, b) => a.photo_order - b.photo_order);
      });
      
      // Update boats with photo gallery data
      state.boats.forEach(boat => {
        if (state.photoGalleries[boat.id]) {
          boat.gallery = state.photoGalleries[boat.id].map(photo => photo.photo_url);
          boat.photoDetails = state.photoGalleries[boat.id];
          
          // Set primary image from photo gallery (photo with is_primary = true)
          const primaryPhoto = state.photoGalleries[boat.id].find(photo => photo.is_primary);
          if (primaryPhoto) {
            boat.primary_image = primaryPhoto.photo_url;
          }
        }
      });
    } catch (e) {
      console.warn("Failed to load photo galleries:", e);
    }
  }
  
  state.filtered = state.boats.filter(b => b.published);
  
  renderCards(state.filtered);
}

function parsePhotoGalleryCSV(csv){
  const rows = parseCSV(csv);
  if (!rows.length) return [];
  const header = rows[0].map(h => (h || "").toString().trim().toLowerCase());
  const photos = rows.slice(1).filter(r => r.some(c => String(c||"").trim().length > 0)).map(r => {
    const obj = {};
    header.forEach((h, i) => obj[h] = r[i]);
    return obj;
  });
  return photos.map(photo => {
    // Convert Google Drive URLs to browser-compatible format
    let photoUrl = photo.photo_url;
    if (photoUrl && photoUrl.includes('drive.google.com/uc?export=view&id=')) {
      const fileId = photoUrl.split('id=')[1];
      photoUrl = `https://drive.google.com/thumbnail?id=${fileId}&sz=w1200`;
    }
    
    return {
      boat_id: photo.boat_id,
      photo_id: photo.photo_id,
      photo_url: photoUrl,
      photo_alt: photo.photo_alt || "",
      photo_order: parseInt(photo.photo_order) || 0,
      is_primary: photo.is_primary === "true" || photo.is_primary === "TRUE",
      photo_type: photo.photo_type || "exterior",
      photo_notes: photo.photo_notes || ""
    };
  });
}

async function normalizeBoats(boats){
  const toNum = v => {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(String(v).replace(/[^0-9.\-]/g, ""));
    return Number.isFinite(n) ? n : null;
  };
  const clean = (v, d="") => (v ?? d).toString().trim();
  
  const normalizedBoats = [];
  for (let i = 0; i < boats.length; i++) {
    const b = boats[i];
    const priceNum = toNum(b.price);
    const yearNum = toNum(b.year);
    let created = b.created_at ? new Date(b.created_at) : new Date(Date.now() - i * 86400000);
    // Ensure the date is valid, fallback to current time if not
    if (isNaN(created.getTime())) {
      created = new Date(Date.now() - i * 86400000);
    }
    let gallery = Array.isArray(b.gallery) ? b.gallery.filter(Boolean) :
      clean(b.gallery_urls || b.gallery || "").split(/[\s]*,[\s]*/).filter(Boolean);
    let primary = clean(b.primary_image || b.primary_image_url || gallery[0] || "");
    const phone = clean(b.contact_phone || GLOBAL_PHONE);
    const email = clean(b.contact_email || GLOBAL_EMAIL);
    // Handle published field - Y/N binary column
    const published = clean(b.published || "").toUpperCase() === "Y";
    normalizedBoats.push({
      id: clean(b.id || `item-${i+1}`),
      title: clean(b.title || `${b.year || ""} ${b.make || ""} ${b.model || ""}`.trim() || "Boat / PWC"),
      category: clean((b.category || "Boat")).replace(/pwc/i, "PWC"),
      status: clean(b.status || "available").toLowerCase(),
      price: priceNum,
      price_display: clean(b.price_display || (priceNum ? `$${priceNum.toLocaleString()}` : "Call for price")),
      year: yearNum,
      make: clean(b.make || ""),
      model: clean(b.model || ""),
      length_ft: toNum(b.length_ft) || toNum(b.length) || null,
      hours: toNum(b.hours),
      engine: clean(b.engine || ""),
      hull: clean(b.hull || ""),
      color: clean(b.color || ""),
      location: clean(b.location || ""),
      description: clean(b.description || ""),
      primary_image: primary,
      gallery: gallery.length ? gallery : [primary],
      contact_phone: phone,
      contact_email: email,
      created_at: created.toISOString(),
      published: published,
      condition: clean(b.condition),
      trailer_included: clean(b.trailer_included),
      propulsion: clean(b.propulsion),
      beam_ft: toNum(b.beam_ft),
      draft_ft: toNum(b.draft_ft),
      fuel_capacity: toNum(b.fuel_capacity),
      seating_capacity: toNum(b.seating_capacity),
      features: clean(b.features),
      history: clean(b.history),
      maintenance_notes: clean(b.maintenance_notes),
    });
  }
  return normalizedBoats;
}

function parseBoatsCSV(csv){
  const rows = parseCSV(csv);
  if (!rows.length) return [];
  const header = rows[0].map(h => (h || "").toString().trim().toLowerCase());
  const items = rows.slice(1).filter(r => r.some(c => String(c||"").trim().length > 0)).map(r => {
    const obj = {};
    header.forEach((h, i) => obj[h] = r[i]);
    return obj;
  });
  return items;
}

function parseCSV(str){
  const rows = [];
  let cur = "", row = [], inQuotes = false;
  for (let i=0;i<str.length;i++){
    const c = str[i];
    if (inQuotes){
      if (c === '"'){
        if (str[i+1] === '"'){ cur += '"'; i++; }
        else { inQuotes = false; }
      } else {
        cur += c;
      }
    } else {
      if (c === '"'){ inQuotes = true; }
      else if (c === ','){ row.push(cur); cur = ""; }
      else if (c === '\n'){ row.push(cur); rows.push(row); row=[]; cur=""; }
      else if (c === '\r'){ /* ignore */ }
      else { cur += c; }
    }
  }
  if (cur.length || row.length){ row.push(cur); rows.push(row); }
  return rows;
}

function initUI(){
  const search = document.getElementById("search");
  
  if (!search) {
    return;
  }
  const onChange = () => {
    const q = (search.value || "").trim().toLowerCase();
    let list = state.boats.filter(b => {
      // Always require published = true
      if (!b.published) return false;
      
      // If no search query, show all boats
      if (!q) return true;
      
      // Search in multiple fields including category and status
      const searchFields = [
        b.title, b.make, b.model, b.year, b.color, 
        b.location, b.description, b.boat_id, b.category, b.status
      ].filter(field => field).join(" ").toLowerCase();
      
      return searchFields.includes(q);
    });
    // Sort by newest first (default)
    list.sort((a,b)=> new Date(b.created_at) - new Date(a.created_at));
    state.filtered = list;
    renderCards(list);
  };
  // Event listeners
  search.addEventListener("input", onChange);
  search.addEventListener("click", (e) => {
    e.target.focus();
  });
  
  // Clear search on Escape
  search.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      search.value = "";
      onChange();
    }
  });
  
  // Clear search when clicking logo
  const logo = document.querySelector(".brand");
  if (logo) {
    logo.addEventListener("click", (e) => {
      e.preventDefault(); // Prevent default anchor behavior
      search.value = "";
      onChange();
      search.focus();
    });
  }
  
  // Initial load
  onChange();
}

function renderCards(list){
  const grid = document.getElementById("inventory");
  grid.innerHTML = "";
  const tpl = document.getElementById("cardTemplate");
  if (!list.length){
    grid.innerHTML = '<p style="opacity:.8">No results. Try changing filters.</p>';
    return;
  }
  list.forEach(b => {
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.classList.toggle("sold", b.status === "sold");
    const img = node.querySelector(".card-img");
    img.src = b.primary_image;
    // Prioritize first card's image for LCP
    if (!document.querySelector('.card-img[fetchpriority="high"]')) {
      img.setAttribute('fetchpriority', 'high');
      img.setAttribute('decoding', 'async');
    }
    img.alt = b.title || "Listing photo";

    const badge = node.querySelector(".status-badge");
    badge.textContent = b.status.charAt(0).toUpperCase() + b.status.slice(1);
    badge.classList.add(`status-${b.status}`);

    const titleEl = node.querySelector(".card-title");
    titleEl.textContent = b.title || `${b.year||""} ${b.make||""} ${b.model||""}`.trim();
    // Provide a unique id so controls can reference it for accessible names
    titleEl.id = `cardTitle-${b.id}`;
    const price = b.price_display || (b.price ? `$${b.price.toLocaleString()}` : "Call for price");
    const subparts = [
      [b.year, b.make, b.model].filter(Boolean).join(" "),
      b.length_ft ? `${b.length_ft} ft` : "",
      b.hours ? `${b.hours} hrs` : "",
      price
    ].filter(Boolean);
    node.querySelector(".card-sub").textContent = subparts.join(" • ");

    const specs = node.querySelector(".specs");
    const addSpec = (label, val) => { if (val) { const li = document.createElement("li"); li.innerHTML = `<b>${label}:</b> ${val}`; specs.appendChild(li);} };
    addSpec("Category", b.category);
    addSpec("Location", b.location);
    addSpec("Engine", b.engine);
    addSpec("Hull", b.hull);
    addSpec("Color", b.color);

    const callBtn = node.querySelector(".call-btn");
    const emailBtn = node.querySelector(".email-btn");
    const galleryBtn = node.querySelector(".gallery-btn");
    callBtn.href = `tel:${b.contact_phone}`;
    emailBtn.href = `mailto:${b.contact_email}?subject=${encodeURIComponent(b.title)}`;
    // Give each button a unique id and tie its name to the card title
    // Use aria-label to avoid duplicate name computation issues in some checkers
    callBtn.setAttribute('aria-label', `Call about ${titleEl.textContent}`);
    emailBtn.setAttribute('aria-label', `Email about ${titleEl.textContent}`);
    galleryBtn.setAttribute('aria-label', `View photos and details for ${titleEl.textContent}`);
    galleryBtn.addEventListener("click", (e)=>{ e.preventDefault(); e.stopPropagation(); openDetailPageWithRouting(b); });
    
    // Make entire card clickable to open detail page (except for buttons)
    node.addEventListener("click", (e) => {
      // Only trigger if the click wasn't on a button or link
      if (!e.target.closest('button') && !e.target.closest('a')) {
        openDetailPageWithRouting(b);
      }
    });
    
    node.addEventListener("keydown", (e)=>{ 
      if (e.key === "Enter" || e.key === " "){ 
        e.preventDefault(); 
        openDetailPageWithRouting(b); 
      } 
    });

    grid.appendChild(node);
  });
}

/* Lightbox */
function openLightbox(b){
  state.lightbox = { index:0, images: b.gallery, title:b.title, phone:b.contact_phone, email:b.contact_email, boat: b };
  const lb = document.getElementById("lightbox");
  document.getElementById("lbTitle").textContent = b.title;
  document.getElementById("lbStatus").innerHTML = `<span class="status-badge status-${b.status}">${b.status.charAt(0).toUpperCase() + b.status.slice(1)}</span> • ${b.price_display}`;
  document.getElementById("lbCall").href = `tel:${b.contact_phone}`;
  document.getElementById("lbEmail").href = `mailto:${b.contact_email}?subject=${encodeURIComponent(b.title)}`;
  
  // Populate description and specs
  populateLightboxDetails(b);
  
  renderLightboxImage();
  renderThumbs();
  lb.hidden = false;
  lb.querySelector(".lb-close").focus();
  trapFocus(lb);
  
  // Show close hint for first-time users (only on mobile/touch devices)
  if (!sessionStorage.getItem('lightbox-hint-shown') && 'ontouchstart' in window) {
    showCloseHint();
  }
}
function closeLightbox(){
  const lb = document.getElementById("lightbox");
  lb.hidden = true;
  releaseFocus();
  
  // Remove any existing close hints
  const existingHint = document.querySelector('.close-hint');
  if (existingHint) {
    existingHint.remove();
  }
}

function showCloseHint(){
  const hint = document.createElement('div');
  hint.className = 'close-hint';
  hint.innerHTML = `
    <div class="close-hint-content">
      <span class="close-hint-icon">👆</span>
      <span class="close-hint-text">Tap outside or the × button to close</span>
    </div>
  `;
  
  const lightbox = document.getElementById("lightbox");
  lightbox.appendChild(hint);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    if (hint.parentNode) {
      hint.remove();
    }
    sessionStorage.setItem('lightbox-hint-shown', 'true');
  }, 3000);
  
  // Hide if user starts interacting
  const hideHint = () => {
    if (hint.parentNode) {
      hint.remove();
      sessionStorage.setItem('lightbox-hint-shown', 'true');
    }
    document.removeEventListener('click', hideHint);
    document.removeEventListener('touchstart', hideHint);
  };
  
  document.addEventListener('click', hideHint);
  document.addEventListener('touchstart', hideHint);
}

function populateLightboxDetails(boat){
  const descriptionEl = document.getElementById("lbDescription");
  const specsEl = document.getElementById("lbSpecs");
  
  // Description section
  if (boat.description && boat.description.trim()) {
    descriptionEl.innerHTML = `
      <h4>Description</h4>
      <p>${boat.description}</p>
    `;
  } else {
    descriptionEl.innerHTML = `
      <h4>Description</h4>
      <p>Contact us for more details about this boat.</p>
    `;
  }
  
  // Specifications
  const specs = [
    { label: "Year", value: boat.year },
    { label: "Make", value: boat.make },
    { label: "Model", value: boat.model },
    { label: "Category", value: boat.category },
    { label: "Length", value: boat.length_ft ? `${boat.length_ft} ft` : null },
    { label: "Hours", value: boat.hours ? `${boat.hours} hrs` : null },
    { label: "Engine", value: boat.engine },
    { label: "Hull", value: boat.hull },
    { label: "Color", value: boat.color },
    { label: "Location", value: boat.location },
    { label: "Condition", value: boat.condition },
    { label: "Propulsion", value: boat.propulsion }
  ].filter(spec => spec.value);
  
  specsEl.innerHTML = `
    <h4>Specifications</h4>
    <ul>
      ${specs.map(spec => `<li><b>${spec.label}:</b> ${spec.value}</li>`).join('')}
    </ul>
  `;
}
document.querySelector(".lb-close").addEventListener("click", closeLightbox);
document.getElementById("lbPrev").addEventListener("click", ()=>{ stepImage(-1); });
document.getElementById("lbNext").addEventListener("click", ()=>{ stepImage(+1); });
document.getElementById("lightbox").addEventListener("click", (e)=>{ if (e.target.id === "lightbox") closeLightbox(); });
document.addEventListener("keydown", (e)=>{
  const lb = document.getElementById("lightbox");
  if (lb.hidden) return;
  if (e.key === "Escape") closeLightbox();
  if (e.key === "ArrowLeft") stepImage(-1);
  if (e.key === "ArrowRight") stepImage(+1);
});

function stepImage(delta){
  const { images } = state.lightbox;
  state.lightbox.index = (state.lightbox.index + delta + images.length) % images.length;
  renderLightboxImage();
  renderThumbs();
}
function renderLightboxImage(){
  const { images, index, title } = state.lightbox;
  const img = document.getElementById("lbImg");
  const cap = document.getElementById("lbCaption");
  img.src = images[index];
  img.alt = `${title} — photo ${index+1} of ${images.length}`;
  cap.textContent = `Photo ${index+1} of ${images.length}`;
}
function renderThumbs(){
  const c = document.getElementById("lbThumbs");
  c.innerHTML = "";
  state.lightbox.images.forEach((src, i) => {
    const btn = document.createElement("button");
    btn.setAttribute("aria-current", i === state.lightbox.index ? "true" : "false");
    const im = document.createElement("img");
    im.src = src; im.alt = `Thumbnail ${i+1}`;
    btn.appendChild(im);
    btn.addEventListener("click", ()=>{ state.lightbox.index = i; renderLightboxImage(); renderThumbs(); });
    c.appendChild(btn);
  });
}

/* Boat Detail Page */
function openDetailPage(boat){
  state.detail.boat = boat;
  state.detail.currentImage = 0;
  
  const detailPage = document.getElementById("boatDetail");
  const mainContent = document.querySelector("main");
  // mark unavailable for styling
  if (detailPage){
    const isUnavailable = boat.status === 'sold' || boat.status === 'pending';
    detailPage.classList.toggle('unavailable', isUnavailable);
  }
  
  // Hide main content and show detail page
  mainContent.style.display = "none";
  detailPage.hidden = false;
  
  // Populate detail page
  document.getElementById("detailTitle").textContent = boat.title;
  document.getElementById("detailPrice").textContent = boat.price_display || (boat.price ? `$${boat.price.toLocaleString()}` : "Call for price");
  // Strike-through for sold/pending
  const titleEl = document.getElementById('detailTitle');
  const priceEl = document.getElementById('detailPrice');
  const shouldStrike = boat.status === 'sold' || boat.status === 'pending';
  if (titleEl) titleEl.classList.toggle('strike', shouldStrike);
  if (priceEl) priceEl.classList.toggle('strike', shouldStrike);
  const statusOverlay = document.getElementById("detailStatusBadge");
  if (statusOverlay){
    if (boat.status === 'available'){
      statusOverlay.style.display = 'none';
      statusOverlay.className = 'status-badge';
      statusOverlay.textContent = '';
    } else {
      statusOverlay.style.display = '';
      statusOverlay.className = `status-badge status-${boat.status}`;
      statusOverlay.textContent = boat.status.charAt(0).toUpperCase() + boat.status.slice(1);
    }
  }
  
  // Contact buttons
  document.getElementById("detailCall").href = `tel:${boat.contact_phone}`;
  document.getElementById("detailEmail").href = `mailto:${boat.contact_email}?subject=${encodeURIComponent(boat.title)}`;
  
  // Recommendations: only for sold or pending
  const recsEl = document.getElementById('detailRecs');
  if (recsEl) {
    if (boat.status === 'sold' || boat.status === 'pending') {
      recsEl.style.display = '';
      renderRecommendations(boat);
    } else {
      recsEl.innerHTML = '';
      recsEl.style.display = 'none';
    }
  }

  // Gallery
  renderDetailGallery();
  
  // Specifications
  renderDetailSpecs(boat);
  
  // Description and location
  document.getElementById("detailDescription").textContent = boat.description || "No description available.";
  document.getElementById("detailLocation").textContent = boat.location || "Location not specified.";
  
  // Additional details (show only if available)
  const featuresEl = document.getElementById("detailFeatures");
  const historyEl = document.getElementById("detailHistory");
  const maintenanceEl = document.getElementById("detailMaintenance");
  
  if (boat.features) {
    document.getElementById("detailFeaturesText").textContent = boat.features;
    featuresEl.style.display = "block";
  } else {
    featuresEl.style.display = "none";
  }
  
  if (boat.history) {
    document.getElementById("detailHistoryText").textContent = boat.history;
    historyEl.style.display = "block";
  } else {
    historyEl.style.display = "none";
  }
  
  if (boat.maintenance_notes) {
    document.getElementById("detailMaintenanceText").textContent = boat.maintenance_notes;
    maintenanceEl.style.display = "block";
  } else {
    maintenanceEl.style.display = "none";
  }
  
  // Focus management
  document.getElementById("detailBack").focus();
  trapFocus(detailPage);
}

// Recommendations: prioritize same category, available first, then nearest price
function renderRecommendations(current){
  try{
    const container = document.getElementById('detailRecs');
    if (!container) return;
    container.innerHTML = '';
    const title = document.createElement('div');
    title.className = 'detail-recs-title';
    title.textContent = 'You might like:';
    const list = document.createElement('div');
    list.className = 'detail-recs-list';

    const candidates = state.boats
      .filter(b => b.id !== current.id && b.status === 'available' && b.published)
      .map(b => ({
        boat: b,
        score: (
          // Availability weight: available > pending > sold
          (b.status === 'available' ? 0 : b.status === 'pending' ? 1 : 2) * 1000000 +
          // Category match bonus (lower is better)
          (b.category && current.category && b.category.toLowerCase() === current.category.toLowerCase() ? 0 : 200000) +
          // Price distance
          Math.abs((b.price || 0) - (current.price || 0))
        )
      }))
      .sort((a,b) => a.score - b.score)
      .slice(0, 3)
      .map(x => x.boat);

    candidates.forEach(b => {
      const a = document.createElement('a');
      a.className = 'rec-card';
      a.href = 'javascript:void(0)';
      a.setAttribute('aria-label', `View ${b.title}`);
      const img = document.createElement('img');
      img.className = 'rec-thumb';
      img.src = b.primary_image;
      img.alt = b.title;
      const meta = document.createElement('div');
      meta.className = 'rec-meta';
      const t = document.createElement('div');
      t.className = 'rec-title';
      t.textContent = b.title;
      const p = document.createElement('div');
      p.className = 'rec-price';
      p.textContent = b.price_display || (b.price ? `$${b.price.toLocaleString()}` : 'Call');
      meta.appendChild(t); meta.appendChild(p);
      a.appendChild(img); a.appendChild(meta);
      a.addEventListener('click', (e)=>{ e.preventDefault(); openDetailPageWithRouting(b); });
      list.appendChild(a);
    });

    if (candidates.length){
      container.appendChild(title);
      container.appendChild(list);
    }
  } catch(_){/* noop */}
}

function renderDetailGallery(){
  const boat = state.detail.boat;
  if (!boat || !boat.gallery || boat.gallery.length === 0) return;
  
  const mainImg = document.getElementById("detailMainImg");
  const thumbsContainer = document.getElementById("detailThumbs");
  
  // Set main image
  mainImg.src = boat.gallery[state.detail.currentImage];
  mainImg.setAttribute('fetchpriority', 'high');
  mainImg.setAttribute('decoding', 'async');
  mainImg.alt = `${boat.title} — photo ${state.detail.currentImage + 1} of ${boat.gallery.length}`;
  
  // Create thumbnails
  thumbsContainer.innerHTML = "";
  boat.gallery.forEach((src, index) => {
    const thumb = document.createElement("img");
    thumb.src = src;
    thumb.alt = `${boat.title} — thumbnail ${index + 1} of ${boat.gallery.length}`;
    thumb.className = index === state.detail.currentImage ? "active" : "";
    thumb.setAttribute("role", "listitem");
    thumb.setAttribute("tabindex", "0");
    thumb.setAttribute("aria-label", `View photo ${index + 1} of ${boat.gallery.length}`);
    
    const clickHandler = () => {
      state.detail.currentImage = index;
      mainImg.src = src;
      mainImg.alt = `${boat.title} — photo ${index + 1} of ${boat.gallery.length}`;
      // Update active thumbnail
      thumbsContainer.querySelectorAll("img").forEach((img, i) => {
        img.className = i === index ? "active" : "";
        img.setAttribute("aria-current", i === index ? "true" : "false");
      });
    };
    
    thumb.addEventListener("click", clickHandler);
    thumb.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        clickHandler();
      }
    });
    
    thumbsContainer.appendChild(thumb);
  });
  
  // Add event listeners for overlay navigation arrows
  setupDetailGalleryNavigation();
}

function setupDetailGalleryNavigation(){
  const prevBtn = document.getElementById('detailPrevImg');
  const nextBtn = document.getElementById('detailNextImg');
  const boat = state.detail.boat;
  
  if (!boat || !boat.gallery || boat.gallery.length <= 1) {
    // Hide arrows if no gallery or only one image
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) nextBtn.style.display = 'none';
    return;
  }
  
  // Show arrows
  if (prevBtn) prevBtn.style.display = 'flex';
  if (nextBtn) nextBtn.style.display = 'flex';
  
  const updateNavButtons = () => {
    const currentIndex = state.detail.currentImage;
    if (prevBtn) {
      prevBtn.disabled = currentIndex === 0;
      prevBtn.style.opacity = currentIndex === 0 ? '0.3' : '';
    }
    if (nextBtn) {
      nextBtn.disabled = currentIndex === boat.gallery.length - 1;
      nextBtn.style.opacity = currentIndex === boat.gallery.length - 1 ? '0.3' : '';
    }
  };
  
  const goToNext = (e) => {
    e.preventDefault();
    if (state.detail.currentImage < boat.gallery.length - 1) {
      state.detail.currentImage++;
      updateDetailMainImage();
      updateNavButtons();
      updateActiveThumbnail();
    }
  };
  
  const goToPrev = (e) => {
    e.preventDefault();
    if (state.detail.currentImage > 0) {
      state.detail.currentImage--;
      updateDetailMainImage();
      updateNavButtons();
      updateActiveThumbnail();
    }
  };
  
  const updateDetailMainImage = () => {
    const mainImg = document.getElementById('detailMainImg');
    mainImg.src = boat.gallery[state.detail.currentImage];
    mainImg.alt = `${boat.title} — photo ${state.detail.currentImage + 1} of ${boat.gallery.length}`;
  };
  
  const updateActiveThumbnail = () => {
    const thumbs = document.querySelectorAll('#detailThumbs img');
    thumbs.forEach((thumb, index) => {
      thumb.className = index === state.detail.currentImage ? "active" : "";
      thumb.setAttribute("aria-current", index === state.detail.currentImage ? "true" : "false");
    });
  };
  
  // Add event listeners
  if (prevBtn) {
    prevBtn.removeEventListener('click', goToPrev); // Remove existing listener to prevent duplicates
    prevBtn.addEventListener('click', goToPrev);
  }
  if (nextBtn) {
    nextBtn.removeEventListener('click', goToNext); // Remove existing listener to prevent duplicates
    nextBtn.addEventListener('click', goToNext);
  }
  
  // Initialize button states
  updateNavButtons();
  
  // Add swipe/touch support for mobile
  setupDetailTouchNavigation();
}

function setupDetailTouchNavigation(){
  const galleryMain = document.querySelector('.gallery-main');
  const boat = state.detail.boat;
  
  if (!galleryMain || !boat || !boat.gallery || boat.gallery.length <= 1) return;
  
  let startX = 0;
  let startY = 0;
  let isDragging = false;
  let startTime = 0;
  
  const handleTouchStart = (e) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    startTime = Date.now();
    isDragging = true;
    galleryMain.style.transition = 'none';
  };
  
  const handleTouchMove = (e) => {
    if (!isDragging) return;
    
    const currentX = e.touches[0].clientX;
    const currentY = e.touches[0].clientY;
    const deltaX = startX - currentX;
    const deltaY = startY - currentY;
    
    // Only trigger horizontal swipes (ignore vertical scrolling)
    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
      e.preventDefault();
    }
  };
  
  const handleTouchEnd = (e) => {
    if (!isDragging) return;
    
    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;
    const deltaX = startX - endX;
    const deltaY = startY - endY;
    const deltaTime = Date.now() - startTime;
    
    galleryMain.style.transition = '';
    
    // Minimum swipe distance and maximum time for swipe
    if (Math.abs(deltaX) > 50 && Math.abs(deltaX) > Math.abs(deltaY) && deltaTime < 500) {
      if (deltaX > 0 && state.detail.currentImage < boat.gallery.length - 1) {
        // Swipe left = next image
        state.detail.currentImage++;
        updateDetailMainImage();
        updateActiveThumbnail();
        updateNavButtons();
      } else if (deltaX < 0 && state.detail.currentImage > 0) {
        // Swipe right = previous image
        state.detail.currentImage--;
        updateDetailMainImage();
        updateActiveThumbnail();
        updateNavButtons();
      }
    }
    
    isDragging = false;
  };
  
  galleryMain.addEventListener('touchstart', handleTouchStart, { passive: false });
  galleryMain.addEventListener('touchmove', handleTouchMove, { passive: false });
  galleryMain.addEventListener('touchend', handleTouchEnd, { passive: false });
}

function renderDetailSpecs(boat){
  const specsContainer = document.getElementById("detailSpecs");
  specsContainer.innerHTML = "";
  
  const specs = [
    { label: "Year", value: boat.year },
    { label: "Make", value: boat.make },
    { label: "Model", value: boat.model },
    { label: "Category", value: boat.category },
    { label: "Length", value: boat.length_ft ? `${boat.length_ft} ft` : null },
    { label: "Beam", value: boat.beam_ft ? `${boat.beam_ft} ft` : null },
    { label: "Draft", value: boat.draft_ft ? `${boat.draft_ft} ft` : null },
    { label: "Hours", value: boat.hours ? `${boat.hours} hrs` : null },
    { label: "Engine", value: boat.engine },
    { label: "Propulsion", value: boat.propulsion },
    { label: "Hull", value: boat.hull },
    { label: "Color", value: boat.color },
    { label: "Condition", value: boat.condition },
    { label: "Trailer", value: boat.trailer_included },
    { label: "Fuel Capacity", value: boat.fuel_capacity ? `${boat.fuel_capacity} gal` : null },
    { label: "Seating", value: boat.seating_capacity ? `${boat.seating_capacity} people` : null },
    { label: "Status", value: boat.status.charAt(0).toUpperCase() + boat.status.slice(1) }
  ];
  
  specs.forEach(spec => {
    if (spec.value) {
      const specItem = document.createElement("div");
      specItem.className = "spec-item";
      specItem.setAttribute("role", "listitem");
      specItem.innerHTML = `
        <span class="spec-label" id="spec-${spec.label.toLowerCase().replace(/\s+/g, '-')}">${spec.label}</span>
        <span class="spec-value" aria-labelledby="spec-${spec.label.toLowerCase().replace(/\s+/g, '-')}">${spec.value}</span>
      `;
      specsContainer.appendChild(specItem);
    }
  });
}

function closeDetailPage(){
  const detailPage = document.getElementById("boatDetail");
  const mainContent = document.querySelector("main");
  
  detailPage.hidden = true;
  mainContent.style.display = "block";
  
  // Update URL to remove hash when returning to inventory
  updateURL(null);
  
  releaseFocus();
}

// Detail page event listeners
document.getElementById("detailBack").addEventListener("click", closeDetailPage);
document.addEventListener("keydown", (e) => {
  const detailPage = document.getElementById("boatDetail");
  if (detailPage.hidden) return;
  if (e.key === "Escape") closeDetailPage();
});

/* Focus trap */
let lastFocus = null;
function trapFocus(el){
  lastFocus = document.activeElement;
  const focusable = el.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  el.addEventListener("keydown", function(e){
    if (e.key !== "Tab") return;
    if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
  });
}
function releaseFocus(){
  if (lastFocus && document.body.contains(lastFocus)) lastFocus.focus();
}

/* URL Routing */
function getBasePath(){
  // supports root or /inventory deployments
  return window.location.pathname.startsWith('/inventory') ? '/inventory' : '';
}

function handleRouting(){
  const path = window.location.pathname;
  const base = getBasePath();
  const detailPage = document.getElementById("boatDetail");
  const mainContent = document.querySelector("main");
  
  // Expect patterns: `${base}/` (list) or `${base}/boat/:id`
  const detailMatch = path.match(new RegExp(`^${base.replace(/\//g,'\\/')}\/boat\/([^\/]+)\/?$`));
  if (detailMatch) {
    const boatId = decodeURIComponent(detailMatch[1]);
    const boat = state.boats.find(b => b.id === boatId);
    if (boat && boat.published) {
      if (detailPage.hidden) {
        openDetailPage(boat);
      }
    } else {
      // If not found or not published, ensure we're on the list view
      if (!detailPage.hidden) closeDetailPage();
      updateURL(null);
    }
    return;
  }
  // List page
  if (!detailPage.hidden) {
    closeDetailPage();
  }
}

function updateURL(boatId){
  const base = getBasePath();
  if (boatId) {
    window.history.pushState(null, '', `${base}/boat/${encodeURIComponent(boatId)}`);
  } else {
    window.history.pushState(null, '', `${base}/`);
  }
}

// Open detail page with URL routing
function openDetailPageWithRouting(boat){
  openDetailPage(boat);
  updateURL(boat.id);
}


