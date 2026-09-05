import { API_ENDPOINTS } from "./api/config.js";

let currentNextPage = null;
let currentPreviousPage = null;

document.addEventListener("DOMContentLoaded", () => {
    const resultsContainer = document.getElementById("search-results");

    if (!resultsContainer) {
        console.error("Missing #search-results container");
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get("q");
    const minPrice = urlParams.get("min_price");
    const maxPrice = urlParams.get("max_price");

    const fetchParams = new URLSearchParams()
    if (query) {fetchParams.append("q", query)}
    if (minPrice) {fetchParams.append("min_price", minPrice)}
    if (maxPrice) {fetchParams.append("max_price", maxPrice)}

    resultsContainer.addEventListener("click", async (e) => {
        const nextBtn = e.target.closest("#nextPageBtn");
        const prevBtn = e.target.closest("#prevPageBtn");

        if (nextBtn && currentNextPage) {
            await fetchBicyclesFromUrl(currentNextPage, resultsContainer);
        }

        if (prevBtn && currentPreviousPage) {
            await fetchBicyclesFromUrl(currentPreviousPage, resultsContainer);
        }
    });

    fetchBicycles(fetchParams, resultsContainer);
});

async function fetchBicycles(params, resultsContainer) {
    try {
        const response = await fetch(`${API_ENDPOINTS.SEARCH_BICYCLE}?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const data = await response.json();

        renderSearchResults(data, resultsContainer);
    } catch (error) {
        console.error("Search error", error);
    }
}

async function fetchBicyclesFromUrl(url, resultsContainer) {
    try {
        if (!url) return;

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const data = await response.json();

        renderSearchResults(data, resultsContainer);
    } catch (error) {
        console.error("Pagination error", error);
    }
}

function renderSearchResults(data, resultsContainer) {
    resultsContainer.innerHTML = "";

    currentNextPage = data.next;
    currentPreviousPage = data.previous;

    const totalResults = data.count || 0;

    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-secondary fs-5 text-center mt-3">
                We couldn't find any bicycles matching your search.
            </div>
        `;
        return;
    }

    let html = ""

    data.results.forEach(bicycle => {
        html += `
            <section class="card shadow-lg rounded-4 border-0 p-4 bg-dark text-light my-3">
                <h2 class="text-accent fs-3 text-center mb-3">${bicycle.name}</h2>

                <div class="row align-items-center g-4">
                    <div class="col-md-4 text-center offset-md-1">
                        <img class="img-fluid rounded-2 shadow-sm" src="${bicycle.img}" />
                    </div>

                    <div class="col-md-7 d-flex flex-column justify-content-center gap-3">
                        <p class="fs-4 text-price fw-bold">${bicycle.current_price} €</p>
                        <p class="fs-4 text-secondary">Reference: ${bicycle.reference}</p>

                        <div class="d-flex flex-wrap gap-3">
                            <a href="${bicycle.url}" class="btn btn-outline-light px-4">Visit site</a>
                            <a href="/price_history/${bicycle.reference}" class="btn btn-outline-light px-4">Price History</a>
                            <a href="/subscription/?reference=${bicycle.reference}" class="btn btn-outline-light px-4">Subscribe</a>
                        </div>
                    </div>
                </div>
            </section>
        `;
    });

    html += `
        <div class="d-flex justify-content-center align-items-center gap-3 mt-4 mb-5">

            ${currentPreviousPage ? `
                <button id="prevPageBtn" class="btn btn-outline-light px-4">
                    ← Previous
                </button>
            ` : `
                <button class="btn btn-outline-secondary px-4" disabled>
                    ← Previous
                </button>
            `}

            <span class="text-light fw-semibold">
                ${totalResults} results
            </span>

            ${currentNextPage ? `
                <button id="nextPageBtn" class="btn btn-outline-light px-4">
                    Next →
                </button>
            ` : `
                <button class="btn btn-outline-secondary px-4" disabled>
                    Next →
                </button>
            `}

        </div>
    `;

    resultsContainer.innerHTML = html
}