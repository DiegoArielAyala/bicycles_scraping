import { API_ENDPOINTS } from "./api/config.js";

const form = document.getElementById("signin-form")
const signinStatusMessage = document.getElementById("status-message")

if (!form) {
    throw new Error("signin-form not found");
}

const googleSigninFailed = new URLSearchParams(window.location.search).get("error") === "google"
if (googleSigninFailed) {
    signinStatusMessage.innerText = "Google sign-in failed. Try username and password, or try Google again in a moment."
    window.history.replaceState({}, "", "/signin/")
}

form.addEventListener("submit", async (e) => {
    e.preventDefault()

    const username = document.getElementById("username-input").value
    const password = document.getElementById("password-input").value

    try {
        const response = await fetch(`${API_ENDPOINTS.SIGN_IN}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
    
        const data = await response.json()
    
        if (!response.ok) {
            const errorMessage = data.detail || data.username?.[0] || data.non_field_errors?.[0] || "Something went wrong"
            signinStatusMessage.innerText = errorMessage
            return
        }
    
        localStorage.setItem("access", data.access)
        localStorage.setItem("refresh", data.refresh)
    
        signinStatusMessage.innerText = "Signed in successfully"
        window.location.href = "/";
    } catch (error) {
        console.error(error)
        signinStatusMessage.innerText = "Network error"
    }
})