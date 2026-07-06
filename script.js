/* ================= DATA MODEL ================= (fixes/normalizes the source class diagram)
   User        { userId, fullName, email, phoneNumber, role, createdAt }
   StreetLight { lightId, zone, x, status: on|off|fault, brightness, manual, lastMaintenance }
   Task        { taskId, lightId, assignedTo, status: pending|ongoing|completed, remarks, createdAt, resolvedAt }
   EnergyLog   { t, kWh }
================================================== */

const ZONES = [
  {key:'A', name:'Zone A — Main Street', onHour:18*60, offHour:6*60},
  {key:'B', name:'Zone B — Park Avenue', onHour:18*60+30, offHour:5*60+45},
  {key:'C', name:'Zone C — Riverside Road', onHour:17*60+45, offHour:6*60+15},
];
const STAFF = ['R. Karki','S. Thapa','B. Gurung'];

let lights = [];
(function seed(){
  let n=1;
  ZONES.forEach(z=>{
    for(let i=0;i<4;i++){
      lights.push({
        lightId:'SL-'+String(n).padStart(3,'0'), zone:z.key,
        status:'off', brightness:70, manual:false, lastMaintenance:null, motion:false
      });
      n++;
    }
  });
})();

let tasks = [];
let taskSeq = 1;
let energyLog = []; // {t,kWh}
let selectedLightId = null;
let currentUser = null; // {name,email,phone,role}
let clockMinutes = 18*60; // 0-1439
let playing = false;
let playTimer = null;

/* ================= HELPERS ================= */
function fmtTime(mins){
  mins = ((mins%1440)+1440)%1440;
  let h = Math.floor(mins/60), m = Math.floor(mins%60);
  return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');
}
function zoneOf(id){ return ZONES.find(z=>z.key===id); }
function inWindow(now,on,off){
  if(on>off) return now>=on || now<off; // wraps midnight
  return now>=on && now<off;
}
function isNightFor(light){
  const z = zoneOf(light.zone);
  return inWindow(clockMinutes, z.onHour, z.offHour);
}
function scheduleLabel(){
  const h = Math.floor(clockMinutes/60);
  if(h>=5 && h<7) return 'Dawn · sensor easing lights off';
  if(h>=7 && h<17) return 'Daylight · lights off';
  if(h>=17 && h<19) return 'Dusk · lights coming on';
  return 'Night · lights on';
}

/* ================= SIMULATION TICK ================= */
function applyAutomation(){
  lights.forEach(l=>{
    if(l.status==='fault' || l.manual) return;
    l.status = isNightFor(l) ? 'on' : 'off';
  });
}
function maybeMotion(){
  const onLights = lights.filter(l=>l.status==='on');
  onLights.forEach(l=> l.motion=false);
  if(onLights.length && Math.random()<0.25){
    const pick = onLights[Math.floor(Math.random()*onLights.length)];
    pick.motion = true;
    pushFeed(`Motion detected near ${pick.lightId} (${zoneOf(pick.zone).name}) — brightness boosted.`,'motion');
  }
}
function maybeFault(){
  const candidates = lights.filter(l=>l.status!=='fault');
  if(candidates.length && Math.random()<0.06){
    const pick = candidates[Math.floor(Math.random()*candidates.length)];
    pick.status='fault'; pick.manual=false;
    const t = {taskId:'MT-'+String(taskSeq++).padStart(3,'0'), lightId:pick.lightId, assignedTo:null, status:'pending', remarks:'', createdAt:fmtTime(clockMinutes), resolvedAt:null};
    tasks.unshift(t);
    pushFeed(`Fault detected on ${pick.lightId} (${zoneOf(pick.zone).name}). Maintenance task ${t.taskId} created.`,'fault');
  }
}
function reportFault(lightId){
  const l = lights.find(x=>x.lightId===lightId);
  if(!l || l.status==='fault') return;
  l.status='fault'; l.manual=false;
  const t = {taskId:'MT-'+String(taskSeq++).padStart(3,'0'), lightId:l.lightId, assignedTo:null, status:'pending', remarks:'', createdAt:fmtTime(clockMinutes), resolvedAt:null};
  tasks.unshift(t);
  pushFeed(`Fault reported on ${l.lightId} (${zoneOf(l.zone).name}). Maintenance task ${t.taskId} created.`,'fault');
  renderAll();
}
function logEnergy(){
  const kWh = lights.reduce((s,l)=> s + (l.status==='on' ? (l.brightness/100)*0.4 : 0.01), 0);
  energyLog.push({t:fmtTime(clockMinutes), kWh:+kWh.toFixed(2)});
  if(energyLog.length>16) energyLog.shift();
}
let feed = [];
function pushFeed(msg,type){
  feed.unshift({msg,type,time:fmtTime(clockMinutes)});
  if(feed.length>12) feed.pop();
}

