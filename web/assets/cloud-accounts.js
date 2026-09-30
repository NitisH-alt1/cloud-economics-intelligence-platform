const CONNECTION_METHODS = {
    aws: "aws_role",
    azure: "azure_service_principal",
    gcp: "gcp_service_account"
};
let cloudLoadVersion = 0;

async function loadCloudAccounts() {
    const list = document.getElementById("cloudAccountsList");
    if (!list) return;

    const version = ++cloudLoadVersion;
    list.textContent = "Loading cloud account records…";
    list.setAttribute("aria-busy", "true");

    try {
        const projectId = document.getElementById("activeProject").value;
        const requests = [
            apiFetch("/api/cloud-accounts"),
            apiFetch("/api/cloud-connections")
        ];
        if (projectId) {
            requests.push(apiFetch(`/api/projects/${encodeURIComponent(projectId)}/cloud-accounts`));
        }

        const [accountsResponse, connectionsResponse, linkedResponse] = await Promise.all(requests);
        if (version !== cloudLoadVersion) return;
        if (!accountsResponse.ok || !connectionsResponse.ok || (linkedResponse && !linkedResponse.ok)) {
            throw new Error("Unable to load cloud account records.");
        }

        const accounts = await responseJson(accountsResponse);
        const connections = await responseJson(connectionsResponse);
        const linkedAccounts = linkedResponse ? await responseJson(linkedResponse) : [];
        if (!isAccountList(accounts) || !Array.isArray(connections) || !Array.isArray(linkedAccounts)) {
            throw new Error("Cloud account response was invalid.");
        }

        renderCloudAccounts(list, accounts, connections, linkedAccounts, projectId);
        updateMetric("cloudAccountCount", accounts.length);
    } catch (error) {
        if (version !== cloudLoadVersion) return;
        list.textContent = error.message || "Unable to load cloud account records.";
        updateMetric("cloudAccountCount", "—");
    } finally {
        if (version === cloudLoadVersion) list.setAttribute("aria-busy", "false");
    }
}

function isAccountList(accounts) {
    return Array.isArray(accounts) && accounts.every(account =>
        account && typeof account === "object" &&
        typeof account.id === "string" &&
        typeof account.provider === "string" &&
        typeof account.display_name === "string" &&
        typeof account.external_account_id === "string"
    );
}

function renderCloudAccounts(list, accounts, connections, linkedAccounts, projectId) {
    list.replaceChildren();
    if (!accounts.length) {
        list.textContent = "No cloud account records yet.";
        return;
    }

    const linkedIds = new Set(linkedAccounts.map(account => account?.id).filter(Boolean));
    accounts.forEach(account => {
        const card = document.createElement("article");
        card.className = "cloud-account-card";

        const title = document.createElement("strong");
        title.textContent = account.display_name;

        const details = document.createElement("div");
        details.textContent = [
            account.provider.toUpperCase(),
            account.external_account_id,
            account.region
        ].filter(Boolean).join(" · ");

        const connection = connections.find(item => item?.cloud_account_id === account.id);
        const status = document.createElement("div");
        status.className = "account-statuses";
        status.append(
            makeStatusBadge("Account", account.status),
            connection
                ? makeStatusBadge("Connection record", connection.status)
                : makeStatusBadge("Connection record", "not configured")
        );

        const note = document.createElement("p");
        note.className = "status";
        note.textContent = "Credentials have not been validated.";

        const association = makeAccountButton(
            linkedIds.has(account.id) ? "Remove from project" : "Associate with project",
            () => associateCloudAccount(account.id, linkedIds.has(account.id))
        );
        association.disabled = !projectId;

        const configure = makeAccountButton(
            connection ? "Connection configured" : "Add connection record",
            () => createConnectionRecord(account)
        );
        configure.disabled = Boolean(connection);

        const remove = makeAccountButton("Remove account", () => deleteCloudAccount(account.id));
        card.append(title, details, status, note, association, configure, remove);
        list.appendChild(card);
    });
}

function makeStatusBadge(label, status) {
    const badge = document.createElement("span");
    badge.className = "status-chip";
    badge.dataset.status = status || "unknown";
    badge.textContent = `${label}: ${status || "unknown"}`;
    return badge;
}

function makeAccountButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-action";
    button.textContent = label;
    button.addEventListener("click", action);
    return button;
}

function setCloudMessage(message) {
    document.getElementById("cloudAccountMessage").textContent = message;
}

async function addCloudAccount(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type='submit']");
    const payload = {
        provider: document.getElementById("cloudProvider").value,
        display_name: document.getElementById("cloudDisplayName").value.trim(),
        external_account_id: document.getElementById("cloudExternalId").value.trim(),
        region: document.getElementById("cloudRegion").value.trim() || null
    };

    button.disabled = true;
    button.textContent = "Adding account…";
    try {
        const response = await apiFetch("/api/cloud-accounts", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        const data = await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to add the cloud account."));

        form.reset();
        setCloudMessage("Cloud account record added. Credentials have not been validated.");
        await loadCloudAccounts();
    } catch (error) {
        setCloudMessage(error.message || "Unable to add the cloud account.");
    } finally {
        button.disabled = false;
        button.textContent = "Add Cloud Account";
    }
}

async function associateCloudAccount(accountId, isLinked) {
    const projectId = document.getElementById("activeProject").value;
    if (!projectId) {
        setCloudMessage("Select a project before changing its account associations.");
        return;
    }

    const method = isLinked ? "DELETE" : "PUT";
    const endpoint = `/api/projects/${encodeURIComponent(projectId)}/cloud-accounts/${encodeURIComponent(accountId)}`;
    try {
        const response = await apiFetch(endpoint, {method});
        const data = response.ok ? null : await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to update the project association."));

        setCloudMessage(isLinked ? "Cloud account removed from the active project." : "Cloud account associated with the active project.");
        await Promise.all([loadCloudAccounts(), loadIntelligence()]);
    } catch (error) {
        setCloudMessage(error.message || "Unable to update the project association.");
    }
}

async function createConnectionRecord(account) {
    const authMethod = CONNECTION_METHODS[account.provider];
    if (!authMethod) {
        setCloudMessage("This cloud provider is not supported.");
        return;
    }

    try {
        const response = await apiFetch("/api/cloud-connections", {
            method: "POST",
            body: JSON.stringify({
                cloud_account_id: account.id,
                provider: account.provider,
                auth_method: authMethod
            })
        });
        const data = await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to create a connection record."));

        setCloudMessage("Connection record configured. Credentials have not been validated.");
        await loadCloudAccounts();
    } catch (error) {
        setCloudMessage(error.message || "Unable to create a connection record.");
    }
}

async function deleteCloudAccount(accountId) {
    if (!confirm("Remove this cloud account record? Its project associations will also be removed.")) return;

    try {
        const response = await apiFetch(`/api/cloud-accounts/${encodeURIComponent(accountId)}`, {method:"DELETE"});
        const data = response.ok ? null : await responseJson(response);
        if (!response.ok) throw new Error(apiError(data, "Unable to remove the cloud account."));

        setCloudMessage("Cloud account record removed.");
        await Promise.all([
            loadCloudAccounts(),
            selectedProjectId ? loadIntelligence() : Promise.resolve()
        ]);
    } catch (error) {
        setCloudMessage(error.message || "Unable to remove the cloud account.");
    }
}

document.getElementById("cloudAccountForm").addEventListener("submit", addCloudAccount);
