<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
<style>
  :root {
    --bg:       #0a0e1a;
    --surface:  #111827;
    --card:     #1a2235;
    --border:   #1e2d45;
    --accent:   #3b82f6;
    --green:    #22c55e;
    --red:      #ef4444;
    --yellow:   #f59e0b;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --win:      #60a5fa;
    --lx:       #a3e635;
    --snmp:     #c084fc;
    --font:     'Courier New', monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font); min-height: 100vh; }

  /* Header */
  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .logo { display: flex; align-items: center; gap: 12px; }
  .logo-icon { font-size: 28px; }
  .logo-text { font-size: 20px; font-weight: bold; letter-spacing: 2px; color: var(--accent); }
  .header-time { color: var(--muted); font-size: 13px; }

  /* Summary bar */
  .summary-bar {
    display: flex;
    gap: 16px;
    padding: 16px 24px;
    overflow-x: auto;
  }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 24px;
    min-width: 160px;
    text-align: center;
    flex-shrink: 0;
  }
  .stat-value { font-size: 36px; font-weight: bold; line-height: 1; }
  .stat-label { font-size: 11px; color: var(--muted); margin-top: 6px; text-transform: uppercase; letter-spacing: 1px; }

  /* Main grid */
  .main { padding: 0 24px 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 900px) { .main { grid-template-columns: 1fr; } }

  .section-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--muted);
    padding: 8px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

  .agent-grid { display: flex; flex-direction: column; gap: 8px; }
  .agent-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    align-items: center;
    transition: border-color 0.2s;
  }
  .agent-card:hover { border-color: var(--accent); }
  .agent-card.offline { opacity: 0.5; }

  .status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .status-dot.online  { background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
  .status-dot.offline { background: var(--red); }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
  }

  .agent-info .hostname { font-size: 14px; font-weight: bold; }
  .agent-info .details  { font-size: 11px; color: var(--muted); margin-top: 3px; }

  .agent-metrics { display: flex; gap: 12px; text-align: right; }
  .metric { }
  .metric-val  { font-size: 16px; font-weight: bold; }
  .metric-name { font-size: 10px; color: var(--muted); text-transform: uppercase; }
  .metric-val.high { color: var(--red); }
  .metric-val.med  { color: var(--yellow); }
  .metric-val.ok   { color: var(--green); }

  .os-badge {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: bold;
    letter-spacing: 1px;
  }
  .os-badge.windows { background: rgba(96,165,250,0.15); color: var(--win); border: 1px solid var(--win); }
  .os-badge.linux   { background: rgba(163,230,53,0.15);  color: var(--lx);  border: 1px solid var(--lx); }

  .roles { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; }
  .role-tag {
    font-size: 9px;
    padding: 1px 6px;
    border-radius: 3px;
    background: rgba(59,130,246,0.15);
    color: var(--accent);
    border: 1px solid rgba(59,130,246,0.3);
  }

  /* SNMP section */
  .snmp-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    align-items: center;
  }
  .snmp-card:hover { border-color: var(--snmp); }
  .snmp-ip { font-size: 13px; color: var(--snmp); font-weight: bold; }
  .snmp-desc { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .snmp-stats { text-align: right; font-size: 11px; color: var(--muted); }

  /* Empty state */
  .empty { text-align: center; padding: 48px; color: var(--muted); font-size: 14px; }

  /* Scrollable panels */
  .panel { max-height: 600px; overflow-y: auto; }
  .panel::-webkit-scrollbar { width: 4px; }
  .panel::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .refresh-indicator {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    display: inline-block;
    margin-right: 6px;
    animation: pulse 1s infinite;
  }
</style>
</head>
<body>

<div class="header">
  <div class="logo">
    <span class="logo-icon">🛡️</span>
    <span class="logo-text">NETBOT</span>
  </div>
  <div class="header-time">
    <span class="refresh-indicator"></span>
    <span id="clock">Loading...</span> · Live
  </div>
</div>

<div class="summary-bar">
  <div class="stat-card">
    <div class="stat-value" id="stat-total" style="color:var(--accent)">0</div>
    <div class="stat-label">Total Agents</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="stat-online" style="color:var(--green)">0</div>
    <div class="stat-label">Online</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="stat-windows" style="color:var(--win)">0</div>
    <div class="stat-label">Windows</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="stat-linux" style="color:var(--lx)">0</div>
    <div class="stat-label">Linux</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="stat-snmp" style="color:var(--snmp)">0</div>
    <div class="stat-label">SNMP Devices</div>
  </div>
</div>

<div class="main">
  <div>
    <div class="section-title">🖥️ Servers & Agents</div>
    <div class="agent-grid panel" id="agent-list">
      <div class="empty">Waiting for agents...</div>
    </div>
  </div>
  <div>
    <div class="section-title">📡 SNMP Devices</div>
    <div class="agent-grid panel" id="snmp-list">
      <div class="empty">No SNMP devices discovered yet</div>
    </div>
  </div>
</div>

<script>
const socket = io();

function metricClass(val) {
  if (val >= 90) return 'high';
  if (val >= 70) return 'med';
  return 'ok';
}

function renderAgents(agents) {
  const el = document.getElementById('agent-list');
  if (!agents || agents.length === 0) {
    el.innerHTML = '<div class="empty">No agents discovered yet.<br>Deploy an agent on your servers to get started.</div>';
    return;
  }
  agents.sort((a,b) => (a.status === 'online' ? -1 : 1));
  el.innerHTML = agents.map(a => {
    const cpu    = parseFloat(a.cpu || 0).toFixed(0);
    const mem    = parseFloat(a.memory || 0).toFixed(0);
    const disk   = parseFloat(a.disk || 0).toFixed(0);
    const online = a.status === 'online';
    const roles  = (a.roles || []).map(r => `<span class="role-tag">${r}</span>`).join('');
    return `
      <div class="agent-card ${online ? '' : 'offline'}">
        <div class="status-dot ${a.status || 'offline'}"></div>
        <div class="agent-info">
          <div class="hostname">
            ${a.hostname || a.ip || 'Unknown'}
            <span class="os-badge ${a.os || 'unknown'}" style="margin-left:8px">${(a.os||'?').toUpperCase()}</span>
          </div>
          <div class="details">${a.ip || ''} ${a.uptime ? '· up ' + a.uptime : ''}</div>
          <div class="roles">${roles}</div>
        </div>
        <div class="agent-metrics">
          <div class="metric">
            <div class="metric-val ${metricClass(cpu)}">${cpu}%</div>
            <div class="metric-name">CPU</div>
          </div>
          <div class="metric">
            <div class="metric-val ${metricClass(mem)}">${mem}%</div>
            <div class="metric-name">MEM</div>
          </div>
          <div class="metric">
            <div class="metric-val ${metricClass(disk)}">${disk}%</div>
            <div class="metric-name">DISK</div>
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderSNMP(devices) {
  const el = document.getElementById('snmp-list');
  if (!devices || devices.length === 0) {
    el.innerHTML = '<div class="empty">No SNMP devices discovered.<br>Make sure SNMP is enabled on your network devices.</div>';
    return;
  }
  el.innerHTML = devices.map(d => `
    <div class="snmp-card">
      <div>
        <div class="snmp-ip">${d.ip || 'Unknown'}</div>
        <div class="snmp-desc">${(d.description || 'Unknown device').substring(0,60)}</div>
        <div class="snmp-desc">Uptime: ${d.uptime || '?'}</div>
      </div>
      <div class="snmp-stats">
        ↓ ${d.if_in || '?'}<br>
        ↑ ${d.if_out || '?'}<br>
        <span style="color:${d.status==='online'?'var(--green)':'var(--red)'}">${d.status || '?'}</span>
      </div>
    </div>`).join('');
}

function updateSummary(agents, snmp) {
  document.getElementById('stat-total').textContent   = agents.length;
  document.getElementById('stat-online').textContent  = agents.filter(a => a.status === 'online').length;
  document.getElementById('stat-windows').textContent = agents.filter(a => a.os === 'windows').length;
  document.getElementById('stat-linux').textContent   = agents.filter(a => a.os === 'linux').length;
  document.getElementById('stat-snmp').textContent    = snmp.length;
}

let _agents = [], _snmp = [];

socket.on('agents_update', data => {
  _agents = data.agents || [];
  renderAgents(_agents);
  updateSummary(_agents, _snmp);
});

socket.on('snmp_update', data => {
  _snmp = data.devices || [];
  renderSNMP(_snmp);
  updateSummary(_agents, _snmp);
});

// Clock
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toUTCString().slice(0, 25);
}, 1000);

// Also poll REST for initial load
fetch('/api/agents').then(r => r.json()).then(renderAgents);
fetch('/api/snmp').then(r => r.json()).then(renderSNMP);
fetch('/api/summary').then(r => r.json()).then(s => {
  document.getElementById('stat-total').textContent   = s.total_agents;
  document.getElementById('stat-online').textContent  = s.online_agents;
  document.getElementById('stat-windows').textContent = s.windows_agents;
  document.getElementById('stat-linux').textContent   = s.linux_agents;
  document.getElementById('stat-snmp').textContent    = s.snmp_devices;
});
</script>
</body>
</html>
