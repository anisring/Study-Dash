async function getTests(){
  const res = await fetch('/api/tests');
  return res.json();
}

function formatDate(value){
  if(!value) return '-';
  const parts = value.slice(0, 10).split('-');
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : value;
}

function toIsoDate(value){
  const parts = (value || '').trim().split('/');
  return parts.length === 3 ? `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}` : value;
}

function setupProfile(){
  fetch('/api/profile').then(response => response.json()).then(profile => {
    const name = profile.name || '';
    const greeting = document.getElementById('dashboard-greeting');
    if(greeting) greeting.textContent = name ? `Hello ${name}!` : 'Set up your profile';
    const link = document.createElement('a');
    link.className = 'profile-link'; link.href = '/profile';
    link.title = profile.name ? `Profile: ${profile.name}` : 'Set up your profile';
    link.setAttribute('aria-label', link.title);
    link.innerHTML = profile.avatar_url ? `<img src="${profile.avatar_url}" alt="">` : `<span>${(profile.name || '?').charAt(0).toUpperCase()}</span>`;
    document.body.appendChild(link);
    const form = document.getElementById('profile-form');
    if(!form) return;
    form.name.value = profile.name || ''; form.email.value = profile.email || '';
    const preview = document.getElementById('profile-preview-avatar');
    if(profile.avatar_url) preview.innerHTML = `<img src="${profile.avatar_url}" alt="">`;
    document.getElementById('profile-preview-name').textContent = profile.name ? `Hello ${profile.name}!` : 'Set up your profile';
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const response = await fetch('/api/profile', {method:'POST', body:new FormData(form)});
      const result = await response.json();
      document.getElementById('profile-message').textContent = response.ok ? 'Profile saved.' : (result.error || 'Could not save profile.');
      if(response.ok) window.location.reload();
    });
  });
}

function drawProgressChart(tests){
  const svg = document.getElementById('progress-chart');
  const msg = document.getElementById('progress-msg');
  if(!svg){ if(msg) msg.textContent='Progress chart not available.'; return; }
  while(svg.firstChild) svg.removeChild(svg.firstChild);
  if(!tests || tests.length===0){ if(msg) msg.textContent='Enter a test to see your progress report.'; return; }
  msg.textContent='';
  const w = Math.max(720, tests.length * 42); const h = +svg.getAttribute('height');
  svg.setAttribute('width', w);
  const margin = {top: 28, right: 20, bottom: 58, left: 46};
  const plotW = w - margin.left - margin.right; const plotH = h - margin.top - margin.bottom;
  const maxY = 180;
  const style = getComputedStyle(document.documentElement);
  const axisCol = style.getPropertyValue('--muted').trim() || '#94A3B8';
  const gridCol = style.getPropertyValue('--border').trim() || '#334155';
  const textColor = style.getPropertyValue('--text').trim() || '#F8FAFC';
  const barColor = style.getPropertyValue('--accent').trim() || '#38BDF8';
  const y = value => margin.top + (1 - value / maxY) * plotH;
  const groupW = plotW / tests.length;
  const barW = Math.min(54, Math.max(8, groupW * 0.62));
  const labelEvery = tests.length <= 20 ? 1 : Math.ceil(tests.length / 20);
  const shortLabel = test => (test.test_name || 'Test').length > 13 ? `${(test.test_name || 'Test').slice(0, 12)}…` : (test.test_name || 'Test');
  const add = (tag, attrs, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if(text !== undefined) node.textContent = text;
    svg.appendChild(node);
    return node;
  };

  for(let value=0; value<=maxY; value+=30){
    const gy = y(value);
    add('line', {x1:margin.left, y1:gy, x2:w-margin.right, y2:gy, stroke:gridCol, 'stroke-width':1, opacity:value===0?0.8:0.45});
    add('text', {x:margin.left-10, y:gy+4, 'font-size':11, fill:textColor, 'text-anchor':'end'}, value);
  }
  add('line', {x1:margin.left, y1:margin.top, x2:margin.left, y2:margin.top+plotH, stroke:axisCol, 'stroke-width':1.5});
  add('line', {x1:margin.left, y1:margin.top+plotH, x2:w-margin.right, y2:margin.top+plotH, stroke:axisCol, 'stroke-width':1.5});
  add('text', {x:margin.left, y:16, 'font-size':12, fill:textColor}, 'Total score / 180');

  tests.forEach((test, index) => {
    const score = Math.max(0, Math.min(maxY, Number(test.total) || 0));
    const center = margin.left + groupW * (index + 0.5);
    const top = y(score);
    const bar = add('rect', {x:center-barW/2, y:top, width:barW, height:margin.top+plotH-top, rx:4, fill:barColor, opacity:0.9});
    bar.style.cursor = 'pointer';
    bar.addEventListener('click', () => alert(`${test.test_name}\n${formatDate(test.date)}\nTotal: ${score}/180`));
    add('text', {x:center, y:top-8, 'font-size':12, 'font-weight':'700', fill:textColor, 'text-anchor':'middle'}, score);
    if(index % labelEvery === 0 || index === tests.length - 1){
      add('text', {x:center, y:margin.top+plotH+20, 'font-size':11, fill:textColor, 'text-anchor':'middle'}, shortLabel(test));
      add('text', {x:center, y:margin.top+plotH+36, 'font-size':10, fill:axisCol, 'text-anchor':'middle'}, formatDate(test.date));
    }
  });
}

