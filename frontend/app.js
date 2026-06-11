const API_BASE = "http://127.0.0.1:8000";

const state = {
  projects: [],
  sites: [],
  audioFiles: [],
  jobs: [],
  detections: [],
  rawOutputs: [],
  reports: [],
  dashboard: null,
  summary: null,
};

const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function formatPercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function shortId(id) {
  return id ? id.slice(0, 8) : "unknown";
}

async function loadData() {
  $("#systemStatus").textContent = "Syncing API";
  const [projects, sites, audioFiles, jobs, detections, rawOutputs, reports] = await Promise.all([
    api("/projects"),
    api("/sites"),
    api("/audio-files"),
    api("/processing-jobs"),
    api("/detections"),
    api("/raw-model-outputs"),
    api("/reports"),
  ]);

  state.projects = projects;
  state.sites = sites;
  state.audioFiles = audioFiles;
  state.jobs = jobs;
  state.detections = detections;
  state.rawOutputs = rawOutputs;
  state.reports = reports;
  state.dashboard = projects[0] ? await api(`/projects/${projects[0].id}/dashboard`) : null;
  state.summary = state.dashboard?.summary || null;
  if (state.dashboard) {
    state.sites = state.dashboard.sites;
    state.audioFiles = state.dashboard.recent_audio_files;
    state.detections = state.dashboard.recent_detections;
  }

  render();
  $("#systemStatus").textContent = "API online";
}

function render() {
  renderSites();
  renderSummary();
  renderJobs();
  renderDetections();
  renderRawOutputs();
  renderReports();
  drawSpectrogram();
}

function renderSites() {
  const select = $("#siteSelect");
  select.innerHTML = state.sites
    .map((site) => `<option value="${site.id}">${site.name} · ${site.habitat_type || "habitat"}</option>`)
    .join("");
}

function renderSummary() {
  const summary = state.summary || {};
  $("#activityScore").textContent = Math.round(summary.biodiversity_activity_score || 0);
  $("#speciesRichness").textContent = summary.species_richness ?? 0;
  $("#noiseScore").textContent = Math.round(summary.noise_score || 0);
  $("#siteCount").textContent = summary.site_count ?? state.sites.length;
  $("#audioCount").textContent = summary.audio_file_count ?? state.audioFiles.length;
  $("#detectionCount").textContent = summary.detection_count ?? state.detections.length;
  const jobCounts = state.dashboard?.job_counts_by_status || {};
  const queuedFromDashboard = jobCounts.queued || state.jobs.filter((job) => job.status === "queued").length;
  $("#queuedCount").textContent = `${queuedFromDashboard} queued`;
}

function renderJobs() {
  $("#jobsTable").innerHTML =
    state.jobs
      .slice(0, 8)
      .map(
        (job) => `
          <tr>
            <td><span class="status ${job.status}">${job.status}</span></td>
            <td>${job.job_type}</td>
            <td>${shortId(job.audio_file_id)}</td>
          </tr>
        `,
      )
      .join("") || `<tr><td colspan="3">No jobs yet</td></tr>`;
}

function renderDetections() {
  $("#detectionsTable").innerHTML =
    state.detections
      .slice(0, 10)
      .map(
        (detection) => `
          <tr>
            <td><strong>${detection.label}</strong></td>
            <td>${detection.detection_type.replace("_", " ")}</td>
            <td>${formatPercent(detection.confidence)}</td>
                    <td>${detection.start_seconds.toFixed(1)}s - ${detection.end_seconds.toFixed(1)}s</td>
                    <td>
                      <div class="review-actions">
                        <span class="status ${detection.review_status}">${detection.review_status}</span>
                        <button type="button" data-review="${detection.id}:confirmed">Confirm</button>
                        <button type="button" data-review="${detection.id}:rejected">Reject</button>
                      </div>
                    </td>
                  </tr>
        `,
      )
      .join("") || `<tr><td colspan="4">No detections yet</td></tr>`;
}

function renderRawOutputs() {
  $("#rawOutputList").innerHTML =
    state.rawOutputs
      .slice(0, 4)
      .map(
        (output) => `
          <div class="raw-item">
            <strong>${output.output_format}</strong>
            <code>${JSON.stringify(output.payload)}</code>
          </div>
        `,
      )
      .join("") || `<div class="raw-item"><strong>Awaiting model output</strong><code>No raw payloads yet</code></div>`;
}

function renderReports() {
  $("#reportList").innerHTML =
    state.reports
      .slice(0, 5)
      .map(
        (report) => `
          <div class="report-item">
            <strong>${report.title}</strong>
            <span>${report.report_type} · ${report.status}</span>
          </div>
        `,
      )
      .join("") || `<div class="report-item"><strong>No reports yet</strong><span>Create a shell from the current project.</span></div>`;
}

function drawSpectrogram() {
  const canvas = $("#spectrogramCanvas");
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);

  const detections = Math.max(state.detections.length, 4);
  for (let x = 0; x < width; x += 10) {
    const wave = Math.sin(x / 24) * 24 + Math.cos(x / 57) * 18;
    const y = height / 2 + wave;
    const alpha = 0.18 + ((x % 70) / 70) * 0.22;
    context.fillStyle = `rgba(124, 226, 213, ${alpha})`;
    context.fillRect(x, y, 7, 70 + Math.sin(x / 19) * 25);
    context.fillStyle = `rgba(245, 209, 122, ${alpha * 0.75})`;
    context.fillRect(x, y - 85, 5, 42 + Math.cos(x / 21) * 18);
  }

  for (let index = 0; index < detections; index += 1) {
    const x = 110 + index * 170;
    context.beginPath();
    context.arc(x % width, 92 + (index % 3) * 54, 9, 0, Math.PI * 2);
    context.fillStyle = index % 2 ? "#7ce2d5" : "#f5d17a";
    context.fill();
  }
}

async function createAudioRecord(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.duration_seconds = Number(payload.duration_seconds || 0);

  $("#formStatus").textContent = "Creating audio record";
  const audio = await api("/audio-files", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("#formStatus").textContent = `Audio ${shortId(audio.id)} queued`;
  await loadData();
}

async function runQueuedJobs() {
  const queuedJobs = state.jobs.filter((job) => job.status === "queued");
  if (!queuedJobs.length) {
    $("#systemStatus").textContent = "No queued jobs";
    return;
  }

  $("#systemStatus").textContent = `Processing ${queuedJobs.length} job(s)`;
  for (const job of queuedJobs) {
    await api(`/processing-jobs/${job.id}/run-mock`, { method: "POST" });
  }
  await loadData();
}

async function createReportShell() {
  if (!state.projects[0]) return;
  await api("/reports", {
    method: "POST",
    body: JSON.stringify({
      project_id: state.projects[0].id,
      title: `Prototype Biodiversity Summary ${state.reports.length + 1}`,
      report_type: "prototype_summary",
    }),
  });
  await loadData();
}

function bindEvents() {
  $("#refreshButton").addEventListener("click", loadData);
  $("#runJobsButton").addEventListener("click", runQueuedJobs);
  $("#audioForm").addEventListener("submit", createAudioRecord);
  $("#createReportButton").addEventListener("click", createReportShell);
  $("#detectionsTable").addEventListener("click", async (event) => {
    const target = event.target.closest("[data-review]");
    if (!target) return;
    const [id, review_status] = target.dataset.review.split(":");
    await api(`/detections/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ review_status }),
    });
    await loadData();
  });
}

bindEvents();
loadData().catch((error) => {
  $("#systemStatus").textContent = "API unavailable";
  $("#formStatus").textContent = error.message;
});
