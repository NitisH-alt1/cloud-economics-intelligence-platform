let selectedProjectId = "";

function redirectToLogin() {
    localStorage.removeItem("access_token");
    window.location.replace("/");
}

async function apiFetch(path, options = {}) {
    const response = await CEAApi.request(path, options);
    if (response.status === 401 || response.status === 403) redirectToLogin();
    return response;
}

const responseJson = CEAApi.readJson;
const apiError = CEAApi.errorMessage;

function formatCurrency(value, currency = "USD") {
    const amount = Number(value);
    if (!Number.isFinite(amount)) return "—";

    try {
        return new Intl.NumberFormat(undefined, {style:"currency", currency}).format(amount);
    } catch {
        return `${amount.toFixed(2)} ${currency}`;
    }
}

function appendCells(row, values) {
    values.forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value == null ? "—" : String(value);
        row.appendChild(cell);
    });
}

function showEmptyRow(tbody, message, columnCount) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = columnCount;
    cell.textContent = message;
    row.appendChild(cell);
    tbody.replaceChildren(row);
}

function updateMetric(id, value) {
    const element = document.getElementById(id);
    const next = String(value);
    if (element.textContent === next) return;

    element.textContent = next;
    element.classList.remove("metric-updated");
    void element.offsetWidth;
    element.classList.add("metric-updated");
}

function setCostDirection(element, amount) {
    const change = Number(amount);
    element.classList.toggle("cost-increase", Number.isFinite(change) && change > 0);
    element.classList.toggle("cost-decrease", Number.isFinite(change) && change < 0);
}

function setIntelligenceLoading(loading) {
    ["costPanel", "causalPanel", "anomalyPanel", "recommendationsPanel"].forEach(id => {
        const panel = document.getElementById(id);
        panel.dataset.loading = String(loading);
        panel.setAttribute("aria-busy", String(loading));
    });
}

async function loadWorkspace() {
    try {
        const response = await apiFetch("/api/workspace/summary");
        if (!response.ok) throw new Error("Unable to load the workspace summary.");

        const data = await responseJson(response);
        if (!data?.organization || !data?.user) throw new Error("Workspace response was incomplete.");

        document.getElementById("orgText").textContent = `${data.organization.id} · ${data.organization.role}`;
        document.getElementById("settingsText").textContent = `Signed in as ${data.user.name} (${data.user.email})`;

        await loadProjects();
        await loadCloudAccounts();
        if (selectedProjectId) await loadIntelligence();
    } catch (error) {
        document.getElementById("settingsText").textContent = error.message || "Unable to load the workspace.";
        document.getElementById("projectList").textContent = "Workspace data is unavailable.";
        document.getElementById("cloudAccountsList").textContent = "Cloud account data is unavailable.";
        updateMetric("projectCount", "—");
        updateMetric("cloudAccountCount", "—");
        showNoProjectIntelligence();
    }
}

async function loadProjects() {
    const list = document.getElementById("projectList");
    list.textContent = "Loading projects…";

    try {
        const response = await apiFetch("/api/projects");
        if (!response.ok) throw new Error("Unable to load projects.");

        const projects = await responseJson(response);
        if (!Array.isArray(projects) || projects.some(project => !project || typeof project.id !== "string" || typeof project.name !== "string")) {
            throw new Error("Project list response was invalid.");
        }

        renderProjects(projects);
    } catch (error) {
        selectedProjectId = "";
        updateMetric("projectCount", "—");
        list.textContent = error.message || "Unable to load projects.";
        setProjectOptions([]);
        showNoProjectIntelligence();
    }
}

function setProjectOptions(projects) {
    const selector = document.getElementById("activeProject");
    const previousId = selectedProjectId;
    selector.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select a project";
    selector.appendChild(placeholder);

    projects.forEach(project => {
        const option = document.createElement("option");
        option.value = project.id;
        option.textContent = project.name;
        selector.appendChild(option);
    });

    selectedProjectId = projects.some(project => project.id === previousId)
        ? previousId
        : projects[0]?.id || "";
    selector.value = selectedProjectId;
}

