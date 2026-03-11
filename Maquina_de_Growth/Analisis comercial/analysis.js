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
    console.log("Reading data...");
    const statsContent = fs.readFileSync('stats_created.csv', 'utf-8');
    const statsData = parseCSV(statsContent);

    const dbContent = fs.readFileSync('BBDD noCRM Completa 260226.csv', 'utf-8');
    const dbData = parseCSV(dbContent);

    // Helpers
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

    // Parse main CRM data
    const leads = dbData.map(r => ({
        ...r,
        amount: parseAmount(r.Amount),
        createdAt: parseDate(r.Created_at),
        closedAt: parseDate(r.Closed_at),
        estimatedCloseAt: parseDate(r.Estimated_closing_date),
        status: r.Status ? r.Status.toLowerCase().trim() : ''
    }));

    // ====== 1. Activity Ratios Analysis ======
    // Filter out 'Total' row from stats
    const sellerStatsRaw = statsData.filter(r => r.Usuarios && r.Usuarios !== 'Total');

    const parseNum = (v) => parseInt(v) || 0;

    const activityRatios = {};
    let totalActSystem = 0;
    let totalWonSystem = 0;

    for (const r of sellerStatsRaw) {
        const u = r.Usuarios.trim();
        const actWhatsapp = parseNum(r['Whatsapp']);
        const actLlamada = parseNum(r['Llamada']);
        const actReunion = parseNum(r['Reunin']) || parseNum(r['Reunión']);
        const actVisita = parseNum(r['Visita/Relevamiento']);
        const actEmail = parseNum(r['E-mail']);

        const sumActivities = actWhatsapp + actLlamada + actReunion + actVisita + actEmail;
        const wonDeals = parseNum(r['ganado']);

        totalActSystem += sumActivities;
        totalWonSystem += wonDeals;

        if (wonDeals > 0) {
            activityRatios[u] = {
                avgTotal: sumActivities / wonDeals,
                avgWhatsapp: actWhatsapp / wonDeals,
                avgLlamada: actLlamada / wonDeals,
                avgReunion: actReunion / wonDeals,
                avgVisita: actVisita / wonDeals
            };
        }
    }

    const overallAvgActivity = totalWonSystem > 0 ? totalActSystem / totalWonSystem : 10; // defaults to 10 if missing

    // ====== 2. Historical Analysis (T2C and Win Rate) ======
    const wonLeads = leads.filter(l => l.status === 'won');
    const lostLeads = leads.filter(l => l.status === 'cancelled' || l.status === 'lost');
    const closedLeads = [...wonLeads, ...lostLeads];

    const overallWinRate = closedLeads.length > 0 ? wonLeads.length / closedLeads.length : 0.16;

    // Amount percentiles for recent data
    const recentWonLeads = wonLeads.filter(l => l.closedAt && l.closedAt.getFullYear() >= 2024);
    const amounts = recentWonLeads.map(l => l.amount).filter(a => a > 0).sort((a, b) => a - b);
    const p33 = amounts[Math.floor(amounts.length * 0.33)] || 1000000;
    const p66 = 20000000; // Hardcoded big deals threshold > 20M

    const bucketT2C = { 'Chicos': { sum: 0, count: 0 }, 'Medianos': { sum: 0, count: 0 }, 'Grandes': { sum: 0, count: 0 } };

    for (const l of recentWonLeads) {
        if (l.amount === 0) continue;
        const t2c = diffDays(l.createdAt, l.closedAt);
        if (l.amount < p33) {
            bucketT2C['Chicos'].sum += t2c; bucketT2C['Chicos'].count++;
        } else if (l.amount >= p66) {
            bucketT2C['Grandes'].sum += t2c; bucketT2C['Grandes'].count++;
        } else {
            bucketT2C['Medianos'].sum += t2c; bucketT2C['Medianos'].count++;
        }
    }

    const avgBucketT2C = {
        'Chicos': bucketT2C['Chicos'].count > 0 ? bucketT2C['Chicos'].sum / bucketT2C['Chicos'].count : 20,
        'Medianos': bucketT2C['Medianos'].count > 0 ? bucketT2C['Medianos'].sum / bucketT2C['Medianos'].count : 40,
        'Grandes': bucketT2C['Grandes'].count > 0 ? bucketT2C['Grandes'].sum / bucketT2C['Grandes'].count : 90,
    };

    // Calculate seller Win Rates
    const userStats = {};
    for (const l of closedLeads) {
        const u = l.User || 'Unknown';
        if (!userStats[u]) userStats[u] = { won: 0, lost: 0 };
        if (l.status === 'won') userStats[u].won++;
        else userStats[u].lost++;
    }

    // ====== 3. Projection ======
    const activeLeads = leads.filter(l => ['todo', 'standby', 'doing'].includes(l.status) || l.status === '');
    const currentDate = new Date(2026, 1, 27);

    const monthsProjection = {
        '2026-03': { amount: 0, deals: 0, activities: 0 },
        '2026-04': { amount: 0, deals: 0, activities: 0 },
        '2026-05': { amount: 0, deals: 0, activities: 0 },
        '2026-06': { amount: 0, deals: 0, activities: 0 },
        '2026-07': { amount: 0, deals: 0, activities: 0 },
        '2026-08': { amount: 0, deals: 0, activities: 0 }
    };

    let activeTotalAmount = 0;
    let projectedTotalAmount = 0;
    let scheduledActivities = 0;

    for (const l of activeLeads) {
        let p = overallWinRate;
        const u = l.User || 'Unknown';

        if (userStats[u] && (userStats[u].won + userStats[u].lost) > 5) {
            p = userStats[u].won / (userStats[u].won + userStats[u].lost);
        }

        let expectedT2C = avgBucketT2C['Medianos'];
        if (l.amount > 0) {
            if (l.amount < p33) expectedT2C = avgBucketT2C['Chicos'];
            else if (l.amount >= p66) expectedT2C = avgBucketT2C['Grandes'];
        }

        let estClose = l.estimatedCloseAt;
        if (!estClose) {
            estClose = new Date(l.createdAt || currentDate);
            estClose.setDate(estClose.getDate() + expectedT2C);
            if (estClose < currentDate) {
                estClose = new Date(currentDate);
                if (l.amount >= p66) estClose.setDate(estClose.getDate() + 45);
                else if (l.amount < p33) estClose.setDate(estClose.getDate() + 15);
                else estClose.setDate(estClose.getDate() + 30);
            }
        }

        const y = estClose.getFullYear();
        let m = estClose.getMonth() + 1;
        const k = `${y}-${m.toString().padStart(2, '0')}`;

        // Match user's activity ratio to estimate workload for this specific lead
        // We match by name directly. A more robust code would use substring matching.
        let sellerRatioMatch = null;
        for (const [sName, sRatio] of Object.entries(activityRatios)) {
            if (sName.toLowerCase().includes(u.toLowerCase()) || u.toLowerCase().includes(sName.toLowerCase())) {
                sellerRatioMatch = sRatio;
                break;
            }
        }
        const neededAct = sellerRatioMatch ? sellerRatioMatch.avgTotal : overallAvgActivity;

        if (monthsProjection[k] !== undefined) {
            const expAmount = l.amount * p;
            monthsProjection[k].amount += expAmount;
            monthsProjection[k].deals += p; // Expected won deals

            // Expected activities (full needed, multiplied by probability to represent "efficient execution")
            // Assuming ALL activities must be done regardless of win or loss, the workload is just neededAct * 1
            const workload = neededAct * 1;
            monthsProjection[k].activities += workload;

            projectedTotalAmount += expAmount;
            scheduledActivities += workload;
        }
        if (l.amount) activeTotalAmount += l.amount;
    }

    // ====== 4. Write Report ======
    let md = `# Análisis Comercial y Proyección de Ventas a 6 Meses\n\n`;
    md += `*Actualización: Impacto de carga operativa (Actividades por vendedor) y negocios >$20M*\n\n`;
    md += `El modelo proyectivo ahora evalúa la estacionalidad de cierres, las probabilidades de éxito puntuales de cada integrante, ajusta los esquemas temporales de cierre categorizando a los negocios "Grandes" como aquellos superiores a 20 millones, e **incluye la carga de actividad proyectada (Workload)** en base al promedio histórico de interacciones necesarias (llamadas, visitas, whatsapp, reuniones) de cada vendedor por cada negocio ganado.\n\n`;

    md += `## 1. Tiempos de Cierre (T2C)\n`;
    md += `- **Negocios Grandes** (> $20.000.000): **${avgBucketT2C['Grandes'].toFixed(0)} días** promedio para concretar.\n`;
    md += `- **Negocios Medianos** (entre límite interior y 20M): **${avgBucketT2C['Medianos'].toFixed(0)} días**.\n`;
    md += `- **Negocios Chicos**: **${avgBucketT2C['Chicos'].toFixed(0)} días**.\n\n`;

    md += `## 2. Esfuerzo Comercial (Actividades históricas por Venta)\n`;
    md += `| Vendedor | Actividades Totales x Venta | Desglose Principal |\n`;
    md += `| -------- | --------------------------- | ------------------ |\n`;
    for (const [sName, ratios] of Object.entries(activityRatios)) {
        md += `| ${sName} | **${ratios.avgTotal.toFixed(1)}** accs. | ${ratios.avgWhatsapp.toFixed(1)} Wpp / ${ratios.avgLlamada.toFixed(1)} Llamas / ${ratios.avgReunion.toFixed(1)} Reus |\n`;
    }
    md += `\n*Promedio General*: ${overallAvgActivity.toFixed(1)} actividades requeridas para llevar un lead a cierre exitoso.\n\n`;

    md += `## 3. Embudo Actual ("Hoy")\n`;
    md += `- **Leads Activos (Standby/ToDo/Doing)**: ${activeLeads.length}\n`;
    md += `- **Valor Total de Leads Activos en Pipeline**: $${activeTotalAmount.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n\n`;

    md += `## 4. Proyección de Ventas y Carga de Trabajo Operativa (6 Meses)\n`;
    md += `Proyección financiera ponderada por probabilidad, correlacionada con los tiempos empujarás cada mes en base a leads activos hoy.\n\n`;

    md += `| Mes | Presupuesto Cierre Estimado | Negocios Esperados (Aprox) | Actividades Operativas Requeridas |\n`;
    md += `| --- | --------------------------- | -------------------------- | --------------------------------- |\n`;
    for (const [k, d] of Object.entries(monthsProjection)) {
        md += `| **${k}** | $${d.amount.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} | ${d.deals.toFixed(1)} | **${d.activities.toFixed(0)}** interacciones |\n`;
    }

    md += `\n**Total Esperado en Próximos 6 Meses**: $${projectedTotalAmount.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n`;
    md += `**Total Actividades a Ejecutar**: ${scheduledActivities.toFixed(0)} interacciones (en seguimientos a la cartera activa).\n`;

    fs.writeFileSync('reporte_proyeccion.md', md);
    console.log("Report generated successfully: reporte_proyeccion.md");

} catch (e) {
    console.error("Error updating projection:", e);
}
