import { API_ENDPOINTS } from "./api/config.js";

const params = new URLSearchParams(window.location.search);
const code = params.get("code");

async function handleGoogleCallback() {
    if (!code) {
        console.error("No code from Google");
        window.location.href = "/signin/?error=google";
        return;
    }
    
    try {
        const response = await fetch(`${API_ENDPOINTS.GOOGLE_SIGN_IN}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ code }),
        });
    
        const data = await response.json();
    
        if (!response.ok) {
            console.error("Google login failed", data);
            window.location.href = "/signin/?error=google";
            return;
        }
    
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);
        window.location.href = "/";
    } catch (error) {
        console.error("Google callback error", error);
        window.location.href = "/signin/?error=google";
    }
}

handleGoogleCallback()