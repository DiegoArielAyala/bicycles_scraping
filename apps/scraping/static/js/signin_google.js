const signinGoogleButton = document.getElementById("signin-google-button");

if (!signinGoogleButton) {
    throw new Error("signin-google-button not found");
}

const GOOGLE_CLIENT_ID = signinGoogleButton.dataset.clientId;
const REDIRECT_URI = signinGoogleButton.dataset.redirectUri;

signinGoogleButton.addEventListener("click", (e) => {
    e.preventDefault();

    const params = new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID,
        redirect_uri: REDIRECT_URI,
        response_type: "code",
        scope: "email profile",
    })

    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`
})