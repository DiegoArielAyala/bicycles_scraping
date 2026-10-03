import { API_ENDPOINTS } from "./api/config.js";

const unsubscribeForm = document.getElementById("unsubscribe-form")
const responseContainer = document.getElementById("response-container")

unsubscribeForm.addEventListener("submit", async (e) => {
    e.preventDefault()

    const emailInput = document.getElementById("email-input").value
    const referenceInput = document.getElementById("reference-input").value
    const accessToken = localStorage.getItem("access")

    try {
        const response = await fetch(`${API_ENDPOINTS.UNSUBSCRIPTION}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                email: emailInput,
                reference: referenceInput
            })
        })

        const data = await response.json()

        if (!response.ok) {
            const errorMessage =
                data.detail ||
                data.reference?.[0] ||
                data.email?.[0] ||
                "Something went wrong"

            responseContainer.innerText = errorMessage
            return
        }

        responseContainer.innerText = data.detail

    } catch (error) {
        console.error("Unsubscription error", error)
        responseContainer.innerText = "Network error"
    }
})