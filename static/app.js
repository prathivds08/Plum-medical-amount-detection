/**
 * Plum AI-Powered Medical Bill Analyzer
 * Frontend Application Logic & State Management
 */

document.addEventListener("DOMContentLoaded", () => {
  // Navigation & Mode Switches
  const btnModeUpload = document.getElementById("btn-mode-upload");
  const btnModeText = document.getElementById("btn-mode-text");
  const viewUpload = document.getElementById("view-upload");
  const viewText = document.getElementById("view-text");

  // File Upload Elements
  const dropZone = document.getElementById("drop-zone");
  const btnBrowse = document.getElementById("btn-browse");
  const fileInput = document.getElementById("file-input");
  const filePreviewCard = document.getElementById("file-preview-card");
  const fileNameDisplay = document.getElementById("file-name-display");
  const fileSizeDisplay = document.getElementById("file-size-display");
  const btnRemoveFile = document.getElementById("btn-remove-file");
  const imagePreview = document.getElementById("image-preview");

  // Text Elements
  const billText = document.getElementById("bill-text");

  // Action Button & Progress
  const btnProcess = document.getElementById("btn-process");
  const btnTextElem = document.getElementById("btn-text");
  const progressBox = document.getElementById("progress-box");
  const pStep1 = document.getElementById("p-step-1");
  const pStep2 = document.getElementById("p-step-2");
  const pStep3 = document.getElementById("p-step-3");
  const pStep4 = document.getElementById("p-step-4");

  // Status & Confidence Elements
  const statusPill = document.getElementById("status-pill");
  const statusPillText = document.getElementById("status-pill-text");
  const statusSubtitle = document.getElementById("status-subtitle");
  const overallConfidenceVal = document.getElementById("overall-confidence-val");
  const confidenceBarFill = document.getElementById("confidence-bar-fill");
  const confidenceDesc = document.getElementById("confidence-desc");
  const guardrailAlert = document.getElementById("guardrail-alert");
  const guardrailReasonText = document.getElementById("guardrail-reason-text");

  // Bill Summary Elements
  const billSummarySection = document.getElementById("bill-summary-section");
  const currencyBadge = document.getElementById("currency-badge");
  const metricTotalVal = document.getElementById("metric-total-val");
  const metricTotalSub = document.getElementById("metric-total-sub");
  const metricPaidVal = document.getElementById("metric-paid-val");
  const metricPaidSub = document.getElementById("metric-paid-sub");
  const metricDueVal = document.getElementById("metric-due-val");
  const metricDueSub = document.getElementById("metric-due-sub");
  const otherAmountsContainer = document.getElementById("other-amounts-container");
  const otherChipsGrid = document.getElementById("other-chips-grid");
  const auditBanner = document.getElementById("audit-banner");
  const auditIcon = document.getElementById("audit-icon");
  const auditTitle = document.getElementById("audit-title");
  const auditEquation = document.getElementById("audit-equation");
  const auditBadge = document.getElementById("audit-badge");

  // Timeline Elements
  const aiTimelineSection = document.getElementById("ai-timeline-section");
  const tStep1Conf = document.getElementById("t-step1-conf");
  const tStep2Conf = document.getElementById("t-step2-conf");
  const tStep3Conf = document.getElementById("t-step3-conf");
  const tStep4Conf = document.getElementById("t-step4-conf");

  // Technical Details Elements
  const provenanceList = document.getElementById("provenance-list");
  const rawTokensPills = document.getElementById("raw-tokens-pills");
  const normTokensPills = document.getElementById("norm-tokens-pills");
  const finalJsonView = document.getElementById("final-json-view");
  const copyJsonBtn = document.getElementById("copy-json-btn");
  const curlSnippet = document.getElementById("curl-snippet");
  const copyCurlBtn = document.getElementById("copy-curl-btn");

  // State
  let activeMode = "text"; // "upload" or "text"
  let selectedFile = null;

  // Currency Symbols
  const currencyMap = {
    INR: "₹",
    USD: "$",
    EUR: "€",
    GBP: "£",
    CAD: "C$",
    AUD: "A$"
  };

  function getCurrencySymbol(code) {
    if (!code) return "₹";
    const upper = code.toUpperCase();
    return currencyMap[upper] || upper;
  }

  function formatMoney(amount, currencyCode) {
    if (amount === undefined || amount === null) return "--";
    const symbol = getCurrencySymbol(currencyCode);
    const formattedNum = Number(amount).toLocaleString();
    return `${symbol}${formattedNum}`;
  }

  function humanizeType(type) {
    if (!type) return "Amount";
    const dict = {
      total_bill: "Total Bill",
      paid: "Amount Paid",
      due: "Amount Due",
      discount: "Discount",
      consultation: "Consultation Fee",
      medicines: "Medicines & Supplies",
      lab_work: "Lab & Diagnostics"
    };
    return dict[type.toLowerCase()] || type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }

  // Preset Configurations
  const presets = {
    pdfText: "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%",
    pdfOcr: "T0tal: Rs l200 | Pald: 1000 | Due: 200",
    hospital: "City Care Super-Speciality Hospital | Patient: John Doe | Consultation: INR 500 | Medicines: 900 | Lab Work: 600 | Total Bill: INR 2000 | Paid: 1500 | Due: 500 | Discount: 5%",
    guardrail: "### $$$ ??? [unreadable crumpled paper artifacts - no numbers here] ~~~"
  };

  // Switch Active Mode
  function setMode(mode) {
    activeMode = mode;
    if (mode === "upload") {
      btnModeUpload.classList.add("active");
      btnModeText.classList.remove("active");
      viewUpload.style.display = "block";
      viewText.style.display = "none";
      if (selectedFile) {
        curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process-image" \\\n  -F "file=@${selectedFile.name}"`;
      } else {
        curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process-image" \\\n  -F "file=@sample_receipt_clean.png"`;
      }
    } else {
      btnModeText.classList.add("active");
      btnModeUpload.classList.remove("active");
      viewText.style.display = "block";
      viewUpload.style.display = "none";
      updateCurlSnippet(billText.value);
    }
  }

  btnModeUpload.addEventListener("click", () => setMode("upload"));
  btnModeText.addEventListener("click", () => setMode("text"));

  function updateCurlSnippet(txt) {
    const escaped = (txt || "").replace(/"/g, '\\"');
    curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process" \\\n  -H "Content-Type: application/json" \\\n  -d '{"text": "${escaped}"}'`;
  }

  billText.addEventListener("input", (e) => {
    if (activeMode === "text") {
      updateCurlSnippet(e.target.value);
    }
  });

  // Presets Handlers
  const presetButtons = [
    { id: "preset-pdf-text", mode: "text", val: presets.pdfText },
    { id: "preset-pdf-ocr", mode: "text", val: presets.pdfOcr },
    { id: "preset-hospital", mode: "text", val: presets.hospital },
    { id: "preset-guardrail", mode: "text", val: presets.guardrail }
  ];

  function setActivePresetBadge(activeBtn) {
    document.querySelectorAll(".preset-badge").forEach(btn => btn.classList.remove("active"));
    if (activeBtn) activeBtn.classList.add("active");
  }

  presetButtons.forEach(p => {
    const btn = document.getElementById(p.id);
    if (btn) {
      btn.addEventListener("click", () => {
        setActivePresetBadge(btn);
        setMode(p.mode);
        billText.value = p.val;
        updateCurlSnippet(p.val);
        triggerAnalysis();
      });
    }
  });

  // Preset: Scanned Receipt (loads synthetic clean image)
  const presetImageBtn = document.getElementById("preset-image-sample");
  if (presetImageBtn) {
    presetImageBtn.addEventListener("click", async () => {
      setActivePresetBadge(presetImageBtn);
      setMode("upload");

      try {
        const res = await fetch("/sample_data/sample_receipt_clean.png");
        if (res.ok) {
          const blob = await res.blob();
          const file = new File([blob], "sample_receipt_clean.png", { type: "image/png" });
          handleSelectedFile(file);
          triggerAnalysis();
        } else {
          // If direct fetch fails, switch to standard sample
          setMode("text");
          billText.value = presets.pdfOcr;
          triggerAnalysis();
        }
      } catch (e) {
        console.error("Failed to load sample image:", e);
      }
    });
  }

  // File Upload Handlers
  dropZone.addEventListener("click", (e) => {
    if (e.target !== btnBrowse) fileInput.click();
  });
  btnBrowse.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  btnRemoveFile.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    imagePreview.src = "";
    imagePreview.style.display = "none";
    filePreviewCard.style.display = "none";
    dropZone.style.display = "block";
    curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process-image" \\\n  -F "file=@sample_receipt_clean.png"`;
  });

  function handleSelectedFile(file) {
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = `${(file.size / 1024).toFixed(1)} KB`;
    dropZone.style.display = "none";
    filePreviewCard.style.display = "block";

    // If image, render thumbnail preview
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (event) => {
        imagePreview.src = event.target.result;
        imagePreview.style.display = "block";
      };
      reader.readAsDataURL(file);
    } else {
      imagePreview.style.display = "none";
    }

    curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process-image" \\\n  -F "file=@${file.name}"`;
  }

  // Copy Buttons
  copyJsonBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(finalJsonView.textContent);
    copyJsonBtn.textContent = "Copied!";
    setTimeout(() => copyJsonBtn.textContent = "Copy JSON", 2000);
  });

  copyCurlBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(curlSnippet.textContent);
    copyCurlBtn.textContent = "Copied!";
    setTimeout(() => copyCurlBtn.textContent = "Copy cURL", 2000);
  });

  // Multi-step Progress Animation
  let progressInterval = null;

  function startProgressAnimation() {
    progressBox.style.display = "block";
    btnProcess.disabled = true;
    btnTextElem.textContent = "Analyzing Document...";

    const steps = [pStep1, pStep2, pStep3, pStep4];
    steps.forEach(s => {
      s.className = "p-step";
      s.querySelector(".p-icon").textContent = "⏳";
    });

    let current = 0;
    steps[0].className = "p-step active";
    steps[0].querySelector(".p-icon").textContent = "●";

    progressInterval = setInterval(() => {
      if (current < steps.length - 1) {
        steps[current].className = "p-step done";
        steps[current].querySelector(".p-icon").textContent = "✓";
        current++;
        steps[current].className = "p-step active";
        steps[current].querySelector(".p-icon").textContent = "●";
      }
    }, 400);
  }

  function stopProgressAnimation() {
    if (progressInterval) clearInterval(progressInterval);
    const steps = [pStep1, pStep2, pStep3, pStep4];
    steps.forEach(s => {
      s.className = "p-step done";
      s.querySelector(".p-icon").textContent = "✓";
    });
    setTimeout(() => {
      progressBox.style.display = "none";
      btnProcess.disabled = false;
      btnTextElem.textContent = "Analyze Bill";
    }, 450);
  }

  // Trigger Analysis Flow
  async function triggerAnalysis() {
    startProgressAnimation();

    try {
      let response;
      if (activeMode === "text") {
        const text = billText.value.trim();
        if (!text) {
          alert("Please enter bill text or select a sample preset.");
          stopProgressAnimation();
          return;
        }

        response = await fetch("/api/v1/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text })
        });
      } else {
        if (!selectedFile) {
          alert("Please select or drop an image file first.");
          stopProgressAnimation();
          return;
        }

        const formData = new FormData();
        formData.append("file", selectedFile);

        response = await fetch("/api/v1/process-image", {
          method: "POST",
          body: formData
        });
      }

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      renderDashboardResults(data);
    } catch (err) {
      console.error(err);
      alert(`Error analyzing document: ${err.message}`);
    } finally {
      stopProgressAnimation();
    }
  }

  btnProcess.addEventListener("click", triggerAnalysis);

  // Render Dashboard Results
  function renderDashboardResults(data) {
    // 1. Check for Guardrail Trigger (e.g. unreadable noisy document)
    const isGuardrail = data.step1 && data.step1.status === "no_amounts_found";

    if (isGuardrail) {
      renderGuardrailState(data);
      return;
    }

    // 2. Standard Success Flow
    renderSuccessState(data);
  }

  function renderGuardrailState(data) {
    // Status Badge
    statusPill.className = "status-pill status-pill-danger";
    statusPillText.textContent = "Document Unreadable";
    statusSubtitle.textContent = "The document was analyzed, but no legible amounts could be recognized.";

    // Confidence
    overallConfidenceVal.textContent = "0%";
    confidenceBarFill.style.width = "0%";
    confidenceDesc.textContent = "Low confidence — please verify manually or try a clearer image.";

    // Show Guardrail Alert Box
    guardrailAlert.style.display = "flex";
    guardrailReasonText.textContent = `The AI could not confidently detect financial amounts. Reason: "${data.step1.reason || 'document too noisy'}".`;

    // Hide Main Bill Summary Cards
    billSummarySection.style.display = "none";

    // Timeline Update
    tStep1Conf.textContent = "Status: Exit Guardrail";
    tStep2Conf.textContent = "Skipped";
    tStep3Conf.textContent = "Skipped";
    tStep4Conf.textContent = "Exit Condition";

    // Populate Technical Details
    provenanceList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">No valid amounts extracted to establish textual provenance.</div>`;
    rawTokensPills.innerHTML = `<span style="color: var(--text-dim); font-size: 0.8rem;">No numeric tokens found</span>`;
    normTokensPills.innerHTML = `<span style="color: var(--text-dim); font-size: 0.8rem;">None</span>`;
    finalJsonView.textContent = JSON.stringify(data.step4, null, 2);
  }

  function renderSuccessState(data) {
    // Hide Guardrail Alert Box, Show Summary Section
    guardrailAlert.style.display = "none";
    billSummarySection.style.display = "block";

    const currency = (data.step4 && data.step4.currency) || (data.step1 && data.step1.currency_hint) || "INR";
    const symbol = getCurrencySymbol(currency);
    currencyBadge.textContent = `Currency: ${currency} (${symbol})`;

    // Compute Confidence
    const step1Conf = (data.step1 && data.step1.confidence) || 0.75;
    const step2Conf = (data.step2 && data.step2.normalization_confidence) || 0.8;
    const step3Conf = (data.step3 && data.step3.confidence) || 0.8;
    const avgConf = Math.round(step3Conf * 100);

    overallConfidenceVal.textContent = `${avgConf}%`;
    confidenceBarFill.style.width = `${avgConf}%`;

    if (avgConf >= 80) {
      statusPill.className = "status-pill status-pill-success";
      statusPillText.textContent = "Analysis Complete";
      statusSubtitle.textContent = "Your document was successfully analyzed and verified.";
      confidenceDesc.textContent = "High confidence — financial values were cleanly identified.";
    } else if (avgConf >= 50) {
      statusPill.className = "status-pill status-pill-warning";
      statusPillText.textContent = "Review Recommended";
      statusSubtitle.textContent = "Amounts were extracted with moderate confidence.";
      confidenceDesc.textContent = "Moderate confidence — you may want to verify this amount.";
    } else {
      statusPill.className = "status-pill status-pill-danger";
      statusPillText.textContent = "Low Confidence";
      statusSubtitle.textContent = "Text extraction was noisy or uncertain.";
      confidenceDesc.textContent = "Low confidence — please verify this amount manually.";
    }

    // Extract Financial Values by Type
    const amounts = (data.step4 && data.step4.amounts) || (data.step3 && data.step3.amounts) || [];
    let totalObj = null;
    let paidObj = null;
    let dueObj = null;
    const otherItems = [];

    amounts.forEach(item => {
      const type = (item.type || "").toLowerCase();
      if (type === "total_bill" || type === "total") {
        totalObj = item;
      } else if (type === "paid" || type === "amount_paid") {
        paidObj = item;
      } else if (type === "due" || type === "amount_due" || type === "balance") {
        dueObj = item;
      } else {
        otherItems.push(item);
      }
    });

    // Populate Big 3 Cards
    if (totalObj) {
      metricTotalVal.textContent = formatMoney(totalObj.value, currency);
      metricTotalSub.textContent = "Overall billed amount";
    } else {
      metricTotalVal.textContent = "--";
      metricTotalSub.textContent = "Not specified";
    }

    if (paidObj) {
      metricPaidVal.textContent = formatMoney(paidObj.value, currency);
      metricPaidSub.textContent = "Settled payments";
    } else {
      metricPaidVal.textContent = "--";
      metricPaidSub.textContent = "Not specified";
    }

    if (dueObj) {
      metricDueVal.textContent = formatMoney(dueObj.value, currency);
      metricDueSub.textContent = "Remaining balance";
    } else {
      metricDueVal.textContent = "--";
      metricDueSub.textContent = "Not specified";
    }

    // Populate Secondary Items (e.g. Medicines, Consultation, Discount)
    if (otherItems.length > 0) {
      otherAmountsContainer.style.display = "block";
      otherChipsGrid.innerHTML = otherItems.map(item => `
        <div class="other-chip">
          <span class="other-chip-label">${humanizeType(item.type)}:</span>
          <span class="other-chip-val">${formatMoney(item.value, currency)}</span>
        </div>
      `).join("");
    } else {
      otherAmountsContainer.style.display = "none";
      otherChipsGrid.innerHTML = "";
    }

    // Mathematical Consistency Audit
    if (data.math_validation && data.math_validation.is_balanced !== null) {
      auditBanner.style.display = "flex";
      const isBal = data.math_validation.is_balanced;
      if (isBal) {
        auditBanner.className = "audit-banner";
        auditIcon.textContent = "✓";
        auditTitle.textContent = "Calculations Balanced";
        auditEquation.textContent = `Total Bill matches Paid + Due (${data.math_validation.equation})`;
        auditBadge.textContent = "Audited";
      } else {
        auditBanner.className = "audit-banner discrepancy";
        auditIcon.textContent = "⚠";
        auditTitle.textContent = "Calculation Discrepancy";
        auditEquation.textContent = `Equation ${data.math_validation.equation} has a variance of ${symbol}${data.math_validation.discrepancy}.`;
        auditBadge.textContent = "Review Needed";
      }
    } else {
      auditBanner.style.display = "none";
    }

    // Timeline Steps Micro-confidence
    tStep1Conf.textContent = `Confidence: ${(step1Conf * 100).toFixed(0)}%`;
    tStep2Conf.textContent = `Confidence: ${(step2Conf * 100).toFixed(0)}%`;
    tStep3Conf.textContent = `Confidence: ${(step3Conf * 100).toFixed(0)}%`;
    tStep4Conf.textContent = `Status: ${data.step4.status || 'OK'}`;

    // Technical Details & Provenance
    provenanceList.innerHTML = amounts.map(item => `
      <div class="provenance-item">
        <div>
          <span class="prov-type">${humanizeType(item.type)}</span>
          <span class="prov-val" style="margin-left: 0.75rem;">${formatMoney(item.value, currency)}</span>
        </div>
        <div class="prov-source">${item.source || 'No text snippet'}</div>
      </div>
    `).join("") || `<div style="color: var(--text-muted);">No provenance items.</div>`;

    // Raw Tokens vs Normalized Tokens
    const rawTokens = (data.step1 && data.step1.raw_tokens) || [];
    rawTokensPills.innerHTML = rawTokens.map(t => {
      const isPercent = t.includes("%");
      return `<span class="pill-token ${isPercent ? 'percent' : ''}">${t}</span>`;
    }).join("") || `<span style="color: var(--text-dim); font-size: 0.8rem;">None</span>`;

    const normAmounts = (data.step2 && data.step2.normalized_amounts) || [];
    normTokensPills.innerHTML = normAmounts.map(n => `
      <span class="pill-token corrected">${n}</span>
    `).join("") || `<span style="color: var(--text-dim); font-size: 0.8rem;">None</span>`;

    // Final JSON Display
    finalJsonView.textContent = JSON.stringify(data.step4, null, 2);
  }

  // Initial trigger with default sample so dashboard is populated on first load
  triggerAnalysis();
});
