import fs from 'fs';
import readline from 'readline';

const csvPath = 'Conversaciones Nuevi/n8n_personalagent_chat_histories_rows (2).csv';

async function parseCSV() {
    const fileStream = fs.createReadStream(csvPath);
    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });

    let isHeader = true;
    const sessions = {};

    for await (const line of rl) {
        if (isHeader) {
            isHeader = false;
            continue;
        }

        // Extremely hacky CSV parser for this specific format
        // id,session_id,message
        const firstComma = line.indexOf(',');
        const secondComma = line.indexOf(',', firstComma + 1);

        if (firstComma === -1 || secondComma === -1) continue;

        const id = line.substring(0, firstComma);
        const session_id = line.substring(firstComma + 1, secondComma);
        let messageStr = line.substring(secondComma + 1);

        // Remove surrounding quotes and unescape double quotes if it's quoted
        if (messageStr.startsWith('"') && messageStr.endsWith('"')) {
            messageStr = messageStr.substring(1, messageStr.length - 1).replace(/""/g, '"');
        }

        try {
            const msg = JSON.parse(messageStr);
            if (!sessions[session_id]) {
                sessions[session_id] = [];
            }
            sessions[session_id].push({ id: parseInt(id), type: msg.type, content: msg.content });
        } catch (e) {
            // some lines might be multiline in the original CSV, this simple readline might break
            // but let's see how much we get.
        }
    }

    let output = '';
    let totalSessions = 0;

    for (const [sid, msgs] of Object.entries(sessions)) {
        msgs.sort((a, b) => a.id - b.id);
        output += `\n--- SESSION: ${sid} ---\n`;
        let userHasSpoken = false;
        let aiHasReplied = false;

        for (const m of msgs) {
            let contentClean = m.content.replace(/```json[\s\S]*?```/g, '[JSON INTENT]').trim();
            if (contentClean.includes('El usuario envió un mensaje con la siguiente información:')) {
                // skip internal processing messages if possible, or just clean them
                continue;
            }
            if (contentClean.includes('Mensaje del usuario:')) {
                contentClean = contentClean.replace('Mensaje del usuario:', '').trim();
            }

            if (contentClean.length > 0 && contentClean !== '[JSON INTENT]') {
                output += `${m.type.toUpperCase()}: ${contentClean}\n`;
            }
        }
        totalSessions++;
    }

    fs.writeFileSync('parsed_conversations.txt', output, 'utf8');
    console.log(`Parsed ${totalSessions} sessions successfully.`);
}

parseCSV();
