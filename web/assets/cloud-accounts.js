const API_BASE = "http://127.0.0.1:8081";
const CLOUD_API = "http://127.0.0.1:8081";

async function loadCloudAccounts() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const response = await fetch(
        CLOUD_API + "/api/cloud-accounts",
        {
            headers: {
                Authorization: "Bearer " + token
            }
        }
    );

    const list = document.getElementById("cloudAccountsList");

    if (!response.ok) {
        list.innerHTML = "<p>Unable to load cloud accounts.</p>";
        return;
    }

    const accounts = await response.json();

    if (!accounts.length) {
        list.innerHTML = "<p>No cloud accounts connected yet.</p>";
        return;
    }

    list.innerHTML = accounts.map(account => `
        <div class="cloud-account-card">
            <strong>${account.display_name}</strong>
            <div>
                ${account.provider.toUpperCase()}
                · ${account.external_account_id}
                ${account.region ? "· " + account.region : ""}
            </div>
            <div>Status: ${account.status}</div>
            <button type="button"
                onclick="deleteCloudAccount('${account.id}')">
                Remove
            </button>
        </div>
    `).join("");
}

async function addCloudAccount(event) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");

    const payload = {
        provider: document.getElementById("cloudProvider").value,
        display_name: document.getElementById("cloudDisplayName").value,
        external_account_id: document.getElementById("cloudExternalId").value,
        region: document.getElementById("cloudRegion").value || null
    };

    const response = await fetch(
        CLOUD_API + "/api/cloud-accounts",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + token
            },
            body: JSON.stringify(payload)
        }
    );

    const data = await response.json();

    document.getElementById("cloudAccountMessage").textContent =
        response.ok
            ? "Cloud account added successfully."
            : (data.detail || "Unable to add cloud account.");

    if (response.ok) {
        document.getElementById("cloudAccountForm").reset();
        await loadCloudAccounts();
    }
}

async function deleteCloudAccount(accountId) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(
        CLOUD_API + "/api/cloud-accounts/" + accountId,
        {
            method: "DELETE",
            headers: {
                Authorization: "Bearer " + token
            }
        }
    );

    if (response.ok) {
        await loadCloudAccounts();
    }
}
