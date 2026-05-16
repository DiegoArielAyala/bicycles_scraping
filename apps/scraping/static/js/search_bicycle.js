const resultsContainer = document.getElementById("search-results")
const params = new URLSearchParams(window.location.search)
const query = params.get("q")

if (query) {
    fetchBicycles(query)
}

function fetchBicycles(query) {
    try {
        const response = await fetch(`/api/search_bicycle/?q=${query}`)

        const data = await response.json()

        renderSearchResults(data)
    } catch (error) {
        console.error("Search error", error)
    }
}

function renderSearchResults(data) {
    resultsContainer.innerHTML = ""

    if (!data.length) {
        resultsContainer.innerHTML = `
            <div class="text-secondary fs-5 text-center mt-3">
                We couldn't find any bicycles matching your search.
            </div>
        `
        return
    } 

    data.forEach(bicycle => {
        resultsContainer.innerHTML += `
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
                            <a href="/price-history/${bicycle.reference}" class="btn btn-outline-light px-4">Price History</a>
                            <a href="/subscription/?reference=${bicycle.reference}" class="btn btn-outline-light px-4">Subscribe</a>
                        </div>
                    </div>
                </div>
            </section>
        `
    });
}
