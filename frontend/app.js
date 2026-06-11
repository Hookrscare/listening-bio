const API_BASE = window.location.origin;

const state = {
  organizations: [],
  projects: [],
  selectedProjectId: null,
  sites: [],
  audioFiles: [],
  jobs: [],
  detections: [],
  rawOutputs: [],
  reports: [],
  dashboard: null,
  summary: null,
  metrics: null,
};

const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) },
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
  const [organizations, projects, sites, audioFiles, jobs, detections, rawOutputs, reports] = await Promise.all([
    api("/organizations"),
    api("/projects"),
    api("/sites"),
    api("/audio-files"),
    api("/processing-jobs"),
    api("/detections"),
    api("/raw-model-outputs"),
    api("/reports"),
  ]);

  state.organizations = organizations;
  state.projects = projects;
  if (!state.selectedProjectId || !projects.some((project) => project.id === state.selectedProjectId)) {
    state.selectedProjectId = projects[0]?.id || null;
  }
  state.sites = sites;
  state.audioFiles = audioFiles;
  state.jobs = jobs;
  state.detections = detections;
  state.rawOutputs = rawOutputs;
  state.reports = reports;
  state.dashboard = state.selectedProjectId ? await api(`/projects/${state.selectedProjectId}/dashboard`) : null;
  state.summary = state.dashboard?.summary || null;
  state.metrics = state.dashboard?.metrics || null;
  if (state.dashboard) {
    state.sites = state.dashboard.sites;
    state.audioFiles = state.dashboard.recent_audio_files;
    state.detections = state.dashboard.recent_detections;
  }

  render();
  $("#systemStatus").textContent = "API online";
}

function render() {
  renderProjects();
  renderSites();
  renderProof();
  renderSummary();
  renderJobs();
  renderDetections();
  renderRawOutputs();
  renderReports();
  drawSpectrogram();
}

function renderProjects() {
  const select = $("#projectSelect");
  select.innerHTML = state.projects
    .map((project) => `<option value="${project.id}" ${project.id === state.selectedProjectId ? "selected" : ""}>${project.name}</option>`)
    .join("");
}

function renderSites() {
  const select = $("#siteSelect");
  select.innerHTML = state.sites
    .map((site) => `<option value="${site.id}">${site.name} · ${site.habitat_type || "habitat"}</option>`)
    .join("");
  select.disabled = state.sites.length === 0;
  $("#createAudioButton").disabled = state.sites.length === 0;
  if (state.sites.length === 0) {
    $("#formStatus").textContent = "Add a site before registering audio.";
  } else if ($("#formStatus").textContent === "Add a site before registering audio.") {
    $("#formStatus").textContent = "";
  }

  $("#siteList").innerHTML =
    state.sites
      .map((site) => {
        const audioCount = state.audioFiles.filter((audio) => audio.site_id === site.id).length;
        const coordinates =
          site.latitude && site.longitude ? `${site.latitude.toFixed(3)}, ${site.longitude.toFixed(3)}` : "Not set";
        return `
          <article class="site-card">
            <strong>${site.name}</strong>
            <span>${site.habitat_type || "Habitat type pending"}</span>
            <dl>
              <div>
                <dt>Coordinates</dt>
                <dd>${coordinates}</dd>
              </div>
              <div>
                <dt>Audio files</dt>
                <dd>${audioCount}</dd>
              </div>
            </dl>
          </article>
        `;
      })
      .join("") || `<article class="site-card"><strong>No sites yet</strong><span>Add a site to activate survey intake.</span></article>`;
}

