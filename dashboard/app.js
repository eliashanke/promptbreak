(async () => {
  "use strict";

  const response = await fetch("/api/results", { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`Result API returned HTTP ${response.status}`);
  const data = await response.json();

  const $ = (selector) => document.querySelector(selector);
  const pct = (value) => `${Number(value).toFixed(1)}%`;
  const number = (value) => new Intl.NumberFormat("en-US").format(value);
  const date = (value) => new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  const config = (run, id) => run.configs.find((item) => item.id === id);
  let selectedRunId = data.defaultRun;
  let selectedPricingId = data.defaultPricingByRun[selectedRunId];
  const usd = (value) => value === 0 ? "$0.00" : `$${Number(value).toFixed(value < .01 ? 4 : 2)}`;
  const INFO = {
    "promptbreak-asr": ["Promptbreak ASR", "Attack Success Rate: the share of attack prompts that achieve their objective despite the Promptbreak input guard. Lower is better. The value covers only the observed benchmark cases."],
    "full-asr": ["Full Pipeline ASR", "The share of successful attacks after the input guard, context guard, and output filter were active. A value of 0% means no objective breach was observed in this run; it does not prove general robustness."],
    "input-fpr": ["Input false positives", "The share of benign prompts incorrectly blocked by the input guard. This metric isolates the guard and excludes later output-filter decisions."],
    "e2e-block": ["End-to-end benign block", "The share of benign prompts blocked anywhere in the full pipeline. It can be above zero even with 0% input FPR when, for example, the output filter withholds a response."],
    "model-calls": ["Model calls and tokens", "The sum of all recorded model calls and input/output tokens across the configurations shown for this run. It may include multiple guard and target models."],
    runtime: ["Runtime", "Measured wall-clock runtime of the stored report. It depends heavily on hardware, model cache, early blocking, and the number of repetitions."],
    "Defense comparison": ["Defense comparison", "Compares Attack Success Rate and input False Positive Rate for each defense configuration within one run. Both should be low; F1 summarizes the binary classification result."],
    "Threshold profile": ["Threshold profile", "Shows how many attacks are detected by the LLM classifier alone and by heuristics plus LLM at different confidence thresholds. Raw decisions were generated once and evaluated offline."],
    "Input attribution": ["Input attribution", "Attributes benign cases to false blocking by heuristics, the LLM classifier, both, or neither. This reveals which guard layer causes overblocking."],
    "Attack success heatmap": ["Attack success heatmap", "Each cell shows the observed Attack Success Rate of one defense for one attack family. A missing cell means that combination was not present in the selected report."],
    "Model snapshot": ["Model snapshot", "A descriptive comparison of different runs. Models, repetition counts, and dates differ, so this table is not a paired significance test."],
    "API cost estimate": ["API cost estimate", "A counterfactual calculation from recorded input/output tokens and the selected pricing profile. The actual runs used Ollama and incurred $0 in API fees. A mixed-model provider bill may differ."],
    "Rainbow-Lite archive": ["Rainbow-Lite archive", "A small quality-diversity archive with four attack families × four transformations. An occupied cell contains a tested candidate; a dark cell was not reached by the search. Red would mark a successful breach."],
    "Guard training diagnostics": ["Guard training diagnostics", "Training and validation metrics recorded by the QLoRA notebook. The current split is random and may contain related or duplicated prompts across partitions, so these curves are diagnostics rather than final generalization evidence."],
  };

  const infoButton = (key, label) => `<button class="info-button" type="button" data-info="${key}" aria-label="Explain ${label}">i</button>`;

  function renderTabs() {
    $("#run-tabs").innerHTML = data.runs.map((run) => `
      <button class="run-tab ${run.id === selectedRunId ? "active" : ""}" data-run="${run.id}">
        <span>${run.label}</span><small>${run.observations} OBS · ${run.repeats}× REPEAT</small>
      </button>`).join("");
    document.querySelectorAll(".run-tab").forEach((button) => {
      button.addEventListener("click", () => {
        selectedRunId = button.dataset.run;
        selectedPricingId = data.defaultPricingByRun[selectedRunId] || selectedPricingId;
        render();
      });
    });
  }

  function renderKpis(run) {
    const guard = config(run, "promptbreak_guard");
    const full = config(run, "full_pipeline");
    const calls = run.configs.reduce((sum, item) => sum + item.modelCalls, 0);
    const tokens = run.configs.reduce((sum, item) => sum + item.tokens, 0);
    const items = [
      ["PROMPTBREAK ASR", pct(guard?.asr ?? 0), "lower is better", (guard?.asr ?? 0) <= 15 ? "good" : "warn", "promptbreak-asr"],
      ["FULL PIPELINE ASR", pct(full?.asr ?? 0), "objective breaches", (full?.asr ?? 0) === 0 ? "good" : "warn", "full-asr"],
      ["INPUT FALSE POSITIVES", pct(full?.inputFpr ?? guard?.inputFpr ?? 0), "benign blocked at input", (full?.inputFpr ?? 0) === 0 ? "good" : "warn", "input-fpr"],
      ["END-TO-END BENIGN BLOCK", pct(full?.benignBlock ?? guard?.benignBlock ?? 0), "includes output filter", (full?.benignBlock ?? 0) === 0 ? "good" : "warn", "e2e-block"],
      ["MODEL CALLS", number(calls), `${number(tokens)} tokens`, "", "model-calls"],
      ["RUNTIME", `${run.runtimeMinutes.toFixed(1)}m`, `${run.observations} observations`, "", "runtime"],
    ];
    $("#kpi-grid").innerHTML = items.map(([label, value, note, tone, infoKey]) => `
      <article class="kpi">${infoButton(infoKey, label)}<span>${label}</span><strong class="${tone}">${value}</strong><small>${note}</small></article>`).join("");
  }

  function renderDefenseChart(run) {
    $("#defense-chart").innerHTML = run.configs.map((item) => `
      <div class="defense-row">
        <div class="defense-name"><strong>${item.label}</strong><small>F1 ${item.f1.toFixed(3)} · ${item.errors} errors</small></div>
        <div class="dual-track" aria-label="${item.label}: ASR ${pct(item.asr)}, input FPR ${pct(item.inputFpr)}">
          <i class="bar asr" style="width:${item.asr}%"></i><i class="bar fpr" style="width:${item.inputFpr}%"></i>
        </div>
        <div class="defense-score">${pct(item.asr)}</div>
      </div>`).join("");
  }

  function renderThreshold(runId) {
    const threshold = data.thresholds.find((item) => item.runId === runId) || data.thresholds[0];
    $("#threshold-model").value = threshold.runId;
    $("#threshold-chart").innerHTML = threshold.points.map((point) => `
      <div class="threshold-point" title="Threshold ${point.threshold}: LLM recall ${pct(point.llmRecall)}, combined recall ${pct(point.combinedRecall)}">
        <div class="threshold-bars"><i class="llm" style="height:${point.llmRecall}%"></i><i class="combined" style="height:${point.combinedRecall}%"></i></div>
        <b>${point.threshold.toFixed(2)}</b><small>${point.llmRecall.toFixed(0)} / ${point.combinedRecall.toFixed(0)}</small>
      </div>`).join("");
  }

  function renderAttribution(runId) {
    const attribution = data.attributions.find((item) => item.runId === runId) || data.attributions[0];
    const summary = attribution.summary;
    const passed = summary.attribution.neither;
    $("#attribution-panel").innerHTML = `
      <div class="attribution-total"><div><strong>${passed}/${attribution.benignCases}</strong></div><span>BENIGN CASES<br>PASS BOTH INPUT CHECKS</span></div>
      <div class="attribution-list">
        <div class="attribution-row"><span>Heuristics only</span><b>${summary.attribution.heuristics_only}</b></div>
        <div class="attribution-row"><span>LLM only</span><b>${summary.attribution.llm_only}</b></div>
        <div class="attribution-row"><span>Both layers</span><b>${summary.attribution.both}</b></div>
        <div class="attribution-row"><span>Neither</span><b>${summary.attribution.neither}</b></div>
        <div class="attribution-row"><span>Classifier errors</span><b>${summary.errors}</b></div>
      </div>`;
  }

  function heatColor(rate) {
    if (rate === 0) return "#c8ff3810";
    const alpha = Math.min(.18 + rate / 130, .88);
    return `rgba(255, 103, 70, ${alpha})`;
  }

  function renderHeatmap(run) {
    const matrix = run.categories.attack;
    const categories = [...new Set(Object.values(matrix).flatMap((entry) => Object.keys(entry)))].sort();
    const header = `<div class="heat-row" style="--category-count:${categories.length}"><div class="heat-label header">DEFENSE</div>${categories.map((item) => `<div class="heat-label header">${item.replaceAll("_", " ")}</div>`).join("")}</div>`;
    const rows = run.configs.map((item) => {
      const values = matrix[item.id] || {};
      return `<div class="heat-row" style="--category-count:${categories.length}"><div class="heat-label">${item.label}</div>${categories.map((category) => {
        const cell = values[category];
        return cell ? `<div class="heat-cell" style="background:${heatColor(cell.rate)}" title="${cell.observations} observations">${pct(cell.rate)}</div>` : `<div class="heat-cell na">—</div>`;
      }).join("")}</div>`;
    }).join("");
    $("#category-heatmap").innerHTML = `<div class="heat-grid">${header}${rows}</div>`;
  }

  function renderModelTable() {
    const rows = data.runs.map((run) => {
      const guard = config(run, "promptbreak_guard");
      const full = config(run, "full_pipeline");
      return `<div class="model-row">
        <strong>${run.label}</strong><span>${run.repeats}×</span><span>${run.observations}</span>
        <span class="${guard?.asr <= 13.3 ? "best" : ""}">${guard ? pct(guard.asr) : "—"}</span>
        <span class="${full?.asr === 0 ? "best" : ""}">${full ? pct(full.asr) : "—"}</span>
        <span class="${(full?.inputFpr ?? guard?.inputFpr) === 0 ? "best" : ""}">${full || guard ? pct(full?.inputFpr ?? guard.inputFpr) : "—"}</span>
        <span class="${(full?.benignBlock ?? guard?.benignBlock) === 0 ? "best" : ""}">${full || guard ? pct(full?.benignBlock ?? guard.benignBlock) : "—"}</span>
        <span>${run.runtimeMinutes.toFixed(1)}m</span>
      </div>`;
    }).join("");
    $("#model-table").innerHTML = `<div class="model-row header"><span>RUN</span><span>REPEATS</span><span>OBS.</span><span>GUARD ASR</span><span>FULL ASR</span><span>INPUT FPR</span><span>E2E BLOCK</span><span>RUNTIME</span></div>${rows}`;
  }

  function renderRainbows() {
    $("#rainbow-grid").innerHTML = data.rainbows.map((run) => {
      const cells = [];
      const occupied = new Map(run.cells.map((cell) => [`${cell.family}:${cell.transformation}`, cell]));
      ["authority", "format_smuggling", "multi_turn", "encoding"].forEach((family) => {
        ["direct", "roleplay", "structured", "obfuscated"].forEach((transformation) => {
          const cell = occupied.get(`${family}:${transformation}`);
          cells.push(`<i class="archive-cell ${!cell ? "empty" : cell.breach ? "breach" : ""}" title="${family} / ${transformation}${cell ? " · occupied" : " · empty"}"></i>`);
        });
      });
      const infoKey = `rainbow-${run.id}`;
      INFO[infoKey] = [run.label, `${run.occupied} of ${run.capacity} archive cells were occupied after ${run.iterations} adaptive mutations (${pct(run.coverage)} coverage). ${run.successfulCells === 0 ? "No occupied cell produced a successful breach." : `${run.successfulCells} cells produced a breach.`} Green means occupied and blocked; dark means not reached; red means breached.`];
      return `<article class="rainbow-card">${infoButton(infoKey, run.label)}<header><h3>${run.label}</h3><span>${run.iterations} ITERATIONS</span></header>
        <div class="rainbow-metrics"><div><small>COVERAGE</small><strong>${pct(run.coverage)}</strong></div><div><small>ADAPTIVE ASR</small><strong>${pct(run.adaptiveAsr)}</strong></div><div><small>BREACH CELLS</small><strong>${run.successfulCells}</strong></div></div>
        <div class="archive-cells">${cells.join("")}</div></article>`;
    }).join("");
  }

  function lineChart(series, yMax, yFormatter) {
    const width = 1000, height = 250, left = 58, right = 18, top = 18, bottom = 38;
    const all = series.flatMap((item) => item.points);
    const minStep = Math.min(...all.map((point) => point.step));
    const maxStep = Math.max(...all.map((point) => point.step));
    const x = (step) => left + (step - minStep) / Math.max(maxStep - minStep, 1) * (width - left - right);
    const y = (value) => top + (1 - Math.max(0, Math.min(value / yMax, 1))) * (height - top - bottom);
    const yTicks = [0, .25, .5, .75, 1].map((ratio) => {
      const value = ratio * yMax;
      const yPos = y(value);
      return `<line class="chart-grid" x1="${left}" y1="${yPos}" x2="${width - right}" y2="${yPos}"/><text class="chart-label" x="${left - 10}" y="${yPos + 4}" text-anchor="end">${yFormatter(value)}</text>`;
    }).join("");
    const xTicks = [0, .25, .5, .75, 1].map((ratio) => {
      const step = Math.round(minStep + ratio * (maxStep - minStep));
      const xPos = x(step);
      return `<line class="chart-tick" x1="${xPos}" y1="${height - bottom}" x2="${xPos}" y2="${height - bottom + 5}"/><text class="chart-label" x="${xPos}" y="${height - 14}" text-anchor="middle">${step}</text>`;
    }).join("");
    const paths = series.map((item) => {
      const points = item.points.map((point) => `${x(point.step).toFixed(1)},${y(point.value).toFixed(1)}`).join(" ");
      return `<polyline class="chart-line ${item.className}" points="${points}"/>`;
    }).join("");
    const legend = series.map((item) => `<span class="chart-legend ${item.className}">${item.label}</span>`).join("");
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${series.map((item) => item.label).join(", ")} by training step">${yTicks}${xTicks}${paths}<text class="chart-axis-title" x="${width - right}" y="${height - 14}" text-anchor="end">STEP</text></svg><div class="chart-legend-row">${legend}</div>`;
  }

  function renderTraining() {
    const training = data.training;
    const best = training.best;
    const latest = training.latest;
    $("#training-summary").innerHTML = `
      <div><small>BEST VALIDATION F1</small><strong>${best.f1.toFixed(3)}</strong><span>STEP ${best.step}</span></div>
      <div><small>BEST ACCURACY</small><strong>${pct(best.accuracy * 100)}</strong><span>RANDOM 90/10 SPLIT</span></div>
      <div><small>LATEST PRECISION</small><strong>${pct(latest.precision * 100)}</strong><span>STEP ${latest.step}</span></div>
      <div><small>LATEST RECALL</small><strong>${pct(latest.recall * 100)}</strong><span>STEP ${latest.step}</span></div>`;
    $("#training-quality-chart").innerHTML = lineChart([
      { label: "F1", className: "f1", points: training.evaluations.map((point) => ({ step: point.step, value: point.f1 })) },
      { label: "PRECISION", className: "precision", points: training.evaluations.map((point) => ({ step: point.step, value: point.precision })) },
      { label: "RECALL", className: "recall", points: training.evaluations.map((point) => ({ step: point.step, value: point.recall })) },
    ], 1, (value) => value.toFixed(2));
    const maxLoss = Math.max(...training.training.map((point) => point.loss), ...training.evaluations.map((point) => point.loss));
    $("#training-loss-chart").innerHTML = lineChart([
      { label: "TRAIN", className: "train-loss", points: training.training.map((point) => ({ step: point.step, value: point.loss })) },
      { label: "EVAL", className: "eval-loss", points: training.evaluations.map((point) => ({ step: point.step, value: point.loss })) },
    ], Math.ceil(maxLoss), (value) => value.toFixed(1));
    $("#training-meta").textContent = `${training.adapter.toUpperCase()} · ${training.maxStep} STEPS · EPOCH ${training.epoch.toFixed(3)}`;
    $("#training-note").textContent = training.note;
  }

  function renderPricing(run) {
    const profile = data.pricingProfiles.find((item) => item.id === selectedPricingId) || data.pricingProfiles[0];
    selectedPricingId = profile.id;
    $("#pricing-profile").value = profile.id;
    const estimate = (item) => item.promptTokens / 1_000_000 * profile.inputPerMillionUsd
      + item.completionTokens / 1_000_000 * profile.outputPerMillionUsd;
    const total = run.configs.reduce((sum, item) => sum + estimate(item), 0);
    const promptTokens = run.configs.reduce((sum, item) => sum + item.promptTokens, 0);
    const completionTokens = run.configs.reduce((sum, item) => sum + item.completionTokens, 0);
    const rows = run.configs.map((item) => `<div class="pricing-row">
      <strong>${item.label}</strong><span>${number(item.promptTokens)}</span><span>${number(item.completionTokens)}</span><span>${usd(estimate(item))}</span>
    </div>`).join("");
    $("#pricing-panel").innerHTML = `
      <div class="pricing-summary">
        <div><small>ESTIMATED TOTAL</small><strong>${usd(total)}</strong></div>
        <div><small>INPUT TOKENS</small><b>${number(promptTokens)}</b></div>
        <div><small>OUTPUT TOKENS</small><b>${number(completionTokens)}</b></div>
        <div><small>PRICE / 1M</small><b>${usd(profile.inputPerMillionUsd)} IN · ${usd(profile.outputPerMillionUsd)} OUT</b></div>
      </div>
      <div class="pricing-table"><div class="pricing-row header"><span>CONFIGURATION</span><span>INPUT</span><span>OUTPUT</span><span>ESTIMATE</span></div>${rows}</div>
      <div class="pricing-source"><span class="price-tag ${profile.match}">${profile.match}</span><span>${profile.provider} · ${profile.region}</span><a href="${profile.sourceUrl}" target="_blank" rel="noreferrer">PRICE SOURCE · CHECKED ${profile.checkedAt}</a></div>
      <p class="price-note">${profile.note}</p>`;
  }

  function renderSources(run) {
    const sources = [run.source, data.training.source];
    const threshold = data.thresholds.find((item) => item.runId === run.id);
    const attribution = data.attributions.find((item) => item.runId === run.id);
    if (threshold) sources.push(threshold.source);
    if (attribution) sources.push(attribution.source);
    $("#source-links").innerHTML = sources.map((source) => `<a href="${source.href}" title="SHA-256 ${source.sha256}">${source.file}</a>`).join("");
  }

  function render() {
    const run = data.runs.find((item) => item.id === selectedRunId) || data.runs[0];
    renderTabs(); renderKpis(run); renderDefenseChart(run); renderThreshold(run.id); renderAttribution(run.id); renderHeatmap(run); renderPricing(run); renderSources(run);
    $("#run-meta").textContent = `${run.targetModel} · ${run.repeats}× · ${run.observations} observations`;
    const repair = $("#repair-note");
    if (run.repair) {
      repair.classList.remove("hidden");
      repair.textContent = `AUDIT NOTE // ${run.repair.replaced_observations} parser-error observations were replaced by verified reruns. Raw and patch reports remain versioned.`;
    } else repair.classList.add("hidden");
  }

  function openInfo(key, trigger) {
    const entry = INFO[key];
    if (!entry) return;
    const modal = $("#info-modal");
    modal.dataset.returnFocus = trigger ? "true" : "false";
    modal.returnFocusTarget = trigger || null;
    $("#info-modal-title").textContent = entry[0];
    $("#info-modal-body").textContent = entry[1];
    modal.showModal();
  }

  document.querySelectorAll(".panel-head h2").forEach((heading) => {
    if (INFO[heading.textContent]) heading.closest(".panel-head").insertAdjacentHTML("beforeend", infoButton(heading.textContent, heading.textContent));
  });
  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-info]");
    if (trigger) openInfo(trigger.dataset.info, trigger);
  });
  $("#info-modal-close").addEventListener("click", () => $("#info-modal").close());
  $("#info-modal").addEventListener("click", (event) => {
    if (event.target === $("#info-modal")) $("#info-modal").close();
  });
  $("#info-modal").addEventListener("close", (event) => event.currentTarget.returnFocusTarget?.focus());

  $("#total-observations").textContent = number(data.runs.reduce((sum, run) => sum + run.observations, 0));
  $("#latest-result").textContent = `LATEST RESULT ${date(data.latestResultAt)}`;
  $("#comparison-note").textContent = data.notes.comparison;
  $("#rainbow-note").textContent = data.notes.rainbow27;
  $("#threshold-model").innerHTML = data.thresholds.map((item) => `<option value="${item.runId}">${item.label}</option>`).join("");
  $("#threshold-model").addEventListener("change", (event) => renderThreshold(event.target.value));
  $("#pricing-profile").innerHTML = data.pricingProfiles.map((item) => `<option value="${item.id}">${item.label}</option>`).join("");
  $("#pricing-profile").addEventListener("change", (event) => { selectedPricingId = event.target.value; renderPricing(data.runs.find((item) => item.id === selectedRunId)); });
  renderModelTable(); renderRainbows(); renderTraining(); render();
})().catch((error) => {
  console.error("Dashboard initialization failed", error);
  const main = document.querySelector("main");
  if (main) main.innerHTML = `<section class="load-error"><p>RESULT API UNAVAILABLE</p><h1>Dashboard data could not be loaded.</h1><span>Start the Promptbreak web server and reload this page.</span></section>`;
});