const themeDefaults = {
  base: '#0F172A',
  surface: '#243B5A',
  secondary: '#1E3A5F',
  text: '#F8FAFC',
  border: '#334155',
  accent: '#F97316',
  graph: '#3B82F6'
};

function applyTheme(theme){
  const values = {...themeDefaults, ...theme};
  document.documentElement.style.setProperty('--base-color', values.base);
  document.documentElement.style.setProperty('--bg', values.base);
  document.documentElement.style.setProperty('--card', values.surface);
  document.documentElement.style.setProperty('--secondary', values.secondary);
  document.documentElement.style.setProperty('--text', values.text);
  document.documentElement.style.setProperty('--border', values.border);
  document.documentElement.style.setProperty('--accent', values.accent);
  document.documentElement.style.setProperty('--accent-hover', values.accent);
  document.documentElement.style.setProperty('--graph-color', values.graph);
  localStorage.setItem('studyDashTheme', JSON.stringify(values));
}

function restoreTheme(){
  try { applyTheme(JSON.parse(localStorage.getItem('studyDashTheme') || '{}')); } catch(e) { applyTheme(themeDefaults); }
}

function setupCustomization(){
  if(document.getElementById('theme-picker')) return;
  let saved = {...themeDefaults};
  try { saved = {...saved, ...JSON.parse(localStorage.getItem('studyDashTheme') || '{}')}; } catch(e) {}
  const labels = {base:'Page background', surface:'Cards and tables', secondary:'Input boxes', text:'Text', border:'Lines and borders', accent:'Buttons and highlights'};
  const picker = document.createElement('aside');
  picker.id = 'theme-picker';
  picker.innerHTML = `<button id="theme-toggle" type="button" aria-label="Open color customization" aria-expanded="false"><span aria-hidden="true"></span></button>
    <form id="customization-form" class="customization" hidden><div class="customization-heading"><strong>Choose app colors</strong><button id="theme-close" type="button" aria-label="Close color customization">×</button></div>
      ${Object.entries(labels).map(([key, label]) => `<label>${label}<input name="${key}" type="color" value="${saved[key]}" aria-label="${label} color"></label>`).join('')}
      <button id="theme-reset" type="button">Reset colors</button></form>`;
  document.body.appendChild(picker);
  const form = picker.querySelector('#customization-form');
  const toggle = picker.querySelector('#theme-toggle');
  const close = picker.querySelector('#theme-close');
  const setOpen = open => { form.hidden = !open; toggle.setAttribute('aria-expanded', String(open)); };
  toggle.addEventListener('click', () => setOpen(form.hidden));
  close.addEventListener('click', () => setOpen(false));
  Object.keys(labels).forEach(key => form.elements[key].addEventListener('input', () => {
    const theme = Object.fromEntries(Object.keys(labels).map(name => [name, form.elements[name].value]));
    applyTheme(theme);
  }));
  picker.querySelector('#theme-reset').addEventListener('click', () => {
    Object.keys(labels).forEach(key => form.elements[key].value = themeDefaults[key]);
    applyTheme(themeDefaults);
  });
}

