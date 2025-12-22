// ========== State Management ==========
let currentConfig = null;
let currentResults = null;
let latestResults = [];

// ========== DOM Elements ==========
const cvZipInput = document.getElementById("cvZip");
const dropZone = document.getElementById("dropZone");
const filePreview = document.getElementById("filePreview");
const fileName = document.getElementById("fileName");
const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");
const loading = document.getElementById("loading");
const resultsSection = document.getElementById("resultsSection");
const resultsTable = document.getElementById("resultsTable");
const detailsModal = document.getElementById("detailsModal");
const modalClose = document.querySelector(".modal-close");
const modalCloseBtn = document.querySelector(".modal-close-btn");

// Weight sliders
const weightSliders = {
  education: document.getElementById("education-weight"),
  experience: document.getElementById("experience-weight"),
  publications: document.getElementById("publications-weight"),
  coherence: document.getElementById("coherence-weight"),
  awards: document.getElementById("awards-weight"),
};

const weightValues = {
  education: document.getElementById("education-value"),
  experience: document.getElementById("experience-value"),
  publications: document.getElementById("publications-value"),
  coherence: document.getElementById("coherence-value"),
  awards: document.getElementById("awards-value"),
};

const subWeightSliders = {
  "edu-gpa": document.getElementById("edu-gpa"),
  "edu-degree": document.getElementById("edu-degree"),
  "edu-tier": document.getElementById("edu-tier"),
  "pub-if": document.getElementById("pub-if"),
  "pub-position": document.getElementById("pub-position"),
  "pub-venue": document.getElementById("pub-venue"),
};

const subWeightValues = {
  "edu-gpa": document.getElementById("edu-gpa-value"),
  "edu-degree": document.getElementById("edu-degree-value"),
  "edu-tier": document.getElementById("edu-tier-value"),
  "pub-if": document.getElementById("pub-if-value"),
  "pub-position": document.getElementById("pub-position-value"),
  "pub-venue": document.getElementById("pub-venue-value"),
};

const policyInputs = {
  missingPenalty: document.getElementById("missing-penalty"),
  minExperience: document.getElementById("min-experience"),
  domain: document.getElementById("domain"),
  firstAuthorBonus: document.getElementById("first-author-bonus"),
};

// ========== File Upload Handling ==========
dropZone.addEventListener("click", () => cvZipInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    cvZipInput.files = files;
    updateFilePreview(files[0].name);
    checkSubmitButton();
  }
});

cvZipInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    updateFilePreview(e.target.files[0].name);
    checkSubmitButton();
  }
});

function updateFilePreview(name) {
  filePreview.classList.remove("hidden");
  fileName.textContent = name;
}

// ========== Weight Slider Handling ==========
Object.entries(weightSliders).forEach(([key, slider]) => {
  slider.addEventListener("input", () => {
    updateWeightDisplay();
    updateConfigJson();
  });
});

Object.entries(subWeightSliders).forEach(([key, slider]) => {
  slider.addEventListener("input", () => {
    updateSubWeightDisplay(key);
    updateConfigJson();
  });
});

function updateWeightDisplay() {
  let total = 0;
  Object.entries(weightSliders).forEach(([key, slider]) => {
    const value = parseInt(slider.value);
    total += value;
    if (weightValues[key]) {
      weightValues[key].textContent = value + "%";
    }
  });
  document.getElementById("total-weight").textContent = total;

  // Warning if total != 100
  const totalWeight = document.querySelector(".weight-total");
  if (total !== 100) {
    totalWeight.style.background = "rgba(245, 101, 101, 0.1)";
    totalWeight.style.color = "#f56565";
  } else {
    totalWeight.style.background = "#f7fafc";
    totalWeight.style.color = "#2d3748";
  }
}

function updateSubWeightDisplay(key) {
  const slider = subWeightSliders[key];
  const value = parseInt(slider.value);
  if (subWeightValues[key]) {
    subWeightValues[key].textContent = value + "%";
  }
}

// ========== Tab Switching ==========
document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => {
    const tabName = button.dataset.tab;

    // Hide all tabs
    document.querySelectorAll(".tab-content").forEach((tab) => {
      tab.classList.remove("active");
    });
    document.querySelectorAll(".tab-button").forEach((btn) => {
      btn.classList.remove("active");
    });

    // Show selected tab
    document.getElementById(tabName + "-tab").classList.add("active");
    button.classList.add("active");
  });
});

