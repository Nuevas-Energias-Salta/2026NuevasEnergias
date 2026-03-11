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
                i++; // skip escaped quote
            } else {
                inQuote = !inQuote;
            }
        } else if (c === ';' && !inQuote) {
            currentRow.push(currentField);
            currentField = '';
        } else if ((c === '\n' || c === '\r') && !inQuote) {
            if (c === '\r' && content[i + 1] === '\n') {
                continue; // skip \r if it's \r\n, handle \n next
            }
            if (c === '\r') {
                currentRow.push(currentField);
                rows.push(currentRow);
                currentRow = [];
                currentField = '';
            }
            if (c === '\n') {
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
    const content = fs.readFileSync('BBDD noCRM Completa 260226.csv', 'utf-8');
    const data = parseCSV(content);

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

    const leads = data.map(r => ({
        ...r,
        amount: parseAmount(r.Amount),
        createdAt: parseDate(r.Created_at),
        closedAt: parseDate(r.Closed_at),
        estimatedCloseAt: parseDate(r.Estimated_closing_date),
        status: r.Status ? r.Status.toLowerCase().trim() : ''
    }));

    const wonLeads = leads.filter(l => l.status === 'won' && l.createdAt && l.closedAt);

    let analysisOutput = "### Análisis de Tiempos de Cierre (Días) vs Monto\n\n";

    // Sort by Closed At to see recent trends
    wonLeads.sort((a, b) => a.closedAt - b.closedAt);

    // Group by half-years
    const periodStats = {};
    for (const l of wonLeads) {
        const y = l.closedAt.getFullYear();
        const half = l.closedAt.getMonth() < 6 ? 'H1' : 'H2';
        const key = `${y}-${half}`;
        if (!periodStats[key]) periodStats[key] = { sum: 0, count: 0 };
        periodStats[key].sum += diffDays(l.createdAt, l.closedAt);
        periodStats[key].count++;
    }

    analysisOutput += "#### Evolución por Semestre:\n";
    for (const [k, v] of Object.entries(periodStats)) {
        analysisOutput += `- ${k}: ${(v.sum / v.count).toFixed(0)} días (sobre ${v.count} cierres)\n`;
    }

    // Group by Amount buckets
    // Find amount distribution
    const amounts = wonLeads.map(l => l.amount).filter(a => a > 0).sort((a, b) => a - b);
    const p33 = amounts[Math.floor(amounts.length * 0.33)] || 1000000;
    const p66 = amounts[Math.floor(amounts.length * 0.66)] || 5000000;

    const bucketStats = {
        ['Chicos ( < ' + p33.toLocaleString('es-AR') + ' )']: { sum: 0, count: 0 },
        'Medianos': { sum: 0, count: 0 },
        ['Grandes ( > ' + p66.toLocaleString('es-AR') + ' )']: { sum: 0, count: 0 }
    };

    for (const l of wonLeads) {
        if (l.amount === 0) continue;
        const t2c = diffDays(l.createdAt, l.closedAt);
        if (l.amount < p33) {
            bucketStats[Object.keys(bucketStats)[0]].sum += t2c;
            bucketStats[Object.keys(bucketStats)[0]].count++;
        } else if (l.amount > p66) {
            bucketStats[Object.keys(bucketStats)[2]].sum += t2c;
            bucketStats[Object.keys(bucketStats)[2]].count++;
        } else {
            bucketStats['Medianos'].sum += t2c;
            bucketStats['Medianos'].count++;
        }
    }

    analysisOutput += "\n#### Tiempos de Cierre por Tamaño del Negocio:\n";
    for (const [k, v] of Object.entries(bucketStats)) {
        if (v.count > 0) {
            analysisOutput += `- ${k}: ${(v.sum / v.count).toFixed(0)} días (sobre ${v.count} cierres)\n`;
        }
    }

    fs.writeFileSync('stats.json', JSON.stringify({ periodStats, bucketStats }, null, 2));
    console.log("Stats written to stats.json");

} catch (e) {
    console.error(e);
}
