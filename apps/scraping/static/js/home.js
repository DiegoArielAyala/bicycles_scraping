const homeAuthContent = document.getElementById("home-auth-content");

if (homeAuthContent && !localStorage.getItem("access")) {
    homeAuthContent.innerHTML = `
        <div class="text-center">
            <p class="mb-3 fs-5 text-secondary">
                Sign in to get price alerts on bikes!
            </p>
            <div class="d-flex justify-content-center gap-3">
                <a href="/signin" class="btn btn-outline-light px-4 py-2">
                    Sign In
                </a>
                <a href="/signup" class="btn btn-light px-4 py-2">
                    Sign Up
                </a>
            </div>
        </div>
    `;
}