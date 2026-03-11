import fs from 'fs';

function parseCSV(content, sep = ';') {
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
        } else if (c === sep && !inQuote) {
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
    const content = fs.readFileSync('stats_created.csv', 'utf-8');
    const data = parseCSV(content);

    let output = "### Stats CSV Analysis\n";
    output += `Filas: ${data.length}\n`;
    output += `Columnas: ${Object.keys(data[0] || {}).join(', ')}\n`;

    console.log(output);
    console.log("Sample 1:", JSON.stringify(data[0], null, 2));

} catch (e) {
    console.error(e);
}
