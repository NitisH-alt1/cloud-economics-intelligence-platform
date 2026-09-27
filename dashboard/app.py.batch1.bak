from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import json

app = FastAPI(
    title="Cloud Economics Intelligence Platform",
    version="1.0.0"
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_json(filename):
    path = DATA_DIR / filename

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_candidates():
    data = load_json("causal_candidates.json")

    if isinstance(data, list):
        return data

    return []


def build_causal_chain():
    data = load_json("causal_chain.json")

    if not data:
        return {
            "anomalous_service": None,
            "event_time": None,
            "causal_chain": [],
            "candidate_root_cause": None,
            "dependency_depth": 0
        }

    return data


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Cloud Economics Intelligence Platform</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #0b1020;
            color: #e8ecf7;
        }

        header {
            padding: 24px 32px;
            background: #11182d;
            border-bottom: 1px solid #26304d;
        }

        header h1 {
            margin: 0 0 8px 0;
            font-size: 28px;
        }

        header p {
            margin: 0;
            color: #9ca8c7;
        }

        .container {
            padding: 28px 32px;
            max-width: 1400px;
            margin: auto;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }

        .card {
            background: #121a30;
            border: 1px solid #26304d;
            border-radius: 12px;
            padding: 20px;
        }

        .card-title {
            color: #8f9bb8;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }

        .card-value {
            font-size: 25px;
            font-weight: 700;
        }

        .section {
            background: #121a30;
            border: 1px solid #26304d;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 24px;
        }

        .section h2 {
            margin-top: 0;
            font-size: 20px;
        }

        .chain {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 18px;
        }

        .node {
            padding: 13px 20px;
            border-radius: 8px;
            background: #1c2744;
            border: 1px solid #3a4a75;
            font-weight: 700;
        }

        .root {
            border-color: #d35f5f;
            background: #351e2a;
        }

        .arrow {
            color: #7785a8;
            font-size: 22px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th,
        td {
            text-align: left;
            padding: 13px 12px;
            border-bottom: 1px solid #26304d;
        }

        th {
            color: #8f9bb8;
            font-size: 13px;
            text-transform: uppercase;
        }

        td {
            color: #dbe2f3;
        }

        .score {
            font-weight: 700;
        }

        .status {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 6px;
            background: #183a2c;
            color: #70d6a0;
            font-size: 12px;
        }

        .muted {
            color: #8f9bb8;
        }

        .error {
            color: #ff8585;
        }

        @media (max-width: 900px) {
            .grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 600px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .container {
                padding: 18px;
            }
        }
    </style>
</head>

<body>

<header>
    <h1>Cloud Economics Intelligence Platform</h1>
    <p>Intelligent cloud cost analysis, causal attribution, and anomaly intelligence</p>
</header>

<div class="container">

    <div class="grid">

        <div class="card">
            <div class="card-title">Anomalous Service</div>
            <div class="card-value" id="anomalous-service">Loading...</div>
        </div>

        <div class="card">
            <div class="card-title">Candidate Root Cause</div>
            <div class="card-value" id="root-cause">Loading...</div>
        </div>

        <div class="card">
            <div class="card-title">Dependency Depth</div>
            <div class="card-value" id="dependency-depth">Loading...</div>
        </div>

        <div class="card">
            <div class="card-title">Engine Status</div>
            <div class="card-value">
                <span class="status">ONLINE</span>
            </div>
        </div>

    </div>

    <div class="section">
        <h2>Causal Chain</h2>
        <div id="causal-chain" class="chain">
            Loading...
        </div>
    </div>

    <div class="section">
        <h2>Causal Candidate Scores</h2>

        <table>
            <thead>
                <tr>
                    <th>Cause Service</th>
                    <th>Affected Service</th>
                    <th>Anomaly Strength</th>
                    <th>Propagation Strength</th>
                    <th>Candidate Score</th>
                </tr>
            </thead>

            <tbody id="candidate-table">
                <tr>
                    <td colspan="5">Loading...</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="section">
        <h2>Cost Attribution</h2>

        <div class="card" style="margin-bottom:18px;">
            <div class="card-title">Total Cost Increase</div>
            <div class="card-value" id="total-cost-increase">Loading...</div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Service</th>
                    <th>Baseline Cost</th>
                    <th>Current Cost</th>
                    <th>Cost Increase</th>
                    <th>Attribution Share</th>
                </tr>
            </thead>
            <tbody id="cost-table">
                <tr>
                    <td colspan="5">Loading...</td>
                </tr>
            </tbody>
        </table>
    </div>


    <div class="section">
        <h2>Anomaly Data</h2>

        <pre id="anomalies" class="muted">Loading...</pre>
    </div>

</div>

<script>
async function fetchJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(
            "HTTP " + response.status + " for " + url
        );
    }

    return await response.json();
}


