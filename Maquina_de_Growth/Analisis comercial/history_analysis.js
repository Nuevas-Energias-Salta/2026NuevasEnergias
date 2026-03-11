const fs = require('fs');

function parseCSV(content) {
    let inQuote = false;
    let currentField = '';
    let currentRow = [];
    let rows = [];
    for (let i = 0; i < content.length; i++) {
        const c = content[i];
        if (c === '"') {
            if (inQuote && content[i + 1] === '"') { currentField += '"'; i++; }
            else { inQuote = !inQuote; }
        } else if (c === ';' && !inQuote) {
            currentRow.push(currentField); currentField = '';
        } else if ((c === '\n' || c === '\r') && !inQuote) {
            if (c === '\r' && content[i + 1] === '\n') { continue; }
            if (c === '\r' || c === '\n') {
                currentRow.push(currentField); rows.push(currentRow);
                currentRow = []; currentField = '';
            }
        } else { currentField += c; }
    }
    if (currentField !== '' || currentRow.length > 0) { currentRow.push(currentField); rows.push(currentRow); }
    if (rows.length === 0) return [];

    const headers = rows[0].map(h => h.trim().replace(/^"|"$/g, '').replace(/\r|\n/g, ''));
    const data = [];
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].length === 0 || (rows[i].length === 1 && rows[i][0] === '')) continue;
        const obj = {};
        for (let j = 0; j < headers.length; j++) {
            let val = rows[i][j] ? rows[i][j].trim() : '';
            if (val.startsWith('"') && val.endsWith('"')) { val = val.substring(1, val.length - 1); }
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
        if (ds.length === 3) { return new Date(parseInt(ds[0]), parseInt(ds[1]) - 1, parseInt(ds[2])); }
        return null;
    };

    const leads = dbData.map(r => ({
        ...r,
        amount: parseAmount(r.Amount),
        createdAt: parseDate(r.Created_at),
        status: r.Status ? r.Status.toLowerCase().trim() : ''
    }));

    const wonLeads = leads.filter(l => l.status === 'won');

    // Find bucket thresholds again to be consistent with previous analysis
    const recentWonLeads = wonLeads.filter(l => l.createdAt && l.createdAt.getFullYear() >= 2024);
    const amounts = recentWonLeads.map(l => l.amount).filter(a => a > 0).sort((a, b) => a - b);
    const p33 = amounts[Math.floor(amounts.length * 0.33)] || 1000000;
    const p66 = 20000000;

    const leads2025 = leads.filter(l => l.createdAt && l.createdAt.getFullYear() === 2025);

    const months2025 = {
        0: { name: 'Enero', G: 0, M: 0, C: 0, Unknown: 0 },
        1: { name: 'Febrero', G: 0, M: 0, C: 0, Unknown: 0 },
        2: { name: 'Marzo', G: 0, M: 0, C: 0, Unknown: 0 },
        3: { name: 'Abril', G: 0, M: 0, C: 0, Unknown: 0 },
        4: { name: 'Mayo', G: 0, M: 0, C: 0, Unknown: 0 },
        5: { name: 'Junio', G: 0, M: 0, C: 0, Unknown: 0 },
        6: { name: 'Julio', G: 0, M: 0, C: 0, Unknown: 0 },
        7: { name: 'Agosto', G: 0, M: 0, C: 0, Unknown: 0 },
        8: { name: 'Septiembre', G: 0, M: 0, C: 0, Unknown: 0 },
        9: { name: 'Octubre', G: 0, M: 0, C: 0, Unknown: 0 },
        10: { name: 'Noviembre', G: 0, M: 0, C: 0, Unknown: 0 },
        11: { name: 'Diciembre', G: 0, M: 0, C: 0, Unknown: 0 },
    };

    let totalG = 0, totalM = 0, totalC = 0, totalU = 0;

    for (const l of leads2025) {
        const m = l.createdAt.getMonth();
        if (l.amount === 0) {
            // Un monto 0 probablemente es que no se completó la cotización, los ponemos como Unknown o Chicos
            months2025[m].Unknown++;
            totalU++;
        } else if (l.amount < p33) {
            months2025[m].C++;
            totalC++;
        } else if (l.amount >= p66) {
            months2025[m].G++;
            totalG++;
        } else {
            months2025[m].M++;
            totalM++;
        }
    }

    // Append to the existing report file
    let existingReport = fs.readFileSync('reporte_objetivo_2026.md', 'utf-8');

    let output = `\n\n## 5. Comparativa Histórica: Generación de Leads 2025\n`;
    output += `Para ver qué tan lejos (o cerca) estamos del **Objetivo 2026**, analizamos todas las oportunidades creadas durante todo 2025 categorizadas por el mismo esquema (las que quedaron en $0 se listan como "Sin Monto").\n\n`;

    output += `**Total Anual Histórico 2025:**\n`;
    output += `- Grandes: **${totalG}** *(vs Meta 2026: 59)*\n`;
    output += `- Medianos: **${totalM}** *(vs Meta 2026: 525)*\n`;
    output += `- Chicos: **${totalC}** *(vs Meta 2026: 285)*\n`;
    output += `- Sin Monto / Incompletos: **${totalU}**\n\n`;

    output += `**Desglose Mensual Real 2025 vs "The Gap"**:\n`;
    output += `| Mes (2025) | Grandes | Medianos | Chicos | Sin Monto | Total Creaciones |\n`;
    output += `| ---------- | ------- | -------- | ------ | --------- | ---------------- |\n`;
    for (let i = 0; i < 12; i++) {
        const d = months2025[i];
        output += `| **${d.name}** | ${d.G} | ${d.M} | ${d.C} | ${d.Unknown} | **${d.G + d.M + d.C + d.Unknown}** |\n`;
    }

    output += `\n### Conclusión Preliminar sobre la Meta vs Realidad 2025\n`;
    output += `Comparando la tabla de 2025 (lo que realmente hicieron) contra la tabla de **Cuotas de Generación 2026** (lo que necesitan hacer para llegar a $2.000 Millones):\n`;

    if (totalG < 59 || totalM < 525) {
        output += `**(Ojo aquí!)** Durante 2025 se generaron ${totalG} negocios Grandes y ${totalM} Medianos con importe en el CRM. La meta para lo que resta de 2026 exige **59 Grandes** y **525 Medianos**. Habrá que hacer un esfuerzo mayúsculo de captación para llegar a esa masa crítica de Leads calificados y valorizarlos correctamente desde el principio.\n`;
    } else {
        output += `¡Buenas noticias! El ritmo histórico de creación que traen de 2025 está dentro o por encima de los requerimientos para alcanzar la meta. Solo tienen que mantener ese volumen calificado.\n`;
    }

    fs.writeFileSync('reporte_objetivo_2026.md', existingReport + output);
    console.log("Histórico 2025 añadido exitosamente al reporte.");

} catch (e) {
    console.error(e);
}
