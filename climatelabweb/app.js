const content = document.querySelector("#page-content");
const breadcrumb = document.querySelector("#breadcrumb-current");
const toast = document.querySelector("#toast");

const PAGE_NAMES = {
  dashboard: "Overview",
  1: "Station objects",
  2: "City comparison",
  3: "Locations & alerts",
  4: "Climate analyzers",
  5: "Sensor monitor",
  6: "Climate summary",
};

let currentPage = "dashboard";
let cachedMay = null;
let toastTimer = null;

async function fetchJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function number(value, digits = 1) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : "—";
}

function badgeClass(label) {
  const value = String(label || "").toLowerCase();
  if (value.includes("severe")) return "severe";
  if (value.includes("heatwave")) return "wave";
  if (value.includes("watch")) return "watch";
  if (value.includes("advisory")) return "advisory";
  if (value.includes("error") || value.includes("invalid")) return "error";
  if (value === "none" || value === "normal") return value;
  return "";
}

function badge(label) {
  return `<span class="badge ${badgeClass(label)}">${escapeHtml(label)}</span>`;
}

function heading(kicker, title, description, meta = "") {
  return `
    <div class="page-heading">
      <div>
        <div class="eyebrow">${escapeHtml(kicker)}</div>
        <h1>${escapeHtml(title)}</h1>
        <p class="page-subtitle">${escapeHtml(description)}</p>
      </div>
      ${meta ? `<div class="heading-meta">${meta}</div>` : ""}
    </div>`;
}

function showLoading(message = "Loading climate observations…") {
  content.innerHTML = `<div class="loading-state"><span class="spinner"></span>${escapeHtml(message)}</div>`;
}

function showError(error) {
  const message = error instanceof Error
    ? error.message
    : typeof error === "string"
      ? error
      : JSON.stringify(error);
  content.innerHTML = `
    <div class="error-state">
      <strong>Couldn’t load this experiment</strong>
      <span>${escapeHtml(message)}</span>
      <button class="tool-button subtle" id="retry-button">Try again</button>
    </div>`;
  document.querySelector("#retry-button")?.addEventListener("click", loadCurrentPage);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2400);
}

function barChart(items, options = {}) {
  if (!items?.length) return `<div class="empty-state">No observations match the current selection.</div>`;
  const values = items.map((item) => Number(item.value) || 0);
  const max = Math.max(...values, 1);
  const min = options.min ?? 0;
  return `<div class="bar-chart">${items.map((item) => {
    const value = Number(item.value) || 0;
    const width = Math.max(1, ((value - min) / (max - min || max)) * 100);
    return `<div class="bar-row">
      <span class="bar-label" title="${escapeHtml(item.label)}">${escapeHtml(item.label)}</span>
      <div class="bar-track"><div class="bar-fill ${options.warm ? "warm" : ""}" style="width:${Math.min(100, width)}%"></div></div>
      <span class="bar-value">${escapeHtml(options.format ? options.format(value) : number(value))}</span>
    </div>`;
  }).join("")}</div>`;
}

function lineChart(items, unit = "", maxPoints = 22) {
  if (!items?.length) return `<div class="empty-state">No chart data available.</div>`;
  const source = items.length > maxPoints
    ? items.filter((_, index) => index % Math.ceil(items.length / maxPoints) === 0 || index === items.length - 1)
    : items;
  const values = source.map((item) => Number(item.value)).filter(Number.isFinite);
  if (!values.length) return `<div class="empty-state">No numeric readings available.</div>`;
  const width = 720;
  const height = 215;
  const pad = { top: 15, right: 18, bottom: 32, left: 42 };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const x = (index) => pad.left + index * ((width - pad.left - pad.right) / Math.max(1, source.length - 1));
  const y = (value) => pad.top + (max - value) * ((height - pad.top - pad.bottom) / spread);
  const points = source.map((item, index) => `${x(index)},${y(Number(item.value))}`).join(" ");
  const area = `${pad.left},${height - pad.bottom} ${points} ${x(source.length - 1)},${height - pad.bottom}`;
  const tickValues = [max, (max + min) / 2, min];
  const grid = tickValues.map((value) => {
    const lineY = y(value);
    return `<g><line class="grid-line" x1="${pad.left}" y1="${lineY}" x2="${width - pad.right}" y2="${lineY}"></line><text class="axis-label" x="2" y="${lineY + 3}">${number(value, 0)}${escapeHtml(unit)}</text></g>`;
  }).join("");
  const dots = source.map((item, index) => `<circle class="chart-dot" cx="${x(index)}" cy="${y(Number(item.value))}" r="3"><title>${escapeHtml(item.label)} · ${number(item.value)}${escapeHtml(unit)}</title></circle>`).join("");
  const labels = [0, Math.floor((source.length - 1) / 2), source.length - 1]
    .filter((index, position, array) => array.indexOf(index) === position)
    .map((index) => `<text class="axis-label" text-anchor="${index === 0 ? "start" : index === source.length - 1 ? "end" : "middle"}" x="${x(index)}" y="${height - 9}">${escapeHtml(source[index].label)}</text>`)
    .join("");
  return `<svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Climate observation chart">
    <defs><linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#48d6bd" stop-opacity=".18"></stop><stop offset="100%" stop-color="#48d6bd" stop-opacity="0"></stop></linearGradient></defs>
    ${grid}<polygon class="chart-area" points="${area}"></polygon><polyline class="chart-line" points="${points}"></polyline>${dots}${labels}
  </svg>`;
}