function setupGraphColor(){
  const input = document.querySelector('#graph-color');
  if(!input) return;
  let saved = themeDefaults.graph;
  try { saved = JSON.parse(localStorage.getItem('studyDashTheme') || '{}').graph || saved; } catch(e) {}
  input.value = saved;
  input.addEventListener('input', () => {
    let theme = {...themeDefaults};
    try { theme = {...theme, ...JSON.parse(localStorage.getItem('studyDashTheme') || '{}')}; } catch(e) {}
    theme.graph = input.value;
    applyTheme(theme);
    getTests().then(drawPerfChart);
  });
}

async function getGoals(){
  const res = await fetch('/api/goals');
  return res.json();
}

function formatLatest(tests){
  if(!tests || tests.length===0) return 'No tests recorded yet.';
  const t = tests[tests.length-1];
  return `<div>${t.test_name} — ${formatDate(t.date)}<br>Physics ${t.physics}/60<br>Chemistry ${t.chemistry}/60<br>Maths ${t.maths}/60<br><b>TOTAL ${t.total}/180</b></div>`;
}

function drawPerfChart(tests){
  const svg = document.getElementById('perf-chart');
  if(!svg) return;
  while(svg.firstChild) svg.removeChild(svg.firstChild);
  if(!tests || tests.length===0) return;
  const w = +svg.getAttribute('width');
  const h = +svg.getAttribute('height');
    const margin = 40;
  const plotW = w - margin*2;
  const plotH = h - margin*2;
  const maxY = 180;
  const n = tests.length;
  function x(i){ return margin + (n===1?plotW/2:(i/(n-1))*plotW); }
  function y(v){ return margin + (1 - v/maxY)*plotH; }

  const style = getComputedStyle(document.documentElement);
  const axisColor = style.getPropertyValue('--muted').trim() || '#CBD5E1';
  const gridColor = style.getPropertyValue('--border').trim() || '#334155';
  const textColor = style.getPropertyValue('--text').trim() || '#F8FAFC';
  const lineColor = style.getPropertyValue('--graph-color').trim() || '#3B82F6';

  // grid lines + y axis ticks
  const step = 30;
  for(let val = 0; val <= maxY; val += step){
    const gy = y(val);
    const g = document.createElementNS('http://www.w3.org/2000/svg','line');
    g.setAttribute('x1',margin); g.setAttribute('y1',gy); g.setAttribute('x2',margin+plotW); g.setAttribute('y2',gy);
    g.setAttribute('stroke',gridColor); g.setAttribute('stroke-width',1); g.setAttribute('opacity',0.25);
    svg.appendChild(g);
    const lab = document.createElementNS('http://www.w3.org/2000/svg','text');
    lab.setAttribute('x',10); lab.setAttribute('y',gy+4); lab.setAttribute('font-size','11'); lab.setAttribute('fill',textColor);
    lab.textContent = val;
    svg.appendChild(lab);
  }

  // x axis ticks
  for(let i=0;i<n;i++){
    const tx = x(i);
    const tline = document.createElementNS('http://www.w3.org/2000/svg','line');
    tline.setAttribute('x1',tx); tline.setAttribute('y1',margin+plotH); tline.setAttribute('x2',tx); tline.setAttribute('y2',margin+plotH+6);
    tline.setAttribute('stroke',axisColor); tline.setAttribute('stroke-width',1); svg.appendChild(tline);
    const lbl = document.createElementNS('http://www.w3.org/2000/svg','text'); lbl.setAttribute('x',tx); lbl.setAttribute('y',margin+plotH+20); lbl.setAttribute('font-size','11'); lbl.setAttribute('fill',textColor); lbl.setAttribute('text-anchor','middle'); lbl.textContent = (i+1);
    svg.appendChild(lbl);
  }

  // axis labels
  const yLabel = document.createElementNS('http://www.w3.org/2000/svg','text');
  yLabel.setAttribute('x',8); yLabel.setAttribute('y',margin-10); yLabel.setAttribute('font-size','12'); yLabel.setAttribute('fill',textColor);
  yLabel.textContent = 'Total'; svg.appendChild(yLabel);
  const xLabel = document.createElementNS('http://www.w3.org/2000/svg','text');
  xLabel.setAttribute('x',margin+plotW/2); xLabel.setAttribute('y',h-6); xLabel.setAttribute('font-size','12'); xLabel.setAttribute('fill',textColor); xLabel.setAttribute('text-anchor','middle'); xLabel.textContent = 'Test #'; svg.appendChild(xLabel);

    // definite axis lines (Y and X) - more visible than grid
    const axisCol = '#64748B';
    const yAxis = document.createElementNS('http://www.w3.org/2000/svg','line');
    yAxis.setAttribute('x1',margin); yAxis.setAttribute('y1',margin); yAxis.setAttribute('x2',margin); yAxis.setAttribute('y2',margin+plotH);
    yAxis.setAttribute('stroke',axisCol); yAxis.setAttribute('stroke-width',1.5); svg.appendChild(yAxis);
    const xAxis = document.createElementNS('http://www.w3.org/2000/svg','line');
    xAxis.setAttribute('x1',margin); xAxis.setAttribute('y1',margin+plotH); xAxis.setAttribute('x2',margin+plotW); xAxis.setAttribute('y2',margin+plotH);
    xAxis.setAttribute('stroke',axisCol); xAxis.setAttribute('stroke-width',1.5); svg.appendChild(xAxis);
  // polyline (no fill) and points
  let path = '';
  for(let i=0;i<n;i++){ const px = x(i); const py = y(tests[i].total); path += (i===0?`M ${px} ${py}`:` L ${px} ${py}`); }
  const pathElem = document.createElementNS('http://www.w3.org/2000/svg','path');
  pathElem.setAttribute('d',path); pathElem.setAttribute('fill','none'); pathElem.setAttribute('stroke',lineColor); pathElem.setAttribute('stroke-width',2.5); svg.appendChild(pathElem);
  for(let i=0;i<n;i++){
    const cx = x(i); const cy = y(tests[i].total);
    const c = document.createElementNS('http://www.w3.org/2000/svg','circle'); c.setAttribute('cx',cx); c.setAttribute('cy',cy); c.setAttribute('r',4.5); c.setAttribute('fill',lineColor); svg.appendChild(c);
      c.addEventListener('click',()=> alert(`${tests[i].test_name}\n${formatDate(tests[i].date)}\nTotal: ${tests[i].total}`));
  }
}

