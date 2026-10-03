import { API_ENDPOINTS } from "./api/config.js";

const statusEl = document.getElementById("subscriptions-status");
const listEl = document.getElementById("subscriptions-list");

function getToken() {
    return localStorage.getItem("access");
}

function renderSubscription(sub) {
    return `
        <article class="border border-accent rounded-4 p-3 bg-dark">
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
                <div>
                    <h3 class="fs-4 text-light mb-2">${sub.bicycle_name}</h3>
                    <p class="text-secondary mb-1">Reference: ${sub.bicycle_reference}</p>
                    <p class="text-secondary mb-1">Web: ${sub.bicycle_web}</p>
                    <p class="text-secondary mb-0">Alert email: ${sub.email}</p>
                </div>
                <div class="d-flex flex-column flex-sm-row gap-2">
                    <a href="/price_history/${sub.bicycle_reference}" class="btn btn-outline-light px-4">
                        Price History
                    </a>
                    <button
                        type="button"
                        class="btn btn-outline-danger px-4 unsubscribe-btn"
                        data-email="${sub.email}"
                        data-reference="${sub.bicycle_reference}"
                    >
                        Unsubscribe
                    </button>
                </div>
            </div>
        </article>
    `;
}

async function unsubscribe(email, reference) {
    const token = getToken();
    const response = await fetch(API_ENDPOINTS.UNSUBSCRIPTION, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email, reference }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Could not unsubscribe");
    }
}

async function loadSubscriptions() {
    const token = getToken();

    if (!token) {
        window.location.href = "/signin/";
        return;
    }

    statusEl.innerText = "Loading...";
    listEl.innerHTML = "";

    try {
        const response = await fetch(API_ENDPOINTS.SUBSCRIPTION, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (response.status === 401) {
            window.location.href = "/signin/";
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            statusEl.innerText = data.detail || "Could not load subscriptions";
            return;
        }

        const subscriptions = Array.isArray(data) ? data : data.results || [];

        if (subscriptions.length === 0) {
            statusEl.innerText = "You have no subscriptions yet.";
            return;
        }

        statusEl.innerText = "";
        listEl.innerHTML = subscriptions.map(renderSubscription).join("");
    } catch (error) {
        console.error(error);
        statusEl.innerText = "Network error";
    }
}

listEl.addEventListener("click", async (e) => {
    const button = e.target.closest(".unsubscribe-btn");
    if (!button) return;

    const { email, reference } = button.dataset;
    button.disabled = true;

    try {
        await unsubscribe(email, reference);
        await loadSubscriptions();
    } catch (error) {
        statusEl.innerText = error.message;
        button.disabled = false;
    }
});

loadSubscriptions();