function table(headers, rows) {
  return `<div class="table-wrap"><table><thead><tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${rows || ""}</tbody></table></div>`;
}

function metric(label, value, note = "", tone = "") {
  return `<div class="metric-card"><div class="metric-label">${escapeHtml(label)}</div><div class="metric-value ${tone}">${escapeHtml(value)}</div>${note ? `<div class="metric-note">${escapeHtml(note)}</div>` : ""}</div>`;
}

function stat(label, value, tone = "") {
  return `<div class="stat-box"><span>${escapeHtml(label)}</span><strong class="${tone}">${escapeHtml(value)}</strong></div>`;
}

function setActivePage(page) {
  currentPage = String(page);
  breadcrumb.textContent = PAGE_NAMES[currentPage] || "Overview";
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === currentPage);
  });
}

async function loadCurrentPage() {
  setActivePage(currentPage);
  showLoading(currentPage === "dashboard" ? "Loading dashboard data…" : "Running experiment…");
  try {
    if (currentPage === "dashboard") await renderDashboard();
    else if (currentPage === "1") await renderExperimentOne();
    else if (currentPage === "2") await renderExperimentTwo();
    else if (currentPage === "3") await renderExperimentThree();
    else if (currentPage === "4") await renderExperimentFour();
    else if (currentPage === "5") await renderExperimentFive();
    else if (currentPage === "6") await renderExperimentSix();
  } catch (error) {
    showError(error);
  }
}

async function renderDashboard() {
  const data = await fetchJson("/api/overview");
  cachedMay = data.hottest_cities;
  const cityBars = [...data.hottest_cities]
    .sort((a, b) => b.average - a.average)
    .map((item) => ({ label: item.city, value: item.average }));
  const extremes = data.historic_extremes.map((item, index) => `
    <div class="extreme-item">
      <span class="rank">0${index + 1}</span>
      <div class="extreme-place"><strong>${escapeHtml(item.city)}</strong><span>${escapeHtml(item.date)} · ${escapeHtml(item.category)}</span></div>
      <span class="extreme-temp">${number(item.maximum)}°</span>
    </div>`).join("");
  content.innerHTML = `
    <section class="hero">
      <div class="hero-content">
        <div class="eyebrow">KJS-CES-01 · CLIMATE INTELLIGENCE</div>
        <h1>Heat, at a glance.</h1>
        <p>Explore heat extremes, compare six cities, inspect air quality and rainfall, and monitor station data across all six Python experiments.</p>
        <div class="hero-note"><span>↗</span> Recorded observations across ${data.dataset_count} supplied datasets · no forecast generated</div>
      </div>
    </section>
    <div class="metric-grid">
      ${metric("Datasets in the lab", String(data.dataset_count).padStart(2, "0"), "CSV files available")}
      ${metric("Cities compared", String(data.city_count).padStart(2, "0"), "May 2022 · supplied records", "teal")}
      ${metric("Days ≥ 40 °C", String(data.hot_days).padStart(2, "0"), "Across the six city series", "amber")}
      ${metric("Data timestamp", "ARCHIVE", "DS19 archived location observations")}
    </div>
    <div class="content-grid">
      <section class="panel">
        <div class="panel-header"><div class="panel-heading"><h2>May heat profile</h2><p>Average daily maximum temperature · May 2022</p></div><span class="chart-legend">Average Tmax</span></div>
        <div class="chart-wrap">${barChart(cityBars, { format: (value) => `${value.toFixed(1)}°` })}</div>
        <div class="chart-foot">The 40 °C threshold is a simplified teaching rule from the experiments.</div>
      </section>
      <section class="panel">
        <div class="panel-header"><div class="panel-heading"><h2>Historic extremes</h2><p>Peak observations in four city records</p></div><span class="panel-kicker">1990–2022</span></div>
        <div class="extreme-list">${extremes}</div>
      </section>
    </div>
    <div class="experiment-strip">
      ${[
        ["01", "Station objects"], ["02", "City comparison"], ["03", "Locations & alerts"],
        ["04", "Climate analyzers"], ["05", "Sensor monitor"], ["06", "Climate summary"],
      ].map(([id, label]) => `<button class="experiment-chip" data-page="${Number(id)}"><span>EXP ${id}</span><strong>${label}</strong></button>`).join("")}
    </div>`;
}

