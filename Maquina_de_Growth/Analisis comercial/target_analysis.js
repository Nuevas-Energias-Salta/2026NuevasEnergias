const fs = require('fs');

function parseCSV(content) {
    let inQuote = false;
    let currentField = '';
    let currentRow = [];
    let rows = [];

    for (let i = 0; i < content.length; i++) {
        const c = content[i];
        if (c === '"') {
            if (inQuote && content[i + 1] === '"') {
                currentField += '"';
                i++;
            } else {
                inQuote = !inQuote;
            }
        } else if (c === ';' && !inQuote) {
            currentRow.push(currentField);
            currentField = '';
        } else if ((c === '\n' || c === '\r') && !inQuote) {
            if (c === '\r' && content[i + 1] === '\n') {
                continue;
            }
            if (c === '\r' || c === '\n') {
                currentRow.push(currentField);
                rows.push(currentRow);
                currentRow = [];
                currentField = '';
            }
        } else {
            currentField += c;
        }
    }
    if (currentField !== '' || currentRow.length > 0) {
        currentRow.push(currentField);
        rows.push(currentRow);
    }

    if (rows.length === 0) return [];
    const headers = rows[0].map(h => h.trim().replace(/^"|"$/g, '').replace(/\r|\n/g, ''));
    const data = [];
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].length === 0 || (rows[i].length === 1 && rows[i][0] === '')) continue;
        const obj = {};
        for (let j = 0; j < headers.length; j++) {
            let val = rows[i][j] ? rows[i][j].trim() : '';
            if (val.startsWith('"') && val.endsWith('"')) {
                val = val.substring(1, val.length - 1);
            }
            obj[headers[j]] = val;
        }
        data.push(obj);
    }
    return data;
}

