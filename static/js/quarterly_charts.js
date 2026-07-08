// static/js/quarterly_charts.js

function renderQuarterlyView() {
    const toggleValue = document.getElementById('analysis-time-toggle').value;
    const targetData = toggleValue === "monthly" ? quarterlyPayload.monthly_series : quarterlyPayload.weekly_series;
    
    if (!targetData || targetData.length === 0) return;

    const labels = targetData.map(item => item.label);
    const volumes = targetData.map(item => item.production);
    
    // Core color array mapper to assign distinctive green highlighting to the maximum cell
    const barColors = targetData.map(item => item.is_best ? '#508848' : '#446183');

    // 🟢 Dynamic Bar Trace Configuration
    const trace = {
        x: labels,
        y: volumes,
        type: 'bar',
        marker: { color: barColors },
        text: volumes.map(v => v.toLocaleString(undefined, {maximumFractionDigits:1}) + " MT"),
        textposition: 'outside',
        textfont: { color: '#ffffff', family: 'Poppins' }
    };

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 50, r: 20, t: 30, b: 60 },
        xaxis: { gridcolor: 'rgba(0,0,0,0)', tickfont: { color: '#ffffff', family: 'Poppins', size: 12 } },
        yaxis: { gridcolor: '#202830', tickfont: { color: '#cbd5e0' }, range: [0, Math.max(...volumes) * 1.25] }
    };

    // 🏆 Generate Highlight Cards Segment HTML
    let cardsHTML = "";
    targetData.forEach(item => {
        const bestGlow = item.is_best ? "crown-gold" : "";
        const crown = item.is_best ? `<span class='crown-tag'>🏆 Best ${toggleValue === "monthly" ? "Month" : "Week"}</span>` : "";
        
        cardsHTML += `
            <div class="highlight-badge-card ${bestGlow}">
                ${crown}
                <div style="font-size:11px; color:#636466; font-weight:700; text-transform:uppercase;">Timeline Segment</div>
                <div style="font-size:15px; font-weight:700; color:#fff; margin:5px 0;">${item.label}</div>
                <div style="font-size:18px; font-weight:800; color:${item.is_best ? '#508848' : '#f47920'}">
                    ${item.production.toLocaleString(undefined, {maximumFractionDigits:1})} <span style="font-size:11px; font-weight:500; color:#cbd5e0;">MT</span>
                </div>
            </div>`;
    });

    document.getElementById('quarterly-chart-title').innerText = toggleValue === "monthly" ? "📊 Monthly Structural Output Volumetrics" : "📊 Weekly Detailed Production Blocks";
    document.getElementById('quarterly-cards-target').innerHTML = cardsHTML;
    Plotly.newPlot('quarterly-plotly-chart', [trace], layout, {responsive: true, displayModeBar: false});
}

document.addEventListener("DOMContentLoaded", renderQuarterlyView);