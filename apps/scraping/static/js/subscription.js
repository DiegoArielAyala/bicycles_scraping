const responseContainer = document.getElementById("response-container")
const subscriptionForm = document.getElementById("subscription-form")

subscriptionForm.addEventListener("submit", async (e) => {
    e.preventDefault()

    const emailInput = document.getElementById("email-input").value
    const referenceInput = document.getElementById("reference-input").value
    const accessToken = localStorage.getItem("access")

    try {
        const response = await fetch("/api/subscription/", {
            method = "POST",
            headers = {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
                "email": emailInput,
                "reference": referenceInput
            })
        })

        const data = await response.json()

        if (!response.ok) {
            const errorMessage = data.detail || data.reference?.[0] || "Something went wrong"
            responseContainer.innerText = errorMessage
            return
        }

        responseContainer.innerText = "Subscribed successfully"

    } catch (error) {
        console.error("Subscription error", error)
        responseContainer.innerText = "Network error"
    }
})