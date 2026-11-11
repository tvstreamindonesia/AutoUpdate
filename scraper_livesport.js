/**
 * LiveSports808 M3U8 Stream Scraper
 * Uses Chrome DevTools Protocol (CDP) / Puppeteer to intercept dynamic HLS manifests
 * and extract valid Referer & User-Agent tokens for IPTV players (TiviMate, OTT Navigator, VLC).
 *
 * Supported Categories:
 * 1. Sepak Bola (Football) -> Group: LIVE EVENT
 * 2. Badminton / Bulu Tangkis (BWF Kumamoto Masters, etc.) -> Group: BADMINTON LIVE
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const SEED_DOMAINS = [
    'https://idn298.livesports808.li',
    'https://livesports808.li',
    'https://www.livesports808.com',
    'https://808ball.com'
];

const DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36';
const DEFAULT_LOGO = 'https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=100067608762978';
const OUTPUT_FILE = path.join(__dirname, 'livesports.m3u');

async function getActiveDomain(browser) {
    const page = await browser.newPage();
    await page.setUserAgent(DEFAULT_USER_AGENT);

    for (const domain of SEED_DOMAINS) {
        try {
            console.log(`[INFO] Menguji domain: ${domain}...`);
            const res = await page.goto(domain, { waitUntil: 'domcontentloaded', timeout: 15000 });
            if (res && res.status() < 400) {
                const finalUrl = page.url();
                const u = new URL(finalUrl);
                const activeBase = `${u.protocol}//${u.host}`;
                console.log(`[INFO] Domain aktif terdeteksi: ${activeBase}`);
                await page.close();
                return activeBase;
            }
        } catch (e) {
            console.log(`[WARN] Domain ${domain} tidak dapat dijangkau: ${e.message}`);
        }
    }
    await page.close();
    return SEED_DOMAINS[0];
}

async function scrapeLiveMatchesFromHomepage(page, baseUrl) {
    console.log(`[INFO] Mengakses halaman utama: ${baseUrl}...`);
    try {
        await page.goto(baseUrl, { waitUntil: 'networkidle2', timeout: 35000 });
    } catch (e) {
        console.log(`[WARN] Goto networkidle2 timeout, tetap melanjutkan...`);
    }

    await new Promise(r => setTimeout(r, 3000));

    const matches = await page.evaluate((defaultLogo) => {
        const results = [];
        const seen = new Set();
        const items = document.querySelectorAll('a.match-item, a[href*="/others/"], a[href*="/football/"]');

        items.forEach(el => {
            const text = (el.innerText || '').trim();
            const href = el.getAttribute('href');
            if (!href || seen.has(href)) return;

            const isLive = text.includes('Live') || el.classList.contains('live');
            if (!isLive) return; // Hanya ambil pertandingan yang benar-benar SEDANG LIVE

            seen.add(href);

            const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
            let tournament = '';
            let matchTitle = '';

            if (lines.length >= 2) {
                tournament = lines[0];
                const cleanLines = lines.filter(l => !l.toLowerCase().includes('live') && l !== tournament);
                matchTitle = cleanLines.join(' - ');
            } else {
                matchTitle = text.replace(/\n+/g, ' ');
            }

            matchTitle = matchTitle.replace(/\s+/g, ' ').trim();
            if (!matchTitle) matchTitle = tournament || 'Live Sports Match';

            const hrefLower = href.toLowerCase();
            const textLower = text.toLowerCase();

            let sport = 'Sepak Bola';
            let groupTitle = 'LIVE EVENT';
            let category = 'football';

            if (hrefLower.includes('/others/') || textLower.includes('masters') || textLower.includes('badminton') || textLower.includes('court') || textLower.includes('bwf') || textLower.includes('bulu')) {
                sport = 'Badminton';
                groupTitle = 'BADMINTON LIVE';
                category = 'others';
            }

            // Ekstrak ID numerik pertandingan jika ada di URL (contoh: /others/8994-round...)
            const idMatch = href.match(/\/(\d+)-/);
            const matchId = idMatch ? idMatch[1] : null;

            // Ekstrak gambar logo jika ada
            const imgEl = el.querySelector('img');
            const logo = imgEl ? (imgEl.src || defaultLogo) : defaultLogo;

            results.push({
                matchId,
                href,
                tournament,
                matchTitle,
                fullTitle: tournament ? `[${tournament}] ${matchTitle}` : matchTitle,
                sport,
                groupTitle,
                category,
                logo
            });
        });

        return results;
    }, DEFAULT_LOGO);

    return matches;
}

async function extractStreamForMatch(browser, match) {
    const page = await browser.newPage();
    await page.setUserAgent(DEFAULT_USER_AGENT);

    let iframeUrl = '';
    if (match.matchId) {
        const b64 = Buffer.from(`matchId=${match.matchId}&mtText=${match.category}&siteKey=8tigoals&skptNum=3rd`).toString('base64');
        iframeUrl = `https://ppdd20.playaindg12.xyz/live.html?_pa=${encodeURIComponent(b64)}&_pb=4`;
    }

    const targetUrl = iframeUrl || (match.href.startsWith('http') ? match.href : `https://idn298.livesports808.li${match.href}`);
    console.log(`   [PLAYER] Target URL: ${targetUrl}`);

    await page.setExtraHTTPHeaders({
        'Referer': match.href.startsWith('http') ? match.href : 'https://www.tigoals245.com/'
    });

    let streamUrl = null;

    page.on('request', req => {
        const u = req.url();
        if ((u.includes('.m3u8') || u.includes('/app/c')) && !streamUrl) {
            console.log(`   -> CAPTURED STREAM: ${u.slice(0, 80)}...`);
            streamUrl = u;
        }
    });

    page.on('response', res => {
        const u = res.url();
        if ((u.includes('.m3u8') || u.includes('/app/c')) && !streamUrl) {
            console.log(`   -> CAPTURED STREAM (RESP): ${u.slice(0, 80)}...`);
            streamUrl = u;
        }
    });

    try {
        await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 25000 }).catch(e => {
            console.log(`   [WARN] Goto timeout / wait: ${e.message}`);
        });

        // Trigger player click & video play
        try {
            await page.click('button, .vjs-big-play-button, .play-button, video, #player, .dplayer-video-wrap');
            await page.evaluate(() => {
                const v = document.querySelector('video');
                if (v) v.play().catch(() => {});
            });
        } catch (e) {}

        for (let i = 0; i < 8; i++) {
            if (streamUrl) break;
            if (i === 4) {
                try {
                    await page.click('button, .vjs-big-play-button, .play-button, video, #player, .dplayer-video-wrap');
                    await page.evaluate(() => {
                        const v = document.querySelector('video');
                        if (v) v.play().catch(() => {});
                    });
                } catch (e) {}
            }
            await new Promise(r => setTimeout(r, 1000));
        }
    } catch (e) {
        console.log(`   [WARN] Error extracting stream: ${e.message}`);
    } finally {
        await page.close().catch(() => {});
    }

    return {
        streamUrl,
        referer: iframeUrl || targetUrl,
        userAgent: DEFAULT_USER_AGENT
    };
}

async function main() {
    console.log('============================================================');
    console.log('Memulai LiveSports808 Stream Scraper (Chrome DevTools)...');
    console.log('============================================================');

    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--autoplay-policy=no-user-gesture-required',
            '--window-size=1280,800'
        ]
    });

    const activeBase = await getActiveDomain(browser);

    const homePage = await browser.newPage();
    await homePage.setUserAgent(DEFAULT_USER_AGENT);

    const liveMatches = await scrapeLiveMatchesFromHomepage(homePage, activeBase);
    await homePage.close().catch(() => {});

    console.log(`[INFO] Ditemukan ${liveMatches.length} pertandingan berstatus LIVE:`);
    liveMatches.forEach((m, idx) => {
        console.log(`  ${idx + 1}. [${m.sport}] ${m.fullTitle} (ID: ${m.matchId || 'N/A'})`);
    });

    const playlistEntries = [];

    for (let i = 0; i < liveMatches.length; i++) {
        const m = liveMatches[i];
        console.log(`\n[${i + 1}/${liveMatches.length}] Memproses siaran: ${m.fullTitle}...`);

        let result = await extractStreamForMatch(browser, m);

        // Jika percobaan pertama belum tertangkap, beri kesempatan retry sekali lagi
        if (!result || !result.streamUrl) {
            console.log(`   [RETRY] Mencoba kembali untuk ${m.fullTitle}...`);
            result = await extractStreamForMatch(browser, m);
        }

        if (result && result.streamUrl) {
            console.log(`   -> BERHASIL!`);
            const cleanTitle = m.fullTitle.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
            const id = 'ls808_' + (m.matchId || Buffer.from(cleanTitle).toString('hex').slice(0, 8));

            playlistEntries.push(
                `#EXTINF:-1 tvg-id="${id}" tvg-name="${cleanTitle}" tvg-logo="${m.logo}" group-title="${m.groupTitle}",(LIVE) ${cleanTitle}`,
                `#EXTVLCOPT:http-referrer=${result.referer}`,
                `#EXTVLCOPT:http-user-agent=${result.userAgent}`,
                result.streamUrl,
                ''
            );
        } else {
            console.log(`   -> Gagal menangkap stream manifest.`);
        }
    }

    await browser.close().catch(() => {});

    const fullContentLines = [
        '#EXTM3U x-tvg-url="" url-tvg="" tvg-shift="0"',
        '',
        '########################################################',
        '## LIVESPORTS808 STREAM PLAYLIST (SEPAK BOLA & BADMINTON)',
        '########################################################',
        ''
    ];

    if (playlistEntries.length > 0) {
        fullContentLines.push(...playlistEntries);
    } else {
        // Fallback saluran siaga jika belum ada pertandingan live
        fullContentLines.push(
            `#EXTINF:-1 tvg-id="livesport_standby" tvg-name="Live Sport 808 Info" tvg-logo="${DEFAULT_LOGO}" group-title="LIVE EVENT",Live Sports 808 Standby (Belum Ada Siaran Aktif)`,
            `#EXTVLCOPT:http-referrer=https://ppdd20.playaindg12.xyz/live.html?_pa=bWF0Y2hJZD04OTkxJm10VGV4dD1vdGhlcnMmc2l0ZUtleT04dGlnb2FscyZza3B0TnVtPTNyZA%3D%3D&_pb=4`,
            `#EXTVLCOPT:http-user-agent=${DEFAULT_USER_AGENT}`,
            'https://live2.jorvakstreamcache.com/live/channel16.m3u8',
            ''
        );
    }

    fs.writeFileSync(OUTPUT_FILE, fullContentLines.join('\n'), 'utf-8');
    console.log(`\n[SUKSES] Berhasil menyimpan ${playlistEntries.length / 5} siaran aktif ke ${OUTPUT_FILE}`);
    console.log('============================================================');
}

main().catch(err => {
    console.error('[ERROR]', err);
    process.exit(0);
});
