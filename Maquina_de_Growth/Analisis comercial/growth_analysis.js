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

    // Categorize leads based on tags, description, and status
    const wonDeals = dbData.filter(r => (r.Status || '').toLowerCase().trim() === 'won').map(r => {
        const t = (r.tags || '').toLowerCase() + ' ' + (r.Productos || '').toLowerCase() + ' ' + (r.Lead || '').toLowerCase();
        let productType = 'Otro';
        if (t.includes('termotanques') || t.includes('acs')) productType = 'Termotanques';
        else if (t.includes('piso') || t.includes('pre') || t.includes('radiante') || t.includes('calefac')) productType = 'Piso_Radiante';
        else if (t.includes('solar') || t.includes('fv') || t.includes('fotovoltaico')) productType = 'Solar';
        else if (t.includes('biomasa') || t.includes('estufa') || t.includes('ñuke') || t.includes('ofen')) productType = 'Biomasa';
        else if (t.includes('bomba') || t.includes('pileta')) productType = 'Bomba_Calor';

        const clientType = (r['Tipo de cliente'] || '').toLowerCase().includes('empresa') || t.includes('b2b') || t.includes('indust') || t.includes('agro') ? 'B2B' : 'B2C';

        return {
            id: r.ID,
            leadName: r.Lead,
            amount: parseAmount(r.Amount),
            productType,
            clientType,
            tags: r.tags
        };
    });

    // Strategy 1: Smart Thermostat Upgrades (Piso Radiante base) -> Target: Chicos
    const preBase = wonDeals.filter(d => d.productType === 'Piso_Radiante');

    // Strategy 2: B2C to B2B Cross-sell -> Target: Medianos / Grandes
    const b2cBase = wonDeals.filter(d => d.clientType === 'B2C');

    // Strategy 3: Upgrades / Expansion for Solar clients (Batteries, more panels) -> Target: Medianos
    const solarBase = wonDeals.filter(d => d.productType === 'Solar');

    const conversionAssumptions = {
        preToSmart: 0.15, // 15% of PRE owners buy a smart thermostat (Lead Chico)
        b2cToB2b: 0.05,  // 5% of B2C clients are business owners who will buy Solar/B2B (Lead Grande/Mediano)
        solarUpgrade: 0.10 // 10% of Solar clients buy batteries or expansions (Lead Mediano)
    };

    const smartLeadsTarget = Math.floor(preBase.length * conversionAssumptions.preToSmart);
    const b2bReferralLeadsTarget = Math.floor(b2cBase.length * conversionAssumptions.b2cToB2b);
    const solarUpgradeLeadsTarget = Math.floor(solarBase.length * conversionAssumptions.solarUpgrade);

    let reportAddition = `\n\n## 6. Estrategia de Máquina de Growth ("Pescar en la Pecera")\n`;
    reportAddition += `Basándonos en la estrategia de rentención y cross-selling, hemos analizado la base histórica de clientes cerrados (won) en noCRM a lo largo de los años para estimar cuántos leads pueden ser generados "desde adentro" en lugar de comprarlos o prospectarlos en frío y con qué tamaño de ticket.\n\n`;

    reportAddition += `**1. Upgrade a Termostatos Smart / Mantenimiento (Ticket Chico)**\n`;
    reportAddition += `- Tamaño de la pecera (Clientes históricos de PRE/Calefacción): **${preBase.length} clientes**.\n`;
    reportAddition += `- Asumiendo una tasa de conversión del 15% mediante campañas de WhatsApp/Email a esta base, esto generaría **~${smartLeadsTarget} Leads Chicos**.\n\n`;

    reportAddition += `**2. Cross-Selling de B2C a B2B (Ticket Mediano/Grande)**\n`;
    reportAddition += `- Tamaño de la pecera (Total Clientes B2C): **${b2cBase.length} clientes residenciales**.\n`;
    reportAddition += `- Campaña "*Ya ahorrás en tu casa, ahorrá en tu empresa*". Asumiendo que el 5% son decisores corporativos que responden positivamente, esto generaría **~${b2bReferralLeadsTarget} Leads B2B (Medianos/Grandes)**.\n\n`;

    reportAddition += `**3. Expansión Solar (Baterías/Backup) (Ticket Mediano)**\n`;
    reportAddition += `- Tamaño de la pecera (Clientes Solares): **${solarBase.length} clientes**.\n`;
    reportAddition += `- Asumiendo una penetración del 10% en venta de upgrade de almacenamiento u off-grid, se generarían **~${solarUpgradeLeadsTarget} Leads Medianos**.\n\n`;

    reportAddition += `### Impacto en la Cuota de 2026\n`;
    reportAddition += `De los **868 Leads Totales** requeridos para 2026, la "Máquina de Growth" interna apalancada en la base actual puede inyectar orgánicamente:\n`;
    reportAddition += `- **${smartLeadsTarget} Leads Chicos** (Cubre el ${(smartLeadsTarget / 285 * 100).toFixed(0)}% de los 285 chicos necesarios).\n`;
    reportAddition += `- **${solarUpgradeLeadsTarget + Math.floor(b2bReferralLeadsTarget * 0.7)} Leads Medianos** (Cubre el ${((solarUpgradeLeadsTarget + b2bReferralLeadsTarget * 0.7) / 525 * 100).toFixed(0)}% de los 525 medianos necesarios).\n`;
    reportAddition += `- **${Math.ceil(b2bReferralLeadsTarget * 0.3)} Leads Grandes** (Cubre el ${(Math.ceil(b2bReferralLeadsTarget * 0.3) / 59 * 100).toFixed(0)}% de los 59 grandes necesarios).\n\n`;

    reportAddition += `**Conclusión Growth**: Pescar en la pecera no va a solucionar la necesidad de "Ballenas" (Grandes), donde todavía deberán salir a prospectar B2B agresivamente o cerrar alianzas. Sin embargo, puede resolver más del 20% de su necesidad de tickets chicos y medianos con un costo de adquisición (CAC) cercano a cero y un ciclo de venta muchísimo más corto debido a la confianza ya establecida.\n`;

    let existingReport = fs.readFileSync('reporte_objetivo_2026.md', 'utf-8');
    fs.writeFileSync('reporte_objetivo_2026.md', existingReport + reportAddition);
    console.log("Sección Growth Machine añadida exitosamente.");

} catch (e) {
    console.error(e);
}