function renderCausalChain(data) {
    const container = document.getElementById("causal-chain");

    const chain = data.causal_chain || [];

    if (chain.length === 0) {
        container.innerHTML = '<span class="muted">No causal chain available.</span>';
        return;
    }

    container.innerHTML = "";

    chain.forEach((service, index) => {
        const node = document.createElement("div");

        node.className =
            "node" +
            (index === 0 ? " root" : "");

        node.textContent = service;

        container.appendChild(node);

        if (index < chain.length - 1) {
            const arrow = document.createElement("div");

            arrow.className = "arrow";
            arrow.textContent = "→";

            container.appendChild(arrow);
        }
    });
}


function renderCandidates(candidates) {
    const table = document.getElementById("candidate-table");

    table.innerHTML = "";

    if (!candidates || candidates.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="5" class="muted">
                    No causal candidates available.
                </td>
            </tr>
        `;
        return;
    }

    candidates.forEach(candidate => {
        const row = document.createElement("tr");

        const cause = candidate.cause_service ?? "-";
        const affected = candidate.affected_service ?? "-";
        const anomaly = Number(candidate.anomaly_strength ?? 0);
        const propagation = Number(candidate.propagation_strength ?? 0);
        const score = Number(candidate.causal_candidate_score ?? 0);

        row.innerHTML = `
            <td>${cause}</td>
            <td>${affected}</td>
            <td>${(anomaly * 100).toFixed(1)}%</td>
            <td>${(propagation * 100).toFixed(1)}%</td>
            <td class="score">
                ${(score * 100).toFixed(1)}%
            </td>
        `;

        table.appendChild(row);
    });
}


function renderCostAttribution(data) {
const total = Number(data.total_cost_increase ?? 0);

document.getElementById("total-cost-increase").textContent =
    `${data.currency ?? "USD"} ${total.toFixed(2)}`;

const table = document.getElementById("cost-table");
table.innerHTML = "";

const services = data.services || {};

Object.entries(services).forEach(([service, values]) => {
    const row = document.createElement("tr");

    const baseline = Number(values.baseline_cost ?? 0);
    const current = Number(values.current_cost ?? 0);
    const increase = Number(values.cost_increase ?? 0);
    const share = Number(values.attribution_share ?? 0);

    row.innerHTML = `
        <td>${service}</td>
        <td>${baseline.toFixed(2)}</td>
        <td>${current.toFixed(2)}</td>
        <td class="score">${increase.toFixed(2)}</td>
        <td>${(share * 100).toFixed(1)}%</td>
    `;

    table.appendChild(row);
});
}
async function loadDashboard() {
    try {
        const chain = await fetchJSON("/api/causal-chain");

        document.getElementById("anomalous-service").textContent =
            chain.anomalous_service ?? "-";

        document.getElementById("root-cause").textContent =
            chain.candidate_root_cause ?? "-";

        document.getElementById("dependency-depth").textContent =
            chain.dependency_depth ?? 0;

        renderCausalChain(chain);

        const candidates =
            await fetchJSON("/api/causal-candidates");

        renderCandidates(candidates);

        

        const cost =
            await fetchJSON("/api/cost");

        renderCostAttribution(cost);const anomalies =
            await fetchJSON("/api/anomalies");

        document.getElementById("anomalies").textContent =
            JSON.stringify(anomalies, null, 2);

    } catch (error) {
        console.error("Dashboard loading error:", error);

        document.getElementById("causal-chain").innerHTML =
            '<span class="error">Failed to load dashboard data.</span>';

        document.getElementById("candidate-table").innerHTML =
            '<tr><td colspan="5" class="error">API loading failed.</td></tr>';
    }
}


loadDashboard();
</script>

</body>
</html>
"""


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "causal-cost-dashboard"
    }


@app.get("/api/causal-chain")
def causal_chain():
    return build_causal_chain()


@app.get("/api/causal-candidates")
def causal_candidates():
    return load_candidates()


@app.get("/api/anomalies")
def anomalies():
    return load_json("anomaly_scores.json")


@app.get("/api/cost")
def cost():
    return load_json("cost_data.json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080
    )