async function loadHome(){
  const tests = await getTests();
  // populate latest test card
  if(tests && tests.length){
    const t = tests[tests.length-1];
    const meta = document.getElementById('latest-meta'); if(meta) meta.textContent = `${t.test_name} · ${formatDate(t.date)}`;
    const lp = document.getElementById('latest-p'); if(lp) lp.textContent = `${t.physics} / 60`;
    const lc = document.getElementById('latest-c'); if(lc) lc.textContent = `${t.chemistry} / 60`;
    const lm = document.getElementById('latest-m'); if(lm) lm.textContent = `${t.maths} / 60`;
    const lt = document.getElementById('latest-total'); if(lt) lt.textContent = `${t.total} / 180`;
  } else {
    const meta = document.getElementById('latest-meta'); if(meta) meta.textContent = 'No tests recorded yet.';
  }
  drawPerfChart(tests);
  const goals = await getGoals();
  const tbody = document.querySelector('#goals-table tbody'); if(tbody) tbody.innerHTML='';
  goals.forEach(g=>{
    const tr=document.createElement('tr');
    const score = g.current_score==null?'-':g.current_score;
    const diff = g.current_score==null?'-':(g.current_score - g.target);
    const status = g.status || '-';
    let cls = '';
    if(status === 'met') cls = 'success'; else if(status === 'pending') cls = 'pending'; else cls = (status.includes('no')||status.includes('missing'))? 'fail' : '';
    tr.innerHTML=`<td>${formatDate(g.start_date)}</td><td>${g.name}</td><td>${g.target}</td><td>${score}</td><td>${diff}</td><td><span class='status ${cls}'>${status}</span></td>`;
    tbody.appendChild(tr);
  });
}