function tick(){
  applyAutomation();
  maybeMotion();
  maybeFault();
  logEnergy();
  renderAll();
}

/* ================= RENDER: MAP ================= */
function renderMap(targetId, onlyFaults){
  const root = document.getElementById(targetId);
  root.innerHTML='';
  ZONES.forEach(z=>{
    const zLights = lights.filter(l=>l.zone===z.key && (!onlyFaults || l.status==='fault'));
    if(onlyFaults && zLights.length===0) return;
    const row = document.createElement('div'); row.className='zone-row';
    row.innerHTML = `<div class="zone-title"><span>${z.name}</span><span>${fmtTime(z.onHour)}–${fmtTime(z.offHour)}</span></div>`;
    const line = document.createElement('div'); line.className='street-line';
    (onlyFaults?zLights:lights.filter(l=>l.zone===z.key)).forEach(l=>{
      const btn = document.createElement('button');
      btn.className = 'pole '+l.status+(l.motion&&l.status==='on'?' motion':'')+(l.lightId===selectedLightId?' selected':'');
      btn.innerHTML = `<span class="bulb"></span><span class="stem"></span><span class="id">${l.lightId}</span>`;
      btn.onclick = ()=>{ selectedLightId=l.lightId; showTab(activeAdminTabIsLights()?'lights':currentTab); renderAll(); };
      line.appendChild(btn);
    });
    row.appendChild(line);
    root.appendChild(row);
  });
  if(onlyFaults && root.innerHTML==='') root.innerHTML = '<p class="detail-empty">No active faults. The network is fully operational.</p>';
}
function activeAdminTabIsLights(){ return currentTab==='lights' || currentTab==='overview'; }

/* ================= RENDER: STATS ================= */
function renderStats(){
  document.getElementById('stat-on').textContent = lights.filter(l=>l.status==='on').length;
  document.getElementById('stat-fault').textContent = lights.filter(l=>l.status==='fault').length;
  const last = energyLog[energyLog.length-1];
  document.getElementById('stat-energy').textContent = (last?last.kWh:0)+' kWh';
  document.getElementById('clock-time').textContent = fmtTime(clockMinutes);
  document.getElementById('clock-phase').textContent = scheduleLabel();
}

