const formatDate = (value) => new Date(`${value}T00:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" });

const activityIcon = (activity) => activity.sport === "Swim" ? "≈" : activity.type === "Interval" ? "⌁" : "↗";

function renderActivity(activity) {
  return `<div class="activity-row" data-activity-id="${activity.id}" role="button" tabindex="0" aria-label="Open ${activity.name} details">
    <span class="activity-icon">${activityIcon(activity)}</span>
    <div class="activity-name">${activity.name}<small>${formatDate(activity.date)} · ${activity.sport}</small></div>
    <div class="activity-value">${activity.distance_km.toFixed(1)} km<small>${activity.pace} / km</small></div>
    <span class="activity-type">${activity.type}</span>
  </div>`;
}

function renderDetail(activity) {
  document.querySelector("#activity-title").textContent = activity.name;
  document.querySelector("#activity-subtitle").textContent = `${formatDate(activity.date)} · ${activity.type} · ${activity.distance_km.toFixed(1)} km`;
  document.querySelector("#detail-metrics").innerHTML = [
    ["PACE", `${activity.pace} / km`],
    ["AVG HR", `${activity.avg_heart_rate} bpm`],
    ["CADENCE", `${activity.cadence || "-"} spm`],
    ["ELEVATION", `${activity.elevation_m} m`],
    ["LOAD", `${activity.training_load}`],
  ].map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join("");
  document.querySelector("#split-list").innerHTML = activity.splits.length
    ? activity.splits.map((split) => `<div class="split-row"><span>${split.km}</span><span>${split.distance_km.toFixed(1)} km</span><strong>${split.pace}</strong></div>`).join("")
    : `<div class="loading-row">Split data is available for running activities.</div>`;
  document.querySelector("#activity-modal").hidden = false;
}

async function openActivity(activityId) {
  const response = await fetch(`/api/activities/${activityId}`);
  if (!response.ok) throw new Error("Unable to load activity detail");
  renderDetail(await response.json());
}

function renderPlan(item) {
  const statusClass = item.status === "next" ? "next" : item.status === "adjusted" ? "adjusted" : "";
  return `<div class="plan-row ${statusClass}">
    <div class="plan-day">${item.day}<strong>${item.date}</strong></div>
    <div class="plan-copy"><span class="plan-type">${item.type}</span><strong>${item.title}</strong><small>${item.detail}</small></div>
  </div>`;
}

async function loadDashboard() {
  const [summaryResponse, activitiesResponse, planResponse, garminResponse] = await Promise.all([
    fetch("/api/dashboard"),
    fetch("/api/activities"),
    fetch("/api/training-plan"),
    fetch("/api/integrations/garmin/status"),
  ]);
  if (!summaryResponse.ok || !activitiesResponse.ok || !planResponse.ok || !garminResponse.ok) throw new Error("Unable to load coach data");
  const summary = await summaryResponse.json();
  const activities = await activitiesResponse.json();
  const plan = await planResponse.json();
  const garmin = await garminResponse.json();

  document.querySelector("#weekly-distance").textContent = summary.weekly_distance_km.toFixed(1);
  document.querySelector("#training-load").textContent = summary.training_load;
  document.querySelector("#load-bar").style.width = `${Math.min(summary.training_load / 3, 100)}%`;
  document.querySelector("#avg-pace").textContent = summary.avg_pace;
  document.querySelector("#recovery").textContent = summary.recovery;
  document.querySelector("#recovery-score").textContent = summary.recovery_score;
  document.querySelector("#training-details").textContent = `${summary.avg_heart_rate} bpm avg · ${summary.avg_cadence} spm cadence`;
  document.querySelector("#recommendation").textContent = summary.recommendation;
  document.querySelector("#week-range").textContent = `${formatDate(summary.week_start)} - ${formatDate(summary.week_end)}`;
  document.querySelector("#activity-list").innerHTML = activities.slice(0, 4).map(renderActivity).join("");
  document.querySelector("#plan-list").innerHTML = plan.map(renderPlan).join("");
  document.querySelector("#garmin-status").textContent = garmin.configured
    ? "Garmin access is configured; authorization flow is next."
    : "Apply for Garmin Developer Program access to enable sync.";
  document.querySelectorAll("[data-activity-id]").forEach((row) => {
    row.addEventListener("click", () => openActivity(row.dataset.activityId).catch(console.error));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") openActivity(row.dataset.activityId).catch(console.error);
    });
  });
}

document.querySelectorAll("[data-close-modal]").forEach((element) => {
  element.addEventListener("click", () => { document.querySelector("#activity-modal").hidden = true; });
});

document.querySelector("#garmin-connect").addEventListener("click", async () => {
  const statusResponse = await fetch("/api/integrations/garmin/status");
  const status = await statusResponse.json();
  if (!status.configured) {
    document.querySelector("#garmin-status").textContent = "Opening Garmin Developer Program...";
    window.open(status.developer_program_url, "_blank", "noopener");
    return;
  }
  const response = await fetch("/api/integrations/garmin/connect");
  const result = await response.json();
  if (!response.ok) document.querySelector("#garmin-status").textContent = result.detail;
});

loadDashboard().catch((error) => {
  document.querySelector("#recommendation").textContent = "The coach data could not be loaded. Check that the API is running.";
  console.error(error);
});
