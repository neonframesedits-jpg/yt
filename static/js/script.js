const form = document.getElementById("url-form");
const urlInput = document.getElementById("url-input");
const analyzeBtn = document.getElementById("analyze-btn");
const errorMsg = document.getElementById("error-msg");
const result = document.getElementById("result");
const thumb = document.getElementById("thumb");
const videoTitle = document.getElementById("video-title");
const videoUploader = document.getElementById("video-uploader");
const videoDuration = document.getElementById("video-duration");
const qualityGrid = document.getElementById("quality-grid");
const downloadBtn = document.getElementById("download-btn");

let currentUrl = "";
let selectedQuality = null;

function setBusy(button, busy) {
  button.disabled = busy;
  button.querySelector(".btn-text").style.opacity = busy ? "0" : "1";
  button.querySelector(".spinner").hidden = !busy;
}

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.hidden = false;
}

function hideError() {
  errorMsg.hidden = true;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();
  result.hidden = true;
  downloadBtn.disabled = true;
  selectedQuality = null;

  const url = urlInput.value.trim();
  currentUrl = url;

  setBusy(analyzeBtn, true);

  try {
    const response = await fetch("/api/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();

    if (!response.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }

    thumb.src = data.thumbnail || "";
    videoTitle.textContent = data.title || "Untitled video";
    videoUploader.textContent = data.uploader || "";
    videoDuration.textContent = data.duration || "";

    qualityGrid.innerHTML = "";
    data.qualities.forEach((q, index) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quality-btn";
      btn.textContent = q.label;
      btn.dataset.value = q.value;
      btn.addEventListener("click", () => selectQuality(btn, q.value));
      qualityGrid.appendChild(btn);
      if (index === 0) selectQuality(btn, q.value);
    });

    result.hidden = false;
  } catch (err) {
    showError("Could not reach the server. Please try again.");
  } finally {
    setBusy(analyzeBtn, false);
  }
});

function selectQuality(button, value) {
  document
    .querySelectorAll(".quality-btn")
    .forEach((el) => el.classList.remove("selected"));
  button.classList.add("selected");
  selectedQuality = value;
  downloadBtn.disabled = false;
}

downloadBtn.addEventListener("click", () => {
  if (!currentUrl || !selectedQuality) return;

  setBusy(downloadBtn, true);
  const params = new URLSearchParams({ url: currentUrl, quality: selectedQuality });
  window.location.href = `/api/download?${params.toString()}`;

  setTimeout(() => setBusy(downloadBtn, false), 2500);
});