function renderProof() {
  const hasApi = state.projects.length > 0 && state.sites.length > 0;
  const hasLoop = state.audioFiles.length > 0 && state.jobs.length > 0 && state.rawOutputs.length > 0 && state.detections.length > 0;
  $("#apiProof").textContent = hasApi ? "Connected" : "No seed data";
  $("#flowProof").textContent = hasLoop ? "Audio to review works" : "Create and run a job";
  $("#syncProof").textContent = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function renderSummary() {
  const summary = state.summary || {};
  $("#activityScore").textContent = Math.round(summary.biodiversity_activity_score || 0);
  $("#speciesRichness").textContent = summary.species_richness ?? 0;
  $("#noiseScore").textContent = Math.round(summary.noise_score || 0);
  $("#recordingHours").textContent = Number(state.metrics?.recording_hours || 0).toFixed(2);
  $("#detectionsPerHour").textContent = Number(state.metrics?.detections_per_hour || 0).toFixed(1);
  $("#confirmedPercent").textContent = `${Number(state.metrics?.confirmed_detection_percent || 0).toFixed(0)}%`;
  $("#siteCount").textContent = summary.site_count ?? state.sites.length;
  $("#audioCount").textContent = summary.audio_file_count ?? state.audioFiles.length;
  $("#detectionCount").textContent = summary.detection_count ?? state.detections.length;
  const jobCounts = state.dashboard?.job_counts_by_status || {};
  const queuedFromDashboard = jobCounts.queued || state.jobs.filter((job) => job.status === "queued").length;
  $("#queuedCount").textContent = `${queuedFromDashboard} queued`;
}

function renderJobs() {
  const hasQueued = state.jobs.some((job) => job.status === "queued");
  const hasProcessed = state.jobs.some((job) => job.status === "completed");
  const hasReviewed = state.detections.some((detection) => detection.review_status !== "unreviewed");
  $("#queuedStep").classList.toggle("active", hasQueued || hasProcessed);
  $("#processedStep").classList.toggle("active", hasProcessed);
  $("#reviewedStep").classList.toggle("active", hasReviewed);

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
            <td>
              <div class="confidence">
                <strong>${formatPercent(detection.confidence)}</strong>
                <span class="confidence-track"><span class="confidence-fill" style="width: ${Math.round(detection.confidence * 100)}%"></span></span>
              </div>
            </td>
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
      .join("") || `<tr><td colspan="5">No detections yet</td></tr>`;
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
  const uploadedFile = form.get("file");
  const payload = Object.fromEntries(form.entries());
  if (!payload.site_id) {
    $("#formStatus").textContent = "Add a site before registering audio.";
    return;
  }

  $("#formStatus").textContent = uploadedFile && uploadedFile.size ? "Uploading WAV" : "Creating audio record";
  let audio;
  if (uploadedFile && uploadedFile.size) {
    form.delete("file_name");
    form.delete("storage_uri");
    form.delete("idempotency_key");
    if (!form.get("duration_seconds")) form.delete("duration_seconds");
    audio = await api("/audio-files/upload", {
      method: "POST",
      body: form,
    });
  } else {
    delete payload.file;
    payload.duration_seconds = Number(payload.duration_seconds || 0);
    audio = await api("/audio-files", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }
  $("#formStatus").textContent = `Audio ${shortId(audio.id)} queued for ${uploadedFile && uploadedFile.size ? "BirdNET adapter" : "mock analysis"}`;
  await loadData();
}

async function createProject(event) {
  event.preventDefault();
  const organization = state.organizations[0];
  if (!organization) {
    $("#systemStatus").textContent = "No organization available";
    return;
  }
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.organization_id = organization.id;
  const project = await api("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.selectedProjectId = project.id;
  await loadData();
  $("#systemStatus").textContent = `Project ${project.name} created`;
}

async function createSite(event) {
  event.preventDefault();
  if (!state.selectedProjectId) {
    $("#systemStatus").textContent = "Create a project first";
    return;
  }
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.project_id = state.selectedProjectId;
  payload.latitude = payload.latitude ? Number(payload.latitude) : null;
  payload.longitude = payload.longitude ? Number(payload.longitude) : null;
  const site = await api("/sites", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadData();
  $("#systemStatus").textContent = `Site ${site.name} created`;
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
  $("#systemStatus").textContent = "Flow verified";
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

function openExport(kind) {
  if (!state.selectedProjectId) return;
  window.open(`${API_BASE}/exports/${kind}.csv?project_id=${state.selectedProjectId}`, "_blank", "noopener");
}

function bindEvents() {
  $("#refreshButton").addEventListener("click", loadData);
  $("#projectSelect").addEventListener("change", async (event) => {
    state.selectedProjectId = event.target.value;
    await loadData();
  });
  $("#projectForm").addEventListener("submit", createProject);
  $("#siteForm").addEventListener("submit", createSite);
  $("#runJobsButton").addEventListener("click", runQueuedJobs);
  $("#audioForm").addEventListener("submit", createAudioRecord);
  $("#createReportButton").addEventListener("click", createReportShell);
  $("#exportDetectionsButton").addEventListener("click", () => openExport("detections"));
  $("#exportSitesButton").addEventListener("click", () => openExport("sites"));
  $("#exportAudioButton").addEventListener("click", () => openExport("audio-files"));
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
