document.addEventListener("DOMContentLoaded", async () => {
    const reference = window.location.pathname.split("/").filter(Boolean).pop()

    try {
        const response = await fetch(`api/price_history/${reference}/`, {
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
        x = data.dates,
        y = data.prices,
        mode: "lines+markers",
        name: "Precio"
    }

    const layout = {
        title: data.name,
        plot_bgcolor: "",
        paper_bgbolor: "",
        font: { color: "" },
        xaxis: { title: "Date" },
        yaxis: { title: "Price (€)" }
    }

    Ploty.newPlot("chart", [trace], layout)
}