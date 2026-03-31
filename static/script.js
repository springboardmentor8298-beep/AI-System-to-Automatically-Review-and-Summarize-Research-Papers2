const range = document.getElementById("max_papers");
const rangeValue = document.getElementById("rangeValue");

range.oninput = () => {
    rangeValue.innerText = range.value;
};

function showStatus(msg, type) {
    const s = document.getElementById("status");
    s.innerText = msg;
    s.className = "status " + type;
    s.style.display = "block";

    if (type !== "loading") {
        setTimeout(() => s.style.display = "none", 3000);
    }
}

async function fetchPapers() {
    const topic = document.getElementById("topic").value;
    const max_papers = document.getElementById("max_papers").value;

    showStatus("Fetching papers...", "loading");

    const res = await fetch("/fetch", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({topic, max_papers})
    });

    const data = await res.json();

    const papersDiv = document.getElementById("papers");
    papersDiv.innerHTML = "";

    data.forEach(p => {
        papersDiv.innerHTML += `
            <div class="paper paper-card">
                <h3>${p.title}</h3>
                <p class="paper-filename">${p.pdf_file}</p>
                <button onclick="analyzePaper('${p.pdf_file}')">Analyze</button>
                <a href="${p.pdf_url}" target="_blank">
                    <button class="btn-download">Download PDF</button>
                </a>
            </div>
        `;
    });

    showStatus("Papers Loaded!", "success");
}

async function analyzePaper(pdf) {
    showStatus("Analyzing...", "loading");

    const res = await fetch("/process", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({pdf})
    });

    const result = await res.json();

    const analysis = document.getElementById("analysis");

    analysis.innerHTML = `
        <div class="analysis-box">
            <h3>Title: ${result.title}</h3>
            <h4>Quality Score: ${result.quality_score}</h4>
        </div>
        <div class="analysis-box">
            <h3>Abstract</h3>
            <p>${result.abstract.substring(0, 500)}...</p>
        </div>
        <div class="analysis-box">
            <h3>Introduction</h3>
            <p>${result.introduction.substring(0, 400)}...</p>
        </div>
        <div class="analysis-box">
            <h3>Key Findings</h3>
            <pre>${result.key_findings}</pre>
        </div>
        <div class="analysis-box">
            <h3>Methodology</h3>
            <p>${result.methodology.substring(0, 400)}...</p>
        </div>
        <div class="analysis-box">
            <h3>Results</h3>
            <p>${result.results.substring(0, 400)}...</p>
        </div>
        <div class="analysis-box">
            <h3>Suggestions</h3>
            <ul>${result.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
        </div>
        <div class="analysis-box">
            <h3>Feedback</h3>
            <p>${result.feedback}</p>
        </div>
    `;

    showStatus("Analysis Done!", "success");
}