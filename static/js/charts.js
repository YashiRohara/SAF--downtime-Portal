// static/js/charts.js

document.addEventListener("DOMContentLoaded", function() {
    if (typeof serverTimeSeriesData !== 'undefined' && serverTimeSeriesData.length > 0) {
        
        // 📊 Data Extraction
        const dates = serverTimeSeriesData.map(item => item.Date);
        const saf1Prod = serverTimeSeriesData.map(item => item.SAF1_Prod);
        const saf2Prod = serverTimeSeriesData.map(item => item.SAF2_Prod);
        const totalProd = serverTimeSeriesData.map(item => item.Total_Production);
        
        // 🧮 Bottom Badges Matrix Calculations
        const validProd = totalProd.filter(v => v > 0);
        const maxVal = Math.max(...validProd);
        const minVal = Math.min(...validProd);
        const avgVal = validProd.reduce((a, b) => a + b, 0) / validProd.length;
        
        document.getElementById('lbl-avg').innerText = avgVal.toFixed(2) + " MT";
        document.getElementById('lbl-max').innerText = maxVal.toFixed(1) + " MT";
        document.getElementById('lbl-min').innerText = minVal.toFixed(1) + " MT";
        document.getElementById('lbl-count').innerText = validProd.length;

        // 1️⃣ TRACE: SAF-1 (Poppins Saffron with Smooth Curvature)
        const traceSAF1 = {
            x: dates,
            y: saf1Prod,
            name: 'SAF-1 Output',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#f47920', width: 2.5, shape: 'spline', smoothing: 1.3 }, // Max smoothing parameter
            fill: 'tozeroy',
            fillcolor: 'rgba(244, 121, 32, 0.02)'
        };

        // 2️⃣ TRACE: SAF-2 (Twilight Blue Smooth Curve)
        const traceSAF2 = {
            x: dates,
            y: saf2Prod,
            name: 'SAF-2 Output',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#446183', width: 2.5, shape: 'spline', smoothing: 1.3 },
            fill: 'tozeroy',
            fillcolor: 'rgba(68, 97, 131, 0.02)'
        };

        // 3️⃣ TRACE: Total Output (Clean Bold White Curve)
        const traceTotal = {
            x: dates,
            y: totalProd,
            name: 'Total Combined Production',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#ffffff', width: 3, shape: 'spline', smoothing: 1.3 }
        };

        // Find the active boundaries where your real data actually starts and ends
        // This cuts off the empty tail space stretching till 2027
        const activeDates = serverTimeSeriesData.filter(item => item.Total_Production > 0).map(item => item.Date);
        const firstActiveDate = activeDates[0] || dates[0];
        const lastActiveDate = activeDates[activeDates.length - 1] || dates[dates.length - 1];

        // 🎨 UI Layout Engine - Wide Spacing Custom Configuration
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 60, r: 40, t: 40, b: 60 },
            showlegend: true,
            legend: { 
                font: { color: '#ffffff', family: 'Poppins', size: 12 },
                orientation: 'h',
                x: 0, y: 1.15
            },
            xaxis: {
                gridcolor: '#202830',
                zeroline: false,
                type: 'date',
                // ✅ CHRONOLOGICAL RANGE LOCK: Graph ko sirf April se July ke beech stretch karega
                range: [firstActiveDate, lastActiveDate], 
                // ✅ TICK CONTROL MATRIX: Ticks ko monthly block par force karega taaki names saaf dikhein
                dtick: "M1", 
                tickformat: "%b %Y", // Dynamic monthly display token format (e.g. Apr 2026, May 2026)
                tickfont: { color: '#ffffff', family: 'Poppins', size: 13, weight: 600 }
            },
            yaxis: {
                gridcolor: '#202830',
                zeroline: false,
                tickfont: { color: '#cbd5e0', family: 'Poppins', size: 12 },
                range: [0, maxVal + 30] // Autoscale vertical window dynamically to maximize display area
            },
            shapes: [{
                type: 'line',
                xref: 'x',
                yref: 'y',
                x0: firstActiveDate,
                y0: 203.0,
                x1: lastActiveDate,
                y1: 203.0,
                line: { color: '#508848', width: 2, dash: 'dash' }
            }]
        };

        const configResponsive = { responsive: true, displayModeBar: false };

        Plotly.newPlot('production-mini-chart', [traceSAF1, traceSAF2, traceTotal], layout, configResponsive);
    }
});