async function renderExperimentOne() {
  const city = new URLSearchParams(location.search).get("city") || "Delhi";
  const data = await fetchJson(`/api/experiments/1?city=${encodeURIComponent(city)}&limit=8`);
  const rows = data.records.map((item) => `<tr>
    <td>${escapeHtml(item.date)}</td><td>${escapeHtml(item.city)}</td>
    <td class="numeric">${number(item.maximum)} °C</td><td class="numeric">${number(item.minimum)} °C</td>
    <td class="numeric">${number(item.range)} °C</td><td class="numeric">${number(item.rainfall)} mm</td>
    <td>${badge(item.category)}</td></tr>`).join("");
  content.innerHTML = `
    ${heading("EXPERIMENT 01 · CLASSES & OBJECTS", "Heatwave station objects", "Create a station-style record for each hottest day. Change city or record count to inspect actual Tmax, Tmin, rainfall, temperature range, and the experiment’s heat category.", `<strong>${escapeHtml(data.dataset)}</strong>Daily Tmax series`)}
    <div class="toolbar">
      <div class="field"><label for="exp1-city">CITY</label><select id="exp1-city">${["Delhi", "Lucknow", "Chennai", "Mumbai"].map((name) => `<option ${name === city ? "selected" : ""}>${name}</option>`).join("")}</select></div>
      <div class="field"><label for="exp1-limit">HOTTEST RECORDS</label><select id="exp1-limit">${[2, 5, 8, 12, 20].map((n) => `<option value="${n}" ${n === 8 ? "selected" : ""}>Top ${n}</option>`).join("")}</select></div>
      <span class="hint">Temperature validity: −10 to 55 °C</span>
    </div>
    <div class="metric-grid">${metric("Station objects", String(data.records.length), "one object per selected record", "teal")}${metric("Peak Tmax", `${number(data.records[0]?.maximum)} °C`, data.records[0]?.date || "No record", "amber")}${metric("Category rules", "40 / 45 / 47°", "Watch · heatwave · severe")}${metric("Dataset period", "33 years", "Daily observations · 1990–2022")}</div>
    <section class="panel">
      <div class="panel-header"><div class="panel-heading"><h2>Hottest recorded days</h2><p>Ordered by daily maximum temperature</p></div><span class="panel-kicker">${escapeHtml(city.toUpperCase())}</span></div>
      ${table(["Date", "City", "Tmax", "Tmin", "Range", "Rainfall", "Heat category"], rows)}
      <p class="table-note">As in Experiment 1, rainfall gaps are treated as 0 for display and rows without Tmax or Tmin are excluded.</p>
    </section>`;
  document.querySelector("#exp1-city").addEventListener("change", (event) => {
    const params = new URLSearchParams({ city: event.target.value });
    history.replaceState(null, "", `?${params}`);
    loadCurrentPage();
  });
  document.querySelector("#exp1-limit").addEventListener("change", async (event) => {
    const selectedCity = document.querySelector("#exp1-city").value;
    try {
      const update = await fetchJson(`/api/experiments/1?city=${encodeURIComponent(selectedCity)}&limit=${event.target.value}`);
      const body = update.records.map((item) => `<tr><td>${escapeHtml(item.date)}</td><td>${escapeHtml(item.city)}</td><td class="numeric">${number(item.maximum)} °C</td><td class="numeric">${number(item.minimum)} °C</td><td class="numeric">${number(item.range)} °C</td><td class="numeric">${number(item.rainfall)} mm</td><td>${badge(item.category)}</td></tr>`).join("");
      document.querySelector("#page-content tbody").innerHTML = body;
      document.querySelector("#page-content .metric-value").textContent = String(update.records.length);
    } catch (error) {
      showToast(error.message);
    }
  });
}

