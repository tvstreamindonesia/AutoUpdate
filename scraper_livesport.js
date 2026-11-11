/**
 * LiveSports808 M3U8 Stream Scraper
 * Uses Chrome DevTools Protocol (CDP) / Puppeteer to intercept dynamic HLS manifests
 * and extract valid Referer & User-Agent tokens for IPTV players (TiviMate, OTT Navigator, VLC).
 *
 * Supported Categories:
 * 1. Sepak Bola (Football)
 * 2. Badminton / Bulu Tangkis (BWF tournaments, etc.)
 */

const fs = require('fs');
const path = require('path');

// Default target domains with fallback mirrors
const SEED_DOMAINS = [
    'https://idn298.livesports808.li',
    'https://livesports808.li',
    'https://www.livesports808.com',
    'https://808ball.com'
];

const DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36';
const DEFAULT_LOGO = 'https://lookaside.fbsbx.com/lookaside/crawler/media/?media_id=100067608762978';
const OUTPUT_FILE = path.join(__dirname, 'livesports.m3u');

async function getActiveDomain(browser) {
    const page = await browser.newPage();
    await page.setUserAgent(DEFAULT_USER_AGENT);

    for (const domain of SEED_DOMAINS) {
        try {
            console.log(`[INFO] Menguji domain: ${domain}...`);
            const res = await page.goto(domain, { waitUntil: 'domcontentloaded', timeout: 12000 });
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

async function scrapeCategoryMatches(page, baseUrl, category) {
    const targetUrl = `${baseUrl}${category.path}`;
    console.log(`[INFO] Mengakses jadwal kategori ${category.name}: ${targetUrl}`);

    try {
        await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 25000 });
    } catch (e) {
        console.log(`[WARN] Halaman ${targetUrl} lambat dimuat, melanjutkan dengan DOM saat ini...`);
    }

    // Ekstraksi kartu pertandingan dari halaman
    const matches = await page.evaluate((catName, defaultLogo) => {
        const results = [];
        const seen = new Set();

        // Selector fleksibel untuk variasi layout Score808/LiveSports808
        const elements = document.querySelectorAll(
            '.match-item, .schedule-item, .match-list-item, a[href*="/live/"], a[href*="/detail/"], a[href*="/match/"]'
        );

        elements.forEach(el => {
            const anchor = el.tagName === 'A' ? el : el.querySelector('a[href*="/live/"], a[href*="/detail/"], a[href*="/match/"]');
            if (!anchor) return;

            const href = anchor.getAttribute('href');
            if (!href || seen.has(href)) return;
            seen.add(href);

            // Nama tim / atlet
            let title = '';
            const homeEl = el.querySelector('.home-team, .home, .team-a, .team1');
            const awayEl = el.querySelector('.away-team, .away, .team-b, .team2');
            if (homeEl && awayEl) {
                title = `${homeEl.innerText.trim()} vs ${awayEl.innerText.trim()}`;
            } else {
                const titleEl = el.querySelector('.title, .match-title, .teams, .event-title');
                title = titleEl ? titleEl.innerText.trim() : anchor.innerText.trim();
            }

            title = title.replace(/\n+/g, ' ').replace(/\s+/g, ' ').trim();
            if (!title || title.length < 3) return;

            // Filter khusus Badminton jika di kategori others
            if (catName === 'Badminton') {
                const textLower = (el.innerText + ' ' + href).toLowerCase();
                const isBadminton = /badminton|bwf|bulu\s*tangkis|thomas|uber|all\s*england|indonesia\s*open|masters|open\s*20\d\d/.test(textLower);
                // Jika halaman khusus badminton, ambil semua; jika under 'others', filter kata kunci
                if (!isBadminton && !href.includes('badminton')) {
                    return;
                }
            }

            // Waktu pertandingan
            const timeEl = el.querySelector('.time, .match-time, .status, .state');
            const timeStr = timeEl ? timeEl.innerText.trim().replace(/\n+/g, ' ') : '';

            // Logo
            const imgEl = el.querySelector('img');
            const logo = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || defaultLogo) : defaultLogo;

            results.push({
                title,
                timeStr,
                href,
                logo
            });
        });

        return results;
    }, category.name, DEFAULT_LOGO);

    return matches;
}