function renderProjects(projects) {
    const list = document.getElementById("projectList");
    updateMetric("projectCount", projects.length);
    setProjectOptions(projects);
    list.replaceChildren();

    if (!projects.length) {
        list.textContent = "No projects yet. Create a project to view its cost and analysis.";
        showNoProjectIntelligence();
        return;
    }

    projects.forEach(project => {
        const row = document.createElement("article");
        row.className = "project-row";

        const identity = document.createElement("div");
        identity.className = "project-identity";
        const name = document.createElement("strong");
        name.textContent = project.name;
        const slug = document.createElement("span");
        slug.textContent = project.slug || "";
        const description = document.createElement("p");
        description.className = "status";
        description.textContent = project.description || "No description";
        identity.append(name, slug, description);

        const actions = document.createElement("div");
        actions.className = "project-actions";
        actions.append(
            makeButton("Open", () => openProject(project.id)),
            makeButton("Edit", () => editProject(project, row)),
            makeButton("Delete", () => deleteProject(project.id))
        );
        row.append(identity, actions);
        list.appendChild(row);
    });
}

function makeButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-action";
    button.textContent = label;
    button.addEventListener("click", action);
    return button;
}

function openProject(projectId) {
    document.getElementById("activeProject").value = projectId;
    selectProject(projectId);
    showPage("overview", document.querySelector('[data-page="overview"]'));
}

function selectProject(projectId) {
    selectedProjectId = projectId || "";
    if (!selectedProjectId) {
        showNoProjectIntelligence();
        loadCloudAccounts();
        return;
    }

    loadIntelligence();
    loadCloudAccounts();
}

async function loadIntelligence() {
    if (!selectedProjectId) {
        showNoProjectIntelligence();
        return;
    }

    const projectId = selectedProjectId;
    setIntelligenceLoading(true);
    document.getElementById("costStatus").textContent = "Updating project estimates…";
    document.getElementById("causalStatus").textContent = "Updating candidate analysis…";

    const base = `/api/projects/${encodeURIComponent(projectId)}`;
    const endpoints = ["cost", "causal", "anomalies", "recommendations"].map(name => `${base}/${name}`);
    const results = await Promise.allSettled(endpoints.map(async endpoint => {
        const response = await apiFetch(endpoint);
        if (!response.ok) throw new Error("Project analysis request failed.");
        const data = await responseJson(response);
        if (!data || typeof data !== "object") throw new Error("Project analysis response was invalid.");
        return data;
    }));

    if (selectedProjectId !== projectId) return;

    const [rawCost, rawCausal, rawAnomalies, rawRecommendations] = results.map(result =>
        result.status === "fulfilled" ? result.value : null
    );
    const cost = rawCost && Array.isArray(rawCost.services) ? rawCost : null;
    const causal = rawCausal && Array.isArray(rawCausal.candidates) ? rawCausal : null;
    const anomalies = rawAnomalies && Array.isArray(rawAnomalies.anomalies) ? rawAnomalies : null;
    const recommendations = rawRecommendations && Array.isArray(rawRecommendations.recommendations) ? rawRecommendations : null;

    if (cost) renderProjectCost(cost);
    else clearCostView("Cost data is unavailable for this project.");

    if (causal) renderCausalAnalysis(causal);
    else {
        renderCausalAnalysis(null);
        document.getElementById("causalStatus").textContent = "Causal analysis is unavailable.";
    }

    renderProjectAnomalies(anomalies);
    renderRecommendations(recommendations);
    document.getElementById("intelligenceSource").textContent = cost && typeof cost.source === "string"
        ? `${cost.source} · Project-scoped estimates · not provider billing`
        : "Project analysis is unavailable.";

    updateMetric("overviewEstimatedCost", cost ? formatCurrency(cost.total_cost, cost.currency) : "—");
    updateMetric("overviewCostChange", cost ? formatCurrency(cost.cost_change, cost.currency) : "—");
    setCostDirection(document.getElementById("overviewCostChange"), cost?.cost_change);
    updateMetric("overviewAnomalyCount", anomalies ? anomalies.anomalies.length : "—");
    updateMetric("overviewCandidateCount", causal ? causal.candidates.length : "—");
    setIntelligenceLoading(false);
}

function clearCostView(message) {
    document.getElementById("costStatus").textContent = message;
    document.getElementById("totalEstimatedCost").textContent = "—";
    const change = document.getElementById("costPercentageChange");
    change.textContent = "—";
    setCostDirection(change, null);
    showEmptyRow(document.getElementById("costServiceRows"), message, 5);
    document.getElementById("costTrendLine").setAttribute("d", "");
    document.getElementById("costTrendDot").hidden = true;
    document.getElementById("costTrend").textContent = "No trend data available.";
    document.getElementById("providerBreakdown").textContent = "—";
    document.getElementById("accountBreakdown").textContent = "—";
}

