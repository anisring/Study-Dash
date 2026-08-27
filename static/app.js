async function getTests(){
  const res = await fetch('/api/tests');
  return res.json();
}

function drawProgressChart(tests){
  const svg = document.getElementById('progress-chart');
  const msg = document.getElementById('progress-msg');
  if(!svg){ if(msg) msg.textContent='Progress chart not available.'; return; }
  while(svg.firstChild) svg.removeChild(svg.firstChild);
  if(!tests || tests.length<2){ if(msg) msg.textContent='Enter at least two tests to see your progress report.'; return; }
  msg.textContent='';
  const diffs = [];
  for(let i=1;i<tests.length;i++){ diffs.push({label:tests[i].test_name||(`T${i+1}`), value: (tests[i].total||0) - (tests[i-1].total||0)}); }
  const w = +svg.getAttribute('width'); const h = +svg.getAttribute('height'); const margin = 40; const plotW = w - margin*2; const plotH = h - margin*2;
  const axisCol = '#64748B'; const gridCol = 'rgba(255,255,255,0.04)'; const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#F8FAFC';
  // y scale
  const maxAbs = Math.max(10, Math.max(...diffs.map(d=>Math.abs(d.value))));
  function ys(v){ const mid = margin + plotH/2; return mid - (v/maxAbs)*(plotH/2); }
  function xs(i){ return margin + (i/(diffs.length-1||1))*plotW; }
  // grid horizontal lines
  for(let val=-maxAbs; val<=maxAbs; val+=Math.max(5, Math.round(maxAbs/4))){ const gy = ys(val); const g = document.createElementNS('http://www.w3.org/2000/svg','line'); g.setAttribute('x1',margin); g.setAttribute('y1',gy); g.setAttribute('x2',margin+plotW); g.setAttribute('y2',gy); g.setAttribute('stroke',gridCol); g.setAttribute('stroke-width',1); svg.appendChild(g); const lab = document.createElementNS('http://www.w3.org/2000/svg','text'); lab.setAttribute('x',8); lab.setAttribute('y',gy+4); lab.setAttribute('font-size','11'); lab.setAttribute('fill',textColor); lab.textContent = val; svg.appendChild(lab); }
  // zero line
  const zeroY = ys(0); const zeroLine = document.createElementNS('http://www.w3.org/2000/svg','line'); zeroLine.setAttribute('x1',margin); zeroLine.setAttribute('y1',zeroY); zeroLine.setAttribute('x2',margin+plotW); zeroLine.setAttribute('y2',zeroY); zeroLine.setAttribute('stroke',axisCol); zeroLine.setAttribute('stroke-width',1.5); svg.appendChild(zeroLine);
  // definite Y and X axis lines
  const yAxis = document.createElementNS('http://www.w3.org/2000/svg','line'); yAxis.setAttribute('x1',margin); yAxis.setAttribute('y1',margin); yAxis.setAttribute('x2',margin); yAxis.setAttribute('y2',margin+plotH); yAxis.setAttribute('stroke',axisCol); yAxis.setAttribute('stroke-width',1.5); svg.appendChild(yAxis);
  const xAxis = document.createElementNS('http://www.w3.org/2000/svg','line'); xAxis.setAttribute('x1',margin); xAxis.setAttribute('y1',margin+plotH); xAxis.setAttribute('x2',margin+plotW); xAxis.setAttribute('y2',margin+plotH); xAxis.setAttribute('stroke',axisCol); xAxis.setAttribute('stroke-width',1.5); svg.appendChild(xAxis);
  // x axis ticks and labels
  for(let i=0;i<diffs.length;i++){ const tx = xs(i); const tline = document.createElementNS('http://www.w3.org/2000/svg','line'); tline.setAttribute('x1',tx); tline.setAttribute('y1',margin+plotH); tline.setAttribute('x2',tx); tline.setAttribute('y2',margin+plotH+6); tline.setAttribute('stroke',axisCol); tline.setAttribute('stroke-width',1); svg.appendChild(tline); const lbl = document.createElementNS('http://www.w3.org/2000/svg','text'); lbl.setAttribute('x',tx); lbl.setAttribute('y',margin+plotH+20); lbl.setAttribute('font-size','11'); lbl.setAttribute('fill',textColor); lbl.setAttribute('text-anchor','middle'); lbl.textContent = diffs[i].label; svg.appendChild(lbl); }
  // bars/points
  for(let i=0;i<diffs.length;i++){ const v = diffs[i].value; const tx = xs(i); const ty = ys(v); const col = v>0?getComputedStyle(document.documentElement).getPropertyValue('--success').trim():'#EF4444'; const negcol = getComputedStyle(document.documentElement).getPropertyValue('--danger').trim(); const color = v>0?getComputedStyle(document.documentElement).getPropertyValue('--success').trim():getComputedStyle(document.documentElement).getPropertyValue('--danger').trim();
    // vertical bar from zero to value
    const bar = document.createElementNS('http://www.w3.org/2000/svg','line'); bar.setAttribute('x1',tx); bar.setAttribute('x2',tx); bar.setAttribute('y1',zeroY); bar.setAttribute('y2',ty); bar.setAttribute('stroke', color); bar.setAttribute('stroke-width',6); svg.appendChild(bar);
    const dot = document.createElementNS('http://www.w3.org/2000/svg','circle'); dot.setAttribute('cx',tx); dot.setAttribute('cy',ty); dot.setAttribute('r',5); dot.setAttribute('fill',color); svg.appendChild(dot);
  }
}

