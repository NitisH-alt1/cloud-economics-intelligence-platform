(() => {
    const configuredBase = window.CEA_CONFIG && window.CEA_CONFIG.apiBaseUrl;
    const apiBase = configuredBase || `${window.location.protocol}//${window.location.hostname}:8081`;

    async function request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        if (options.body != null && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
            headers.set("Content-Type", "application/json");
        }

        const token = localStorage.getItem("access_token");
        if (token) headers.set("Authorization", `Bearer ${token}`);
        const response = await fetch(apiBase + path, {...options, headers});
        if (response.status === 401 || response.status === 403) localStorage.removeItem("access_token");
        return response;
    }

    async function readJson(response) {
        try { return await response.json(); } catch { return null; }
    }

    function errorMessage(payload, fallback) {
        const detail = payload && payload.detail;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) {
            return detail.map(item => item && item.msg ? item.msg : String(item)).join("; ");
        }
        return fallback;
    }

    window.CEAApi = {request, readJson, errorMessage};
})();
