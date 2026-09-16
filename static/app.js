// Frontend Application Logic for Plum AI-Powered Amount Detection

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const tabText = document.getElementById("tab-text");
  const tabImage = document.getElementById("tab-image");
  const textView = document.getElementById("text-input-view");
  const imageView = document.getElementById("image-input-view");
  const billText = document.getElementById("bill-text");
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileInfo = document.getElementById("file-info");
  const fileName = document.getElementById("file-name");
  const clearFile = document.getElementById("clear-file");
  const btnProcess = document.getElementById("btn-process");
  const btnText = document.getElementById("btn-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const curlSnippet = document.getElementById("curl-snippet");
  const copyCurlBtn = document.getElementById("copy-curl-btn");
  const copyJsonBtn = document.getElementById("copy-json-btn");
  const finalJsonView = document.getElementById("final-json-view");

  // Output cards
  const s1Badge = document.getElementById("s1-badge");
  const s1Content = document.getElementById("s1-content");
  const s2Badge = document.getElementById("s2-badge");
  const s2Content = document.getElementById("s2-content");
  const s3Badge = document.getElementById("s3-badge");
  const s3Content = document.getElementById("s3-content");
  const s4Badge = document.getElementById("s4-badge");
  const s4MathContainer = document.getElementById("s4-math-container");
  const overallStatus = document.getElementById("overall-status");

  let activeMode = "text";
  let selectedFile = null;

  // Presets
  const presets = {
    pdfText: "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%",
    pdfOcr: "T0tal: Rs l200 | Pald: 1000 | Due: 200",
    hospital: "City Care Super-Speciality Hospital | Patient: John Doe | Consultation: INR 500 | Medicines: 900 | Lab Work: 600 | Total Bill: INR 2000 | Paid: 1500 | Due: 500 | Discount: 5%",
    guardrail: "### $$$ ??? [unreadable crumpled paper artifacts - no numbers here] ~~~"
  };

  document.getElementById("preset-pdf-text").addEventListener("click", () => {
    selectTextTab();
    billText.value = presets.pdfText;
    updateCurl(presets.pdfText);
  });

  document.getElementById("preset-pdf-ocr").addEventListener("click", () => {
    selectTextTab();
    billText.value = presets.pdfOcr;
    updateCurl(presets.pdfOcr);
  });

  document.getElementById("preset-hospital").addEventListener("click", () => {
    selectTextTab();
    billText.value = presets.hospital;
    updateCurl(presets.hospital);
  });

  document.getElementById("preset-guardrail").addEventListener("click", () => {
    selectTextTab();
    billText.value = presets.guardrail;
    updateCurl(presets.guardrail);
  });

  // Tab switching
  function selectTextTab() {
    activeMode = "text";
    tabText.classList.add("active");
    tabImage.classList.remove("active");
    textView.style.display = "block";
    imageView.style.display = "none";
    updateCurl(billText.value);
  }

  function selectImageTab() {
    activeMode = "image";
    tabImage.classList.add("active");
    tabText.classList.remove("active");
    textView.style.display = "none";
    imageView.style.display = "block";
    curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process-image" \\\n  -F "file=@sample_receipt.png"`;
  }

  tabText.addEventListener("click", selectTextTab);
  tabImage.addEventListener("click", selectImageTab);

  function updateCurl(txt) {
    const escaped = txt.replace(/"/g, '\\"');
    curlSnippet.textContent = `curl -X POST "http://localhost:8000/api/v1/process" \\\n  -H "Content-Type: application/json" \\\n  -d '{"text": "${escaped}"}'`;
  }

  billText.addEventListener("input", (e) => {
    updateCurl(e.target.value);
  });

  // Drag & drop file handling
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  clearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    fileInfo.style.display = "none";
    dropZone.style.display = "block";
  });

  function handleFile(file) {
    selectedFile = file;
    fileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    dropZone.style.display = "none";
    fileInfo.style.display = "flex";
  }

  // Copy Buttons
  copyCurlBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(curlSnippet.textContent);
    copyCurlBtn.textContent = "Copied!";
    setTimeout(() => copyCurlBtn.textContent = "Copy", 2000);
  });

  copyJsonBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(finalJsonView.textContent);
    copyJsonBtn.textContent = "Copied!";
    setTimeout(() => copyJsonBtn.textContent = "Copy JSON", 2000);
  });

  // Processing Execution
  btnProcess.addEventListener("click", async () => {
    setLoading(true);

    try {
      let response;
      if (activeMode === "text") {
        const text = billText.value.trim();
        if (!text) {
          alert("Please enter bill text or select a preset.");
          setLoading(false);
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
          setLoading(false);
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
      renderPipelineResults(data);
    } catch (err) {
      console.error(err);
      alert(`Error processing bill: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    if (isLoading) {
      btnProcess.disabled = true;
      btnSpinner.style.display = "inline-block";
      btnText.textContent = "Analyzing & Extracting...";
      overallStatus.textContent = "Processing";
      overallStatus.className = "badge badge-guard";
    } else {
      btnProcess.disabled = false;
      btnSpinner.style.display = "none";
      btnText.textContent = "Execute AI Pipeline";
    }
  }

  function renderPipelineResults(data) {
    // Check if guardrail triggered
    const isGuardrail = data.step1 && data.step1.status === "no_amounts_found";

    if (isGuardrail) {
      overallStatus.textContent = "Guardrail Triggered";
      overallStatus.className = "badge badge-guard";

      s1Badge.textContent = "Status: no_amounts_found";
      s1Badge.className = "badge badge-guard";
      s1Content.innerHTML = `
        <div style="color: #f87171; font-weight: 600; margin-bottom: 0.25rem;">
          &#9888; Guardrail Exit Triggered
        </div>
        <div>Reason: <code>${data.step1.reason}</code></div>
      `;

      s2Badge.textContent = "Skipped";
      s2Badge.className = "badge badge-guard";
      s2Content.innerHTML = `<span style="color: var(--text-muted);">No valid numeric tokens to normalize.</span>`;

      s3Badge.textContent = "Skipped";
      s3Badge.className = "badge badge-guard";
      s3Content.innerHTML = `<span style="color: var(--text-muted);">Context classification bypassed.</span>`;

      s4Badge.textContent = "Exit Condition";
      s4Badge.className = "badge badge-guard";
      s4MathContainer.innerHTML = "";
      finalJsonView.textContent = JSON.stringify(data.step4, null, 2);
      return;
    }

    // Success flow
    overallStatus.textContent = "Success";
    overallStatus.className = "badge badge-conf";

    // Step 1
    s1Badge.textContent = `Confidence: ${(data.step1.confidence * 100).toFixed(0)}%`;
    s1Badge.className = "badge badge-conf";
    const tokenPills = (data.step1.raw_tokens || []).map(t => {
      const isPercent = t.includes("%");
      return `<span class="token-pill ${isPercent ? 'percentage' : ''}">${t}</span>`;
    }).join("");
    s1Content.innerHTML = `
      <div><strong>Extracted Raw Tokens:</strong></div>
      <div class="tokens-list">${tokenPills || 'None'}</div>
      <div style="margin-top: 0.5rem; font-size: 0.82rem; color: #a5b4fc;">
        Currency Hint: <strong>${data.step1.currency_hint || 'INR'}</strong>
      </div>
    `;

    // Step 2
    if (data.step2) {
      s2Badge.textContent = `Confidence: ${(data.step2.normalization_confidence * 100).toFixed(0)}%`;
      s2Badge.className = "badge badge-conf";
      const normalizedPills = (data.step2.normalized_amounts || []).map(num => {
        return `<span class="token-pill corrected">${num}</span>`;
      }).join("");
      s2Content.innerHTML = `
        <div><strong>Cleaned Amounts (OCR Corrected & Filtered):</strong></div>
        <div class="tokens-list">${normalizedPills || 'None'}</div>
      `;
    }

    // Step 3
    if (data.step3) {
      s3Badge.textContent = `Confidence: ${(data.step3.confidence * 100).toFixed(0)}%`;
      s3Badge.className = "badge badge-conf";
      const amountCards = (data.step3.amounts || []).map(item => `
        <div class="amount-card">
          <div class="amount-type">${item.type}</div>
          <div class="amount-val">${data.step4.currency || 'INR'} ${item.value}</div>
        </div>
      `).join("");
      s3Content.innerHTML = `
        <div><strong>Context Classification:</strong></div>
        <div class="amounts-grid">${amountCards}</div>
      `;
    }

    // Step 4
    s4Badge.textContent = `Status: ${data.step4.status || 'ok'}`;
    s4Badge.className = "badge badge-conf";

    if (data.math_validation && data.math_validation.is_balanced !== null) {
      const isBal = data.math_validation.is_balanced;
      s4MathContainer.innerHTML = `
        <div class="math-banner" style="${isBal ? '' : 'background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); color: #fbbf24;'}">
          <span>&#10003; Arithmetic Check: <strong>${data.math_validation.equation}</strong></span>
          <span style="font-weight: 700;">${isBal ? 'Balanced (Audited)' : 'Discrepancy: ' + data.math_validation.discrepancy}</span>
        </div>
      `;
    } else {
      s4MathContainer.innerHTML = "";
    }

    // Final JSON Display strictly showing Step 4 JSON output
    finalJsonView.textContent = JSON.stringify(data.step4, null, 2);
  }

  // Initial trigger with default text
  btnProcess.click();
});