async function getGoals(){
  const res = await fetch('/api/goals');
  return res.json();
}

function formatLatest(tests){
  if(!tests || tests.length===0) return 'No tests recorded yet.';
  const t = tests[tests.length-1];
  return `<div>${t.test_name} — ${t.date}<br>Physics ${t.physics}/60<br>Chemistry ${t.chemistry}/60<br>Maths ${t.maths}/60<br><b>TOTAL ${t.total}/180</b></div>`;
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
  const lineColor = '#3B82F6'; // keep it blue

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
    c.addEventListener('click',()=> alert(`${tests[i].test_name}\n${tests[i].date}\nTotal: ${tests[i].total}`));
  }
}

async function loadHome(){
  const tests = await getTests();
  // populate latest test card
  if(tests && tests.length){
    const t = tests[tests.length-1];
    const meta = document.getElementById('latest-meta'); if(meta) meta.textContent = `${t.test_name} · ${t.date}`;
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
    tr.innerHTML=`<td>${g.start_date||'-'}</td><td>${g.name}</td><td>${g.target}</td><td>${score}</td><td>${diff}</td><td><span class='status ${cls}'>${status}</span></td>`;
    tbody.appendChild(tr);
  });
}

async function setupHome(){
  const form = document.getElementById('enter-form'); if(!form) return;
  form.date.value = new Date().toISOString().slice(0,10);
  // style submit button
  const submit = form.querySelector('button[type=submit]'); if(submit) submit.classList.add('btn-accent');
  // live total calculation
  const pIn = form.physics, cIn = form.chemistry, mIn = form.maths, live = document.getElementById('live-total');
  function updateLive(){ const p = parseInt(pIn.value||0)||0; const c = parseInt(cIn.value||0)||0; const m = parseInt(mIn.value||0)||0; if(live) live.textContent = `${p+c+m}`; }
  [pIn,cIn,mIn].forEach(i=>i.addEventListener('input', updateLive)); updateLive();
  form.addEventListener('submit', async e=>{
    e.preventDefault();
    const data = { date: form.date.value, test_name: form.test_name.value, physics: form.physics.value, chemistry: form.chemistry.value, maths: form.maths.value };
    const res = await fetch('/api/tests',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(data)});
    const j = await res.json(); if(res.status===201){ document.getElementById('enter-msg').textContent='Saved'; loadHome(); form.reset(); form.date.value=new Date().toISOString().slice(0,10); updateLive();} else { document.getElementById('enter-msg').textContent=j.error||'Error'; }
  });
}

async function loadHistory(){
  const tests = await getTests();
  const tbody = document.querySelector('#history-table tbody'); tbody.innerHTML='';
  tests.forEach(t=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${t.date}</td><td>${t.test_name}</td><td>${t.physics}</td><td>${t.chemistry}</td><td>${t.maths}</td><td>${t.total}</td><td><button data-id='${t.id}' class='del'>Delete</button></td>`; tbody.appendChild(tr); });
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
  analysisDiv.innerHTML = `<div class="panel"><p><strong>Overall average:</strong> ${avgTotal.toFixed(1)} / 180</p><p><strong>Subject averages:</strong> Physics ${avgP.toFixed(1)}, Chemistry ${avgC.toFixed(1)}, Maths ${avgM.toFixed(1)}</p><p><strong>Best subject (avg):</strong> ${bestSubject}</p><p><strong>Best single test:</strong> ${bestSingle.total} — ${bestSingle.name} (${bestSingle.date})</p><p><strong>Recent change:</strong> ${recentText}</p></div>`;
  // draw progress chart
  try{ drawProgressChart(all); } catch(e){ console.error('progress draw error', e); }
}

async function setupGoals(){
  const form = document.getElementById('goal-form'); if(!form) return; form.addEventListener('submit',async e=>{ e.preventDefault(); const data={ name: form.name.value, type: form.type.value, target: form.target.value, start_date: form.start_date.value||null, end_date: form.end_date.value||null, test_id: form.test_id.value||null }; const res=await fetch('/api/goals',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(data)}); if(res.status===201){ alert('Goal saved'); form.reset(); loadGoals(); } else { alert((await res.json()).error||'Error'); } }); loadGoals(); }

async function loadGoals(){ const goals = await getGoals(); const tbody=document.querySelector('#goals-list tbody'); if(!tbody) return; tbody.innerHTML=''; goals.forEach(g=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${g.name}</td><td>${g.type}</td><td>${g.target}</td><td>${g.start_date||'-'}</td><td>${g.end_date||'-'}</td>`; tbody.appendChild(tr); }); }

document.addEventListener('DOMContentLoaded', ()=>{
  if(document.getElementById('enter-form')){ loadHome(); setupHome(); }
  if(document.getElementById('history-table')){ loadHistory(); }
  if(document.getElementById('goal-form')){ setupGoals(); }
  // slide menu behavior
  const menuBtn = document.getElementById('menu-btn');
  const closeBtn = document.getElementById('menu-close');
  const side = document.getElementById('side-menu');
  if(menuBtn && side){ menuBtn.addEventListener('click',()=>side.classList.add('open')); }
  if(closeBtn && side){ closeBtn.addEventListener('click',()=>side.classList.remove('open')); }
  // menu link navigation
  document.querySelectorAll('.menu-link').forEach(b=> b.addEventListener('click', e=>{ const dest = b.dataset.href; if(dest) window.location.href = dest; }));
});
