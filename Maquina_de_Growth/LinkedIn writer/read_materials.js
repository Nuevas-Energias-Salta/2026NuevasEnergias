const AdmZip = require('adm-zip');
const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

// ==========================================
// 1. LEER EXCEL - CASOS DE ÉXITO
// ==========================================
console.log('\n========== EXCEL: CASOS DE ÉXITO ==========\n');
const wb = XLSX.readFile('casos de exito/Casos de Exito.xlsx');
console.log('Hojas encontradas:', wb.SheetNames);

wb.SheetNames.forEach(sheetName => {
    const ws = wb.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });

    // Filtrar filas vacías
    const nonEmpty = data.filter(row => row.some(v => String(v).trim() !== ''));
    if (nonEmpty.length === 0) return;

    console.log(`\n--- HOJA: "${sheetName}" ---`);
    nonEmpty.slice(0, 50).forEach((row, i) => {
        console.log(row.map(v => String(v).substring(0, 80)).join(' | '));
    });
});

// ==========================================
// 2. LEER PPTX - PRESENTACIONES DE VISTAGE
// ==========================================
const pptxFiles = [
    'presentaciones de vistage/Presentacion NE 24- Vistage .pptx',
    'presentaciones de vistage/Presentacion NE Oct 25.pptx'
];

pptxFiles.forEach(filePath => {
    console.log(`\n\n========== PPTX: ${path.basename(filePath)} ==========\n`);

    try {
        const zip = new AdmZip(filePath);
        const entries = zip.getEntries();

        // Obtener slides ordenados
        const slideEntries = entries
            .filter(e => e.entryName.match(/^ppt\/slides\/slide\d+\.xml$/))
            .sort((a, b) => {
                const numA = parseInt(a.entryName.match(/slide(\d+)/)[1]);
                const numB = parseInt(b.entryName.match(/slide(\d+)/)[1]);
                return numA - numB;
            });

        console.log(`Total slides: ${slideEntries.length}`);

        slideEntries.forEach((entry, idx) => {
            const xml = zip.readAsText(entry);

            // Extraer texto de los elementos <a:t>
            const textMatches = xml.match(/<a:t[^>]*>([^<]+)<\/a:t>/g) || [];
            const texts = textMatches
                .map(m => m.replace(/<[^>]+>/g, '').trim())
                .filter(t => t.length > 0);

            if (texts.length > 0) {
                console.log(`\n--- Slide ${idx + 1} ---`);
                // Agrupar texto único
                const unique = [...new Set(texts)];
                unique.forEach(t => console.log('  ' + t));
            }
        });

    } catch (e) {
        console.error('Error leyendo', filePath, ':', e.message);
    }
});