function renderProjectCost(cost) {
    const period = Number.isFinite(Number(cost.period_days)) ? cost.period_days : "—";
    document.getElementById("costStatus").textContent = `${cost.source || "Local demo estimate"} · ${period} day estimate · compared with previous period`;
    document.getElementById("totalEstimatedCost").textContent = formatCurrency(cost.total_cost, cost.currency);
    document.getElementById("costPercentageChange").textContent = cost.percentage_change == null ? "—" : `${cost.percentage_change > 0 ? "+" : ""}${cost.percentage_change}%`;
    setCostDirection(document.getElementById("costPercentageChange"), cost.cost_change);

    const rows = document.getElementById("costServiceRows");
    rows.replaceChildren();
    (Array.isArray(cost.services) ? cost.services : []).filter(item => item && typeof item === "object").forEach(item => {
        const share = Number(item.share);
        const row = document.createElement("tr");
        appendCells(row, [
            item.service,
            formatCurrency(item.previous_cost, cost.currency),
            formatCurrency(item.current_cost, cost.currency),
            formatCurrency(item.change, cost.currency),
            Number.isFinite(share) ? `${(share * 100).toFixed(1)}%` : "—"
        ]);
        rows.appendChild(row);
    });
    if (!rows.children.length) showEmptyRow(rows, "No cost records are available.", 5);

    renderCostTrend(cost);
    document.getElementById("providerBreakdown").textContent = breakdown(cost.providers, "provider", cost.currency, "No provider breakdown available.");
    document.getElementById("accountBreakdown").textContent = breakdown(cost.cloud_accounts, "account", cost.currency, "No cloud account breakdown available.");
}

function breakdown(items, nameField, currency, emptyText) {
    if (!Array.isArray(items)) return emptyText;
    const values = items.filter(item => item && typeof item === "object").map(item =>
        `${item[nameField] || "—"}: ${formatCurrency(item.cost, currency)}`
    );
    return values.join(" · ") || emptyText;
}

function renderCostTrend(cost) {
    const points = (Array.isArray(cost.trend) ? cost.trend : []).filter(point =>
        point && typeof point === "object" && Number.isFinite(Number(point.cost))
    );
    const line = document.getElementById("costTrendLine");
    const dot = document.getElementById("costTrendDot");

    if (points.length > 1) {
        const values = points.map(point => Number(point.cost));
        const min = Math.min(...values);
        const spread = Math.max(...values) - min || 1;
        const coordinates = values.map((value, index) => [
            12 + index * (696 / (values.length - 1)),
            138 - ((value - min) / spread) * 112
        ]);
        line.setAttribute("d", coordinates.map(([x, y], index) =>
            `${index ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`
        ).join(" "));
        const last = coordinates[coordinates.length - 1];
        dot.setAttribute("cx", last[0].toFixed(1));
        dot.setAttribute("cy", last[1].toFixed(1));
        dot.hidden = false;
    } else {
        line.setAttribute("d", "");
        dot.hidden = true;
    }

    const first = points[0];
    const last = points[points.length - 1];
    document.getElementById("costTrend").textContent = points.length
        ? `${points.length} daily sample points · ${first.date || "start"} to ${last.date || "latest"}`
        : "No trend data available.";
}

function renderProjectAnomalies(data) {
    const container = document.getElementById("anomalyList");
    container.replaceChildren();
    (data && Array.isArray(data.anomalies) ? data.anomalies : []).filter(item => item && typeof item === "object").forEach(item => {
        const entry = document.createElement("p");
        entry.className = "anomaly-item has-signal";
        entry.dataset.severity = item.severity || "unknown";
        entry.textContent = [
            item.service,
            item.metric,
            `observed ${item.observed ?? "—"}`,
            `/ baseline ${item.baseline ?? "—"}`,
            `score ${item.score ?? "—"}`,
            item.severity,
            item.period,
            item.explanation
        ].filter(Boolean).join(" · ");
        container.appendChild(entry);
    });
    if (!container.children.length) {
        container.classList.add("state-message");
        container.textContent = data ? "No anomalies detected in the available sample." : "Anomaly analysis is unavailable.";
    } else {
        container.classList.remove("state-message");
    }

    const rows = document.getElementById("anomalyRows");
    rows.replaceChildren();
    (data && Array.isArray(data.anomalies) ? data.anomalies : []).filter(item => item && typeof item === "object").forEach(item => {
        const row = document.createElement("tr");
        appendCells(row, [item.service, item.metric, item.score]);
        rows.appendChild(row);
    });
    if (!rows.children.length) showEmptyRow(rows, "No anomaly results.", 3);
}