/* ================= RENDER: LIGHTS TABLE + DETAIL ================= */
function renderLightsTable(){
  const tb = document.getElementById('lights-tbody');
  tb.innerHTML = lights.map(l=>`
    <tr>
      <td style="font-family:var(--mono)">${l.lightId}</td>
      <td>${zoneOf(l.zone).name.split('—')[1].trim()}</td>
      <td><span class="badge ${l.status}">${l.status}</span></td>
      <td>${l.status==='fault'?'—':l.brightness+'%'}</td>
      <td style="color:var(--fog);font-size:.78rem;">${l.manual?'Manual':'Auto'}</td>
      <td><button class="mini-btn" data-select="${l.lightId}">Control</button></td>
    </tr>`).join('');
  tb.querySelectorAll('[data-select]').forEach(b=> b.onclick=()=>{ selectedLightId=b.dataset.select; renderDetail(); renderMap('city-map'); document.querySelectorAll('#lights-tbody tr').forEach(r=>r.style.background=''); });
  renderDetail();
}
function renderDetail(){
  const root = document.getElementById('light-detail');
  const l = lights.find(x=>x.lightId===selectedLightId);
  if(!l){ root.innerHTML='<p class="detail-empty">Select a light from the map or table to control it.</p>'; return; }
  root.innerHTML = `
    <div class="detail">
      <h3>${l.lightId}</h3>
      <p class="loc">${zoneOf(l.zone).name} · ${l.manual?'manual override active':'automatic (daylight schedule)'}</p>
      <div class="row-flex"><span>Power</span></div>
      <div class="toggle-pair" style="margin-bottom:16px;">
        <button class="tg ${l.status==='on'?'active-on':''}" id="det-on">Turn on</button>
        <button class="tg ${l.status==='off'?'active-off':''}" id="det-off">Turn off</button>
      </div>
      <div class="row-flex"><span>Brightness</span><span class="slider-val" id="det-bval">${l.brightness}%</span></div>
      <input type="range" min="10" max="100" step="5" value="${l.brightness}" id="det-brightness" ${l.status==='fault'?'disabled':''}>
      ${l.status==='fault' ? '<p class="hint" style="margin-top:14px;color:var(--fault);">This light is reporting a fault and cannot be controlled remotely. A maintenance task has been logged.</p>' : `<button class="mini-btn danger" id="det-report-fault" style="margin-top:16px;">Report fault</button>`}
      <button class="mini-btn" id="det-reset" style="margin-top:16px;">Reset to automatic schedule</button>
    </div>`;
  document.getElementById('det-on').onclick=()=>{ if(l.status!=='fault'){l.status='on'; l.manual=true; renderAll();} };
  document.getElementById('det-off').onclick=()=>{ if(l.status!=='fault'){l.status='off'; l.manual=true; renderAll();} };
  document.getElementById('det-brightness').oninput=(e)=>{ l.brightness=+e.target.value; document.getElementById('det-bval').textContent=l.brightness+'%'; };
  document.getElementById('det-reset').onclick=()=>{ l.manual=false; renderAll(); };
  if(document.getElementById('det-report-fault')){
    document.getElementById('det-report-fault').onclick=()=> reportFault(l.lightId);
  }
}

/* ================= RENDER: SCHEDULE ================= */
function renderSchedule(){
  const root = document.getElementById('schedule-list');
  root.innerHTML = ZONES.map((z,i)=>`
    <div class="form-grid" style="margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid var(--line);">
      <div><label>${z.name} — turn on at</label><input type="time" data-zone="${i}" data-field="onHour" value="${fmtTime(z.onHour)}"></div>
      <div><label>${z.name} — turn off at</label><input type="time" data-zone="${i}" data-field="offHour" value="${fmtTime(z.offHour)}"></div>
    </div>`).join('');
  root.querySelectorAll('input[type=time]').forEach(inp=>{
    inp.onchange=(e)=>{
      const [h,m] = e.target.value.split(':').map(Number);
      ZONES[+e.target.dataset.zone][e.target.dataset.field] = h*60+m;
      renderAll();
    };
  });
}

/* ================= RENDER: MAINTENANCE FEED + ASSIGN ================= */
function renderFeedAndAssign(){
  const feedRoot = document.getElementById('alert-feed');
  feedRoot.innerHTML = feed.length ? feed.map(f=>`<div class="feed-item ${f.type}">${f.msg}<time>${f.time}</time></div>`).join('') : '<p class="feed-empty">No alerts yet — this feed updates as the city clock advances.</p>';

  const openTasks = tasks.filter(t=>t.status==='pending');
  const countEl = document.getElementById('assign-count');
  if(countEl) countEl.textContent = openTasks.length;
  const assignRoot = document.getElementById('assign-list');
  assignRoot.innerHTML = openTasks.length ? openTasks.map(t=>`
    <div class="row-flex" style="border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:10px;">
      <div><strong style="font-family:var(--mono);font-size:.85rem;">${t.taskId}</strong><br><span style="color:var(--fog);font-size:.78rem;">${t.lightId} · ${zoneOf(lights.find(l=>l.lightId===t.lightId).zone).name}</span></div>
      <select data-assign="${t.taskId}" style="width:auto;"><option value="">Assign to…</option>${STAFF.map(s=>`<option value="${s}">${s}</option>`).join('')}</select>
    </div>`).join('') : '<p class="feed-empty">No open faults awaiting assignment.</p>';
  assignRoot.querySelectorAll('[data-assign]').forEach(sel=>{
    sel.onchange=(e)=>{
      if(!e.target.value) return;
      const t = tasks.find(x=>x.taskId===e.target.dataset.assign);
      t.assignedTo = e.target.value; t.status='ongoing';
      pushFeed(`${t.taskId} (${t.lightId}) assigned to ${t.assignedTo}.`,'motion');
      renderAll();
    };
  });
}