async function renderExperimentTwo() {
  const data = await fetchJson("/api/experiments/2");
  cachedMay = data.cities;
  const city = new URLSearchParams(location.search).get("city") || "Delhi";
  content.innerHTML = `
    ${heading("EXPERIMENT 02 · CONSTRUCTORS & LISTS", "Compare a month of heat", "Use the May 2022 daily Tmax lists to sort cities, explore an individual city series, and change the hot-day threshold.")}
    <div class="toolbar">
      <div class="field"><label for="exp2-city">CITY SERIES</label><select id="exp2-city">${data.cities.map((item) => `<option ${item.city === city ? "selected" : ""}>${escapeHtml(item.city)}</option>`).join("")}</select></div>
      <div class="field"><label for="exp2-threshold">HOT-DAY THRESHOLD</label><div class="range-control"><input id="exp2-threshold" type="range" min="30" max="47" step="1" value="40"><output id="threshold-value">40 °C</output></div></div>
      <div class="field"><label for="exp2-sort">RANK CITIES BY</label><select id="exp2-sort"><option value="average">Average Tmax</option><option value="hot_days">Hot days</option><option value="maximum">Peak Tmax</option></select></div>
      <span class="hint">May 2022 · DS01–DS06</span>
    </div>
    <div class="metric-grid" id="exp2-metrics"></div>
    <div class="content-grid">
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2 id="exp2-chart-title">Daily temperature</h2><p>Each bar is one observed day's maximum temperature</p></div><span class="chart-legend">Tmax</span></div><div id="exp2-chart" class="chart-wrap"></div></section>
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>City ranking</h2><p>Sorted using the selected measure</p></div><span class="panel-kicker">6 CITIES</span></div><div id="exp2-ranking"></div></section>
    </div>
    <section class="panel" style="margin-top:15px"><div class="panel-header"><div class="panel-heading"><h2>Monthly city statistics</h2><p>Missing Tmax values are excluded, not counted as zero</p></div></div><div id="exp2-table"></div></section>`;
  const render = () => {
    const threshold = Number(document.querySelector("#exp2-threshold").value);
    const sortKey = document.querySelector("#exp2-sort").value;
    const rankingKey = sortKey === "hot_days" ? "threshold_days" : sortKey;
    const selected = document.querySelector("#exp2-city").value;
    const sorted = [...data.cities].map((item) => ({
      ...item,
      threshold_days: item.series.filter((reading) => reading.temperature >= threshold).length,
    })).sort((a, b) => b[rankingKey] - a[rankingKey]);
    const cityData = data.cities.find((item) => item.city === selected);
    document.querySelector("#threshold-value").textContent = `${threshold} °C`;
    document.querySelector("#exp2-chart-title").textContent = `${selected} · May daily Tmax`;
    document.querySelector("#exp2-chart").innerHTML = barChart(cityData.series.map((item) => ({ label: item.date, value: item.temperature })), { format: (value) => `${value.toFixed(1)}°`, warm: true });
    document.querySelector("#exp2-metrics").innerHTML =
      metric("Average Tmax", `${number(cityData.average, 2)} °C`, `${selected} · May 2022`) +
      metric("Monthly peak", `${number(cityData.maximum)} °C`, "Highest daily maximum", "amber") +
      metric(`Days ≥ ${threshold} °C`, String(cityData.threshold_days), "Threshold applied to this city", "teal") +
      metric("Readings", String(cityData.days), "Valid daily Tmax values");
    document.querySelector("#exp2-ranking").innerHTML = barChart(sorted.map((item) => ({ label: item.city, value: item[rankingKey] })), { format: (value) => sortKey === "hot_days" ? `${value} d` : `${value.toFixed(1)}°` });
    document.querySelector("#exp2-table").innerHTML = table(
      ["City", "Valid days", "Average Tmax", "Peak Tmax", `Days ≥ ${threshold}°C`, "Lab alert (40 °C)"],
      sorted.map((item) => `<tr><td>${escapeHtml(item.city)}</td><td class="numeric">${item.days}</td><td class="numeric">${number(item.average, 2)} °C</td><td class="numeric">${number(item.maximum)} °C</td><td class="numeric">${item.threshold_days}</td><td>${badge(item.alert)}</td></tr>`).join(""),
    );
  };
  document.getElementById("exp2-threshold").addEventListener("input", render);
  ["exp2-city", "exp2-sort"].forEach((id) => document.getElementById(id).addEventListener("change", render));
  render();
}

