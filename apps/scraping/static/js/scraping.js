import { API_ENDPOINTS } from "./api/config.js";

const scrapingForm = document.getElementById("scraping-form")
const scrapingStatusMessage = document.getElementById("response-message")

form.addEventListener("submit", async (event) => {
    event.preventDefault()

    const startPage = document.getElementById("start_page_input")
    const lastPage = document.getElementById("last_page_input")
    const web = document.getElementById("web_selector")
    const deleteCheckbox = document.getElementById("delete_checkbox")
    const cronToken = document.querySelector("input[name='token']").value
    const accessToken = localStorage.getItem("access")

    try {
        const response = await fetch(`${API_ENDPOINTS.SCRAPING}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`,
                "X-CRON-TOKEN": cronToken
            },
            body: JSON.stringify({
                start_page: startPage,
                last_page: lastPage,
                web: web,
                delete: deleteCheckbox
            })
        })

        const data = await response.json()

        if (!response.ok) {
            scrapingStatusMessage.innerText = data.error || "Something went wrong"
            return
        }

        scrapingStatusMessage.innerText = data.message

    } catch (error) {
        scrapingStatusMessage.innerText = "Network error"
        console.error(error)
    }
})