async function setupHome(){
  const form = document.getElementById('enter-form'); if(!form) return;
  form.date.value = formatDate(new Date().toISOString());
  // style submit button
  const submit = form.querySelector('button[type=submit]'); if(submit) submit.classList.add('btn-accent');
  // live total calculation
  const pIn = form.physics, cIn = form.chemistry, mIn = form.maths, live = document.getElementById('live-total');
  function updateLive(){ const p = parseInt(pIn.value||0)||0; const c = parseInt(cIn.value||0)||0; const m = parseInt(mIn.value||0)||0; if(live) live.textContent = `${p+c+m}`; }
  [pIn,cIn,mIn].forEach(i=>i.addEventListener('input', updateLive)); updateLive();
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const data = { date: toIsoDate(form.date.value), test_name: form.test_name.value, physics: form.physics.value, chemistry: form.chemistry.value, maths: form.maths.value };
    const res = await fetch('/api/tests',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(data)});
    const j = await res.json(); if(res.status===201){ document.getElementById('enter-msg').textContent='Saved'; loadHome(); form.reset(); form.date.value=formatDate(new Date().toISOString()); updateLive();} else { document.getElementById('enter-msg').textContent=j.error||'Error'; }
  });
}

async function loadHistory(){
  const tests = await getTests();
  const tbody = document.querySelector('#history-table tbody'); tbody.innerHTML='';
  tests.forEach(t=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${formatDate(t.date)}</td><td>${t.test_name}</td><td>${t.physics}</td><td>${t.chemistry}</td><td>${t.maths}</td><td>${t.total}</td><td><button data-id='${t.id}' class='del'>Delete</button></td>`; tbody.appendChild(tr); });
  document.querySelectorAll('.del').forEach(b=>b.addEventListener('click',async ev=>{ const id=ev.target.dataset.id; await fetch('/api/tests/'+id,{method:'DELETE'}); loadHistory(); }));
  // analysis: compute averages, best subject, recent trend
  const all = tests; // already fetched
  const analysisDiv = document.getElementById('analysis');
  if(!analysisDiv) return;
  if(!all || all.length===0){ analysisDiv.textContent = 'No tests yet.'; return; }
  const n = all.length;
  let totalSum = 0; let s = {physics:0, chemistry:0, maths:0};
  let bestSingle = {total:-1, date:null, name:null};
  all.forEach(t=>{ totalSum += (t.total||0); s.physics += (t.physics||0); s.chemistry += (t.chemistry||0); s.maths += (t.maths||0); if((t.total||0) > bestSingle.total){ bestSingle = { total: t.total||0, date: t.date, name: t.test_name }; } });
  const avgTotal = totalSum / n;
  const avgP = s.physics / n; const avgC = s.chemistry / n; const avgM = s.maths / n;
  const subjAverages = [{k:'Physics', v:avgP},{k:'Chemistry', v:avgC},{k:'Maths', v:avgM}];
  subjAverages.sort((a,b)=>b.v-a.v);
  const bestSubject = subjAverages[0].k;
  // recent change
  let recentText = 'Not enough data to compute trend.';
  if(n>=2){ const last = all[n-1].total||0; const prev = all[n-2].total||0; const diff = last - prev; const pct = prev?((diff/prev)*100).toFixed(1):'—'; recentText = (diff>0?`Improved by ${diff} (+${pct}%) since previous test.`:(diff<0?`Dropped by ${-diff} (${pct}%).`:'No change from previous test.')); }
  analysisDiv.innerHTML = `<p><strong>Overall average:</strong> ${avgTotal.toFixed(1)} / 180</p><p><strong>Subject averages:</strong> Physics ${avgP.toFixed(1)}, Chemistry ${avgC.toFixed(1)}, Maths ${avgM.toFixed(1)}</p><p><strong>Best subject (avg):</strong> ${bestSubject}</p><p><strong>Best single test:</strong> ${bestSingle.total} — ${bestSingle.name} (${bestSingle.date})</p><p><strong>Recent change:</strong> ${recentText}</p>`;
  setupTestComparison(tests);
  // draw progress chart
  try{ drawProgressChart(all); } catch(e){ console.error('progress draw error', e); }
}

function setupTestComparison(tests){
  const first = document.getElementById('compare-first');
  const second = document.getElementById('compare-second');
  const button = document.getElementById('compare-button');
  const result = document.getElementById('compare-result');
  if(!first || !second || !button || !result) return;
  const options = tests.map((test, index) => `<option value="${test.id}">${index + 1}. ${test.test_name} (${formatDate(test.date)})</option>`).join('');
  first.innerHTML = options;
  second.innerHTML = options;
  if(tests.length > 1) { first.value = tests[0].id; second.value = tests[tests.length - 1].id; }
  const compare = () => {
    const left = tests.find(test => String(test.id) === first.value);
    const right = tests.find(test => String(test.id) === second.value);
    if(!left || !right) { result.textContent = 'Select two tests to compare.'; return; }
    if(left.id === right.id) { result.textContent = 'Choose two different tests.'; return; }
    const rows = [['Total', left.total, right.total, 180], ['Physics', left.physics, right.physics, 60], ['Chemistry', left.chemistry, right.chemistry, 60], ['Maths', left.maths, right.maths, 60]];
    const changes = rows.map(([subject, before, after]) => ({subject, before, after, diff: after - before}));
    const improved = changes.filter(change => change.diff > 0).sort((a, b) => b.diff - a.diff);
    const subjectImproved = improved.filter(change => change.subject !== 'Total');
    const summary = subjectImproved.length ? `Biggest subject improvement: ${subjectImproved[0].subject} (+${subjectImproved[0].diff}). Overall total change: ${changes[0].diff > 0 ? '+' : ''}${changes[0].diff}.` : `No subject improved in the second test. Overall total change: ${changes[0].diff > 0 ? '+' : ''}${changes[0].diff}.`;
    result.innerHTML = `<p><strong>${left.test_name}</strong> (${formatDate(left.date)}) compared with <strong>${right.test_name}</strong> (${formatDate(right.date)})</p><div class="compare-grid">${changes.map(change => `<div class="compare-row"><strong>${change.subject}</strong><span>${change.before} → ${change.after}</span><b class="${change.diff > 0 ? 'compare-up' : change.diff < 0 ? 'compare-down' : ''}">${change.diff > 0 ? '+' : ''}${change.diff}</b></div>`).join('')}</div><p>${summary}</p>`;
  };
  button.onclick = compare;
  compare();
}

async function setupGoals(){
  const form = document.getElementById('goal-form'); if(!form) return; form.addEventListener('submit',async e=>{ e.preventDefault(); const data={ name: form.name.value, type: form.type.value, target: form.target.value, start_date: toIsoDate(form.start_date.value)||null, end_date: toIsoDate(form.end_date.value)||null }; const res=await fetch('/api/goals',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(data)}); if(res.status===201){ alert('Goal saved'); form.reset(); loadGoals(); } else { alert((await res.json()).error||'Error'); } }); loadGoals(); }

async function loadGoals(){ const goals = await getGoals(); const tbody=document.querySelector('#goals-list tbody'); if(!tbody) return; tbody.innerHTML=''; goals.forEach(g=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${g.name}</td><td>${g.type}</td><td>${g.target}</td><td>${formatDate(g.start_date)}</td><td>${formatDate(g.end_date)}</td><td><button data-id='${g.id}' class='del-goal'>Delete</button></td>`; tbody.appendChild(tr); });
  document.querySelectorAll('.del-goal').forEach(button=>button.addEventListener('click',async event=>{
    const id = event.currentTarget.dataset.id;
    if(!confirm('Delete this goal?')) return;
    const res = await fetch('/api/goals/'+id,{method:'DELETE'});
    if(res.ok) loadGoals(); else alert('Could not delete goal.');
  }));
}