async function renderExperimentThree(page = 1) {
  const query = document.querySelector("#exp3-query")?.value || "";
  const mode = document.querySelector("#exp3-mode")?.value || "all";
  const data = await fetchJson(`/api/experiments/3?q=${encodeURIComponent(query)}&mode=${encodeURIComponent(mode)}&page=${page}`);
  const locations = data.locations.map((item) => `<tr>
    <td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.region)}</td><td class="numeric">${number(item.temperature)} °C</td>
    <td>${escapeHtml(item.condition || "—")}</td><td class="numeric">${number(item.humidity, 0)}%</td><td>${escapeHtml(item.last_updated)}</td></tr>`).join("");
  const alertRows = data.alerts.map((item) => `<div class="alert-row ${item.category.includes("SEVERE") ? "severe" : ""}"><span class="alert-dot">●</span><div class="alert-text"><strong>${escapeHtml(item.category)}</strong> · ${escapeHtml(item.city)} · ${escapeHtml(item.date)} · ${number(item.maximum)} °C</div></div>`).join("");
  content.innerHTML = `
    ${heading("EXPERIMENT 03 · STRINGS & INHERITANCE", "Locations, cleaned up.", "Search the supplied 543-location weather snapshot, apply string-based filters, normalize the historic Orissa label, and inspect inherited heat-alert records.", `<strong>DS19 · SNAPSHOT</strong>Latest source row · ${escapeHtml(data.snapshot_time)}`)}
    <div class="stat-row">
      ${stat("Unique locations", String(data.metadata.location_count), "teal")}
      ${stat("Names containing “pur”", String(data.metadata.pur_count))}
      ${stat("Old state-name rows", String(data.metadata.old_region_rows), "amber")}
    </div>
    <div class="toolbar">
      <div class="field"><label for="exp3-query">SEARCH LOCATION OR REGION</label><input id="exp3-query" type="search" value="${escapeHtml(query)}" placeholder="e.g. Delhi, Bengaluru, Odisha"></div>
      <div class="field"><label for="exp3-mode">STRING FILTER</label><select id="exp3-mode"><option value="all" ${mode === "all" ? "selected" : ""}>All locations</option><option value="starts-ban" ${mode === "starts-ban" ? "selected" : ""}>Starts with “Ban”</option><option value="contains-pur" ${mode === "contains-pur" ? "selected" : ""}>Contains “pur”</option></select></div>
      <button class="tool-button" id="exp3-search">Search locations</button><span class="hint">Longest name: ${escapeHtml(data.metadata.longest_location)}</span>
    </div>
    <section class="panel">
      <div class="panel-header"><div class="panel-heading"><h2>Location snapshot</h2><p>Latest row per location from the provided source file</p></div><span class="panel-kicker">${data.total_matches} MATCHES</span></div>
      ${data.total_matches ? table(["Location", "Region", "Temperature", "Conditions", "Humidity", "Source timestamp"], locations) : `<div class="empty-state">No locations match your search.</div>`}
      <div class="toolbar" style="margin:12px 0 0"><span class="results-count">PAGE ${data.page} · ${data.total_matches} RESULTS</span><span class="hint"></span><button class="tool-button subtle" id="exp3-prev" ${page <= 1 ? "disabled" : ""}>Previous</button><button class="tool-button subtle" id="exp3-next" ${page * data.page_size >= data.total_matches ? "disabled" : ""}>Next</button></div>
    </section>
    <div class="split-panels" style="margin-top:15px">
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>Inherited heat alerts</h2><p>Location → Observation → HeatAlert · top three days per city</p></div></div><div class="alert-feed">${alertRows}</div></section>
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>String transformations</h2><p>Applied to source values in the browser</p></div></div>
        <div class="stack"><div><div class="panel-kicker">REGION NORMALIZATION</div><div class="pill-row" style="margin-top:8px"><span class="pill">Orissa → Odisha</span><span class="pill">strip()</span><span class="pill">title()</span></div></div><div><div class="panel-kicker">FILTER EXAMPLES</div><div class="pill-row" style="margin-top:8px"><span class="pill">startswith("Ban")</span><span class="pill">"pur" in name</span></div></div><p class="table-note">DS19 is an archived snapshot (2023), despite “real-time” in its filename. It is displayed as source data, not a current feed.</p></div>
      </section>
    </div>`;
  document.querySelector("#exp3-search").addEventListener("click", () => renderExperimentThree(1).catch(showError));
  document.querySelector("#exp3-query").addEventListener("keydown", (event) => {
    if (event.key === "Enter") renderExperimentThree(1).catch(showError);
  });
  document.querySelector("#exp3-mode").addEventListener("change", () => renderExperimentThree(1).catch(showError));
  document.querySelector("#exp3-prev").addEventListener("click", () => renderExperimentThree(page - 1).catch(showError));
  document.querySelector("#exp3-next").addEventListener("click", () => renderExperimentThree(page + 1).catch(showError));
}

