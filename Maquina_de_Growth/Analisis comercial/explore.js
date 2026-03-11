const fs = require('fs');

try {
    const content = fs.readFileSync('BBDD noCRM Completa 260226.csv', 'utf-8');

    let inQuote = false;
    let currentField = '';
    let currentRow = [];
    let rows = [];

    for (let c of content) {
        if (c === '"') {
            inQuote = !inQuote;
        } else if (c === ';' && !inQuote) {
            currentRow.push(currentField);
            currentField = '';
        } else if ((c === '\n' || c === '\r') && !inQuote) {
            if (c === '\r') continue;
            currentRow.push(currentField);
            if (currentRow.length > 1) rows.push(currentRow);
            currentRow = [];
            currentField = '';
            if (rows.length > 5) break;
        } else {
            currentField += c;
        }
    }

    const headers = rows[0].map(h => h.trim().replace(/^"|"$/g, '').replace(/\r/g, ''));
    const sample = {};
    headers.forEach((h, i) => {
        sample[h] = rows[1]?.[i]?.trim().replace(/^"|"$/g, '').replace(/\r/g, '') || '';
    });

    // Check possible status values
    let statuses = new Set();
    let rowsAll = [];
    let count = 0;
    // Just regex for status field which is near the start
    // Actually, step id = Status? Let's check headers first.
    fs.writeFileSync('schema.json', JSON.stringify({ headers, sample }, null, 2));
} catch (e) {
    console.error(e);
}