function setupLibrary(){
  const uploadForm = document.getElementById('library-upload-form');
  if(!uploadForm) return;
  const fileInput = document.getElementById('library-file');
  const dropzone = document.getElementById('library-dropzone');
  const fileName = document.getElementById('library-file-name');
  const message = document.getElementById('library-upload-msg');
  const setFile = file => { if(!file) return; const transfer = new DataTransfer(); transfer.items.add(file); fileInput.files = transfer.files; fileName.textContent = file.name; };
  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', event => { if(event.key === 'Enter' || event.key === ' ') fileInput.click(); });
  fileInput.addEventListener('change', () => setFile(fileInput.files[0]));
  ['dragenter', 'dragover'].forEach(type => dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.add('dragging'); }));
  ['dragleave', 'drop'].forEach(type => dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.remove('dragging'); }));
  dropzone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
  uploadForm.addEventListener('submit', async event => {
    event.preventDefault();
    if(!fileInput.files[0]) { message.textContent = 'Choose a paper first.'; return; }
    message.textContent = 'Reading and saving paper...';
    const response = await fetch('/api/library', {method:'POST', body:new FormData(uploadForm)});
    const result = await response.json();
    message.textContent = response.ok ? 'Saved to The Library.' : (result.error || 'Could not save paper.');
    if(response.ok) { uploadForm.reset(); fileName.textContent = 'No file selected'; loadLibrary(); }
  });
  document.getElementById('library-ask-form').addEventListener('submit', async event => {
    event.preventDefault();
    const answer = document.getElementById('library-answer');
    const question = event.currentTarget.question.value.trim();
    answer.textContent = 'Searching your papers...';
    const response = await fetch('/api/library/ask', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({question})});
    const result = await response.json();
    if(!response.ok) { answer.textContent = result.error || 'Could not search papers.'; return; }
    answer.innerHTML = `<p>${result.answer}</p>${result.matches.length ? result.matches.map(match => `<article><strong>${match.paper}</strong><p>${match.excerpt}</p></article>`).join('') : '<p>No close passage found in your saved papers.</p>'}`;
  });
  setupSchedule();
  loadLibrary();
}

