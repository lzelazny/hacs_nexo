/* Nexo connection overview, command controls and latest init JSON. */
class NexoInspector extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
    this.rows = [];
    this.selected = new URLSearchParams(window.location.search).get("config_entry") || "";
    this.filter = "";
    this.busy = false;
  }
  set hass(value) {
    this._hass = value;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = value;
  }
  connectedCallback() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {display:block;color:var(--primary-text-color);background:var(--primary-background-color);height:100%;overflow:auto;font:14px system-ui}
        header {display:flex;align-items:center;gap:16px;padding:16px 24px;background:var(--app-header-background-color);color:var(--app-header-text-color)}
        .section {margin:16px 0;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:12px}
        .section > summary {font:600 17px system-ui;padding:18px;cursor:pointer}
        .body {padding:0 20px 20px} .stats {display:flex;flex-wrap:wrap;gap:12px;margin-top:16px}
        .stat {padding:12px;background:var(--secondary-background-color,#f3f5f7);border-radius:8px;min-width:130px}
        .stat strong {display:block;font-size:24px;margin-top:6px} #types {line-height:1.8;margin-top:12px}
        textarea {box-sizing:border-box;width:100%;min-height:72px;font:inherit;color:inherit;background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:8px;padding:10px}
        label {line-height:1.8} #command-status, #save-status {min-height:22px;white-space:pre-wrap}
        h1 {font-size:20px;margin:0} main {max-width:1100px;margin:auto;padding:24px}
        .tools {display:flex;gap:12px;flex-wrap:wrap;margin:20px 0;align-items:center}
        button, input, select {font:inherit;padding:10px;border-radius:8px;border:1px solid var(--divider-color);color:inherit;background:var(--card-background-color)}
        button {cursor:pointer} input {flex:1;min-width:180px} #meta {line-height:1.8;white-space:pre-line}
        #tree {background:var(--card-background-color);padding:20px;border-radius:12px;overflow:auto;font:13px ui-monospace,monospace}
        #tree details {margin-left:16px} #tree summary {cursor:pointer;padding:4px} .leaf {padding:4px 0 4px 16px;white-space:pre-wrap;overflow-wrap:anywhere}
        #error {color:var(--error-color)} a {color:var(--primary-color)}
      </style>
      <header><ha-menu-button></ha-menu-button><h1>Nexo</h1></header>
      <main><a href="/config/integrations/integration/nexo">Back to Nexo integration</a>
      <div id="error" role="status"></div>
      <details class="section" open><summary>1. General Information</summary><div class="body">
        <div id="meta">Waiting for initial data…</div><div class="stats" id="stats"></div><div id="types"></div>
      </div></details>
      <details class="section" open><summary>2. Send command</summary><div class="body">
        <label for="command">Choose a known command or enter a command name</label>
        <form id="send-form" class="tools"><input id="command" list="known-commands" autocomplete="off" placeholder="Command name" aria-label="Command name" required><datalist id="known-commands"></datalist><button id="send" type="submit">Send command</button></form>
        <div id="command-status" role="status"></div>
        <label for="manual-commands">Saved command names (comma separated)</label>
        <textarea id="manual-commands" placeholder="open gate, close gate"></textarea>
        <div class="tools"><button id="save-commands">Save command names</button><span>Saving updates command button entities and reloads this bridge.</span></div>
        <div id="save-status" role="status"></div>
      </div></details>
      <details class="section"><summary>3. Inspect Init JSON</summary><div class="body">
        <div class="tools"><button id="copy">Copy JSON</button><button id="download">Download JSON</button>
        <button id="expand">Expand all</button><button id="collapse">Collapse all</button>
        <input id="search" type="search" placeholder="Search keys or values" aria-label="Search JSON"></div>
        <div id="tree"></div>
      </div></details></main>`;
    this.shadowRoot.querySelector("ha-menu-button").hass = this._hass;
    this.el("send-form").onsubmit = e => { e.preventDefault(); this.sendCommand(); };
    this.el("save-commands").onclick = () => this.saveCommands();
    this.el("search").oninput = e => { this.filter = e.target.value.toLowerCase(); this.renderTree(); };
    this.el("copy").onclick = async () => {
      try { await navigator.clipboard.writeText(JSON.stringify(this.row().initial_data, null, 2)); this.el("error").textContent = "JSON copied."; }
      catch { this.el("error").textContent = "Copy failed. Use Download JSON instead."; }
    };
    this.el("download").onclick = () => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(this.row().initial_data, null, 2)], {type:"application/json"}));
      const link = document.createElement("a"); link.href = url; link.download = `nexo-init-${this.selected}.json`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    for (const [id, open] of [["expand", true], ["collapse", false]]) this.el(id).onclick = () => this.el("tree").querySelectorAll("details").forEach(d => d.open = open);
    this.render();
    this.load();
    this.timer = setInterval(() => this.load(), 3000);
  }
  disconnectedCallback() { clearInterval(this.timer); }
  el(id) { return this.shadowRoot.getElementById(id); }
  row() { return this.rows.find(r => r.entry_id === this.selected); }
  async load() {
    if (!this._hass || this.busy) return;
    this.busy = true;
    try {
      const rows = await this._hass.callWS({type:"nexo/initial_data"});
      if (!this.isConnected) return;
      this.el("error").textContent = "";
      const changed = JSON.stringify(rows) !== JSON.stringify(this.rows);
      this.rows = rows;
      if (!this.selected) this.selected = rows[0]?.entry_id || "";
      if (changed) this.render();
    } catch (e) { if (this.isConnected) this.el("error").textContent = `Unable to refresh: ${e.message || e}. Retrying…`; }
    finally { this.busy = false; }
  }
  render() {
    const row = this.row();
    this.el("meta").textContent = row ? `Host: ${row.host}:${row.port}\nConnection: ${row.connected ? "Connected" : "Disconnected — showing last received snapshot"}\nReceived: ${row.received_at ? new Date(row.received_at).toLocaleString() : "Waiting for initial data"}` : "Nexo entry unavailable. Open this page from the integration gear.";
    for (const id of ["copy", "download", "expand", "collapse"]) this.el(id).disabled = !row?.initial_data;
    this.renderCommands(row);
    this.renderStats(row);
    this.renderTree();
  }
  renderCommands(row) {
    if (this.commandEntry !== this.selected) {
      this.commandEntry = this.selected;
      this.el("command").value = "";
      this.el("manual-commands").value = (row?.configured_commands || []).join(", ");
      this.el("command-status").textContent = "";
      this.el("save-status").textContent = "";
    }
    this.el("known-commands").replaceChildren(...(row?.commands || []).map(command => {
      const option = document.createElement("option"); option.value = command; return option;
    }));
    this.el("send").disabled = !row?.connected || this.sending;
    this.el("command").disabled = !row?.connected || this.sending;
    this.el("save-commands").disabled = !row || this.saving;
    this.el("manual-commands").disabled = !row || this.saving;
  }
  renderStats(row) {
    const payload = row?.initial_data;
    const resources = payload?.resources;
    const values = resources && typeof resources === "object" ? Object.values(resources) : [];
    const counts = new Map();
    for (const resource of values) {
      const type = typeof resource?.type === "string" ? resource.type : "Unknown";
      counts.set(type, (counts.get(type) || 0) + 1);
    }
    const stats = [["Resources", payload ? values.length : "—"],
      ["Resource Types", payload ? counts.size : "—"],
      ["Known Commands", row?.commands?.length || 0],
      ["JSON Size", payload ? `${new TextEncoder().encode(JSON.stringify(payload)).length.toLocaleString()} bytes` : "—"]];
    this.el("stats").replaceChildren(...stats.map(([label, value]) => {
      const card = document.createElement("div"); card.className = "stat"; card.textContent = label;
      const number = document.createElement("strong"); number.textContent = value; card.append(number); return card;
    }));
    this.el("types").textContent = [...counts].sort(([a], [b]) => a.localeCompare(b)).map(([type, count]) => `${type}: ${count}`).join(" · ");
  }
  async sendCommand() {
    const command = this.el("command").value.trim();
    const entry = this.selected;
    if (!command || this.sending || !this.row()?.connected) return;
    this.sending = true; this.renderCommands(this.row());
    this.el("command-status").textContent = `Sending “${command}”…`;
    try {
      await this._hass.callWS({type:"nexo/send_command", entry_id:entry, command});
      if (this.selected === entry) this.el("command-status").textContent = `Sent “${command}” to the bridge.`;
    } catch (e) {
      if (this.selected === entry) this.el("command-status").textContent = `Command failed: ${e.message || e}`;
    } finally { this.sending = false; if (this.isConnected) this.renderCommands(this.row()); }
  }
  async saveCommands() {
    const entry = this.selected;
    if (!entry || this.saving) return;
    const commands = this.el("manual-commands").value;
    this.saving = true; this.renderCommands(this.row());
    this.el("save-status").textContent = "Saving…";
    try {
      const result = await this._hass.callWS({type:"nexo/save_commands", entry_id:entry, commands});
      if (this.selected === entry) {
        this.el("manual-commands").value = result.commands.join(", ");
        this.el("save-status").textContent = "Command names saved. The bridge will reload if settings changed.";
      }
      await this.load();
    } catch (e) {
      if (this.selected === entry) this.el("save-status").textContent = `Save failed: ${e.message || e}`;
    } finally { this.saving = false; if (this.isConnected) this.renderCommands(this.row()); }
  }
  renderTree() {
    const root = this.el("tree");
    const openPaths = new Set([...root.querySelectorAll("details[open]")].map(d => d.dataset.path));
    const first = !root.querySelector("details") || this.renderedEntry !== this.selected;
    this.renderedEntry = this.selected;
    root.replaceChildren();
    const payload = this.row()?.initial_data;
    if (!payload) { root.textContent = "Waiting for initial data…"; return; }
    const build = (key, value, path, depth) => {
      if (this.filter && !`${key} ${JSON.stringify(value)}`.toLowerCase().includes(this.filter)) return null;
      if (value !== null && typeof value === "object") {
        const node = document.createElement("details"); node.dataset.path = path;
        node.open = Boolean(this.filter) || openPaths.has(path) || (first && depth === 0);
        const label = document.createElement("summary"); label.textContent = `${key} ${Array.isArray(value) ? "[]" : "{}"} (${Object.keys(value).length})`; node.append(label);
        for (const [childKey, childValue] of Object.entries(value)) {
          const child = build(childKey, childValue, `${path}/${JSON.stringify(childKey)}`, depth + 1); if (child) node.append(child);
        }
        return node;
      }
      const leaf = document.createElement("div"); leaf.className = "leaf"; leaf.textContent = `${key}: ${JSON.stringify(value)}`; return leaf;
    };
    const tree = build("initial_data", payload, "", 0);
    if (tree) root.append(tree); else root.textContent = "No matching keys or values.";
  }
}
customElements.define("nexo-inspector", NexoInspector);
