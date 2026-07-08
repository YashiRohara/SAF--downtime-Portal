// static/js/raw_material_charts.js

document.addEventListener("DOMContentLoaded", function() {
    if (typeof rawMaterialLocationData !== 'undefined' && rawMaterialLocationData.length > 0) {
        
        const labels = rawMaterialLocationData.map(item => item.material);
        const portStock = rawMaterialLocationData.map(item => item.port);
        const transitStock = rawMaterialLocationData.map(item => item.transit);
        const plantStock = rawMaterialLocationData.map(item => item.plant);

        // 1️⃣ TRACE: Port Stock (Twilight Blue)
        const tracePort = {
            x: labels, y: portStock, name: '⚓ Port Balance (MT)',
            type: 'bar', marker: { color: '#446183' }
        };

        // 2️⃣ TRACE: In-Transit (Saffron)
        const traceTransit = {
            x: labels, y: transitStock, name: '🚂 In-Transit / Rakes (MT)',
            type: 'bar', marker: { color: '#f47920' }
        };

        // 3️⃣ TRACE: Plant Stock (Spring Green)
        const tracePlant = {
            x: labels, y: plantStock, name: '🏗️ Plant Yard Stock (MT)',
            type: 'bar', marker: { color: '#508848' }
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 60, r: 20, t: 30, b: 60 },
            barmode: 'group', // Places bars side-by-side cleanly
            showlegend: true,
            legend: { font: { color: '#ffffff', family: 'Poppins' }, orientation: 'h', x: 0, y: 1.15 },
            xaxis: { gridcolor: 'rgba(0,0,0,0)', tickfont: { color: '#ffffff', family: 'Poppins', size: 12 } },
            yaxis: { gridcolor: '#202830', tickfont: { color: '#cbd5e0' }, title: { text: "Tonnage (MT)", font: { color: '#cbd5e0' } } }
        };

        Plotly.newPlot('rm-location-comparison-chart', [tracePort, traceTransit, tracePlant], layout, {responsive: true, displayModeBar: false});
    }
});