function setupSchedule(){
  const uploadForm = document.getElementById('schedule-upload-form');
  const entryForm = document.getElementById('schedule-entry-form');
  if(!uploadForm || !entryForm) return;
  const fileInput = document.getElementById('schedule-file');
  const dropzone = document.getElementById('schedule-dropzone');
  const fileName = document.getElementById('schedule-file-name');
  const setFile = file => { if(!file) return; const transfer = new DataTransfer(); transfer.items.add(file); fileInput.files = transfer.files; fileName.textContent = file.name; };
  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', event => { if(event.key === 'Enter' || event.key === ' ') fileInput.click(); });
  fileInput.addEventListener('change', () => setFile(fileInput.files[0]));
  ['dragenter', 'dragover'].forEach(type => dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.add('dragging'); }));
  ['dragleave', 'drop'].forEach(type => dropzone.addEventListener(type, event => { event.preventDefault(); dropzone.classList.remove('dragging'); }));
  dropzone.addEventListener('drop', event => setFile(event.dataTransfer.files[0]));
  uploadForm.addEventListener('submit', async event => {
    event.preventDefault();
    const message = document.getElementById('schedule-upload-msg');
    if(!fileInput.files[0]) { message.textContent = 'Choose a sheet first.'; return; }
    message.textContent = 'Reading schedule...';
    const response = await fetch('/api/schedule/import', {method:'POST', body:new FormData(uploadForm)});
    const result = await response.json();
    message.textContent = response.ok ? `${result.imported} test date${result.imported === 1 ? '' : 's'} saved.` : (result.error || 'Could not read the sheet.');
    if(response.ok) { uploadForm.reset(); fileName.textContent = 'No sheet selected'; loadSchedule(); }
  });
  entryForm.addEventListener('submit', async event => {
    event.preventDefault();
    const data = {title:entryForm.title.value, exam_date:entryForm.exam_date.value, exam_time:entryForm.exam_time.value, portions:entryForm.portions.value};
    const response = await fetch('/api/schedule', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(data)});
    const result = await response.json();
    document.getElementById('schedule-entry-msg').textContent = response.ok ? 'Test date saved.' : (result.error || 'Could not save test date.');
    if(response.ok) { entryForm.reset(); loadSchedule(); }
  });
  document.getElementById('send-reminders').addEventListener('click', async () => {
    const response = await fetch('/api/schedule/send-reminders', {method:'POST'});
    const result = await response.json();
    document.getElementById('schedule-reminder-msg').textContent = result.error || (result.sent ? `${result.sent} reminder sent.` : result.message);
  });
  loadSchedule();
}

