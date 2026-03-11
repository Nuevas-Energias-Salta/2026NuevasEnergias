const { nodewhisper } = require('nodejs-whisper');

async function main() {
    try {
        console.log('Descargando modelo tiny...');
        await nodewhisper.download('tiny');
        console.log('Modelo descargado OK');
    } catch (e) {
        console.error('Error en download:', e.message);
        // Puede ser que el método sea diferente, mostrar API
        console.log('API disponible:', JSON.stringify(Object.keys(nodewhisper)));
        console.log('Tipo:', typeof nodewhisper);
    }
}

main();