// ========== Policy Inputs ==========
Object.values(policyInputs).forEach((input) => {
  if (input) {
    input.addEventListener("input", updateConfigJson);
  }
});

// ========== Config JSON Generation ==========
function getConfigObject() {
  return {
    weights: {
      education: parseInt(weightSliders.education.value) / 100,
      experience: parseInt(weightSliders.experience.value) / 100,
      publications: parseInt(weightSliders.publications.value) / 100,
      coherence: parseInt(weightSliders.coherence.value) / 100,
      awards_other: parseInt(weightSliders.awards.value) / 100,
    },
    subweights: {
      education: {
        gpa: parseInt(subWeightSliders["edu-gpa"].value) / 100,
        degree_level: parseInt(subWeightSliders["edu-degree"].value) / 100,
        university_tier: parseInt(subWeightSliders["edu-tier"].value) / 100,
      },
      publications: {
        if: parseInt(subWeightSliders["pub-if"].value) / 100,
        author_position: parseInt(subWeightSliders["pub-position"].value) / 100,
        venue_quality: parseInt(subWeightSliders["pub-venue"].value) / 100,
      },
    },
    policies: {
      missing_values_penalty: parseFloat(policyInputs.missingPenalty.value),
      min_months_experience_for_bonus: parseInt(
        policyInputs.minExperience.value
      ),
      domain: policyInputs.domain.value,
      first_author_bonus: parseFloat(policyInputs.firstAuthorBonus.value),
    },
  };
}

function updateConfigJson() {
  currentConfig = getConfigObject();
  const configTextarea = document.getElementById("configJson");
  configTextarea.value = JSON.stringify(currentConfig, null, 2);
}

function checkSubmitButton() {
  const hasFile = cvZipInput.files.length > 0;
  submitBtn.disabled = !hasFile;
}

// ========== Config Management ==========
document.getElementById("loadDefault").addEventListener("click", () => {
  // Reset to default values
  weightSliders.education.value = 30;
  weightSliders.experience.value = 30;
  weightSliders.publications.value = 25;
  weightSliders.coherence.value = 10;
  weightSliders.awards.value = 5;

  subWeightSliders["edu-gpa"].value = 50;
  subWeightSliders["edu-degree"].value = 20;
  subWeightSliders["edu-tier"].value = 30;

  subWeightSliders["pub-if"].value = 50;
  subWeightSliders["pub-position"].value = 30;
  subWeightSliders["pub-venue"].value = 20;

  policyInputs.missingPenalty.value = 0.1;
  policyInputs.minExperience.value = 24;
  policyInputs.domain.value = "NLP";
  policyInputs.firstAuthorBonus.value = 0.15;

  updateWeightDisplay();
  updateConfigJson();
});

document.getElementById("loadCustom").addEventListener("click", () => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const config = JSON.parse(event.target.result);
        applyConfigToUI(config);
        updateWeightDisplay();
        updateConfigJson();
      } catch (err) {
        alert("Invalid JSON file: " + err.message);
      }
    };
    reader.readAsText(file);
  });
  input.click();
});

function applyConfigToUI(config) {
  if (config.weights) {
    weightSliders.education.value = Math.round(config.weights.education * 100);
    weightSliders.experience.value = Math.round(
      config.weights.experience * 100
    );
    weightSliders.publications.value = Math.round(
      config.weights.publications * 100
    );
    weightSliders.coherence.value = Math.round(config.weights.coherence * 100);
    weightSliders.awards.value = Math.round(config.weights.awards_other * 100);
  }

  if (config.subweights) {
    if (config.subweights.education) {
      subWeightSliders["edu-gpa"].value = Math.round(
        config.subweights.education.gpa * 100
      );
      subWeightSliders["edu-degree"].value = Math.round(
        config.subweights.education.degree_level * 100
      );
      subWeightSliders["edu-tier"].value = Math.round(
        config.subweights.education.university_tier * 100
      );
    }
    if (config.subweights.publications) {
      subWeightSliders["pub-if"].value = Math.round(
        config.subweights.publications.if * 100
      );
      subWeightSliders["pub-position"].value = Math.round(
        config.subweights.publications.author_position * 100
      );
      subWeightSliders["pub-venue"].value = Math.round(
        config.subweights.publications.venue_quality * 100
      );
    }
  }

  if (config.policies) {
    if (config.policies.missing_values_penalty !== undefined) {
      policyInputs.missingPenalty.value =
        config.policies.missing_values_penalty;
    }
    if (config.policies.min_months_experience_for_bonus !== undefined) {
      policyInputs.minExperience.value =
        config.policies.min_months_experience_for_bonus;
    }
    if (config.policies.domain) {
      policyInputs.domain.value = config.policies.domain;
    }
    if (config.policies.first_author_bonus !== undefined) {
      policyInputs.firstAuthorBonus.value = config.policies.first_author_bonus;
    }
  }
}