async function loadSchedule(){
  const list = document.getElementById('schedule-list');
  if(!list) return;
  const events = await (await fetch('/api/schedule')).json();
  document.getElementById('schedule-count').textContent = `${events.length} upcoming entr${events.length === 1 ? 'y' : 'ies'}`;
  list.innerHTML = events.length ? events.map(event => `<article class="schedule-item"><div><h3>${event.title}</h3><p><strong>${formatDate(event.exam_date)}</strong>${event.exam_time ? ` · ${event.exam_time}` : ''}</p><p>${event.portions || 'No portions added.'}</p>${event.reminder_sent_at ? '<small>Reminder sent</small>' : ''}</div><button class="schedule-delete" data-event-id="${event.id}">Delete</button></article>`).join('') : '<p class="hint">No test dates saved yet.</p>';
  list.querySelectorAll('.schedule-delete').forEach(button => button.addEventListener('click', async () => { await fetch(`/api/schedule/${button.dataset.eventId}`, {method:'DELETE'}); loadSchedule(); }));
}

async function loadLibrary(){
  const list = document.getElementById('library-list');
  if(!list) return;
  const papers = await (await fetch('/api/library')).json();
  document.getElementById('library-count').textContent = `${papers.length} saved paper${papers.length === 1 ? '' : 's'}`;
  list.innerHTML = papers.length ? papers.map(paper => `<article class="library-paper"><div><h3>${paper.original_name}</h3><p>${paper.file_type.toUpperCase()} · ${paper.question_count || 0} questions · <strong>${paper.difficulty}</strong></p><small>Saved ${formatDate(paper.uploaded_at)}</small></div><div class="library-actions"><a href="/api/library/${paper.id}/file">Download</a><button data-paper-id="${paper.id}" class="library-delete">Delete</button></div></article>`).join('') : '<div class="panel"><p>No papers saved yet.</p></div>';
  list.querySelectorAll('.library-delete').forEach(button => button.addEventListener('click', async () => { if(!confirm('Delete this saved paper?')) return; await fetch(`/api/library/${button.dataset.paperId}`, {method:'DELETE'}); loadLibrary(); }));
}

document.addEventListener('DOMContentLoaded', ()=>{
  setupProfile();
  restoreTheme();
  setupCustomization();
  setupGraphColor();
  if(document.getElementById('enter-form')){ loadHome(); setupHome(); }
  if(document.getElementById('history-table')){ loadHistory(); }
  if(document.getElementById('goal-form')){ setupGoals(); }
  setupLibrary();
  // slide menu behavior
  const menuBtn = document.getElementById('menu-btn');
  const closeBtn = document.getElementById('menu-close');
  const side = document.getElementById('side-menu');
  if(menuBtn && side){ menuBtn.addEventListener('click',()=>side.classList.add('open')); }
  if(closeBtn && side){ closeBtn.addEventListener('click',()=>side.classList.remove('open')); }
  // menu link navigation
  document.querySelectorAll('.menu-link').forEach(b=> b.addEventListener('click', e=>{ const dest = b.dataset.href; if(dest) window.location.href = dest; }));
});
