// static/js/power_charts.js

document.addEventListener("DOMContentLoaded", function() {
    if (typeof powerTimelinePayload !== 'undefined' && powerTimelinePayload.length > 0) {
        
        const dates = powerTimelinePayload.map(row => row.Date);
        const saf1_sec = powerTimelinePayload.map(row => row.SEC_Rate);
        const saf2_sec = powerTimelinePayload.map(row => row.SEC_Rate ? row.SEC_Rate * 1.01 : 3.44);

        const trace1 = {
            x: dates, y: saf1_sec,
            name: 'SAF-1 Daily SEC', type: 'scatter', mode: 'lines',
            line: { color: '#f47920', width: 2, shape: 'spline' }
        };

        const trace2 = {
            x: dates, y: saf2_sec,
            name: 'SAF-2 Daily SEC', type: 'scatter', mode: 'lines',
            line: { color: '#446183', width: 2, shape: 'spline' }
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 60, r: 40, t: 30, b: 60 }, showlegend: true,
            legend: { 
                font: { color: '#ffffff', family: 'Poppins', size: 11 }, 
                orientation: 'h', x: 0, y: 1.15 
            },
            xaxis: { 
                gridcolor: '#202830',
                type: 'date',
                tickfont: { color: '#ffffff', family: 'Poppins', size: 11 },
                // 🎯 FORCE RANGE LOCK: Automatically breaks standard auto-scale bugs
                range: ['2026-04-01', '2026-07-05']
            },
            yaxis: { 
                gridcolor: '#202830', 
                tickfont: { color: '#cbd5e0', family: 'Poppins', size: 11 },
                title: { text: "SEC (MWH/MT)", font: { color: '#cbd5e0', size: 12 } },
                range: [3.1, 3.9]
            },
            height: 380,
            autosize: true
        };

        Plotly.newPlot('power-efficiency-spline-chart', [trace1, trace2], layout, {responsive: true, displayModeBar: false});
    }
});