/* ================= RENDER: REPORTS / ENERGY ================= */
let chart;
function renderEnergyChart(){
  const ctx = document.getElementById('energy-chart');
  const labels = energyLog.map(e=>e.t);
  const data = energyLog.map(e=>e.kWh);
  if(!chart){
    chart = new Chart(ctx, {
      type:'line',
      data:{ labels, datasets:[{ label:'kWh', data, borderColor:'#5EEAD4', backgroundColor:'rgba(94,234,212,0.12)', fill:true, tension:.35, pointRadius:0, borderWidth:2 }]},
      options:{ responsive:true, plugins:{legend:{display:false}}, scales:{ x:{ ticks:{color:'#7C8AA5',font:{family:'IBM Plex Mono',size:10}}, grid:{color:'#1e2740'} }, y:{ ticks:{color:'#7C8AA5',font:{family:'IBM Plex Mono',size:10}}, grid:{color:'#1e2740'} } } }
    });
  } else {
    chart.data.labels = labels; chart.data.datasets[0].data = data; chart.update();
  }
}
function generateReport(){
  const totalOn = lights.filter(l=>l.status==='on').length;
  const totalFault = lights.filter(l=>l.status==='fault').length;
  const avgKwh = energyLog.length ? (energyLog.reduce((s,e)=>s+e.kWh,0)/energyLog.length).toFixed(2) : '0.00';
  const completed = tasks.filter(t=>t.status==='completed').length;
  document.getElementById('report-output').innerHTML = `
    <div class="panel" style="background:var(--panel-2);">
      <p style="margin:0 0 6px;font-family:var(--mono);color:var(--cyan);">Report generated at ${fmtTime(clockMinutes)}</p>
      <p style="margin:4px 0;">Lights currently active: <strong>${totalOn}</strong> / ${lights.length}</p>
      <p style="margin:4px 0;">Open faults: <strong>${totalFault}</strong></p>
      <p style="margin:4px 0;">Average grid draw: <strong>${avgKwh} kWh</strong> per sample</p>
      <p style="margin:4px 0;">Maintenance tasks completed to date: <strong>${completed}</strong></p>
    </div>`;
}

/* ================= RENDER: TASKS (maintenance staff) ================= */
let taskFilter='pending';
function renderTasks(){
  const tb = document.getElementById('tasks-tbody');
  const list = tasks.filter(t=>t.status===taskFilter);
  tb.innerHTML = list.length ? list.map(t=>`
    <tr>
      <td style="font-family:var(--mono)">${t.taskId}</td>
      <td>${t.lightId}</td>
      <td>${zoneOf(lights.find(l=>l.lightId===t.lightId).zone).name.split('—')[1].trim()}</td>
      <td style="font-family:var(--mono);font-size:.78rem;">${t.createdAt}</td>
      <td><span class="badge ${t.status}">${t.status}</span></td>
      <td>${t.status!=='completed' ? `<button class="mini-btn" data-update="${t.taskId}">Update</button>` : ''}</td>
    </tr>`).join('') : `<tr><td colspan="6" class="feed-empty">No ${taskFilter} tasks.</td></tr>`;
  tb.querySelectorAll('[data-update]').forEach(b=> b.onclick=()=>{ showTab('updaterepair'); renderRepairForm(b.dataset.update); });
}
function renderRepairForm(taskId){
  const t = tasks.find(x=>x.taskId===taskId);
  const root = document.getElementById('repair-form');
  root.innerHTML = `
    <p class="loc">${t.taskId} · ${t.lightId} · reported ${t.createdAt}</p>
    <label>Repair status</label>
    <select id="rp-status">
      <option value="ongoing" ${t.status==='ongoing'?'selected':''}>Ongoing</option>
      <option value="completed">Completed</option>
    </select>
    <label>Remarks</label>
    <textarea id="rp-remarks" rows="4" placeholder="Describe the fault and repair work...">${t.remarks}</textarea>
    <button class="mini-btn" id="rp-save" style="margin-top:14px;">Save update</button>`;
  document.getElementById('rp-save').onclick=()=>{
    t.status = document.getElementById('rp-status').value;
    t.remarks = document.getElementById('rp-remarks').value;
    if(t.status==='completed'){
      t.resolvedAt = fmtTime(clockMinutes);
      const light = lights.find(l=>l.lightId===t.lightId);
      light.status='off'; light.manual=false;
      pushFeed(`${t.taskId} (${t.lightId}) marked completed by ${t.assignedTo||'maintenance staff'}.`,'motion');
    }
    showTab('tasks'); renderAll();
  };
}