async function extractStreamWithCDP(browser, matchUrl) {
    const page = await browser.newPage();
    await page.setUserAgent(DEFAULT_USER_AGENT);

    let streamResult = null;

    // Aktifkan intercept request Chrome DevTools
    await page.setRequestInterception(true);

    page.on('request', req => {
        const url = req.url();
        const headers = req.headers();

        // Tangkap manifest stream (.m3u8)
        if ((url.includes('.m3u8') || url.includes('/live/') && url.includes('.ts')) && !streamResult) {
            streamResult = {
                streamUrl: url,
                referer: headers['referer'] || headers['Referer'] || matchUrl,
                userAgent: headers['user-agent'] || headers['User-Agent'] || DEFAULT_USER_AGENT
            };
        }
        req.continue();
    });

    try {
        await page.goto(matchUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });

        // Periksa juga apakah ada iframe player seperti playaindg12.xyz
        const iframeSrc = await page.evaluate(() => {
            const iframe = document.querySelector('iframe[src*="live.html"], iframe[src*="play"], iframe[src*="stream"]');
            return iframe ? iframe.src : null;
        });

        // Tunggu maksimal 7 detik untuk stream manifest
        const maxWait = 7;
        for (let i = 0; i < maxWait; i++) {
            if (streamResult) break;
            await new Promise(r => setTimeout(r, 1000));
        }

        if (streamResult && iframeSrc && (!streamResult.referer || streamResult.referer === matchUrl)) {
            streamResult.referer = iframeSrc;
        }
    } catch (e) {
        // Halaman mungkin lambat atau pop-up, abaikan jika stream sudah tertangkap
    } finally {
        await page.close().catch(() => {});
    }

    return streamResult;
}

async function main() {
    console.log('============================================================');
    console.log('Memulai LiveSports808 Stream Scraper (Chrome DevTools)...');
    console.log('============================================================');

    let puppeteer;
    try {
        puppeteer = require('puppeteer');
    } catch (e) {
        console.error('[FATAL] Modul "puppeteer" belum terinstall. Jalankan: npm install puppeteer');
        process.exit(1);
    }

    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1280,800'
        ]
    });

    const activeBase = await getActiveDomain(browser);

    const categories = [
        { name: 'Sepak Bola', path: '/football', group: 'LIVE EVENT' },
        { name: 'Badminton', path: '/others', group: 'BADMINTON LIVE' }
    ];

    const playlistLines = [
        '#EXTM3U x-tvg-url="" url-tvg="" tvg-shift="0"',
        ''
    ];

    let totalStreamsFound = 0;

    for (const cat of categories) {
        const catPage = await browser.newPage();
        await catPage.setUserAgent(DEFAULT_USER_AGENT);

        const matches = await scrapeCategoryMatches(catPage, activeBase, cat);
        await catPage.close();

        console.log(`[INFO] Kategori ${cat.name}: Ditemukan ${matches.length} pertandingan kandidat.`);

        // Batasi pengecekan per kategori untuk menjaga performa (maksimal 8 pertandingan aktif)
        const activeCandidates = matches.slice(0, 8);

        for (let i = 0; i < activeCandidates.length; i++) {
            const m = activeCandidates[i];
            const fullUrl = m.href.startsWith('http') ? m.href : `${activeBase}${m.href}`;
            console.log(`[${i + 1}/${activeCandidates.length}] Memeriksa stream: [${cat.name}] ${m.title}...`);

            const stream = await extractStreamWithCDP(browser, fullUrl);
            if (stream && stream.streamUrl) {
                console.log(`   -> BERHASIL: .m3u8 ditemukan!`);
                totalStreamsFound++;

                const displayTitle = m.timeStr ? `[${m.timeStr}] ${m.title}` : m.title;
                const matchId = `ls808_${Buffer.from(m.title).toString('hex').slice(0, 10)}`;

                playlistLines.push(
                    `#EXTINF:-1 tvg-id="${matchId}" tvg-name="${m.title}" tvg-logo="${m.logo}" group-title="${cat.group}",${displayTitle}`,
                    `#EXTVLCOPT:http-referrer=${stream.referer}`,
                    `#EXTVLCOPT:http-user-agent=${stream.userAgent}`,
                    stream.streamUrl,
                    ''
                );
            } else {
                console.log(`   -> Belum ada sinyal siaran langsung (Upcoming / Offline).`);
            }
        }
    }

    await browser.close();

    // Tulis ke file livesports.m3u jika ada siaran yang ditemukan
    if (totalStreamsFound > 0) {
        fs.writeFileSync(OUTPUT_FILE, playlistLines.join('\n'), 'utf-8');
        console.log(`[SUKSES] Berhasil menyimpan ${totalStreamsFound} siaran ke ${OUTPUT_FILE}`);
    } else {
        console.log('[INFO] Belum ada stream aktif dari LiveSports808 saat ini.');
    }

    console.log('============================================================');
    console.log(`Selesai! Total siaran LiveSports808 aktif: ${totalStreamsFound}`);
    console.log('============================================================');
}

main().catch(err => {
    console.error('[ERROR]', err);
    process.exit(0); // exit 0 agar GitHub Actions tidak gagal jika situs eksternal sedang down
});
