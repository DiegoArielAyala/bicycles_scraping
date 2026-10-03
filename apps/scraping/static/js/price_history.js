import { API_ENDPOINTS } from "./api/config.js";

document.addEventListener("DOMContentLoaded", async () => {
    const reference = window.location.pathname.split("/").filter(Boolean).pop()

    try {
        const response = await fetch(`${API_ENDPOINTS.PRICE_HISTORY}${reference}/`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            }
        })

        const data = await response.json()

        if (!response.ok) {
            console.error(data)
            return
        }

        renderChart(data)

    } catch (error) {
        console.error("Error fetching price history", error)
    }
})

function renderChart(data) {
    const trace = {
        x: data.dates,
        y: data.prices,
        mode: "lines+markers",
        name: "Precio"
    }

    const layout = {
        title: data.name,
        plot_bgcolor: "#212529",
        paper_bgcolor: "#212529",
        font: { color: "#f8f9fa" },
        xaxis: { title: "Date" },
        yaxis: { title: "Price (€)" }
    }

    Plotly.newPlot("chart", [trace], layout)
}