/* ================= RENDER: HISTORY ================= */
function renderHistory(){
  const tb = document.getElementById('history-tbody');
  const done = tasks.filter(t=>t.status==='completed');
  tb.innerHTML = done.length ? done.map(t=>`
    <tr><td style="font-family:var(--mono)">${t.taskId}</td><td>${t.lightId}</td><td style="font-family:var(--mono);font-size:.78rem;">${t.resolvedAt}</td><td>${t.remarks||'—'}</td></tr>
  `).join('') : `<tr><td colspan="4" class="feed-empty">No completed maintenance yet.</td></tr>`;
}

/* ================= RENDER ALL ================= */
function renderAll(){
  renderStats();
  renderMap('city-map', false);
  renderFeedAndAssign();
  renderEnergyChart();
  renderLightsTable();
  if(document.getElementById('tab-tasks').classList.contains('active')) renderTasks();
  if(document.getElementById('tab-faultmap').classList.contains('active')) renderMap('fault-map', true);
  if(document.getElementById('tab-schedule').classList.contains('active')) renderSchedule();
  if(document.getElementById('tab-history').classList.contains('active')) renderHistory();
}

/* ================= NAV / TABS ================= */
const NAV = {
  admin:[
    {tab:'overview', label:'Overview', ic:'◆'},
    {tab:'lights', label:'Street Lights', ic:'◈'},
    {tab:'schedule', label:'Schedule', ic:'◷'},
    {tab:'maintenance', label:'Maintenance', ic:'!'},
    {tab:'reports', label:'Reports & Energy', ic:'▤'},
    {tab:'profile', label:'Profile', ic:'●'},
  ],
  maintenance:[
    {tab:'tasks', label:'Maintenance Status', ic:'◆'},
    {tab:'faultmap', label:'Fault Location', ic:'◈'},
    {tab:'history', label:'History', ic:'▤'},
    {tab:'profile', label:'Profile', ic:'●'},
  ]
};
let currentTab='overview';
function buildNav(role){
  const root = document.getElementById('nav-container');
  root.innerHTML = NAV[role].map(item=>`<button class="navbtn" data-tab="${item.tab}"><span class="ic">${item.ic}</span><span class="label">${item.label}</span></button>`).join('');
  root.querySelectorAll('.navbtn').forEach(b=> b.onclick=()=> showTab(b.dataset.tab));
}
const TITLES = {
  overview:['Overview','Real-time status of the city lighting network.'],
  lights:['Street Lights','Remotely control power and brightness for every light.'],
  schedule:['Schedule','Automatic on/off windows per zone.'],
  maintenance:['Maintenance','Fault alerts and task assignment.'],
  reports:['Reports & Energy','Consumption tracking and generated summaries.'],
  tasks:['Maintenance Status','Faults assigned to the maintenance team.'],
  faultmap:['Fault Location','Where active faults are on the network.'],
  updaterepair:['Update Repair Status','Log completed or ongoing repair work.'],
  history:['Maintenance History','Past repairs and remarks.'],
  profile:['My Profile','Update your account details.'],
};
function showTab(tab){
  currentTab = tab;
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.getElementById('tab-'+tab).classList.add('active');
  document.querySelectorAll('.navbtn').forEach(b=>b.classList.toggle('active', b.dataset.tab===tab));
  document.getElementById('page-title').textContent = TITLES[tab][0];
  document.getElementById('page-sub').textContent = TITLES[tab][1];
  renderAll();
  if(tab==='tasks'){
    document.querySelectorAll('#task-tabs .tab-btn').forEach(b=>b.classList.toggle('active', b.dataset.status===taskFilter));
  }
}