const ANALYZERS = [
  ["temperature", "Temperature"], ["rainfall", "Rainfall"], ["air-quality", "Air quality"],
  ["humidity", "Humidity"], ["regions", "Regional climate"],
];

async function renderExperimentFour(analyzer = document.querySelector("#exp4-tabs .active")?.dataset.analyzer || "temperature") {
  const data = await fetchJson(`/api/experiments/4?analyzer=${encodeURIComponent(analyzer)}`);
  content.innerHTML = `
    ${heading("EXPERIMENT 04 · ABSTRACT CLASSES & POLYMORPHISM", "One interface. Five analyses.", "Choose an analyzer to run its own calculation against its original dataset. Each uses the same reporting shape—different data, different insight.")}
    <div class="analyzer-tabs" id="exp4-tabs">${ANALYZERS.map(([key, label]) => `<button class="analyzer-tab ${key === analyzer ? "active" : ""}" data-analyzer="${key}">${label}</button>`).join("")}</div>
    <div class="stat-row">${stat("Concrete analyzer", data.title, "teal")}${stat("Dataset rows", data.rows_loaded.toLocaleString())}${stat("Dataset", data.dataset)}</div>
    <section class="panel">
      <div class="panel-header"><div class="panel-heading"><h2>${escapeHtml(data.chart_title)}</h2><p>${escapeHtml(data.dataset)}</p></div><span class="panel-kicker">${escapeHtml(data.unit)}</span></div>
      <div class="analysis-summary">${data.summary.map((item) => `<div class="analysis-cell"><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></div>`).join("")}</div>
      <div class="chart-wrap">${barChart(data.series.map((item) => ({ label: item.label, value: item.value })), { warm: analyzer === "rainfall" || analyzer === "air-quality", format: (value) => `${number(value)} ${data.unit}` })}</div>
    </section>
    <p class="table-note">The abstract ClimateAnalyzer contract requires each concrete class to implement analyze(); the shared report() call dispatches to that implementation. Dataset-specific coverage and granularity differ; use the dataset catalog for source notes.</p>`;
  document.querySelectorAll("#exp4-tabs .analyzer-tab").forEach((button) => {
    button.addEventListener("click", () => renderExperimentFour(button.dataset.analyzer).catch(showError));
  });
}

