// Point this at your running backend (see backend/main.py).
const API_URL = "http://127.0.0.1:8000/analyze";

const form = document.getElementById("analyze-form");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("error");
const loadingBox = document.getElementById("loading");
const resultsBox = document.getElementById("results");
const scoreElement = document.querySelector('.score-circle');
const score = 52; // Target score out of 100

scoreElement.style.setProperty('--score-pct', `${score}%`);

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const resumeFile = document.getElementById("resume-file").files[0];
  const jobDescription = document.getElementById("job-description").value;

  hide(errorBox);
  hide(resultsBox);
  show(loadingBox);
  submitBtn.disabled = true;

  const formData = new FormData();
  formData.append("resume", resumeFile);
  formData.append("job_description", jobDescription);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Request failed with status ${response.status}`);
    }

    const data = await response.json();
    renderResults(data);
  } catch (err) {
    errorBox.textContent = err.message || "Something went wrong. Is the backend running?";
    show(errorBox);
  } finally {
    hide(loadingBox);
    submitBtn.disabled = false;
  }
});

function renderResults(data) {
  document.getElementById("overall-score").textContent = data.overall_score;

  const subScoresEl = document.getElementById("sub-scores");
  subScoresEl.innerHTML = "";
  const labels = {
    keyword_match: "Keyword match",
    formatting: "Formatting",
    action_verbs: "Action verbs",
    quantification: "Quantified impact",
  };
  for (const [key, value] of Object.entries(data.sub_scores)) {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `<span class="label">${labels[key] || key}</span><span class="leader"></span><span class="value">${value}%</span>`;
    subScoresEl.appendChild(row);
  }

  fillList("strengths-list", data.strengths);
  fillList("weaknesses-list", data.weaknesses);
  fillList("suggestions-list", data.suggestions);

  fillTags("matched-keywords", data.matched_keywords);
  fillTags("missing-keywords", data.missing_keywords);

  const aiBanner = document.getElementById("ai-banner");
  const aiFeedback = document.getElementById("ai-overall-feedback");
  if (data.ai_powered) {
    aiBanner.textContent = "✨ Suggestions rewritten by Gemini";
    show(aiBanner);
    if (data.ai_overall_feedback) {
      aiFeedback.textContent = data.ai_overall_feedback;
      show(aiFeedback);
    } else {
      hide(aiFeedback);
    }
  } else {
    hide(aiBanner);
    hide(aiFeedback);
  }

  show(resultsBox);
}

function fillList(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items || items.length === 0) {
    el.innerHTML = "<li>None found.</li>";
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  }
}

function fillTags(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items || items.length === 0) {
    el.innerHTML = "<li>None</li>";
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  }
}

function show(el) { el.classList.remove("hidden"); }
function hide(el) { el.classList.add("hidden"); }
