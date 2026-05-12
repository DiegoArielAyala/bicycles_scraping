const form = document.getElementById("signin-form")
const signinStatusMessage = document.getElementById("status-message")

form.addEventListener("submit", async (e) => {
    e.preventDefault()

    const username = document.getElementById("username-input").value
    const password = document.getElementById("password-input").value

    try {
        const response = await fetch("/api/signin/", {
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
        window.location.href = "/"
    } catch (error) {
        console.error(error)
        signinStatusMessage.innerText = "Network error"
    }
})