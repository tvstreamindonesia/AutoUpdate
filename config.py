"""
Configuration Module for Automated Xoilac M3U8 Playlist Generator.
Defines data sources, competition whitelist rules, headers, and output parameters.
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output playlist file name and path
OUTPUT_FILE = os.path.join(BASE_DIR, "xoilac.m3u")

# Timezone setting for kick-off display (UTC+7 / WIB)
TIMEZONE_NAME = "Asia/Jakarta"
TIMEZONE_OFFSET_HOURS = 7

# Request headers to mimic standard browser
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Data source URLs with Dynamic Seed Domain Resolution and Mirror Fallbacks
# When Xoilac/Vebo rotates domains, the seed URLs automatically redirect to the new active domain.
DATA_SOURCES = [
    {
        "name": "Vebo/Xoilac Live Seed",
        "seed_url": "https://vebo.live",
        "fallback_url": "https://vebozbr.cc",
        "home_path": "/",
        "hot_path": "/sport/football/filter/hot",
        "live_path": "/sport/football/filter/live",
        "load_more_path": "/sport/football/load-more/home/page/{page}/per/50",
        "max_pages": 4
    },
    {
        "name": "Vebo TV Network Mirror",
        "seed_url": "https://vebotv.net",
        "fallback_url": "https://www.vebotv.net",
        "home_path": "/",
        "hot_path": "/sport/football/filter/hot",
        "live_path": "/sport/football/filter/live",
        "load_more_path": "/sport/football/load-more/home/page/{page}/per/50",
        "max_pages": 3
    },
    {
        "name": "Xoilac Fun/Club Seed",
        "seed_url": "https://xoilac66.fun",
        "fallback_url": "https://xoilac66.club",
        "home_path": "/",
        "hot_path": "/sport/football/filter/hot",
        "live_path": "/sport/football/filter/live",
        "load_more_path": "/sport/football/load-more/home/page/{page}/per/50",
        "max_pages": 3
    }
]

# Fallback stream when an upcoming match does not yet have an active live stream
DEFAULT_STANDBY_STREAM = "https://live2.jorvakstreamcache.com/live/channel16.m3u8"

# Maximum time (seconds) to verify stream connectivity
STREAM_CHECK_TIMEOUT = 3.0

# Playlist generation options
CHECK_STREAM_ONLINE = True       # Test whether stream responds before adding
INCLUDE_UPCOMING_MATCHES = True  # Include upcoming whitelisted matches
UPCOMING_DAYS_AHEAD = 1          # Window for upcoming matches: 1 = Hari ini & Besok (misal tgl 16 & 17)
USE_COMPETITION_LOGO = True      # Gunakan Logo Kompetisi/Liga (bukan logo klub) untuk tvg-logo
# Custom manual channels (digabung otomatis ke xoilac.m3u tanpa terhapus saat auto-update)
CUSTOM_CHANNELS_FILE = "custom_channels.m3u"
CUSTOM_CHANNELS_POSITION = "top"  # Pilihan: "top" (di atas jadwal bola) atau "bottom" (di bawah)

# Group title / Kategori untuk semua pertandingan Xoilac di IPTV player
# Nilai "LIVE EVENT" membuat semua pertandingan terkumpul rapi di 1 grup/kategori "LIVE EVENT"
XOILAC_GROUP_TITLE = "LIVE EVENT"

SPLIT_SERVERS_INTO_ITEMS = False # If True, creates separate items for Server 1, Server 2
UPDATE_INTERVAL_SECONDS = 300   # 5 minutes for daemon / watch mode
LOCAL_SERVER_PORT = 8080         # Port for built-in HTTP server

# ==============================================================================
# WHITELIST COMPETITIONS CONFIGURATION
# ==============================================================================
# Categories strictly aligned with user requirements:
# 1. Top European Leagues (Premier League, La Liga, Serie A Italia, Bundesliga, Ligue 1, Eredivisie, Primeira Liga Portugal)
# 2. Kompetisi Eropa (UEFA Champions League, UEFA Europa League, UEFA Conference League, UEFA Super Cup)
# 3. Liga Indonesia (Liga 1 / Super League Indonesia, Liga 2 Indonesia, Piala Presiden, Piala Indonesia)
# 4. MLS (Major League Soccer, MLS Cup Playoffs, MLS Cup, Leagues Cup)
# 5. Kompetisi Asia (AFC Champions League Elite, AFC Champions League Two, AFC Challenge League, AFC Asian Cup, Kualifikasi Piala Asia, AFC U23 Asian Cup, Kompetisi resmi utama AFC lainnya)
# 6. Timnas Indonesia (Senior putra, U-23, U-20, U-17, putri, kelompok umur putri)
# 7. Turnamen Bergengsi (FIFA World Cup, Kualifikasi Piala Dunia, EURO, Copa América, Africa Cup of Nations, CONCACAF Gold Cup, FIFA Club World Cup, FIFA Intercontinental Cup, Olimpiade sepak bola)
# ==============================================================================

COMPETITION_WHITELIST = [
    # ---------------- 1. Top European Leagues ----------------
    {
        "category": "Top European Leagues",
        "competition": "Premier League",
        "pattern": r"(?i)\b(premier\s*league|ngoại\s*hạng\s*anh|epl|english\s*premier\s*league)\b",
        "exclude": r"(?i)(bahrain|mizoram|israel|kuwait|egypt|russia|youth|u\d+|women|nữ|futsal|masters|esports|dota|gaming)"
    },
    {
        "category": "Top European Leagues",
        "competition": "La Liga",
        "pattern": r"(?i)\b(la\s*liga|laliga|vđqg\s*tây\s*ban\s*nha|primera\s*divisi[oó]n)\b",
        "exclude": r"(?i)(la\s*liga\s*2|segunda|women|nữ|u\d+|futsal)"
    },
    {
        "category": "Top European Leagues",
        "competition": "Serie A Italia",
        "pattern": r"(?i)\b(serie\s*a|vđqg\s*ý|vđqg\s*italia|italian\s*serie\s*a)\b",
        "exclude": r"(?i)(serie\s*a2|serie\s*b|serie\s*c|women|nữ|u\d+|brazil|ecuador|futsal)"
    },
    {
        "category": "Top European Leagues",
        "competition": "Bundesliga",
        "pattern": r"(?i)\b(bundesliga|vđqg\s*đức|german\s*bundesliga)\b",
        "exclude": r"(?i)(bundesliga\s*2|2\.\s*bundesliga|3\.\s*liga|frauen|women|nữ|u\d+|austria|áo|futsal)"
    },
    {
        "category": "Top European Leagues",
        "competition": "Ligue 1",
        "pattern": r"(?i)\b(ligue\s*1|vđqg\s*pháp|french\s*ligue\s*1)\b",
        "exclude": r"(?i)(ligue\s*2|women|nữ|u\d+|futsal)"
    },
    {
        "category": "Top European Leagues",
        "competition": "Eredivisie",
        "pattern": r"(?i)\b(eredivisie|vđqg\s*hà\s*lan|dutch\s*eredivisie)\b",
        "exclude": r"(?i)(eerste|women|nữ|u\d+|futsal)"
    },
    {
        "category": "Top European Leagues",
        "competition": "Primeira Liga Portugal",
        "pattern": r"(?i)\b(primeira\s*liga|liga\s*portugal|vđqg\s*bồ\s*đào\s*nha)\b",
        "exclude": r"(?i)(liga\s*2|segunda|women|nữ|u\d+|futsal)"
    },

    # ---------------- 2. Kompetisi Eropa ----------------
    {
        "category": "Kompetisi Eropa",
        "competition": "UEFA Champions League",
        "pattern": r"(?i)\b(uefa\s*champions\s*league|champions\s*league|cúp\s*c1\b|ucl\b)",
        "exclude": r"(?i)(caf|afc|ofc|concacaf|women|nữ|youth|u\d+|futsal)"
    },
    {
        "category": "Kompetisi Eropa",
        "competition": "UEFA Europa League",
        "pattern": r"(?i)\b(uefa\s*europa\s*league|europa\s*league|cúp\s*c2\b|uel\b)",
        "exclude": r"(?i)(caf|afc|women|nữ|youth|u\d+|futsal)"
    },
    {
        "category": "Kompetisi Eropa",
        "competition": "UEFA Conference League",
        "pattern": r"(?i)\b(uefa\s*conference\s*league|conference\s*league|cúp\s*c3\b|uecl\b)",
        "exclude": r"(?i)(caf|afc|women|nữ|youth|u\d+|futsal)"
    },
    {
        "category": "Kompetisi Eropa",
        "competition": "UEFA Super Cup",
        "pattern": r"(?i)\b(uefa\s*super\s*cup|siêu\s*cúp\s*châu\s*âu)\b",
        "exclude": None
    },

    # ---------------- 3. Liga Indonesia ----------------
    {
        "category": "Liga Indonesia",
        "competition": "Liga 1 Indonesia",
        "pattern": r"(?i)\b(bri\s*liga\s*1|super\s*league\s*indonesia|vđqg\s*indonesia|liga\s*1\s*indonesia|\bliga\s*1\b)\b",
        "exclude": r"(?i)(thái|thai|pháp|nga|ba\s*lan|peru|hàn|korea|la\s*liga)"
    },
    {
        "category": "Liga Indonesia",
        "competition": "Liga 2 Indonesia",
        "pattern": r"(?i)\b(pegadaian\s*liga\s*2|hạng\s*2\s*indonesia|liga\s*2\s*indonesia|\bliga\s*2\b)\b",
        "exclude": r"(?i)(la\s*liga|spanyol|spain|bồ\s*đào\s*nha|israel|nhật|japan)"
    },
    {
        "category": "Liga Indonesia",
        "competition": "Piala Presiden",
        "pattern": r"(?i)\b(piala\s*presiden|presiden\s*cup)\b",
        "exclude": None
    },
    {
        "category": "Liga Indonesia",
        "competition": "Piala Indonesia",
        "pattern": r"(?i)\b(piala\s*indonesia|indonesia\s*cup)\b",
        "exclude": None
    },

    # ---------------- 4. MLS ----------------
    {
        "category": "MLS",
        "competition": "Major League Soccer",
        "pattern": r"(?i)\b(mls\s*cup\s*playoffs|mls\s*cup|leagues\s*cup|major\s*league\s*soccer|nhà\s*nghề\s*mỹ|\bmls\b)",
        "exclude": r"(?i)(next\s*pro|u\d+)"
    },

    # ---------------- 5. Kompetisi Asia ----------------
    {
        "category": "Kompetisi Asia",
        "competition": "AFC Champions League Elite",
        "pattern": r"(?i)\b(afc\s*champions\s*league\s*elite|acl\s*elite|cúp\s*c1\s*châu\s*á\s*elite)\b",
        "exclude": None
    },
    {
        "category": "Kompetisi Asia",
        "competition": "AFC Champions League Two",
        "pattern": r"(?i)\b(afc\s*champions\s*league\s*two|acl\s*two|cúp\s*c2\s*châu\s*á)\b",
        "exclude": None
    },
    {
        "category": "Kompetisi Asia",
        "competition": "AFC Challenge League",
        "pattern": r"(?i)\b(afc\s*challenge\s*league|acgl)\b",
        "exclude": None
    },
    {
        "category": "Kompetisi Asia",
        "competition": "AFC Asian Cup",
        "pattern": r"(?i)\b(afc\s*asian\s*cup|asian\s*cup|cúp\s*châu\s*á|piala\s*asia)\b",
        "exclude": r"(?i)(kualifikasi|qualification|vòng\s*loại|u23|u20|u17)"
    },
    {
        "category": "Kompetisi Asia",
        "competition": "Kualifikasi Piala Asia",
        "pattern": r"(?i)\b(kualifikasi\s*piala\s*asia|asian\s*cup\s*qualif|vòng\s*loại\s*asian\s*cup)\b",
        "exclude": None
    },
    {
        "category": "Kompetisi Asia",
        "competition": "AFC U23 Asian Cup",
        "pattern": r"(?i)\b(afc\s*u23|afc\s*u-23|u23\s*asian\s*cup)\b",
        "exclude": None
    },
    {
        "category": "Kompetisi Asia",
        "competition": "Kompetisi Resmi AFC",
        "pattern": r"(?i)\b(afc\s*champions\s*league|cúp\s*c1\s*châu\s*á|afc\s*cup|afc\s*u20|afc\s*u17)\b",
        "exclude": None
    },

    # ---------------- 6. Turnamen Bergengsi ----------------
    {
        "category": "Turnamen Bergengsi",
        "competition": "Piala Dunia U-17",
        "pattern": r"(?i)\b(fifa\s*u-?17\s*world\s*cup|u-?17\s*world\s*cup|world\s*cup\s*u-?17|piala\s*dunia\s*u-?17|piala\s*dunia\s*u17|u-?17\s*thế\s*giới|u17\s*world\s*cup)\b",
        "exclude": r"(?i)(women|nữ|futsal|club)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Kualifikasi Piala Dunia U-17",
        "pattern": r"(?i)\b(kualifikasi\s*piala\s*dunia\s*u-?17|vòng\s*loại\s*(?:u-?17\s*world\s*cup|u-?17\s*thế\s*giới)|u-?17\s*world\s*cup\s*qualif)\b",
        "exclude": r"(?i)(women|nữ|futsal)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Piala Dunia U-20",
        "pattern": r"(?i)\b(fifa\s*u-?20\s*world\s*cup|u-?20\s*world\s*cup|world\s*cup\s*u-?20|piala\s*dunia\s*u-?20|piala\s*dunia\s*u20|u-?20\s*thế\s*giới|u20\s*world\s*cup)\b",
        "exclude": r"(?i)(women|nữ|futsal|club)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "FIFA World Cup",
        "pattern": r"(?i)\b(fifa\s*world\s*cup|world\s*cup|piala\s*dunia)\b",
        "exclude": r"(?i)(kualifikasi|qualification|vòng\s*loại|u20|u17|club)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Kualifikasi Piala Dunia",
        "pattern": r"(?i)\b(kualifikasi\s*piala\s*dunia|world\s*cup\s*qualif|vòng\s*loại\s*world\s*cup|wc\s*qualif)\b",
        "exclude": None
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "EURO",
        "pattern": r"(?i)\b(uefa\s*euro|euro\s*20\d\d|\beuro\b|european\s*championship)\b",
        "exclude": r"(?i)(u\d+|women|nữ)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Copa América",
        "pattern": r"(?i)\b(copa\s*am[eé]rica)\b",
        "exclude": None
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Africa Cup of Nations",
        "pattern": r"(?i)\b(africa\s*cup\s*of\s*nations|afcon|\bcan\b)\b",
        "exclude": r"(?i)(u\d+|women|nữ)"
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "CONCACAF Gold Cup",
        "pattern": r"(?i)\b(concacaf\s*gold\s*cup|gold\s*cup)\b",
        "exclude": None
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "FIFA Club World Cup",
        "pattern": r"(?i)\b(fifa\s*club\s*world\s*cup|club\s*world\s*cup|fifa\s*cwc)\b",
        "exclude": None
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "FIFA Intercontinental Cup",
        "pattern": r"(?i)\b(fifa\s*intercontinental\s*cup|intercontinental\s*cup)\b",
        "exclude": None
    },
    {
        "category": "Turnamen Bergengsi",
        "competition": "Olimpiade Sepak Bola",
        "pattern": r"(?i)\b(olimpiade\s*sepak\s*bola|olympic\s*games\s*football|olympic\s*football|\bolympic\b)\b",
        "exclude": None
    }
]