async function renderExperimentFive(station = document.querySelector("#exp5-station")?.value || "Wanaparthy", days = Number(document.querySelector("#exp5-days")?.value || 15), sensor = document.querySelector("#exp5-sensor")?.value || "temperature") {
  const [stationsData, data] = await Promise.all([
    fetchJson("/api/stations"),
    fetchJson(`/api/experiments/5?station=${encodeURIComponent(station)}&days=${days}`),
  ]);
  const selectedSensor = data.sensors[sensor];
  const warnings = Object.values(data.sensors).flatMap((item) => item.warnings.map((alert) => ({ ...alert, sensor: item.sensor })));
  const errors = Object.values(data.sensors).flatMap((item) => item.errors.map((alert) => ({ ...alert, sensor: item.sensor })));
  const faulty = data.faulty_reading
    ? `<div class="alert-row error-alert"><span class="alert-dot">!</span><div class="alert-text"><strong>Rejected faulty reading</strong> · ${escapeHtml(data.faulty_reading.station)} · ${escapeHtml(data.faulty_reading.date)} · ${number(data.faulty_reading.temperature)} °C. ${escapeHtml(data.faulty_reading.reason)}</div></div>`
    : `<div class="alert-row"><span class="alert-dot">✓</span><div class="alert-text">No out-of-range temperature found in the north India station file.</div></div>`;
  const events = [...warnings.map((item) => ({ ...item, kind: "warning" })), ...errors.map((item) => ({ ...item, kind: "error" }))]
    .slice(0, 12)
    .map((item) => `<div class="alert-row ${item.kind === "error" ? "error-alert" : ""}"><span class="alert-dot">${item.kind === "error" ? "!" : "●"}</span><div class="alert-text"><strong>${escapeHtml(item.sensor.replace("_", " "))}</strong> · ${escapeHtml(item.date)} · ${escapeHtml(item.message)}</div></div>`)
    .join("");
  content.innerHTML = `
    ${heading("EXPERIMENT 05 · EXCEPTIONS & THREADS", "Listen to each sensor.", "Run temperature, humidity, and wind checks concurrently against a Telangana station. Missing and physically invalid values stay visible as data-quality errors.", `<strong>THREAD POOL · 3 SENSORS</strong>${escapeHtml(data.dataset)}`)}
    <div class="toolbar">
      <div class="field"><label for="exp5-station">STATION / MANDAL</label><select id="exp5-station">${stationsData.stations.map((name) => `<option ${name === station ? "selected" : ""}>${escapeHtml(name)}</option>`).join("")}</select></div>
      <div class="field"><label for="exp5-days">DAYS TO MONITOR</label><select id="exp5-days">${[7, 15, 31].map((n) => `<option value="${n}" ${n === days ? "selected" : ""}>First ${n} days</option>`).join("")}</select></div>
      <div class="field"><label for="exp5-sensor">CHART SENSOR</label><select id="exp5-sensor">${Object.keys(data.sensors).map((name) => `<option value="${name}" ${name === sensor ? "selected" : ""}>${escapeHtml(name.replace("_", " "))}</option>`).join("")}</select></div>
      <button class="tool-button" id="exp5-run">Run concurrent check</button>
    </div>
    <div class="stat-row">${Object.values(data.sensors).map((item) => stat(item.sensor.replace("_", " "), `${item.valid} valid · ${item.warnings.length} warnings · ${item.errors.length} errors`, item.errors.length ? "amber" : "teal")).join("")}</div>
    <div class="content-grid">
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>${escapeHtml(sensor.replace("_", " "))} readings</h2><p>First ${data.days_requested} days · valid observations only</p></div><span class="panel-kicker">LIMIT ${number(selectedSensor.threshold)} ${escapeHtml(selectedSensor.unit)}</span></div>
        ${lineChart(selectedSensor.readings.map((item) => ({ label: item.date, value: item.value })).filter((item) => item.value !== null), selectedSensor.unit)}
        <div class="chart-foot">Warning thresholds: temperature &gt; 41 °C · humidity &gt; 80% · wind &gt; 20 km/h. Valid ranges are checked first.</div>
      </section>
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>Monitor events</h2><p>${warnings.length} warnings · ${errors.length} invalid or missing readings</p></div></div>
        <div class="alert-feed">${events || `<div class="alert-row"><span class="alert-dot">✓</span><div class="alert-text">No warnings or invalid values in the selected window.</div></div>`}</div>
      </section>
    </div>
    <section class="panel" style="margin-top:15px"><div class="panel-header"><div class="panel-heading"><h2>Independent data-quality check</h2><p>DS20 north India station records · accepted range −10 to 55 °C</p></div><span class="panel-kicker">FAULT IN SOURCE DATA</span></div><div class="alert-feed">${faulty}</div></section>`;
  document.querySelector("#exp5-run").addEventListener("click", () => {
    showLoading("Running temperature, humidity, and wind monitors…");
    renderExperimentFive(document.querySelector("#exp5-station")?.value || station, Number(document.querySelector("#exp5-days")?.value || days), document.querySelector("#exp5-sensor")?.value || sensor).catch(showError);
  });
  ["exp5-station", "exp5-days", "exp5-sensor"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => {
      renderExperimentFive(
        document.querySelector("#exp5-station").value,
        Number(document.querySelector("#exp5-days").value),
        document.querySelector("#exp5-sensor").value,
      ).catch(showError);
    });
  });
}

