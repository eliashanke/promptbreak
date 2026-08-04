const state = {
  levels: [],
  playbooks: {},
  layerDefinitions: [],
  presets: {},
  layers: {},
  preset: "prompt_only",
  level: 1,
  defense: "baseline",
  sessionId: null,
  histories: {},
  busy: false,
};

const $ = (selector) => document.querySelector(selector);
const elements = {
  levels: $("#level-list"),
  messages: $("#messages"),
  form: $("#prompt-form"),
  input: $("#prompt-input"),
  send: $("#send-button"),
  objective: $("#objective"),
  title: $("#terminal-title"),
  model: $("#model-select"),
  status: $("#ollama-status"),
  toast: $("#toast"),
  evalPanel: $("#evaluation-panel"),
  evalButton: $("#evaluation-button"),
  benchmarkPanel: $("#benchmark-panel"),
  benchmarkButton: $("#benchmark-button"),
  redteamButton: $("#redteam-button"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data;
  try { data = await response.json(); } catch { data = { error: `HTTP ${response.status}` }; }
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function historyKey() {
  const signature = Object.keys(state.layers).sort().map((key) => state.layers[key] ? "1" : "0").join("");
  return `${state.level}:${state.defense}:${signature}`;
}
function currentHistory() { return state.histories[historyKey()] ||= []; }
function currentLevel() { return state.levels.find((item) => item.id === state.level); }

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}

function showToast(message, error = false) {
  elements.toast.textContent = message;
  elements.toast.className = `toast show${error ? " error" : ""}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => elements.toast.className = "toast", 4200);
}

function renderLevels() {
  elements.levels.innerHTML = state.levels.map((level) => `
    <button class="level ${level.id === state.level ? "active" : ""}" data-level="${level.id}">
      <span class="num">0${level.id}</span>
      <span><strong>${escapeHtml(level.title)}</strong><small>${escapeHtml(level.codename)}</small></span>
      <span class="arrow">›</span>
    </button>`).join("");
}

function renderHeader() {
  const level = currentLevel();
  if (!level) return;
  elements.title.textContent = `${level.codename} / ${level.title.toUpperCase()}`;
  elements.objective.innerHTML = `<b>OBJECTIVE</b>${escapeHtml(level.objective)}`;
}

function renderPlaybook() {
  const playbook = state.playbooks[state.level];
  if (!playbook) return;
  $("#playbook-content").innerHTML = `
    <div class="playbook-title">
      <h2>${escapeHtml(playbook.name)}</h2>
      <span class="difficulty">${escapeHtml(playbook.difficulty)}</span>
    </div>
    <p class="principle">${escapeHtml(playbook.principle)}</p>
    <div class="signal-list">${playbook.signals.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>
    ${playbook.payloads.map((payload, index) => `
      <article class="payload-card">
        <header>${escapeHtml(payload.label)}${payload.mode ? `<span>${escapeHtml(payload.mode.toUpperCase())}</span>` : ""}</header>
        <pre>${escapeHtml(payload.text)}</pre>
        <button class="load-payload" data-payload="${index}">LOAD INTO TERMINAL</button>
      </article>`).join("")}`;
}

function addMessage(role, content, options = {}) {
  const item = document.createElement("div");
  const cssRole = role === "operator" ? "user" : role === "system" ? "system" : "assistant";
  item.className = `message ${cssRole}${options.breach ? " breach" : ""}${options.blocked ? " blocked" : ""}`;
  item.innerHTML = `
    <div class="role">${role.toUpperCase()}</div>
    <div class="content">${escapeHtml(content)}</div>
    ${options.meta ? `<div class="meta">${escapeHtml(options.meta)}</div>` : ""}
    ${options.trace ? `
      <div class="defense-trace">
        ${Object.entries(options.trace).map(([key, value]) => `
          <span class="${String(value).includes("BYPASS") || String(value).includes("MISSED") || String(value).includes("BREACH") ? "trace-hot" : String(value) === "BLOCKED" ? "trace-safe" : ""}">
            <small>${escapeHtml(key.replaceAll("_", " "))}</small>${escapeHtml(value)}
          </span>`).join("<b>→</b>")}
      </div>` : ""}`;
  elements.messages.appendChild(item);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return item;
}

function renderHistory() {
  elements.messages.innerHTML = "";
  addMessage("system", `Secure channel established. Defense=${state.defense.toUpperCase()}. Target awaiting input.`);
  for (const message of currentHistory()) {
    addMessage(message.role === "user" ? "operator" : "target", message.content, message.ui || {});
  }
}

function presetLabel(name) {
  return {
    prompt_only: "Prompt only",
    input_guard: "Input guard",
    output_filter: "Output filter",
    standard_guarded: "Standard",
    full_pipeline: "Full pipeline",
    custom: "Custom build",
  }[name] || name;
}

function renderDefenseBuilder() {
  $("#preset-list").innerHTML = Object.keys(state.presets).map((name) => `
    <button class="${state.preset === name ? "active" : ""}" data-preset="${name}">${escapeHtml(presetLabel(name))}</button>
  `).join("");
  $("#layer-list").innerHTML = state.layerDefinitions.map((layer) => `
    <label class="layer-toggle">
      <input type="checkbox" data-layer="${layer.id}" ${state.layers[layer.id] ? "checked" : ""} />
      <span class="layer-switch"></span>
      <span class="layer-copy"><strong>${escapeHtml(layer.name)}</strong><small>${escapeHtml(layer.description)}</small></span>
      <span class="layer-cost">${escapeHtml(layer.cost)}</span>
    </label>
  `).join("");
  const active = state.layerDefinitions.filter((layer) => state.layers[layer.id]);
  $("#builder-pipeline").innerHTML = [
    "<span>INPUT</span>",
    ...active.map((layer) => `<b>→</b><span>${escapeHtml(layer.name.toUpperCase())}</span>`),
    "<b>→</b><span>TARGET</span>",
  ].join("");
  $("#builder-status").textContent = presetLabel(state.preset).toUpperCase();
}

function applyPreset(name) {
  state.preset = name;
  state.layers = { ...state.presets[name] };
  if (name === "prompt_only") state.defense = "baseline";
  else if (name === "standard_guarded") state.defense = "guarded";
  else state.defense = "custom";
  document.querySelectorAll("[data-defense]").forEach((button) => {
    button.classList.toggle("active", button.dataset.defense === state.defense);
  });
  renderDefenseBuilder();
  updateDefenseSummary();
  renderHistory();
}

function updateDefenseSummary() {
  const activeCount = Object.values(state.layers).filter(Boolean).length;
  const baseline = activeCount === 0;
  $("#defense-badge").textContent = baseline ? "VULNERABLE" : state.preset === "full_pipeline" ? "MAXIMUM" : "CUSTOM";
  $("#defense-badge").className = `pill ${baseline ? "danger" : "safe"}`;
  $("#defense-description").textContent = baseline
    ? "Nur der Ziel-Prompt ist aktiv. Keine zusätzliche Schutzschicht."
    : `${activeCount} Defense-Layer aktiv · ${presetLabel(state.preset)}.`;
  $("#pipeline-guard").classList.toggle("muted", !(state.layers.heuristics || state.layers.llm_guard || state.layers.context_guard));
  $("#pipeline-filter").classList.toggle("muted", !(state.layers.output_filter || state.layers.encoding_detector));
}

function setDefense(defense) {
  applyPreset(defense === "baseline" ? "prompt_only" : "standard_guarded");
}

function setBusy(value) {
  state.busy = value;
  elements.send.disabled = value;
  elements.input.disabled = value;
  elements.evalButton.disabled = value;
  elements.benchmarkButton.disabled = value;
  elements.redteamButton.disabled = value;
}

function showTyping() {
  const item = document.createElement("div");
  item.className = "message assistant";
  item.innerHTML = `<div class="role">TARGET</div><div class="typing"><i></i><i></i><i></i></div>`;
  elements.messages.appendChild(item);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return item;
}

function showBreach(method = "direct") {
  $("#breach-technique").textContent = `EXFILTRATION: ${String(method).toUpperCase()}`;
  $("#breach-overlay").classList.add("visible");
  $("#breach-overlay").setAttribute("aria-hidden", "false");
}

async function sendPrompt(event) {
  event.preventDefault();
  const text = elements.input.value.trim();
  if (!text || state.busy) return;
  const history = currentHistory();
  addMessage("operator", text);
  elements.input.value = "";
  setBusy(true);
  const typing = showTyping();
  try {
    const result = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.sessionId,
        level: state.level,
        defense: state.defense,
        layers: state.layers,
        model: elements.model.value,
        message: text,
        history: history.map(({ role, content }) => ({ role, content })),
      }),
    });
    typing.remove();
    const metaParts = [`${result.latency_ms} MS`, `${result.eval_tokens} TOKENS`];
    if (result.guard) metaParts.push(`GUARD ${(Number(result.guard.confidence || 0) * 100).toFixed(0)}%`);
    if (result.exfiltration_method) metaParts.push(`EXFIL ${result.exfiltration_method.toUpperCase()}`);
    const ui = { breach: result.breach, blocked: result.blocked, meta: metaParts.join("  //  "), trace: result.trace };
    addMessage("target", result.answer, ui);
    history.push({ role: "user", content: text }, { role: "assistant", content: result.answer, ui });
    updateMetrics(result.stats);
    if (result.breach) {
      showToast("ACCESS GRANTED // Secret exfiltriert", false);
      showBreach(result.exfiltration_method);
    }
    else if (result.blocked) showToast("PAYLOAD BLOCKED // Guard aktiv", false);
  } catch (error) {
    typing.remove();
    addMessage("system", `ERROR: ${error.message}`);
    showToast(error.message, true);
  } finally {
    setBusy(false);
    elements.input.focus();
  }
}

function updateMetrics(stats) {
  $("#metric-attempts").textContent = String(stats.attempts).padStart(2, "0");
  $("#metric-breaches").textContent = String(stats.breaches).padStart(2, "0");
  $("#metric-asr").textContent = `${Number(stats.attack_success_rate || 0).toFixed(1)}%`;
  $("#metric-latency").textContent = stats.avg_latency_ms ? `${stats.avg_latency_ms}ms` : "—";
}

async function runEvaluation() {
  if (state.busy) return;
  setBusy(true);
  elements.evalPanel.classList.remove("hidden");
  elements.evalPanel.innerHTML = `<div class="message system"><div class="role">EVAL</div><div class="typing"><i></i><i></i><i></i></div></div>`;
  elements.evalPanel.scrollIntoView({ behavior: "smooth", block: "center" });
  try {
    const result = await api("/api/evaluate", {
      method: "POST",
      body: JSON.stringify({ level: state.level, defense: state.defense, layers: state.layers, model: elements.model.value }),
    });
    const m = result.metrics;
    elements.evalPanel.innerHTML = `
      <div class="eval-summary">
        <div><span>ATTACK SUCCESS ↓</span><strong>${m.attack_success_rate}%</strong></div>
        <div><span>FALSE POSITIVES ↓</span><strong>${m.false_positive_rate}%</strong></div>
        <div><span>ACCURACY ↑</span><strong>${m.accuracy}%</strong></div>
        <div><span>AVG. LATENCY</span><strong>${m.avg_latency_ms}ms</strong></div>
      </div>
      ${result.cases.map((row) => `
        <div class="eval-row">
          <span class="kind">${row.kind.toUpperCase()}</span>
          <span>${escapeHtml(row.prompt)}</span>
          <span class="${row.passed ? "pass" : "fail"}">${row.passed ? "PASS" : "FAIL"}</span>
          <span>${row.latency_ms} MS</span>
        </div>`).join("")}`;
  } catch (error) {
    elements.evalPanel.innerHTML = `<div class="message breach"><div class="role">ERROR</div><div class="content">${escapeHtml(error.message)}</div></div>`;
  } finally {
    setBusy(false);
  }
}

async function runRedteam() {
  if (state.busy) return;
  setBusy(true);
  const panel = $("#redteam-results");
  panel.innerHTML = `<div class="empty-state">Attacker model is planning its first move<span>_</span></div>`;
  try {
    const result = await api("/api/redteam", {
      method: "POST",
      body: JSON.stringify({
        level: state.level,
        defense: state.defense,
        layers: state.layers,
        rounds: Number($("#redteam-rounds").value),
        attacker_model: elements.model.value,
        target_model: elements.model.value,
      }),
    });
    panel.innerHTML = result.attempts.map((attempt) => `
      <article class="agent-round">
        <header>
          <strong>ROUND ${attempt.round} · ${escapeHtml(attempt.source.toUpperCase())}</strong>
          <span class="${attempt.breach ? "won" : "lost"}">${attempt.breach ? "BREACH" : attempt.blocked ? "BLOCKED" : "NO LEAK"}</span>
        </header>
        <div class="agent-body">
          <div class="strategy">${escapeHtml(attempt.strategy)}</div>
          <div class="payload-preview">${escapeHtml(attempt.prompt)}</div>
        </div>
      </article>`).join("") + `
      <div class="arena-summary">
        ${result.success ? "ACCESS ACHIEVED" : "DEFENSE HELD"} ·
        ${result.rounds_used} ROUND${result.rounds_used === 1 ? "" : "S"} ·
        ${(result.runtime_ms / 1000).toFixed(1)}S
      </div>`;
    if (result.success) showBreach(result.attempts.at(-1).exfiltration_method || "agent");
  } catch (error) {
    panel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    showToast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function heatClass(value) {
  if (value === 0) return "safe";
  if (value < 50) return "warn";
  return "danger";
}

async function runBenchmark() {
  if (state.busy) return;
  setBusy(true);
  elements.benchmarkPanel.classList.remove("hidden");
  elements.benchmarkPanel.innerHTML = `<div class="empty-state">Running local ablation benchmark · this can take a few minutes<span>_</span></div>`;
  elements.benchmarkPanel.scrollIntoView({ behavior: "smooth", block: "center" });
  try {
    const result = await api("/api/benchmark", {
      method: "POST",
      body: JSON.stringify({ model: elements.model.value }),
    });
    const cellMap = new Map(result.cells.map((cell) => [`${cell.category}:${cell.configuration}`, cell.asr]));
    elements.benchmarkPanel.innerHTML = `
      <div class="heatmap">
        <div class="heat-head">ATTACK CLASS</div>
        ${result.configurations.map((name) => `<div class="heat-head">${escapeHtml(presetLabel(name))}</div>`).join("")}
        ${result.categories.map((category) => `
          <div class="heat-label">${escapeHtml(category)}</div>
          ${result.configurations.map((configuration) => {
            const value = cellMap.get(`${category}:${configuration}`) ?? 0;
            return `<div class="heat-cell ${heatClass(value)}">${value}%</div>`;
          }).join("")}
        `).join("")}
      </div>
      <div class="benchmark-summary">
        ${result.configurations.map((name) => {
          const summary = result.summaries[name];
          return `<article>
            <strong>${escapeHtml(presetLabel(name))}</strong>
            <span>ASR ${summary.asr}%</span>
            <span>FALSE POSITIVES ${summary.fpr}%</span>
            <span>AVG LATENCY ${summary.latency_ms}MS</span>
          </article>`;
        }).join("")}
      </div>
      <div class="arena-summary">${result.case_count} RUNS · ${(result.runtime_ms / 1000).toFixed(1)}S · MODEL ${escapeHtml(result.model)}</div>`;
  } catch (error) {
    elements.benchmarkPanel.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    showToast(error.message, true);
  } finally {
    setBusy(false);
  }
}

async function checkOllama() {
  try {
    const health = await api("/api/health");
    elements.status.className = "connection online";
    elements.status.querySelector("span").textContent = "OLLAMA ONLINE";
    if (health.models.length) {
      const existing = new Set([...elements.model.options].map((option) => option.value));
      for (const model of health.models) {
        if (!existing.has(model)) elements.model.add(new Option(model, model));
      }
      if (health.models.includes(elements.model.value)) return;
      const gemma = health.models.find((model) => model.startsWith("gemma3"));
      elements.model.value = gemma || health.models[0];
    } else {
      showToast("Ollama läuft, aber kein Modell ist installiert. Führe `ollama pull gemma3:4b` aus.", true);
    }
  } catch (error) {
    elements.status.className = "connection offline";
    elements.status.querySelector("span").textContent = "OLLAMA OFFLINE";
  }
}

async function init() {
  try {
    const [config, session] = await Promise.all([api("/api/config"), api("/api/session")]);
    state.levels = config.levels;
    state.playbooks = config.playbooks;
    state.layerDefinitions = config.defense_layers;
    state.presets = config.defense_presets;
    state.layers = { ...config.defense_presets.prompt_only };
    state.sessionId = session.session_id;
    $("#build-version").textContent = config.build;
    elements.model.innerHTML = `<option value="${escapeHtml(config.default_model)}">${escapeHtml(config.default_model)}</option>`;
    renderLevels();
    renderHeader();
    renderDefenseBuilder();
    updateDefenseSummary();
    renderHistory();
    checkOllama();
  } catch (error) {
    showToast(error.message, true);
  }
}

elements.form.addEventListener("submit", sendPrompt);
elements.input.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") elements.form.requestSubmit();
});
elements.levels.addEventListener("click", (event) => {
  const button = event.target.closest("[data-level]");
  if (!button || state.busy) return;
  state.level = Number(button.dataset.level);
  renderLevels();
  renderHeader();
  renderHistory();
});
document.querySelector(".segmented").addEventListener("click", (event) => {
  const button = event.target.closest("[data-defense]");
  if (button && !state.busy) setDefense(button.dataset.defense);
});
$("#preset-list").addEventListener("click", (event) => {
  const button = event.target.closest("[data-preset]");
  if (button && !state.busy) applyPreset(button.dataset.preset);
});
$("#layer-list").addEventListener("change", (event) => {
  const input = event.target.closest("[data-layer]");
  if (!input || state.busy) return;
  state.layers[input.dataset.layer] = input.checked;
  state.preset = "custom";
  state.defense = "custom";
  document.querySelectorAll("[data-defense]").forEach((button) => button.classList.remove("active"));
  renderDefenseBuilder();
  updateDefenseSummary();
  renderHistory();
});
$("#clear-button").addEventListener("click", () => { state.histories[historyKey()] = []; renderHistory(); });
$("#hint-button").addEventListener("click", () => showToast(currentLevel().hint));
elements.evalButton.addEventListener("click", runEvaluation);
elements.redteamButton.addEventListener("click", runRedteam);
elements.benchmarkButton.addEventListener("click", runBenchmark);
$("#help-button").addEventListener("click", () => $("#help-dialog").showModal());
$("#playbook-button").addEventListener("click", () => { renderPlaybook(); $("#playbook-dialog").showModal(); });
$("#playbook-content").addEventListener("click", (event) => {
  const button = event.target.closest("[data-payload]");
  if (!button) return;
  const payload = state.playbooks[state.level].payloads[Number(button.dataset.payload)];
  elements.input.value = payload.text;
  $("#playbook-dialog").close();
  elements.input.focus();
});
document.querySelectorAll("#help-dialog .dialog-close, #help-dialog .dialog-ok").forEach((button) => button.addEventListener("click", () => $("#help-dialog").close()));
document.querySelector("#playbook-dialog .dialog-close").addEventListener("click", () => $("#playbook-dialog").close());
$("#breach-close").addEventListener("click", () => {
  $("#breach-overlay").classList.remove("visible");
  $("#breach-overlay").setAttribute("aria-hidden", "true");
});

init();
