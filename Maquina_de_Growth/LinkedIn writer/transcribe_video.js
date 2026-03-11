// Transcriptor de video: @xenova/transformers (Whisper tiny) + ffmpeg + wavefile
// Uso: node transcribe_video.js 1         -> transcribe video 1
//      node transcribe_video.js all       -> transcribe todos
//      node transcribe_video.js 1 5 8     -> transcribe videos 1, 5 y 8

const { pipeline } = require('@xenova/transformers');
const ffmpegPath = require('ffmpeg-static');
const { execFileSync } = require('child_process');
const { WaveFile } = require('wavefile');
const fs = require('fs');
const path = require('path');

const VIDEOS_DIR = path.join(__dirname, 'Videos Cortos');
const OUTPUT_DIR = path.join(__dirname, 'transcripciones_videos');

if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// Extraer audio como WAV 16kHz mono
function extractAudio(videoPath, wavPath) {
    console.log('  -> Extrayendo audio: ' + path.basename(videoPath));
    execFileSync(ffmpegPath, [
        '-i', videoPath,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        '-y', wavPath
    ], { stdio: 'pipe' });
}

// Leer WAV y convertir a Float32Array (requerido por transformers.js en Node)
function readWavAsFloat32(wavPath) {
    const buffer = fs.readFileSync(wavPath);
    const wav = new WaveFile(buffer);
    wav.toBitDepth('32f');
    wav.toSampleRate(16000);
    const samples = wav.getSamples(false, Float32Array);
    if (Array.isArray(samples)) {
        const mono = new Float32Array(samples[0].length);
        for (let i = 0; i < samples[0].length; i++) {
            mono[i] = (samples[0][i] + samples[1][i]) / 2;
        }
        return mono;
    }
    return samples;
}

async function transcribeVideo(transcriber, videoFile, index, total) {
    const videoPath = path.join(VIDEOS_DIR, videoFile);
    const baseName = path.basename(videoFile, '.mp4');
    const wavPath = path.join(OUTPUT_DIR, 'temp_' + baseName + '.wav');
    const txtPath = path.join(OUTPUT_DIR, String(index).padStart(2, '0') + '_transcripcion.txt');

    console.log('\n[' + index + '/' + total + '] ' + videoFile);

    try {
        extractAudio(videoPath, wavPath);

        console.log('  -> Leyendo audio...');
        const audioData = readWavAsFloat32(wavPath);
        const durSeg = (audioData.length / 16000).toFixed(0);
        console.log('  -> Duracion: ' + durSeg + ' segundos');

        console.log('  -> Transcribiendo...');
        const result = await transcriber(audioData, {
            language: 'spanish',
            task: 'transcribe',
            chunk_length_s: 30,
            stride_length_s: 5,
            return_timestamps: true,
        });

        let output = '# Video ' + index + ': ' + videoFile + '\nFecha: 3 de diciembre 2025\n\n';
        output += '## Transcripcion completa:\n\n' + result.text + '\n\n';

        if (result.chunks && result.chunks.length > 0) {
            output += '## Con timestamps:\n\n';
            result.chunks.forEach(function (chunk) {
                if (!chunk.timestamp) return;
                const start = chunk.timestamp[0] || 0;
                const m = Math.floor(start / 60).toString().padStart(2, '0');
                const s = Math.floor(start % 60).toString().padStart(2, '0');
                output += '[' + m + ':' + s + '] ' + chunk.text.trim() + '\n';
            });
        }

        fs.writeFileSync(txtPath, output, 'utf8');
        console.log('  OK guardado: ' + path.basename(txtPath));

        if (fs.existsSync(wavPath)) fs.unlinkSync(wavPath);

        return result.text;
    } catch (e) {
        console.error('  ERROR:', e.message);
        if (fs.existsSync(wavPath)) try { fs.unlinkSync(wavPath); } catch (_) { }
        return null;
    }
}

async function main() {
    const args = process.argv.slice(2);

    const allVideos = fs.readdirSync(VIDEOS_DIR)
        .filter(function (f) { return f.endsWith('.mp4'); })
        .sort();

    console.log('\nVideos disponibles (' + allVideos.length + '):');
    allVideos.forEach(function (v, i) {
        const mb = (fs.statSync(path.join(VIDEOS_DIR, v)).size / 1024 / 1024).toFixed(0);
        console.log('  ' + (i + 1) + '. ' + v + ' (' + mb + ' MB)');
    });

    var indices = [];
    if (args[0] === 'all') {
        indices = allVideos.map(function (_, i) { return i + 1; });
    } else if (args.length > 0) {
        indices = args.map(function (a) { return parseInt(a); })
            .filter(function (n) { return !isNaN(n) && n >= 1 && n <= allVideos.length; });
    } else {
        // Sin args: procesar todos por orden de tamaño (menores primero)
        var bySize = allVideos.map(function (v, i) {
            return { i: i + 1, size: fs.statSync(path.join(VIDEOS_DIR, v)).size };
        }).sort(function (a, b) { return a.size - b.size; });
        indices = bySize.map(function (x) { return x.i; });
        console.log('\nSin argumento: procesando tous los videos (del mas corto al mas largo).');
        console.log('Para un solo video usa: node transcribe_video.js 1');
    }

    console.log('\nCargando modelo Whisper tiny (multilingual)...');
    const transcriber = await pipeline('automatic-speech-recognition', 'Xenova/whisper-tiny');
    console.log('Modelo cargado OK!\n');

    const summaryPath = path.join(OUTPUT_DIR, 'RESUMEN_TODOS_LOS_VIDEOS.md');
    var summary = '# Transcripciones de Videos - 3 de diciembre 2025\n\n';

    for (var k = 0; k < indices.length; k++) {
        var idx = indices[k];
        var text = await transcribeVideo(transcriber, allVideos[idx - 1], idx, allVideos.length);
        if (text) {
            summary += '## Video ' + idx + ': ' + allVideos[idx - 1] + '\n\n' + text + '\n\n---\n\n';
        }
    }

    fs.writeFileSync(summaryPath, summary, 'utf8');
    console.log('\nResumen guardado: ' + summaryPath);
    console.log('Transcripciones individuales en: ' + OUTPUT_DIR);
}

main().catch(function (e) {
    console.error('Error fatal:', e.message);
    process.exit(1);
});
