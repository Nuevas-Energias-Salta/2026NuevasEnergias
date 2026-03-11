const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'publicaciones linkedin');

async function scrapeLinkedIn() {
    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    const browser = await chromium.launch({ headless: false, slowMo: 300 });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1280, height: 900 }
    });
    const page = await context.newPage();

    console.log('Navegando al perfil de LinkedIn...');
    await page.goto('https://www.linkedin.com/in/agustin-isasmendi/', { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Pausa para login manual
    console.log('\n========================================');
    console.log('=== ACCIÓN REQUERIDA: INICIAR SESIÓN ===');
    console.log('========================================');
    console.log('Si LinkedIn pide login, iniciá sesión manualmente en el browser abierto.');
    console.log('Tenés 3 MINUTOS para hacerlo. Cuenta regresiva:');
    for (let t = 180; t > 0; t -= 30) {
        console.log(`  ⏳ ${t} segundos restantes...`);
        await page.waitForTimeout(30000);
    }
    console.log('  ✅ Tiempo de login completado. Continuando...\n');

    // Capturar info del perfil
    console.log('Capturando información del perfil...');
    let profileData = { name: '', headline: '', location: '', about: '' };
    try {
        await page.waitForSelector('h1', { timeout: 10000 });
        profileData.name = await page.$eval('h1', el => el.innerText.trim()).catch(() => 'N/A');
        profileData.headline = await page.$$eval('.text-body-medium', els => els[0]?.innerText.trim() || 'N/A').catch(() => 'N/A');
        profileData.location = await page.$$eval('.pb2 .text-body-small', els => els.map(e => e.innerText.trim()).find(t => t.length > 2) || 'N/A').catch(() => 'N/A');

        // Click "ver más" en About si existe
        const showMoreBtn = await page.$('[data-generated-suggestion-target] button, .lt-line-clamp__more');
        if (showMoreBtn) await showMoreBtn.click().catch(() => { });

        profileData.about = await page.$$eval('#about ~ * span[aria-hidden="true"], .display-flex.ph5 p',
            els => els.map(e => e.innerText.trim()).filter(t => t.length > 50).slice(0, 3).join('\n')
        ).catch(() => 'N/A');
    } catch (e) {
        console.log('Error capturando perfil:', e.message);
    }

    // Guardar perfil
    const profileContent = `# Perfil LinkedIn - ${profileData.name}

**Titular:** ${profileData.headline}
**Ubicación:** ${profileData.location}

## Acerca de
${profileData.about}
`;
    fs.writeFileSync(path.join(OUTPUT_DIR, '00_perfil.md'), profileContent, 'utf8');
    console.log(`Perfil guardado. Nombre: ${profileData.name}`);

    // Navegar a publicaciones
    console.log('\nNavegando a publicaciones...');
    await page.goto('https://www.linkedin.com/in/agustin-isasmendi/recent-activity/shares/', {
        waitUntil: 'domcontentloaded', timeout: 30000
    });
    await page.waitForTimeout(4000);

    // Expandir "ver más" en posts y hacer scroll
    const posts = new Map(); // usar Map para deduplicar por texto

    for (let i = 0; i < 25; i++) {
        // Expandir todos los "see more" / "ver más"
        try {
            const expandBtns = await page.$$('button.feed-shared-inline-show-more-text__see-more-less-toggle, button[aria-label*="more"], .see-more');
            for (const btn of expandBtns) {
                await btn.click().catch(() => { });
                await page.waitForTimeout(300);
            }
        } catch (e) { }

        // Extraer posts con estrategia amplia
        const pagePosts = await page.evaluate(() => {
            const results = [];

            // Estrategia 1: buscar contenedores de posts comunes de LinkedIn
            const containers = document.querySelectorAll(
                '[data-urn*="activity"], ' +
                '[data-id*="activity"], ' +
                '.occludable-update, ' +
                '.feed-shared-update-v2, ' +
                '.profile-creator-shared-feed-update__container'
            );

            containers.forEach(container => {
                // Buscar el texto dentro del contenedor
                const textSelectors = [
                    '.feed-shared-text span[dir="ltr"]',
                    '.attributed-text-segment-list__content',
                    '.break-words span[aria-hidden="true"]',
                    '.feed-shared-text',
                    '.update-components-text',
                    '[data-test-id*="main-feed-activity-card__commentary"]',
                    '.commentary',
                ];

                let text = '';
                for (const sel of textSelectors) {
                    const el = container.querySelector(sel);
                    if (el && el.innerText.trim().length > 20) {
                        text = el.innerText.trim();
                        break;
                    }
                }

                // Fecha
                const dateEl = container.querySelector('time, .feed-shared-actor__sub-description span[aria-hidden="true"]');
                const date = dateEl ? dateEl.innerText.trim() : '';

                if (text && text.length > 20) {
                    results.push({ text, date });
                }
            });

            // Estrategia 2: si no encontró nada, buscar todos los span con texto largo
            if (results.length === 0) {
                const allSpans = document.querySelectorAll('main span[dir="ltr"], main .break-words');
                allSpans.forEach(span => {
                    const text = span.innerText?.trim();
                    if (text && text.length > 100 && !text.includes('Conectar') && !text.includes('Seguir')) {
                        results.push({ text, date: '' });
                    }
                });
            }

            return results;
        });

        // Agregar al Map (deduplicar)
        for (const post of pagePosts) {
            const key = post.text.substring(0, 80);
            if (!posts.has(key)) {
                posts.set(key, post);
            }
        }

        console.log(`Scroll ${i + 1}/25 - Posts únicos acumulados: ${posts.size}`);

        // Scroll
        await page.evaluate(() => window.scrollBy(0, 2500));
        await page.waitForTimeout(2000);

        // Si llevamos 3 scrolls seguidos sin nuevos posts, parar
        if (i > 5 && posts.size === previousSize) {
            noProgress++;
            if (noProgress >= 3) {
                console.log('Sin nuevos posts en 3 scrolls. Terminando.');
                break;
            }
        } else {
            noProgress = 0;
        }
        var previousSize = posts.size;
        var noProgress = noProgress || 0;
    }

    await browser.close();

    // Guardar archivos individuales
    const allPosts = Array.from(posts.values());
    allPosts.forEach((post, index) => {
        const num = String(index + 1).padStart(3, '0');
        const content = `# Publicación ${index + 1}\n\n**Fecha:** ${post.date || 'N/A'}\n\n## Contenido\n\n${post.text}\n`;
        fs.writeFileSync(path.join(OUTPUT_DIR, `${num}_publicacion.md`), content, 'utf8');
    });

    // Guardar archivo consolidado
    const allContent = allPosts.map((p, i) =>
        `---\n## Publicación ${i + 1}\n**Fecha:** ${p.date || 'N/A'}\n\n${p.text}`
    ).join('\n\n');

    fs.writeFileSync(
        path.join(OUTPUT_DIR, 'TODAS_LAS_PUBLICACIONES.md'),
        `# Todas las Publicaciones - Agustín Isasmendi\n\nTotal: ${allPosts.length} publicaciones\n\n${allContent}`,
        'utf8'
    );

    console.log(`\n✅ LISTO! Se guardaron ${allPosts.length} publicaciones en "${OUTPUT_DIR}"`);
}

scrapeLinkedIn().catch(console.error);