document.getElementById("copyConfig").addEventListener("click", () => {
  const configTextarea = document.getElementById("configJson");
  configTextarea.select();
  document.execCommand("copy");

  const btn = document.getElementById("copyConfig");
  const originalText = btn.textContent;
  btn.textContent = "✓ Copied!";
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);
});

// ========== Submit Handler ==========
submitBtn.addEventListener("click", async () => {
  try {
    console.log("=== Submit button clicked ===");

    if (!cvZipInput.files.length) {
      alert("Please select a CV ZIP file");
      return;
    }

    console.log("File selected:", cvZipInput.files[0].name);
    console.log("Current config:", currentConfig);

    console.log("Setting UI state...");
    loading.style.display = "block";
    resultsSection.classList.add("hidden");
    submitBtn.disabled = true;

    console.log("Creating mappings...");
    // Default mappings
    const defaultMappings = {
      degree_levels: {
        phd: 1.0,
        master: 0.8,
        bachelor: 0.6,
        diploma: 0.4,
      },
      university_tiers: {
        MIT: 1.0,
        Stanford: 0.95,
        Harvard: 0.95,
        Oxford: 0.9,
        Cambridge: 0.9,
        "Top Tier": 0.9,
        "Tier 1": 0.7,
        "Tier 2": 0.5,
      },
      journal_impact: {
        Nature: 1.0,
        Science: 0.95,
        IEEE: 0.7,
        ACM: 0.65,
        Elsevier: 0.6,
      },
    };

    console.log("Creating FormData...");
    const formData = new FormData();
    formData.append("cvs_zip", cvZipInput.files[0]);
    formData.append("config", JSON.stringify(currentConfig));
    formData.append("mappings", JSON.stringify(defaultMappings));

    console.log("Sending request to /rank...");

    const response = await fetch("/rank", {
      method: "POST",
      body: formData,
    });

    console.log("Response status:", response.status);

    if (!response.ok) {
      const error = await response.json();
      console.error("Server error:", error);
      throw new Error(error.detail || "Server error");
    }

    const data = await response.json();
    console.log("Response data:", data);

    displayResults(data);
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("FULL ERROR STACK:", err);
    alert("❌ Error: " + err.message);
  } finally {
    loading.style.display = "none";
    submitBtn.disabled = false;
  }
});

// ========== Results Display ==========
function displayResults(data) {
  currentResults = data;
  latestResults = data.ranked_candidates || [];

  // Summary stats
  document.getElementById("totalCandidates").textContent = latestResults.length;

  if (latestResults.length > 0) {
    const scores = latestResults.map((c) => c.sys_score);
    const topScore = Math.max(...scores);
    const avgScore = (
      scores.reduce((a, b) => a + b, 0) / scores.length
    ).toFixed(2);
    const range = (topScore - Math.min(...scores)).toFixed(2);

    document.getElementById("topScore").textContent = topScore.toFixed(2);
    document.getElementById("avgScore").textContent = avgScore;
    document.getElementById("scoreRange").textContent = range;
  }

  // Results table
  resultsTable.innerHTML = "";
  latestResults.forEach((cv, index) => {
    const row = document.createElement("tr");
    row.innerHTML = `
            <td><span class="rank-badge">#${index + 1}</span></td>
            <td><strong>${escapeHtml(cv.name)}</strong></td>
            <td><span class="score">${
              cv.sys_score?.toFixed(2) || "N/A"
            }</span></td>
            <td>${(cv.subscores?.education || 0).toFixed(2)}</td>
            <td>${(cv.subscores?.experience || 0).toFixed(2)}</td>
            <td>${(cv.subscores?.publications || 0).toFixed(2)}</td>
            <td>
                <button class="action-btn" onclick="showDetails('${index}')">View Details</button>
            </td>
        `;
    resultsTable.appendChild(row);
  });

  // Explanations
  const explanationsContainer = document.getElementById("explanations");
  explanationsContainer.innerHTML = "";

  latestResults.slice(0, 3).forEach((cv, index) => {
    const card = document.createElement("div");
    card.className = "explanation-card";

    let reasonsHtml = "";
    if (cv.explanation && cv.explanation.reasons) {
      cv.explanation.reasons.forEach((reason) => {
        reasonsHtml += `<div class="explanation-reason"><strong>•</strong> ${escapeHtml(
          reason
        )}</div>`;
      });
    }

    card.innerHTML = `
            <h4>#{${index + 1} - ${escapeHtml(cv.name)}</h4>
            <p><strong>Score:</strong> ${cv.sys_score?.toFixed(2)}</p>
            ${reasonsHtml}
            ${
              cv.explanation?.summary
                ? `<p><em>${escapeHtml(cv.explanation.summary)}</em></p>`
                : ""
            }
        `;
    explanationsContainer.appendChild(card);
  });
}

