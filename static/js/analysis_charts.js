// static/js/analysis_charts.js

document.addEventListener("DOMContentLoaded", function() {
    if (typeof crossAnalysisPayload !== 'undefined' && crossAnalysisPayload.length > 0) {
        
        // Filter out zero entries to map only actual operational days vectors
        const activeData = crossAnalysisPayload.filter(item => item.Total_Production > 0 && item.Total_Power > 0);
        
        const totalPower = activeData.map(item => item.Total_Power);
        const totalProduction = activeData.map(item => item.Total_Production);
        const textLabels = activeData.map(item => "Date: " + item.Date.split(' ')[0]);

        // 🟢 TRACE 1: Scatter Data Clusters Points
        const traceScatter = {
            x: totalPower,
            y: totalProduction,
            mode: 'markers',
            type: 'scatter',
            name: 'Daily Operational Runs',
            text: textLabels,
            marker: {
                color: '#f47920', // Saffron clusters
                size: 9,
                line: { color: '#ffffff', width: 1 },
                opacity: 0.8
            }
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 60, r: 30, t: 30, b: 60 },
            showlegend: false,
            xaxis: {
                gridcolor: '#202830',
                zeroline: false,
                title: { text: 'Total Power Ingested (MWH) ->', font: { color: '#cbd5e0', family: 'Poppins', size: 13 } },
                tickfont: { color: '#ffffff', family: 'Poppins' }
            },
            yaxis: {
                gridcolor: '#202830',
                zeroline: false,
                title: { text: 'Furnace Steel Yield (MT) ->', font: { color: '#cbd5e0', family: 'Poppins', size: 13 } },
                tickfont: { color: '#ffffff', family: 'Poppins' }
            }
        };

        Plotly.newPlot('consumption-efficiency-scatter', [traceScatter], layout, {responsive: true, displayModeBar: false});
    }
});