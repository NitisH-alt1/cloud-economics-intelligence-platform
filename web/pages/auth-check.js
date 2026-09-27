

const API = "";

function showLogin() {
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("signupForm").style.display = "none";

    document.querySelectorAll(".tab")[0].classList.add("active");
    document.querySelectorAll(".tab")[1].classList.remove("active");
}

function showSignup() {
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("signupForm").style.display = "block";

    document.querySelectorAll(".tab")[0].classList.remove("active");
    document.querySelectorAll(".tab")[1].classList.add("active");
}

function showMessage(id, text, success=false) {
    const element = document.getElementById(id);

    element.textContent = text;
    element.style.display = "block";

    element.className =
        "message " + (success ? "success" : "error");
}

async function signup() {

    const body = {
        email: document.getElementById("signupEmail").value,
        password: document.getElementById("signupPassword").value,
        full_name: document.getElementById("signupName").value,
        organization_name:
            document.getElementById("signupOrganization").value
    };

    try {

        const response = await fetch(
            "http://localhost:8081/api/auth/signup",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Signup failed."
            );
        }

        localStorage.setItem(
            "access_token",
            data.access_token
        );

        showWorkspace(data);

    } catch (error) {

        showMessage(
            "signupMessage",
            error.message
        );
    }
}

async function login() {

    const body = {
        email: document.getElementById("loginEmail").value,
        password: document.getElementById("loginPassword").value
    };

    try {

        const response = await fetch(
            "http://localhost:8081/api/auth/login",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Login failed."
            );
        }

        localStorage.setItem(
            "access_token",
            data.access_token
        );

        showWorkspace(data);

    } catch (error) {

        showMessage(
            "loginMessage",
            error.message
        );
    }
}

async function showWorkspace(authData) {

    const token = authData.access_token;

    const response = await fetch(
        "http://localhost:8081/api/account/me",
        {
            headers: {
                "Authorization":
                    "Bearer " + token
            }
        }
    );

    const account = await response.json();

    if (!response.ok) {
        throw new Error(
            account.detail || "Unable to load account."
        );
    }

    document.getElementById("authBox").style.display = "none";
    window.location.href = "/workspace";

    document.getElementById("welcomeText").textContent =
        "Welcome, " + account.full_name + ".";

    document.getElementById("organizationText").textContent =
        account.organization_id +
        " Â· " +
        account.role;
}

function logout() {

    localStorage.removeItem("access_token");

    document.getElementById("dashboard").style.display = "none";
    document.getElementById("authBox").style.display = "block";

    showLogin();
}

async function restoreSession() {

    const token = localStorage.getItem("access_token");

    if (!token) {
        return;
    }

    try {

        const response = await fetch(
            "http://localhost:8081/api/account/me",
            {
                headers: {
                    "Authorization":
                        "Bearer " + token
                }
            }
        );

        if (!response.ok) {
            localStorage.removeItem("access_token");
            return;
        }

        const account = await response.json();

        document.getElementById("authBox").style.display = "none";
        window.location.href = "/workspace";

        document.getElementById("welcomeText").textContent =
            "Welcome, " + account.full_name + ".";

        document.getElementById("organizationText").textContent =
            account.organization_id +
            " Â· " +
            account.role;

    } catch {
        localStorage.removeItem("access_token");
    }
}

restoreSession();


