// static/js/logistics_charts.js

document.addEventListener("DOMContentLoaded", function() {
    if (typeof inventoryDatasetMatrix !== 'undefined' && inventoryDatasetMatrix.length > 0) {
        
        const labels = inventoryDatasetMatrix.map(item => item.material);
        const tonnages = inventoryDatasetMatrix.map(item => item.tonnage);
        const coverDays = inventoryDatasetMatrix.map(item => item.cover);

        // Trace 1: Available Tonnage - Represented with Guideline Twilight Blue (#446183)
        const traceTonnage = {
            x: labels,
            y: tonnages,
            name: 'Available Stock (MT)',
            type: 'bar',
            marker: { color: '#446183' },
            text: tonnages.map(v => v.toLocaleString() + " MT"),
            textposition: 'outside',
            textfont: { color: '#ffffff', family: 'Poppins', size: 11 }
        };

        // UI Layout Grid Configurations
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 50, r: 20, t: 40, b: 60 },
            showlegend: false,
            xaxis: {
                gridcolor: 'rgba(0,0,0,0)',
                zeroline: false,
                tickfont: { color: '#ffffff', family: 'Poppins', size: 13, weight: 600 }
            },
            yaxis: {
                gridcolor: '#202830',
                zeroline: false,
                tickfont: { color: '#cbd5e0', family: 'Poppins', size: 12 },
                range: [0, Math.max(...tonnages) + 1200] // Dynamic cushion padding at top
            }
        };

        Plotly.newPlot('logistics-inventory-chart', [traceTonnage], layout, {responsive: true, displayModeBar: false});
    }
});