/* ================= LOGIN FLOW ================= */
let chosenRole = 'admin';
document.querySelectorAll('.role-btn').forEach(b=>{
  b.onclick=()=>{ document.querySelectorAll('.role-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active'); chosenRole=b.dataset.role;
    document.getElementById('li-user').value = chosenRole==='admin' ? 'admin':'maintenance';
  };
});
document.getElementById('btn-login').onclick=()=>{
  const uname = document.getElementById('li-user').value || (chosenRole==='admin'?'Admin':'Staff');
  currentUser = {
    name: chosenRole==='admin' ? 'City Admin' : 'Maintenance Staff',
    email: uname.toLowerCase()+'@lumen-city.gov',
    phone:'+977-98-0000-0000',
    role: chosenRole
  };
  document.getElementById('screen-login').style.display='none';
  document.getElementById('app').style.display='block';
  document.getElementById('who-name').textContent = currentUser.name;
  document.getElementById('who-role').textContent = chosenRole==='admin' ? 'Administrator' : 'Maintenance Staff';
  document.getElementById('who-initial').textContent = currentUser.name[0];
  document.getElementById('pf-name').value = currentUser.name;
  document.getElementById('pf-email').value = currentUser.email;
  document.getElementById('pf-phone').value = currentUser.phone;
  buildNav(chosenRole);
  showTab(NAV[chosenRole][0].tab);
  tick();
};
document.getElementById('btn-logout').onclick=()=>{
  clearInterval(playTimer); playing=false;
  document.getElementById('app').style.display='none';
  document.getElementById('screen-login').style.display='flex';
};

/* ================= PROFILE ================= */
document.getElementById('btn-save-profile').onclick=()=>{
  currentUser.name=document.getElementById('pf-name').value;
  currentUser.email=document.getElementById('pf-email').value;
  currentUser.phone=document.getElementById('pf-phone').value;
  document.getElementById('who-name').textContent=currentUser.name;
  document.getElementById('who-initial').textContent=currentUser.name[0]||'?';
  const s = document.getElementById('pf-saved'); s.style.display='block';
  setTimeout(()=> s.style.display='none', 2000);
};

/* ================= REPORT BTN ================= */
document.getElementById('btn-generate-report').onclick=generateReport;

/* ================= TASK FILTER TABS ================= */
document.querySelectorAll('#task-tabs .tab-btn').forEach(b=>{
  b.onclick=()=>{ taskFilter=b.dataset.status; document.querySelectorAll('#task-tabs .tab-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active'); renderTasks(); };
});

/* ================= CLOCK ================= */
const slider = document.getElementById('clock-slider');
slider.oninput=(e)=>{ clockMinutes=+e.target.value; tick(); };
document.getElementById('btn-play').onclick=(e)=>{
  playing=!playing;
  e.target.classList.toggle('on',playing);
  e.target.textContent = playing ? '❙❙ Pause simulation' : '▶ Simulate day cycle';
  if(playing){
    playTimer=setInterval(()=>{
      clockMinutes=(clockMinutes+15)%1440;
      slider.value=clockMinutes;
      tick();
    },700);
  } else clearInterval(playTimer);
};

/* seed a little history so the maintenance views aren't empty on first login */
(function seedHistory(){
  tasks.push({taskId:'MT-000', lightId:'SL-005', assignedTo:'S. Thapa', status:'completed', remarks:'Replaced blown LED driver.', createdAt:'21:10', resolvedAt:'09:40'});
})();