function renderRecommendations(data) {
    const container = document.getElementById("recommendationList");
    container.replaceChildren();
    (data && Array.isArray(data.recommendations) ? data.recommendations : []).filter(item => item && typeof item === "object").forEach(item => {
        const card = document.createElement("article");
        card.className = "cloud-account-card recommendation-card";
        const title = document.createElement("strong");
        title.textContent = item.title || "Recommendation";
        const detail = document.createElement("p");
        detail.textContent = `${item.description || ""}${item.affected_service ? ` Affected service: ${item.affected_service}.` : ""}${item.severity ? ` Severity: ${item.severity}.` : ""}`;
        const evidence = document.createElement("p");
        evidence.textContent = item.evidence == null ? "Evidence unavailable." : `Evidence: ${JSON.stringify(item.evidence)}`;
        card.append(title, detail, evidence);
        container.appendChild(card);
    });

    if (!container.children.length) {
        const state = document.createElement("p");
        state.className = "state-message";
        state.textContent = data ? "No recommendations are available for this project." : "Recommendations are unavailable.";
        container.appendChild(state);
    }
}

function renderCausalAnalysis(data) {
    const chain = data?.chain && typeof data.chain === "object" ? data.chain : {};
    const chainServices = Array.isArray(chain.causal_chain) ? chain.causal_chain : [];
    document.getElementById("causalStatus").textContent = "Model-derived candidate evidence. Not definitive causality.";

    const chainElement = document.getElementById("causalChain");
    chainElement.replaceChildren();
    chainElement.classList.remove("has-focus");
    chainServices.forEach((service, index) => {
        if (index) {
            const arrow = document.createElement("span");
            arrow.className = "causal-arrow";
            arrow.setAttribute("aria-hidden", "true");
            arrow.textContent = "→";
            chainElement.appendChild(arrow);
        }

        const node = document.createElement("button");
        node.type = "button";
        node.className = "causal-node";
        node.textContent = String(service);
        node.setAttribute("aria-pressed", "false");
        node.addEventListener("click", () => focusCausalNode(chainElement, index));
        chainElement.appendChild(node);
    });
    if (!chainServices.length) {
        const empty = document.createElement("span");
        empty.className = "state-message";
        empty.textContent = "No candidate chain available.";
        chainElement.appendChild(empty);
    }

    document.getElementById("causalSummary").textContent =
        `Candidate root: ${chain.candidate_root_cause || "—"} · Dependency depth: ${chain.dependency_depth ?? "—"}`;

    const candidates = Array.isArray(data?.candidates) ? data.candidates : [];
    const rows = document.getElementById("causalCandidateRows");
    rows.replaceChildren();
    candidates.filter(item => item && typeof item === "object").forEach(item => {
        const row = document.createElement("tr");
        appendCells(row, [item.cause_service, item.affected_service, item.dependency, item.anomaly_strength, item.propagation_strength, item.causal_candidate_score]);
        rows.appendChild(row);
    });
    if (!rows.children.length) showEmptyRow(rows, "No causal candidates available.", 6);

    const costRows = document.getElementById("causalCostRows");
    costRows.replaceChildren();
    (Array.isArray(data?.cost_attribution) ? data.cost_attribution : []).filter(item => item && typeof item === "object").forEach(item => {
        const row = document.createElement("tr");
        appendCells(row, [item.service, formatCurrency(item.estimated_change, item.currency)]);
        costRows.appendChild(row);
    });
    if (!costRows.children.length) showEmptyRow(costRows, "No estimated cost attribution available.", 2);
}

function focusCausalNode(chain, selectedIndex) {
    const nodes = Array.from(chain.querySelectorAll(".causal-node"));
    const selected = nodes[selectedIndex].getAttribute("aria-pressed") === "true";
    chain.classList.toggle("has-focus", !selected);
    nodes.forEach((node, index) => {
        const distance = Math.abs(index - selectedIndex);
        node.classList.toggle("is-muted", !selected && distance > 1);
        node.classList.toggle("is-related", !selected && distance === 1);
        node.classList.toggle("is-active", !selected && index === selectedIndex);
        node.setAttribute("aria-pressed", String(!selected && index === selectedIndex));
    });
}

function showNoProjectIntelligence() {
    clearCostView("Select a project to view cost estimates.");
    renderCausalAnalysis(null);
    document.getElementById("causalStatus").textContent = "Select a project to view candidate analysis.";
    renderProjectAnomalies(null);
    renderRecommendations(null);
    document.getElementById("intelligenceSource").textContent = "Select a project to view local demo estimates.";
    updateMetric("overviewEstimatedCost", "—");
    updateMetric("overviewCostChange", "—");
    updateMetric("overviewAnomalyCount", "—");
    updateMetric("overviewCandidateCount", "—");
    setIntelligenceLoading(false);
}

