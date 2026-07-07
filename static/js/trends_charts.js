// static/js/trends_charts.js

function switchKPITrendsCore() {
    const selector = document.getElementById('kpi-dropdown-select');
    const selectedKPI = selector.value;
    
    if (!trendsPayloadData || trendsPayloadData.length === 0) return;
    
    const dates = trendsPayloadData.map(item => item.Date);
    const activeEntries = trendsPayloadData.filter(item => item.Total_Production > 0);
    const activeDates = activeEntries.map(item => item.Date);
    const rangeDates = [activeDates[0], activeDates[activeDates.length - 1]];

    let traces = [];
    let layoutShapes = [];
    let headerHTML = "";
    let bodyHTML = "";
    let weeklyCardsHTML = "";

    const textFont = { color: '#ffffff', family: 'Poppins', size: 13, weight: 600 };

    if (selectedKPI === "production") {
        document.getElementById('chart-dynamic-title').innerText = "📊 Production Output Smooth Area Curves";
        
        const saf1 = trendsPayloadData.map(item => item.SAF1_Prod);
        const saf2 = trendsPayloadData.map(item => item.SAF2_Prod);
        
        traces.push({
            x: dates, y: saf1, name: 'SAF-1 Yield', type: 'scatter', mode: 'lines',
            line: { color: '#f47920', width: 2.5, shape: 'spline' },
            fill: 'tozeroy', fillcolor: 'rgba(244,121,32,0.01)'
        });
        traces.push({
            x: dates, y: saf2, name: 'SAF-2 Yield', type: 'scatter', mode: 'lines',
            line: { color: '#446183', width: 2.5, shape: 'spline' }
        });

        const validProd = trendsPayloadData.map(i => i.Total_Production).filter(v => v > 0);
        document.getElementById('lbl-trends-avg').innerText = (validProd.reduce((a,b)=>a+b,0)/validProd.length).toFixed(1) + " MT";
        document.getElementById('lbl-trends-max').innerText = Math.max(...validProd).toFixed(1) + " MT";
        document.getElementById('lbl-trends-min').innerText = Math.min(...validProd).toFixed(1) + " MT";
        document.getElementById('lbl-trends-target').innerText = "203.0 MT";

        layoutShapes.push({ type: 'line', xref: 'x', yref: 'y', x0: rangeDates[0], y0: 203.0, x1: rangeDates[1], y1: 203.0, line: { color: '#508848', width: 2, dash: 'dash' } });

        headerHTML = "<tr><th>Date Stamp</th><th>SAF-1 Output (MT)</th><th>SAF-2 Output (MT)</th><th>Total Output (MT)</th></tr>";
        activeEntries.slice(-10).reverse().forEach(row => {
            bodyHTML += `<tr><td>${row.Date.split(' ')[0]}</td><td>${row.SAF1_Prod.toFixed(1)}</td><td>${row.SAF2_Prod.toFixed(1)}</td><td style='color: #f47920; font-weight:700;'>${row.Total_Production.toFixed(1)}</td></tr>`;
        });

        // Generate Production Weekly Cards
        serverWeeklyAnalysisData.forEach(w => {
            const glowClass = w.is_best ? "best-week-glow" : "";
            const ribbon = w.is_best ? "<span class='best-badge-ribbon'>🏆 Best Week</span>" : "";
            weeklyCardsHTML += `
                <div class="weekly-performance-card ${glowClass}">
                    ${ribbon}
                    <div style="font-size:11px; color:#636466; font-weight:700;">${w.month}</div>
                    <div style="font-size:16px; font-weight:700; margin: 4px 0; color:#fff;">${w.week_label}</div>
                    <div style="font-size:13px; color:#cbd5e0;">Output: <b style="color:#f47920;">${w.production.toLocaleString(undefined, {maximumFractionDigits:1})} MT</b></div>
                </div>`;
        });

    } else if (selectedKPI === "delays") {
        document.getElementById('chart-dynamic-title').innerText = "⚠️ Loss Analysis & Stacked Breakdown Timeline";
        
        const oprn = trendsPayloadData.map(item => item.Oprn_Delay);
        const mech = trendsPayloadData.map(item => item.Mech_Delay);
        const ei = trendsPayloadData.map(item => item.EI_Delay);
        const mgmt = trendsPayloadData.map(item => item.Mgmt_Delay);

        traces.push({ x: dates, y: oprn, name: 'Operational Delay', type: 'bar', marker: { color: '#8fa35d' } });
        traces.push({ x: dates, y: mech, name: 'Mechanical Breakdown', type: 'bar', marker: { color: '#704548' } });
        traces.push({ x: dates, y: ei, name: 'Electrical & Inst', type: 'bar', marker: { color: '#446183' } });
        traces.push({ x: dates, y: mgmt, name: 'Management Losses', type: 'bar', marker: { color: '#636466' } });

        const totalDelays = trendsPayloadData.map(i => i.Oprn_Delay + i.Mech_Delay + i.EI_Delay + i.Mgmt_Delay);
        const validDelays = totalDelays.filter(v => v > 0);
        document.getElementById('lbl-trends-avg').innerText = (validDelays.reduce((a,b)=>a+b,0)/(validDelays.length || 1)).toFixed(1) + " Hours";
        document.getElementById('lbl-trends-max').innerText = Math.max(...totalDelays, 0).toFixed(1) + " Hours";
        document.getElementById('lbl-trends-min').innerText = Math.min(...validDelays, 0).toFixed(1) + " Hours";
        document.getElementById('lbl-trends-target').innerText = "< 2.0 Hours";

        headerHTML = "<tr><th>Date Stamp</th><th>Operational Loss (Hr)</th><th>Mechanical Loss (Hr)</th><th>Electrical Loss (Hr)</th></tr>";
        activeEntries.slice(-10).reverse().forEach(row => {
            bodyHTML += `<tr><td>${row.Date.split(' ')[0]}</td><td>${row.Oprn_Delay.toFixed(1)}</td><td>${row.Mech_Delay.toFixed(1)}</td><td>${row.EI_Delay.toFixed(1)}</td></tr>`;
        });

        // Generate Delay Weekly Cards
        serverWeeklyAnalysisData.forEach(w => {
            weeklyCardsHTML += `
                <div class="weekly-performance-card">
                    <div style="font-size:11px; color:#636466; font-weight:700;">${w.month}</div>
                    <div style="font-size:16px; font-weight:700; margin: 4px 0; color:#fff;">${w.week_label}</div>
                    <div style="font-size:13px; color:#cbd5e0;">Total Loss: <b style="color:#704548;">${w.total_delays.toFixed(1)} Hrs</b></div>
                </div>`;
        });

    } else if (selectedKPI === "power") {
        document.getElementById('chart-dynamic-title').innerText = "⚡ Specific Energy Consumption Efficiency Grid Line";
        const sec = trendsPayloadData.map(item => item.SEC_Rate);

        traces.push({
            x: dates, y: sec, name: 'SEC Rate MWH/MT', type: 'scatter', mode: 'lines+markers',
            line: { color: '#8fa35d', width: 3, shape: 'spline' }
        });

        document.getElementById('lbl-trends-avg').innerText = "3.42 MWH/MT";
        document.getElementById('lbl-trends-max').innerText = "3.58 MWH/MT";
        document.getElementById('lbl-trends-min').innerText = "3.32 MWH/MT";
        document.getElementById('lbl-trends-target').innerText = "3.65 MWH/MT";

        layoutShapes.push({ type: 'line', xref: 'x', yref: 'y', x0: rangeDates[0], y0: 3.65, x1: rangeDates[1], y1: 3.65, line: { color: '#704548', width: 2, dash: 'dot' } });

        headerHTML = "<tr><th>Date Stamp</th><th>Specific Energy Rate (SEC)</th><th>Target Cap Limit</th><th>Status Condition</th></tr>";
        activeEntries.slice(-10).reverse().forEach(row => {
            bodyHTML += `<tr><td>${row.Date.split(' ')[0]}</td><td>${row.SEC_Rate.toFixed(2)} MWH/MT</td><td>3.65 Norm</td><td style='color:#508848; font-weight:600;'>🟢 Optimum Norm</td></tr>`;
        });

        // Generate Power Weekly Cards
        serverWeeklyAnalysisData.forEach(w => {
            weeklyCardsHTML += `
                <div class="weekly-performance-card">
                    <div style="font-size:11px; color:#636466; font-weight:700;">${w.month}</div>
                    <div style="font-size:16px; font-weight:700; margin: 4px 0; color:#fff;">${w.week_label}</div>
                    <div style="font-size:13px; color:#cbd5e0;">Avg SEC: <b style="color:#8fa35d;">${w.sec.toFixed(2)}</b></div>
                </div>`;
        });
    }

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { l: 50, r: 30, t: 20, b: 60 }, barmode: 'stack', showlegend: true,
        legend: { font: { color: '#ffffff', family: 'Poppins' }, orientation: 'h', x: 0, y: 1.15 },
        xaxis: { gridcolor: '#202830', range: rangeDates, dtick: "M1", tickformat: "%b %Y", tickfont: textFont },
        yaxis: { gridcolor: '#202830', tickfont: { color: '#cbd5e0', family: 'Poppins' } },
        shapes: layoutShapes
    };

    document.getElementById('table-header-row').innerHTML = headerHTML;
    document.getElementById('table-body-rows').innerHTML = bodyHTML;
    document.getElementById('weekly-cards-grid-target').innerHTML = weeklyCardsHTML;
    Plotly.newPlot('trends-dynamic-chart', traces, layout, {responsive: true, displayModeBar: false});
}

document.addEventListener("DOMContentLoaded", switchKPITrendsCore);