const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, downloadMediaMessage, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const express = require('express');
const axios = require('axios');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');

const app = express();
app.use(express.json({ limit: '50mb' }));

const ARIA_URL = process.env.ARIA_INTERNAL_URL || 'http://api:8000/internal/whatsapp/inbound';
const PORT = parseInt(process.env.BAILEYS_PORT || '3001');

let sock = null;
const contacts = {};

const store = { messages: {} };


async function startBaileys() {
    const sessionDir = path.join(__dirname, 'session');
    if (!fs.existsSync(sessionDir)) fs.mkdirSync(sessionDir, { recursive: true });

    const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
    const { version, isLatest } = await fetchLatestBaileysVersion();
    console.log(`Using WA v${version.join('.')}, isLatest: ${isLatest}`);

    sock = makeWASocket({
        version,
        auth: state,
        browser: ['ARIA', 'Chrome', '120.0'],
    });

    sock.ev.on('contacts.upsert', (newContacts) => {
        for (const contact of newContacts) {
            contacts[contact.id] = {
                id: contact.id,
                name: contact.name || contact.notify || contact.verifiedName || '',
                phone: contact.id.split('@')[0],
            };
        }
    });

    sock.ev.on('contacts.update', (updates) => {
        for (const update of updates) {
            if (contacts[update.id]) {
                if (update.name) contacts[update.id].name = update.name;
                if (update.verifiedName) contacts[update.id].name = update.verifiedName;
            }
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
        if (qr) {
            console.log('Scan this QR code to authenticate with WhatsApp:');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
            console.log(`Connection closed: ${reason}`);
            
            if (reason === 405 || reason === 401 || reason === DisconnectReason.loggedOut) {
                console.log('Session invalid (405/401) or logged out. Deleting session to force re-pairing.');
                fs.rmSync(sessionDir, { recursive: true, force: true });
                setTimeout(startBaileys, 3000);
            } else {
                console.log('Reconnecting...');
                setTimeout(startBaileys, 3000);
            }
        } else if (connection === 'open') {
            console.log('WhatsApp connection established!');
        }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;
        for (const msg of messages) {
            try {
                if (msg.key.fromMe) continue;
                if (!msg.message) continue;

                const jid = msg.key.remoteJid || '';
                if (jid === 'status@broadcast') continue;

                const pushName = msg.pushName || '';
                if (jid && pushName && !jid.endsWith('@g.us')) {
                    contacts[jid] = {
                        id: jid,
                        name: pushName,
                        phone: jid.split('@')[0],
                    };
                }
                const messageId = msg.key.id || '';
                let messageType = 'text';
                let text = '';
                let caption = '';
                let mediaUrl = '';

                if (msg.message.conversation) {
                    messageType = 'conversation';
                    text = msg.message.conversation;
                } else if (msg.message.extendedTextMessage) {
                    messageType = 'extendedText';
                    text = msg.message.extendedTextMessage.text || '';
                } else if (msg.message.imageMessage) {
                    messageType = 'image';
                    caption = msg.message.imageMessage.caption || '';
                    // Media handling would require download + upload to MinIO
                } else if (msg.message.audioMessage) {
                    messageType = 'audio';
                    // Audio handling
                } else if (msg.message.documentMessage) {
                    messageType = 'document';
                    caption = msg.message.documentMessage.caption || '';
                } else if (msg.message.videoMessage) {
                    messageType = 'video';
                    caption = msg.message.videoMessage.caption || '';
                }

                const payload = { jid, pushName, messageId, messageType, text: text || caption, caption, mediaUrl };
                console.log(`[MSG] ${pushName} (${jid}): ${(text || caption).substring(0, 80)}`);

                await axios.post(ARIA_URL, payload, { timeout: 10000 });
            } catch (err) {
                console.error('Error processing message:', err.message);
            }
        }
    });

    // REST API for sending
    app.post('/send', async (req, res) => {
        try {
            const { jid, text } = req.body;
            if (!jid || !text) return res.status(400).json({ error: 'jid and text required' });
            await sock.sendMessage(jid, { text });
            console.log(`[SENT] → ${jid}: ${text.substring(0, 80)}`);
            res.json({ ok: true });
        } catch (err) {
            console.error('Send error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    app.post('/send-media', async (req, res) => {
        try {
            const { jid, url, mimetype, caption } = req.body;
            if (!jid || !url) return res.status(400).json({ error: 'jid and url required' });
            const response = await axios.get(url, { responseType: 'arraybuffer', timeout: 30000 });
            const buffer = Buffer.from(response.data);
            if (mimetype && mimetype.startsWith('image/')) {
                await sock.sendMessage(jid, { image: buffer, caption: caption || '' });
            } else {
                await sock.sendMessage(jid, { document: buffer, mimetype: mimetype || 'application/octet-stream', caption: caption || '' });
            }
            res.json({ ok: true });
        } catch (err) {
            console.error('Send-media error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    app.get('/messages', (req, res) => {
        try {
            const jid = req.query.jid;
            const limit = parseInt(req.query.limit || '50');
            if (!jid) return res.status(400).json({ error: 'jid required' });
            
            const msgs = store.messages[jid]?.array || [];
            res.json({ ok: true, messages: msgs.slice(-limit) });
        } catch (err) {
            console.error('Fetch messages error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    app.get('/search', (req, res) => {
        try {
            const query = (req.query.q || '').toLowerCase();
            const limit = parseInt(req.query.limit || '20');
            if (!query) return res.status(400).json({ error: 'query required' });
            
            const results = [];
            for (const jid in store.messages) {
                const msgs = store.messages[jid]?.array || [];
                for (let i = msgs.length - 1; i >= 0; i--) {
                    const msg = msgs[i];
                    let text = '';
                    if (msg.message?.conversation) text = msg.message.conversation;
                    else if (msg.message?.extendedTextMessage) text = msg.message.extendedTextMessage.text;
                    else if (msg.message?.imageMessage) text = msg.message.imageMessage.caption;
                    
                    if (text && text.toLowerCase().includes(query)) {
                        results.push({
                            jid,
                            pushName: msg.pushName || jid,
                            text,
                            timestamp: msg.messageTimestamp,
                            messageId: msg.key.id
                        });
                        if (results.length >= limit) break;
                    }
                }
                if (results.length >= limit) break;
            }
            res.json({ ok: true, results });
        } catch (err) {
            console.error('Search error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    app.get('/contacts', async (req, res) => {
        try {
            if (!sock) return res.status(500).json({ error: 'Socket not initialized' });
            const list = Object.values(contacts).map(c => ({
                jid: c.id,
                name: c.name || c.id.split('@')[0],
                phone: c.id.split('@')[0],
                isGroup: false
            }));
            
            try {
                const groups = await sock.groupFetchAllParticipating();
                for (const g of Object.values(groups)) {
                    list.push({
                        jid: g.id,
                        name: g.subject,
                        phone: '',
                        isGroup: true
                    });
                }
            } catch (groupErr) {
                console.error('Failed to fetch groups:', groupErr.message);
            }
            
            res.json({ ok: true, contacts: list });
        } catch (err) {
            console.error('Fetch contacts error:', err.message);
            res.status(500).json({ error: err.message });
        }
    });

    app.get('/health', (req, res) => {
        res.json({ status: 'ok', connected: sock?.user ? true : false });
    });
}

startBaileys().catch(console.error);
app.listen(PORT, () => console.log(`Baileys API running on :${PORT}`));
