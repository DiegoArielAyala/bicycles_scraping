import { API_ENDPOINTS } from "./api/config.js";

const navbarAuth = document.getElementById("navbar-auth");

function getToken() {
    return localStorage.getItem("access");
}

function clearSession() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    sessionStorage.removeItem("roles");
}

function renderGuestNavbar() {
    if (!navbarAuth) return;

    navbarAuth.innerHTML = `
        <li class="nav-item">
            <a class="nav-link" href="/">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/search_bicycle/">Search bicycles</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/signin/">Sign in</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/signup/">Sign up</a>
        </li>
    `;
}

async function renderNavbar() {
    if (!navbarAuth) return;

    const token = getToken();

    if (!token) {
        renderGuestNavbar();
        return;
    }

    const response = await fetch(`${API_ENDPOINTS.ME}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        clearSession();
        renderGuestNavbar();
        return;
    }

    const data = await response.json();
    sessionStorage.setItem("roles", JSON.stringify(data.roles));

    navbarAuth.innerHTML = `
        <li class="nav-item">
            <a class="nav-link" href="/">Home</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/search_bicycle/">Search bicycles</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/my_subscriptions/">My Subscriptions</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="#" id="signout">Sign out</a>
        </li>
    `;

    if (data.roles.includes("admin")) {
        navbarAuth.innerHTML += `
            <li class="nav-item">
                <a class="nav-link" href="/scraping/">Scraping</a>
            </li>
        `;
    }
}

document.addEventListener("click", async (e) => {
    if (e.target.id !== "signout") return;

    e.preventDefault();

    try {
        const refresh = localStorage.getItem("refresh");

        if (refresh) {
            const response = await fetch(`${API_ENDPOINTS.SIGN_OUT}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access")}`,
                },
                body: JSON.stringify({ token: refresh }),
            });

            if (!response.ok) {
                console.error("Signout failed", response.status);
            }
        }
    } catch (error) {
        console.error("Signout error", error);
    } finally {
        clearSession();
        window.location.href = "/";
    }
});

renderNavbar();