function showDetails(index) {
  const cv = latestResults[index];
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");

  modalTitle.textContent = `Candidate #${index + 1}: ${escapeHtml(cv.name)}`;

  let detailsHtml = `
        <div style="margin-bottom: 1.5rem;">
            <h4>Scores</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;"><strong>Overall Score</strong></td>
                    <td style="padding: 0.5rem; text-align: right;"><strong>${cv.sys_score?.toFixed(
                      2
                    )}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;">Education</td>
                    <td style="padding: 0.5rem; text-align: right;">${(
                      cv.subscores?.education || 0
                    ).toFixed(2)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;">Experience</td>
                    <td style="padding: 0.5rem; text-align: right;">${(
                      cv.subscores?.experience || 0
                    ).toFixed(2)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;">Publications</td>
                    <td style="padding: 0.5rem; text-align: right;">${(
                      cv.subscores?.publications || 0
                    ).toFixed(2)}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 0.5rem;">Coherence</td>
                    <td style="padding: 0.5rem; text-align: right;">${(
                      cv.subscores?.coherence || 0
                    ).toFixed(2)}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem;">Awards & Other</td>
                    <td style="padding: 0.5rem; text-align: right;">${(
                      cv.subscores?.awards || 0
                    ).toFixed(2)}</td>
                </tr>
            </table>
        </div>
    `;

  if (cv.explanation?.reasons && cv.explanation.reasons.length > 0) {
    detailsHtml += `
            <div>
                <h4>Key Reasons</h4>
                <ul style="margin: 1rem 0; padding-left: 1.5rem;">
                    ${cv.explanation.reasons
                      .map((reason) => `<li>${escapeHtml(reason)}</li>`)
                      .join("")}
                </ul>
            </div>
        `;
  }

  modalBody.innerHTML = detailsHtml;
  detailsModal.classList.remove("hidden");
}

// Modal closing
modalClose.addEventListener("click", () => {
  detailsModal.classList.add("hidden");
});

modalCloseBtn.addEventListener("click", () => {
  detailsModal.classList.add("hidden");
});

detailsModal.addEventListener("click", (e) => {
  if (e.target === detailsModal) {
    detailsModal.classList.add("hidden");
  }
});

// ========== Export Functions ==========
document.getElementById("downloadCSV").addEventListener("click", () => {
  let csv =
    "Rank,Name,Overall Score,Education,Experience,Publications,Coherence,Awards\n";
  latestResults.forEach((cv, index) => {
    csv += `${index + 1},"${escapeHtml(cv.name)}",${cv.sys_score || 0},${
      cv.subscores?.education || 0
    },${cv.subscores?.experience || 0},${cv.subscores?.publications || 0},${
      cv.subscores?.coherence || 0
    },${cv.subscores?.awards || 0}\n`;
  });

  downloadFile(csv, "cv_ranking_report.csv", "text/csv");
});

document.getElementById("downloadJSON").addEventListener("click", () => {
  const json = JSON.stringify(
    {
      timestamp: new Date().toISOString(),
      config: currentConfig,
      results: latestResults,
    },
    null,
    2
  );

  downloadFile(json, "cv_ranking_report.json", "application/json");
});

document.getElementById("printResults").addEventListener("click", () => {
  window.print();
});

function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ========== Reset ==========
resetBtn.addEventListener("click", () => {
  cvZipInput.value = "";
  filePreview.classList.add("hidden");
  resultsSection.classList.add("hidden");
  resultsTable.innerHTML = "";
  document.getElementById("loadDefault").click();
  checkSubmitButton();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ========== Utility Functions ==========
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ========== Initialization ==========
document.addEventListener("DOMContentLoaded", () => {
  updateWeightDisplay();
  updateConfigJson();
  checkSubmitButton();
});