try {
    const dbContent = fs.readFileSync('BBDD noCRM Completa 260226.csv', 'utf-8');
    const dbData = parseCSV(dbContent);

    const parseAmount = (val) => {
        if (!val) return 0;
        let c = val.replace(/[^0-9,-]/g, '').replace(',', '.');
        return parseFloat(c) || 0;
    };

    const parseDate = (val) => {
        if (!val) return null;
        const parts = val.split(' ');
        const ds = parts[0].split('-');
        if (ds.length === 3) {
            return new Date(parseInt(ds[0]), parseInt(ds[1]) - 1, parseInt(ds[2]));
        }
        return null;
    };

    const diffDays = (d1, d2) => {
        if (!d1 || !d2) return null;
        const diffTime = d2 - d1;
        return Math.floor(diffTime / (1000 * 60 * 60 * 24));
    };

    const leads = dbData.map(r => ({
        ...r,
        amount: parseAmount(r.Amount),
        createdAt: parseDate(r.Created_at),
        closedAt: parseDate(r.Closed_at),
        estimatedCloseAt: parseDate(r.Estimated_closing_date),
        status: r.Status ? r.Status.toLowerCase().trim() : ''
    }));

    const wonLeads = leads.filter(l => l.status === 'won');
    const lostLeads = leads.filter(l => l.status === 'cancelled' || l.status === 'lost');
    const closedLeads = [...wonLeads, ...lostLeads];
    const overallWinRate = closedLeads.length > 0 ? wonLeads.length / closedLeads.length : 0.16;

    const recentWonLeads = wonLeads.filter(l => l.closedAt && l.closedAt.getFullYear() >= 2024);
    const amounts = recentWonLeads.map(l => l.amount).filter(a => a > 0).sort((a, b) => a - b);
    const p33 = amounts[Math.floor(amounts.length * 0.33)] || 1000000;
    const p66 = 20000000;

    // Averages per bucket
    let sumC = 0, countC = 0, sumM = 0, countM = 0, sumG = 0, countG = 0;
    for (const l of recentWonLeads) {
        if (l.amount === 0) continue;
        if (l.amount < p33) { sumC += l.amount; countC++; }
        else if (l.amount >= p66) { sumG += l.amount; countG++; }
        else { sumM += l.amount; countM++; }
    }
    const avgChico = countC > 0 ? sumC / countC : p33 / 2;
    const avgMediano = countM > 0 ? sumM / countM : p33 + (p66 - p33) / 2;
    const avgGrande = countG > 0 ? sumG / countG : p66 * 1.5;

    // 1. Calculate 2026 YTD Won
    let won2026YTD = 0;
    for (const l of wonLeads) {
        if (l.closedAt && l.closedAt.getFullYear() === 2026 && (l.closedAt.getMonth() === 0 || l.closedAt.getMonth() === 1)) {
            won2026YTD += l.amount;
        }
    }

    // 2. Projected from active funnel (Simplified)
    const activeLeads = leads.filter(l => ['todo', 'standby', 'doing'].includes(l.status) || l.status === '');
    let projectedActiveAmount = 0;

    // We get the win rates per user again for precise projection
    const userStats = {};
    for (const l of closedLeads) {
        const u = l.User || 'Unknown';
        if (!userStats[u]) userStats[u] = { won: 0, lost: 0 };
        if (l.status === 'won') userStats[u].won++;
        else userStats[u].lost++;
    }

    for (const l of activeLeads) {
        let p = overallWinRate;
        const u = l.User || 'Unknown';
        if (userStats[u] && (userStats[u].won + userStats[u].lost) > 5) {
            p = userStats[u].won / (userStats[u].won + userStats[u].lost);
        }
        projectedActiveAmount += (l.amount * p);
    }

    // 3. The Gap
    const target2026 = 2000000000; // 2.000 Millones
    const totalExpectedSoFar = won2026YTD + projectedActiveAmount;
    const gapAmount = target2026 - totalExpectedSoFar;

    // Total Pipeline value needed to close the gap
    // If win rate is ~16%, we need 1 / 0.16 = 6.25x the gap in pipeline
    const pipelineGapNeeded = gapAmount / overallWinRate;

    // 4. Seasonality Distribution
    // The user noted Dec, Jan, Feb are very slow. 
    // We have 10 months left to create leads (Mar-Dec). 
    // We should weight lead creation heavily in Mar-Nov, and very little in Dec.
    // Let's create a weight array for lead generation targets:
    // Mar: 12%, Apr: 12%, May: 12%, Jun: 12%, Jul: 12%, Aug: 12%, Sep: 10%, Oct: 10%, Nov: 6%, Dec: 2% (Sum = 100%)

    const monthlyWeights = {
        'Marzo': 0.12, 'Abril': 0.12, 'Mayo': 0.12, 'Junio': 0.12,
        'Julio': 0.12, 'Agosto': 0.12, 'Septiembre': 0.10, 'Octubre': 0.10,
        'Noviembre': 0.06, 'Diciembre': 0.02
    };

    // We need a mix of tickets to hit the pipeline target. Let's assume a healthy mix similar to historical:
    // Historical amounts (sum):
    const totalHistoricalVolume = sumC + sumM + sumG;
    const mixC = sumC / totalHistoricalVolume;
    const mixM = sumM / totalHistoricalVolume;
    const mixG = sumG / totalHistoricalVolume;

    // Amount needed from each bucket
    const pipeC = pipelineGapNeeded * mixC;
    const pipeM = pipelineGapNeeded * mixM;
    const pipeG = pipelineGapNeeded * mixG;

    // Number of leads needed from each bucket in total
    const leadsC = pipeC / avgChico;
    const leadsM = pipeM / avgMediano;
    const leadsG = pipeG / avgGrande;

    let output = `# Objetivo 2026: Estrategia de Generación de Leads\n\n`;
    output += `*En base al objetivo anual de $2.000.000.000*\n\n`;

    output += `## 1. Estado Actual de la Meta\n`;
    output += `- **Objetivo Anual**: $2.000.000.000\n`;
    output += `- **Vendido Ene-Feb 2026**: $${won2026YTD.toLocaleString('es-AR', { maximumFractionDigits: 0 })}\n`;
    output += `- **Proyección del Embudo Activo**: $${projectedActiveAmount.toLocaleString('es-AR', { maximumFractionDigits: 0 })}\n`;
    output += `- **Brecha a cubrir (GAP)**: $${gapAmount.toLocaleString('es-AR', { maximumFractionDigits: 0 })}\n\n`;

    if (gapAmount <= 0) {
        output += `¡El embudo actual y las ventas cerradas ya cubren el objetivo!\n`;
    } else {
        output += `## 2. Volumen de Pipeline Necesario\n`;
        output += `Dado el Win Rate histórico general del ${(overallWinRate * 100).toFixed(1)}%, para facturar esos $${gapAmount.toLocaleString('es-AR', { maximumFractionDigits: 0 })} extra, es necesario generar nuevos negocios en el embudo por un valor bruto total de:\n`;
        output += `**Valor de Pipeline a generar: $${pipelineGapNeeded.toLocaleString('es-AR', { maximumFractionDigits: 0 })}**\n\n`;

        output += `## 3. Mix de Leads Sugerido\n`;
        output += `Basado en la distribución histórica de tus ventas por tamaño de negocio, este pipeline se divide de la siguiente forma:\n`;
        output += `- **Grandes (> 20M)**: ~(Promedio $${avgGrande.toLocaleString('es-AR', { maximumFractionDigits: 0 })}) -> **${Math.ceil(leadsG)} leads totales** a conseguir.\n`;
        output += `- **Medianos**: ~(Promedio $${avgMediano.toLocaleString('es-AR', { maximumFractionDigits: 0 })}) -> **${Math.ceil(leadsM)} leads totales** a conseguir.\n`;
        output += `- **Chicos (< ${p33.toLocaleString('es-AR')})**: ~(Promedio $${avgChico.toLocaleString('es-AR', { maximumFractionDigits: 0 })}) -> **${Math.ceil(leadsC)} leads totales** a conseguir.\n\n`;
        output += `*Total de nuevos leads a ingresar al sistema: ${Math.ceil(leadsG + leadsM + leadsC)}.*\n\n`;

        output += `## 4. Cuotas de Generación Mensual (Ajustado por Estacionalidad)\n`;
        output += `Considerando que Diciembre, Enero y Febrero son meses lentos tanto en decisión como en esfuerzo (y además los ciclos de venta de negocios grandes superan los 90 días, por lo que un lead generado en diciembre casi seguro se cierra en 2027), la carga de captación debe concentrarse fuertemente entre Marzo y Agosto.\n\n`;

        output += `| Mes (2026) | Ponderación | Grandes a crear | Medianos a crear | Chicos a crear | Total Leads/Mes |\n`;
        output += `| ---------- | ----------- | --------------- | ---------------- | -------------- | --------------- |\n`;
        for (const [m, w] of Object.entries(monthlyWeights)) {
            const lg = Math.ceil(leadsG * w);
            const lm = Math.ceil(leadsM * w);
            const lc = Math.ceil(leadsC * w);
            output += `| **${m}** | ${(w * 100).toFixed(0)}% | ${lg} | ${lm} | ${lc} | **${lg + lm + lc}** |\n`;
        }
    }

    fs.writeFileSync('reporte_objetivo_2026.md', output);
    console.log("Generado reporte_objetivo_2026.md");

} catch (e) {
    console.error(e);
}
