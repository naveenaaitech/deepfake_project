/**
 * SPECULUM — Media Authenticity Intelligence
 * Client-Side Controller & Django API Integration
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const htmlEl = document.documentElement;
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeLabel = document.getElementById("themeLabel");
  
  const dropZone = document.getElementById("dropZone");
  const dropZoneContent = document.getElementById("dropZoneContent");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const selectedFileCard = document.getElementById("selectedFileCard");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const fileSizeDisplay = document.getElementById("fileSizeDisplay");
  const fileTypeBadge = document.getElementById("fileTypeBadge");
  const fileIconWrapper = document.getElementById("fileIconWrapper");
  const removeFileBtn = document.getElementById("removeFileBtn");
  
  const errorBanner = document.getElementById("errorBanner");
  const errorMessage = document.getElementById("errorMessage");
  const dismissErrorBtn = document.getElementById("dismissErrorBtn");
  
  const analyzeVideoBtn = document.getElementById("analyzeVideoBtn");
  const analyzeAudioBtn = document.getElementById("analyzeAudioBtn");
  
  const resultPanel = document.getElementById("resultPanel");
  const resultLoadingState = document.getElementById("resultLoadingState");
  const resultDisconnectedState = document.getElementById("resultDisconnectedState");
  const loadingStateDesc = document.getElementById("loadingStateDesc");
  
  const resultFileName = document.getElementById("resultFileName");
  const resultAnalysisStatus = document.getElementById("resultAnalysisStatus");
  const resultClassification = document.getElementById("resultClassification");
  const resultConfidence = document.getElementById("resultConfidence");
  const resultExplanation = document.getElementById("resultExplanation");
  
  const statReviewedCount = document.getElementById("statReviewedCount");
  const statAuthenticCount = document.getElementById("statAuthenticCount");
  const statManipulatedCount = document.getElementById("statManipulatedCount");
  
  const reportsEmptyState = document.getElementById("reportsEmptyState");
  const reportsTableContainer = document.getElementById("reportsTableContainer");
  const reportsTableBody = document.getElementById("reportsTableBody");
  
  const toggleGuideBtn = document.getElementById("toggleGuideBtn");
  const guideBody = document.getElementById("guideBody");
  const guideArrow = document.getElementById("guideArrow");

  let currentFile = null;

  // --- Helpers: CSRF Token ---
  function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.getAttribute("content")) {
      return metaTag.getAttribute("content");
    }
    const inputTag = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (inputTag && inputTag.value) {
      return inputTag.value;
    }
    return "";
  }

  // --- Theme Toggle ---
  function initTheme() {
    const savedTheme = localStorage.getItem("speculum-theme") || "light";
    setTheme(savedTheme);
  }

  function setTheme(theme) {
    htmlEl.setAttribute("data-theme", theme);
    localStorage.setItem("speculum-theme", theme);
    if (themeLabel) {
      themeLabel.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const current = htmlEl.getAttribute("data-theme") || "light";
      setTheme(current === "light" ? "dark" : "light");
    });
  }

  initTheme();

  // --- Guide Drawer Toggle ---
  if (toggleGuideBtn && guideBody) {
    toggleGuideBtn.addEventListener("click", () => {
      const isHidden = guideBody.classList.contains("hidden");
      guideBody.classList.toggle("hidden", !isHidden);
      toggleGuideBtn.setAttribute("aria-expanded", String(isHidden));
      if (guideArrow) {
        guideArrow.style.transform = isHidden ? "rotate(180deg)" : "rotate(0deg)";
      }
    });
  }

  // --- Error Banner ---
  function showError(msg) {
    if (errorMessage && errorBanner) {
      errorMessage.textContent = msg;
      errorBanner.classList.remove("hidden");
    }
  }

  function clearError() {
    if (errorBanner) {
      errorBanner.classList.add("hidden");
    }
  }

  if (dismissErrorBtn) {
    dismissErrorBtn.addEventListener("click", clearError);
  }

  // --- File Selection & Drag/Drop ---
  if (browseBtn) {
    browseBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropZone) {
    dropZone.addEventListener("click", () => {
      if (!currentFile) fileInput.click();
    });

    ["dragenter", "dragover"].forEach((evt) => {
      dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
      });
    });

    dropZone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        handleFileSelection(files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      resetFileSelection();
    });
  }

  function handleFileSelection(file) {
    clearError();
    const validVideoExts = [".mp4", ".mov", ".avi", ".webm"];
    const validAudioExts = [".wav", ".mp3", ".m4a", ".aac"];
    const fileName = file.name.toLowerCase();
    const isVideo = validVideoExts.some((ext) => fileName.endsWith(ext));
    const isAudio = validAudioExts.some((ext) => fileName.endsWith(ext));

    if (!isVideo && !isAudio) {
      showError("Unsupported file type. Please upload a valid MP4, MOV, AVI, WEBM, WAV, or MP3 file.");
      return;
    }

    currentFile = file;

    if (fileNameDisplay) fileNameDisplay.textContent = file.name;
    if (fileSizeDisplay) fileSizeDisplay.textContent = formatBytes(file.size);
    if (fileTypeBadge) fileTypeBadge.textContent = isVideo ? "Video" : "Audio";

    if (fileIconWrapper) {
      fileIconWrapper.innerHTML = isVideo
        ? `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>`
        : `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>`;
    }

    if (dropZoneContent) dropZoneContent.classList.add("hidden");
    if (selectedFileCard) selectedFileCard.classList.remove("hidden");

    if (analyzeVideoBtn) analyzeVideoBtn.disabled = !isVideo;
    if (analyzeAudioBtn) analyzeAudioBtn.disabled = !isAudio;
  }

  function resetFileSelection() {
    currentFile = null;
    if (fileInput) fileInput.value = "";
    if (dropZoneContent) dropZoneContent.classList.remove("hidden");
    if (selectedFileCard) selectedFileCard.classList.add("hidden");
    if (analyzeVideoBtn) analyzeVideoBtn.disabled = true;
    if (analyzeAudioBtn) analyzeAudioBtn.disabled = true;
    clearError();
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // --- API Analysis Workflows ---
  if (analyzeVideoBtn) {
    analyzeVideoBtn.addEventListener("click", () => runAnalysis("video"));
  }

  if (analyzeAudioBtn) {
    analyzeAudioBtn.addEventListener("click", () => runAnalysis("audio"));
  }

  async function runAnalysis(type) {
    if (!currentFile) return;

    setLoading(true, `Uploading ${currentFile.name} to Django forensic pipeline...`);

    const formData = new FormData();
    formData.append("video", currentFile);

    try {
      // 1. Upload Video
      const uploadResp = await fetch("/api/videos/upload/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
        },
        body: formData,
      });

      if (!uploadResp.ok) {
        const err = await uploadResp.json();
        throw new Error(err.video ? err.video.join(" ") : "Failed to upload media file.");
      }

      const uploadData = await uploadResp.json();
      const analysisId = uploadData.analysis.id;

      // 2. Start Analysis
      setLoading(true, "Running deep learning verification & frame extraction...");
      await fetch(`/api/videos/start/${analysisId}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "Content-Type": "application/json",
        },
      });

      // 3. Poll or Check Result
      pollAnalysisResult(analysisId, currentFile.name);

    } catch (err) {
      setLoading(false);
      showError(err.message || "An error occurred during media inspection.");
    }
  }

  async function pollAnalysisResult(analysisId, fileName, maxAttempts = 60) {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const resp = await fetch(`/api/videos/result/${analysisId}/`);
        if (!resp.ok) throw new Error("Could not fetch analysis result.");
        const data = await resp.json();

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          setLoading(false);
          displayAnalysisResult(data, fileName);
          loadAuditHistory();
        } else if (attempts >= maxAttempts) {
          clearInterval(interval);
          setLoading(false);
          displayAnalysisResult(data, fileName);
          loadAuditHistory();
          showError("Analysis is taking longer than usual. Please check the Recent Reports table below.");
        }
      } catch (e) {
        clearInterval(interval);
        setLoading(false);
        showError("Failed to retrieve analysis progress.");
      }
    }, 1500);
  }

  function setLoading(isLoading, text = "") {
    if (resultLoadingState && resultDisconnectedState) {
      if (isLoading) {
        resultLoadingState.classList.remove("hidden");
        resultDisconnectedState.classList.add("hidden");
        if (loadingStateDesc) loadingStateDesc.textContent = text;
      } else {
        resultLoadingState.classList.add("hidden");
        resultDisconnectedState.classList.remove("hidden");
      }
    }
  }

  function displayAnalysisResult(data, fileName) {
    if (resultFileName) resultFileName.textContent = fileName;
    
    if (resultAnalysisStatus) {
      let statusClass = "tag-standby";
      if (data.status === "completed") statusClass = "tag-real";
      if (data.status === "failed") statusClass = "tag-deepfake";
      resultAnalysisStatus.innerHTML = `<span class="tag-status ${statusClass}">${data.status.toUpperCase()}</span>`;
    }

    const classification = data.result || "Analyzed";
    let tagClass = "tag-standby";
    if (data.result === "real") tagClass = "tag-real";
    if (data.result === "deepfake") tagClass = "tag-deepfake";
    if (data.result === "inconclusive") tagClass = "tag-unverified";

    if (resultClassification) {
      resultClassification.innerHTML = `<span class="tag-status ${tagClass}">${classification.toUpperCase()}</span>`;
    }

    if (resultConfidence) {
      resultConfidence.textContent = data.confidence !== null && data.confidence !== undefined
        ? `${(data.confidence * 100).toFixed(1)}%`
        : "N/A";
    }

    if (resultExplanation) {
      if (data.result === "deepfake") {
        resultExplanation.innerHTML = `Model flagged synthetic facial patterns and boundary blending anomalies with <strong>${((data.confidence || 0) * 100).toFixed(1)}%</strong> confidence. Synthetic manipulation detected.`;
      } else if (data.result === "real") {
        resultExplanation.innerHTML = `Facial micro-textures and boundary consistency align with authentic, non-synthesized footage with <strong>${((data.confidence || 0) * 100).toFixed(1)}%</strong> confidence.`;
      } else if (data.result === "inconclusive") {
        resultExplanation.innerHTML = data.error_message
          ? `${data.error_message}`
          : `Forensic indicators are ambiguous or insufficient face frames were detected. Analysis inconclusive.`;
      } else if (data.status === "failed") {
        resultExplanation.innerHTML = `<span style="color: var(--color-danger, #e53e3e);">${data.error_message || "Video analysis encountered an error."}</span>`;
      } else {
        resultExplanation.textContent = `Analysis status: ${data.status}. Video inspected and stored in database with record ID #${data.id}.`;
      }
    }
  }

  // --- Audit History & Session Statistics ---
  async function loadAuditHistory() {
    try {
      const resp = await fetch("/api/videos/history/");
      if (!resp.ok) return;
      const data = await resp.json();

      const items = data.results || [];
      if (statReviewedCount) statReviewedCount.textContent = items.length;

      let authenticCount = 0;
      let manipulatedCount = 0;

      items.forEach((item) => {
        if (item.result === "real") authenticCount++;
        if (item.result === "deepfake") manipulatedCount++;
      });

      if (statAuthenticCount) statAuthenticCount.textContent = authenticCount;
      if (statManipulatedCount) statManipulatedCount.textContent = manipulatedCount;

      if (items.length > 0 && reportsTableBody && reportsTableContainer && reportsEmptyState) {
        reportsEmptyState.classList.add("hidden");
        reportsTableContainer.classList.remove("hidden");
        
        reportsTableBody.innerHTML = items
          .map((item) => {
            const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : "—";
            const videoName = item.video ? item.video.split("/").pop() : `Asset #${item.id}`;
            const conf = item.confidence !== null && item.confidence !== undefined
              ? `${(item.confidence * 100).toFixed(1)}%`
              : "—";

            let resBadge = '<span class="tag-status tag-standby">Pending</span>';
            if (item.result === "real") resBadge = '<span class="tag-status tag-real">Likely Authentic</span>';
            if (item.result === "deepfake") resBadge = '<span class="tag-status tag-deepfake">Manipulated</span>';
            if (item.result === "inconclusive") resBadge = '<span class="tag-status tag-unverified">Inconclusive</span>';

            return `
              <tr>
                <td class="mono">#${item.id}</td>
                <td>${dateStr}</td>
                <td><strong>${videoName}</strong></td>
                <td>${resBadge}</td>
                <td class="mono">${conf}</td>
                <td><span class="tag-status tag-standby">${item.status}</span></td>
              </tr>
            `;
          })
          .join("");
      }
    } catch (e) {
      console.warn("Could not load audit history:", e);
    }
  }

  // Load audit records on init
  loadAuditHistory();
});
