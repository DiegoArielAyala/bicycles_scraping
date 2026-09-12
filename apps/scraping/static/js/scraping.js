import { API_ENDPOINTS } from "./api/config.js";

const scrapingForm = document.getElementById("scraping-form");
const scrapingStatusMessage = document.getElementById("response-message");

async function ensureAdminAccess() {
    const token = localStorage.getItem("access");

    if (!token) {
        window.location.href = "/";
        return false;
    }

    const response = await fetch(`${API_ENDPOINTS.ME}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        sessionStorage.removeItem("roles");
        window.location.href = "/";
        return false;
    }

    const data = await response.json();
    sessionStorage.setItem("roles", JSON.stringify(data.roles));

    if (!data.roles.includes("admin")) {
        window.location.href = "/";
        return false;
    }

    return true;
}

const canUseScraping = await ensureAdminAccess();

if (canUseScraping && scrapingForm) {
    scrapingForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const startPage = document.getElementById("start_page_input").value;
        const lastPage = document.getElementById("last_page_input").value;
        const web = document.getElementById("web_selector").value;
        const deleteCheckbox = document.getElementById("delete_checkbox").checked;
        const cronToken = document.querySelector("input[name='token']").value;
        const accessToken = localStorage.getItem("access");

        try {
            const response = await fetch(`${API_ENDPOINTS.SCRAPING}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                    "X-CRON-TOKEN": cronToken,
                },
                body: JSON.stringify({
                    start_page: Number(startPage),
                    last_page: Number(lastPage),
                    web: web,
                    delete: deleteCheckbox,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                scrapingStatusMessage.innerText =
                    data.detail || data.message || data.error || "Something went wrong";
                return;
            }

            scrapingStatusMessage.innerText = data.message;
        } catch (error) {
            scrapingStatusMessage.innerText = "Network error";
            console.error(error);
        }
    });
}
