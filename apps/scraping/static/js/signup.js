import { API_ENDPOINTS } from "./api/config.js";

const form = document.getElementById("signup-form")
const responseContainer = document.getElementById("response-container")

form.addEventListener("submit", async (e) => {
    e.preventDefault()

    const username = document.getElementById("username-input").value
    const password1 = document.getElementById("password1-input").value
    const password2 = document.getElementById("password2-input").value

    try {
        const response = await fetch(`${API_ENDPOINTS.SIGN_UP}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                username: username,
                password1: password1,
                password2: password2
            })

        })

        const data = await response.json()

        if (!response.ok) {
            const errorMessage = data.username?.[0] || data.non_field_errors?.[0] || "Something went wrong"
            responseContainer.innerText = errorMessage
            return
        }

        responseContainer.innerText = "User created successfully"

        setTimeout(() => {
            window.location.href = "/signin/"
        }, 1000)
        
    } catch (error) {
        console.error("Signup error", error)
        responseContainer.innerText = "Network error"
    }
})