async function createProject(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const nameInput = document.getElementById("projectName");
    const button = form.querySelector("button[type='submit']");
    document.getElementById("projectFormMessage").textContent = "";
    const name = nameInput.value.trim();
    const description = document.getElementById("projectDescription").value.trim();
    if (name.length < 2) {
        nameInput.setCustomValidity("Enter at least two characters.");
        nameInput.reportValidity();
        nameInput.setCustomValidity("");
        return;
    }

    button.disabled = true;
    button.textContent = "Creating…";
    try {
        const response = await apiFetch("/api/projects", {method:"POST", body:JSON.stringify({name, description:description || null})});
        const data = await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to create project."));
        form.reset();
        await loadProjects();
        if (selectedProjectId) {
            await loadIntelligence();
            await loadCloudAccounts();
        }
    } catch (error) {
        document.getElementById("projectFormMessage").textContent = error.message || "Unable to create project.";
    } finally {
        button.disabled = false;
        button.textContent = "Create Project";
    }
}

function editProject(project, row) {
    const form = document.createElement("form");
    form.className = "project-edit-form";

    const nameLabel = document.createElement("label");
    nameLabel.className = "visually-hidden";
    nameLabel.htmlFor = `editProjectName-${project.id}`;
    nameLabel.textContent = "Project name";
    const nameInput = document.createElement("input");
    nameInput.id = nameLabel.htmlFor;
    nameInput.name = "name";
    nameInput.type = "text";
    nameInput.minLength = 2;
    nameInput.maxLength = 200;
    nameInput.required = true;
    nameInput.value = project.name;

    const descriptionLabel = document.createElement("label");
    descriptionLabel.className = "visually-hidden";
    descriptionLabel.htmlFor = `editProjectDescription-${project.id}`;
    descriptionLabel.textContent = "Project description";
    const descriptionInput = document.createElement("input");
    descriptionInput.id = descriptionLabel.htmlFor;
    descriptionInput.name = "description";
    descriptionInput.type = "text";
    descriptionInput.maxLength = 500;
    descriptionInput.value = project.description || "";
    descriptionInput.placeholder = "Project description";

    const save = document.createElement("button");
    save.type = "submit";
    save.className = "primary";
    save.textContent = "Save changes";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "secondary-action";
    cancel.textContent = "Cancel";
    cancel.addEventListener("click", () => loadProjects());

    form.append(nameLabel, nameInput, descriptionLabel, descriptionInput, save, cancel);
    form.addEventListener("submit", event => saveProjectEdit(event, project, form, save));
    row.replaceChildren(form);
    nameInput.focus();
}

async function saveProjectEdit(event, project, form, button) {
    event.preventDefault();
    const name = form.elements.name.value.trim();
    const description = form.elements.description.value.trim();
    button.disabled = true;
    button.textContent = "Saving…";
    try {
        const response = await apiFetch(`/api/projects/${encodeURIComponent(project.id)}`, {
            method:"PUT",
            body:JSON.stringify({name, description:description || null})
        });
        const data = await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to update project."));
        document.getElementById("projectFormMessage").textContent = "";
        await loadProjects();
    } catch (error) {
        document.getElementById("projectFormMessage").textContent = error.message || "Unable to update project.";
        button.disabled = false;
        button.textContent = "Save changes";
    }
}

async function deleteProject(projectId) {
    if (!confirm("Delete this project and its local demo cost records?")) return;
    try {
        const response = await apiFetch(`/api/projects/${encodeURIComponent(projectId)}`, {method:"DELETE"});
        const data = response.ok ? null : await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to delete project."));
        document.getElementById("projectFormMessage").textContent = "";
        if (selectedProjectId === projectId) selectedProjectId = "";
        await loadProjects();
        if (selectedProjectId) await Promise.all([loadIntelligence(), loadCloudAccounts()]);
    } catch (error) {
        document.getElementById("projectFormMessage").textContent = error.message || "Unable to delete project.";
    }
}

function showPage(id, button) {
    const page = document.getElementById(id);
    if (!page || !button) return;

    document.querySelectorAll(".page").forEach(section => section.classList.toggle("hidden", section !== page));
    document.querySelectorAll(".nav button").forEach(navButton => {
        const active = navButton === button;
        navButton.classList.toggle("active", active);
        if (active) navButton.setAttribute("aria-current", "page");
        else navButton.removeAttribute("aria-current");
    });
    document.getElementById("pageTitle").textContent = button.textContent.trim();
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.replace("/");
}

document.getElementById("projectForm").addEventListener("submit", createProject);

if (!localStorage.getItem("access_token")) redirectToLogin();
else loadWorkspace();