async function renderExperimentSix(stations = ["Adilabad Rural", "Wanaparthy"]) {
  const data = await fetchJson(`/api/experiments/6?station=${encodeURIComponent(stations.join(","))}`);
  const allStations = await fetchJson("/api/stations");
  const chosen = data.stations[0];
  const rows = data.stations.map((item) => `<tr><td>${escapeHtml(item.station)}</td><td>${escapeHtml(item.district)}</td><td class="numeric">${item.days_observed}</td><td class="numeric">${number(item.maximum_temperature_c)} °C</td><td class="numeric">${number(item.mean_humidity_percent)}%</td><td class="numeric">${number(item.mean_wind_speed_kmh)} km/h</td><td class="numeric">${number(item.total_rainfall_mm)} mm</td><td>${item.alert_levels.map(badge).join(" ")}</td></tr>`).join("");
  content.innerHTML = `
    ${heading("EXPERIMENT 06 · COLLECTIONS & CLIMATE SUMMARY", "A station-level picture.", "Summarize complete temperature, humidity, wind, and rainfall observations for selected Telangana stations. Explore the experiment’s list, tuple, set, and dictionary concepts as actual outputs.", `<strong>${escapeHtml(data.dataset)}</strong>${escapeHtml(data.period)}`)}
    <div class="toolbar">
      <div class="field"><label for="exp6-station">ADD / SELECT STATION</label><select id="exp6-station">${allStations.stations.map((name) => `<option>${escapeHtml(name)}</option>`).join("")}</select></div>
      <button class="tool-button subtle" id="exp6-add">Add station</button><button class="tool-button" id="exp6-run">Update summary</button>
      <span class="hint">Choose 1–6 stations; default matches the original experiment.</span>
    </div>
    <div class="pill-row" id="exp6-selected">${stations.map((name) => `<span class="pill" data-station="${escapeHtml(name)}">${escapeHtml(name)} <button class="remove-station" data-remove="${escapeHtml(name)}" aria-label="Remove ${escapeHtml(name)}">×</button></span>`).join("")}</div>
    <div class="metric-grid" style="margin-top:15px">
      ${metric("Stations summarized", String(data.stations.length), "Selected from DS44", "teal")}
      ${metric("Days in report", String(data.stations.reduce((sum, item) => sum + item.days_observed, 0)), "Complete required sensor fields")}
      ${metric("Maximum observed", `${number(Math.max(...data.stations.map((item) => item.maximum_temperature_c)))} °C`, "Across selected stations", "amber")}
      ${metric("Data period", "May 2022", "Historical observations")}
    </div>
    <div class="content-grid">
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>${escapeHtml(chosen.station)} · daily Tmax</h2><p>May daily readings · complete records only</p></div><span class="chart-legend">Tmax °C</span></div>
        ${lineChart(chosen.series.map((item) => ({ label: item.date, value: item.temperature })), "°")}
      </section>
      <section class="panel"><div class="panel-header"><div class="panel-heading"><h2>Collection outputs</h2><p>Live values from the selected records</p></div></div>
        <div class="stack">
          <div><div class="panel-kicker">LIST · TEMPERATURES IN °F (FIRST 5)</div><div class="pill-row" style="margin-top:8px">${chosen.fahrenheit_preview.map((value) => `<span class="pill">${number(value)}°</span>`).join("")}</div></div>
          <div><div class="panel-kicker">SET · DISTINCT ALERT LEVELS</div><div class="pill-row" style="margin-top:8px">${chosen.alert_levels.map((level) => badge(level)).join("")}</div></div>
          <div>${stat("FILTER · readings ≥ 40 °C", `${chosen.heat_monitor_readings} days`)}</div>
          <div>${stat("REDUCE · total Tmax values", `${number(chosen.total_temperature_c)} °C`)}</div>
        </div>
      </section>
    </div>
    <section class="panel" style="margin-top:15px"><div class="panel-header"><div class="panel-heading"><h2>Station dictionary</h2><p>Per-station summaries · missing required sensor values excluded</p></div><span class="panel-kicker">DICT → JSON</span></div>${table(["Station", "District", "Days", "Peak Tmax", "Mean humidity", "Mean wind", "Rainfall", "Alert levels"], rows)}</section>
    <p class="table-note">Rainfall totals ignore missing rainfall values; they are not imputed. The ≥40 °C monitoring limit is a simplified lab threshold, not an official warning.</p>`;

  const readSelection = () => [...document.querySelectorAll("#exp6-selected .pill")].map((element) => element.dataset.station);
  document.querySelector("#exp6-add").addEventListener("click", () => {
    const value = document.querySelector("#exp6-station").value;
    const selected = readSelection();
    if (selected.includes(value)) return showToast("Station is already selected.");
    if (selected.length >= 6) return showToast("Select no more than six stations.");
    renderExperimentSix([...selected, value]).catch(showError);
  });
  document.querySelector("#exp6-run").addEventListener("click", () => renderExperimentSix(readSelection()).catch(showError));
  document.querySelectorAll("[data-remove]").forEach((button) => button.addEventListener("click", () => {
    const selected = readSelection().filter((name) => name !== button.dataset.remove);
    if (!selected.length) return showToast("Keep at least one station selected.");
    renderExperimentSix(selected).catch(showError);
  }));
}

document.querySelectorAll("[data-page]").forEach((button) => {
  button.addEventListener("click", () => {
    setActivePage(button.dataset.page);
    history.replaceState(null, "", button.dataset.page === "dashboard" ? location.pathname : `?experiment=${button.dataset.page}`);
    loadCurrentPage();
  });
});

document.querySelector("#refresh-button").addEventListener("click", () => {
  loadCurrentPage();
  showToast("Refreshed from the supplied CSV datasets.");
});

const initialExperiment = new URLSearchParams(location.search).get("experiment");
if (initialExperiment && PAGE_NAMES[initialExperiment]) currentPage = initialExperiment;
loadCurrentPage();
