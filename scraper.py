"""
Scraper Module for Xoilac/Vebo Football Matches and Streams.
Fetches match schedules, applies competition whitelist filtering,
and resolves HLS (.m3u8) / FLV live stream manifests.
"""

import re
import json
import datetime
import logging
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import pytz

from config import (
    DATA_SOURCES,
    DEFAULT_HEADERS,
    COMPETITION_WHITELIST,
    DEFAULT_STANDBY_STREAM,
    CHECK_STREAM_ONLINE,
    STREAM_CHECK_TIMEOUT,
    TIMEZONE_NAME,
    TIMEZONE_OFFSET_HOURS,
    UPCOMING_DAYS_AHEAD
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class MatchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        try:
            self.tz = pytz.timezone(TIMEZONE_NAME)
        except Exception:
            self.tz = datetime.timezone(datetime.timedelta(hours=TIMEZONE_OFFSET_HOURS))

    def filter_competition(self, league_name: str, home_team: str, away_team: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Filters matches against the user-defined whitelist.
        Returns:
            (category, competition_display_name) or (None, None) if not whitelisted.
        """
        league_clean = (league_name or "").strip()
        h_clean = (home_team or "").strip()
        a_clean = (away_team or "").strip()
        h_low = h_clean.lower()
        a_low = a_clean.lower()

        # Priority Check: Timnas Indonesia (Senior, U-23, U-20, U-17, Putri)
        is_indonesia = (
            "indonesia" in h_low or "indonesia" in a_low or
            re.search(r"\b(idn|ina)\b", h_low) or re.search(r"\b(idn|ina)\b", a_low)
        )
        if is_indonesia:
            team_str = h_clean if ("indonesia" in h_low or re.search(r"\b(idn|ina)\b", h_low)) else a_clean
            team_low = team_str.lower()
            league_low = (league_clean or "").lower()
            is_wc = any(w in league_low for w in ["world cup", "piala dunia", "thế giới"])

            if "u-17" in team_low or "u17" in team_low or "u-17" in league_low or "u17" in league_low:
                if is_wc:
                    comp = "Timnas Indonesia U-17 (Piala Dunia U-17)"
                else:
                    comp = "Timnas Indonesia U-17"
            elif "u-20" in team_low or "u20" in team_low or "u-20" in league_low or "u20" in league_low:
                if is_wc:
                    comp = "Timnas Indonesia U-20 (Piala Dunia U-20)"
                else:
                    comp = "Timnas Indonesia U-20"
            elif "u-23" in team_low or "u23" in team_low or "u-23" in league_low or "u23" in league_low:
                comp = "Timnas Indonesia U-23"
            elif any(k in team_low for k in ["putri", "women", "nữ"]):
                comp = "Timnas Putri Indonesia"
            else:
                if is_wc:
                    comp = "Timnas Indonesia (Piala Dunia)"
                else:
                    comp = "Timnas Indonesia Senior"
            return "Timnas Indonesia", comp

        # Check against Whitelist Competitions
        for rule in COMPETITION_WHITELIST:
            if re.search(rule["pattern"], league_clean):
                if rule.get("exclude") and re.search(rule["exclude"], league_clean):
                    continue
                return rule["category"], rule["competition"]

        return None, None

    def resolve_active_domain(self, source: Dict) -> Optional[str]:
        """
        Dynamically discovers the current active domain by testing seed_url and following redirects.
        Falls back to fallback_url or base_url if needed.
        """
        candidates = [source.get("seed_url"), source.get("fallback_url"), source.get("base_url")]
        candidates = [c for c in candidates if c]

        for url in candidates:
            try:
                r = self.session.get(url, timeout=6, allow_redirects=True)
                if r.status_code == 200:
                    # Extract active scheme + host
                    from urllib.parse import urlparse
                    parsed = urlparse(r.url)
                    active_base = f"{parsed.scheme}://{parsed.netloc}"
                    logger.info(f"[{source.get('name')}] Terhubung ke domain aktif: {active_base}")
                    return active_base
            except Exception as e:
                logger.debug(f"Candidate {url} unreachable: {e}")

        logger.warning(f"Semua domain untuk '{source.get('name')}' gagal diakses.")
        return None

    def fetch_all_matches(self) -> List[Dict]:
        """
        Scrapes all raw football match cards across data source endpoints.
        Automatically adapts if Xoilac rotates its domain name.
        """
        raw_items = []
        seen_fids = set()

        for source in DATA_SOURCES:
            base_url = self.resolve_active_domain(source)
            if not base_url:
                continue

            source_headers = dict(self.session.headers)
            source_headers["Referer"] = base_url + "/"

            # 1. Fetch Homepage
            try:
                r = self.session.get(base_url + source.get("home_path", "/"), headers=source_headers, timeout=10)
                r.encoding = "utf-8"
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    items = soup.select(".main-grid-match.match-football-item, .main-grid-match[data-sport='football']")
                    for it in items:
                        fid = it.get("data-fid") or it.get("id")
                        if fid and fid not in seen_fids:
                            seen_fids.add(fid)
                            raw_items.append((it, base_url))
            except Exception as e:
                logger.warning(f"Error fetching home from {base_url}: {e}")

            # 2. Fetch Hot Matches Filter
            try:
                hot_url = base_url + source.get("hot_path", "/sport/football/filter/hot")
                ajax_headers = dict(source_headers)
                ajax_headers["X-Requested-With"] = "XMLHttpRequest"
                r = self.session.get(hot_url, headers=ajax_headers, timeout=10)
                r.encoding = "utf-8"
                if r.status_code == 200:
                    data = r.json()
                    htmls = data.get("data", {}).get("htmls", [])
                    for h in htmls:
                        soup = BeautifulSoup(h, "html.parser")
                        it = soup.select_one(".main-grid-match")
                        if it:
                            fid = it.get("data-fid") or it.get("id")
                            if fid and fid not in seen_fids:
                                seen_fids.add(fid)
                                raw_items.append((it, base_url))
            except Exception as e:
                logger.warning(f"Error fetching hot matches from {base_url}: {e}")

            # 3. Fetch Load-More Pages for upcoming fixtures
            max_pages = source.get("max_pages", 3)
            for p in range(1, max_pages + 1):
                try:
                    lm_path = source.get("load_more_path", "/sport/football/load-more/home/page/{page}/per/50").format(page=p)
                    r = self.session.get(base_url + lm_path, headers=ajax_headers, timeout=10)
                    r.encoding = "utf-8"
                    if r.status_code == 200:
                        res = r.json()
                        html = res.get("data", {}).get("html", "")
                        soup = BeautifulSoup(f"<div>{html}</div>", "html.parser")
                        for it in soup.select(".main-grid-match"):
                            fid = it.get("data-fid") or it.get("id")
                            if fid and fid not in seen_fids:
                                seen_fids.add(fid)
                                raw_items.append((it, base_url))
                except Exception as e:
                    logger.warning(f"Error loading page {p} from {base_url}: {e}")
                    break

            if raw_items:
                break  # Stop if primary source yielded matches

        # Parse collected items
        parsed_matches = []
        for item, base_url in raw_items:
            parsed = self._parse_match_element(item, base_url)
            if parsed:
                parsed_matches.append(parsed)

        return parsed_matches

    def _parse_match_element(self, item, base_url: str) -> Optional[Dict]:
        """
        Parses a single HTML match card element into structured data.
        """
        try:
            fid = item.get("data-fid") or item.get("id") or ""
            classes = item.get("class", [])

            # Teams
            home_el = item.select_one(".gmd-home_team p")
            away_el = item.select_one(".gmd-away_team p")
            home_name = home_el.get_text(strip=True) if home_el else ""
            away_name = away_el.get_text(strip=True) if away_el else ""

            if not home_name or not away_name:
                # Try fallback content_match
                cm = item.select_one(".gmd-content_match")
                if cm:
                    parts = cm.get_text(strip=True).split("VS")
                    if len(parts) == 2:
                        home_name = parts[0].strip()
                        away_name = parts[1].strip()

            if not home_name or not away_name:
                return None

            # Team Logos
            home_img = item.select_one(".gmd-home_team img, .team-logo-group-home-logo img")
            away_img = item.select_one(".gmd-away_team img, .team-logo-group-away-logo img")
            home_logo = (home_img.get("src") or home_img.get("data-src") or "") if home_img else ""
            away_logo = (away_img.get("src") or away_img.get("data-src") or "") if away_img else ""

            # League Name & Logo
            league_el = item.select_one(".gmd-match-league span, .grid-match__league")
            league_name = league_el.get_text(strip=True) if league_el else item.get("data-league", "")
            league_img = item.select_one(".gmd-comp_logo, .gmd-match-league img")
            league_logo = (league_img.get("src") or league_img.get("data-src") or "") if league_img else ""

            # Kickoff Time
            runtime_str = item.get("data-runtime")
            kickoff_ts = int(runtime_str) if runtime_str and runtime_str.isdigit() else 0
            kickoff_display = ""
            if kickoff_ts > 0:
                dt = datetime.datetime.fromtimestamp(kickoff_ts, self.tz)
                kickoff_display = dt.strftime("%d/%m %H:%M WIB")
            else:
                date_el = item.select_one(".gmd-match-date, .grid-match__date")
                kickoff_display = date_el.get_text(strip=True) if date_el else ""

            # Match Status and Finished/End Check
            data_status = str(item.get("data-status", "")).strip()
            score_box = item.select_one(".gmd-score-box, .grid-match__vs")
            score = score_box.get_text(strip=True) if score_box else "VS"
            elapsed_el = item.select_one(".gmd-elapsed-time, .gmd-e_minutes, .grid-match__status")
            elapsed_txt = elapsed_el.get_text(strip=True) if elapsed_el else ""
            status_text = f"{score} {elapsed_txt}".lower()

            # 1. Finished / Ended Match Check -> Automatically dropped/deleted from playlist!
            # STATUS_END = 8, STATUS_CUT_IN_HALF = 11, STATUS_CANCEL = 12
            if data_status in ["8", "11", "12"] or any(
                k in status_text for k in ["hết giờ", "kết thúc", "ft", "full time", "ended", "finished"]
            ):
                return None  # Dropped from active playlist!

            # 2. Live Match Detection (including Extra Time & Penalty Shootout)
            # STATUS_FIRST_HALF = 2, STATUS_HALF_TIME = 3, STATUS_SECOND_HALF = 4,
            # STATUS_OVERTIME = 5, 6 (Extra Time), STATUS_PENALTY = 7 (Adu Penalti)
            is_live = False
            live_status_tag = "LIVE"

            if (
                data_status in ["2", "3", "4", "5", "6", "7"]
                or "data-live-match" in classes
                or "live" in " ".join(classes).lower()
            ):
                is_live = True

                # Detect Extra Time (Babak Tambahan)
                if data_status in ["5", "6"] or any(
                    k in status_text for k in ["hiệp phụ", "extra time", "overtime", "et", "aet", "hiệp phụ 1", "hiệp phụ 2"]
                ):
                    live_status_tag = "Extra Time"
                # Detect Penalty Shootout (Adu Penalti)
                elif data_status == "7" or any(
                    k in status_text for k in ["pen", "luân lưu", "penalty", "penalties", "pk"]
                ):
                    live_status_tag = "Adu Penalti"
                elif data_status == "3" or "ht" in status_text:
                    live_status_tag = "Halftime"
                elif data_status == "2":
                    live_status_tag = "Babak 1"
                elif data_status == "4":
                    live_status_tag = "Babak 2"
                else:
                    live_status_tag = "LIVE"

            # 3. Date Window Filter for Upcoming Matches (e.g. Hari ini & Besok / tgl 16 & 17)
            if not is_live:
                today = datetime.datetime.now(self.tz).date()
                max_upcoming_date = today + datetime.timedelta(days=UPCOMING_DAYS_AHEAD)

                match_date = None
                if kickoff_ts > 0:
                    match_date = datetime.datetime.fromtimestamp(kickoff_ts, self.tz).date()
                elif item.get("data-day") and len(item.get("data-day")) == 8:
                    d_str = item.get("data-day")
                    match_date = datetime.date(int(d_str[:4]), int(d_str[4:6]), int(d_str[6:8]))
                else:
                    match_date = today

                # Skip past matches or matches beyond the configured date window
                if match_date < today or match_date > max_upcoming_date:
                    return None

            # Detail URL
            link_el = item.select_one("a[href*='/truc-tiep/'], .grid-match[href*='/truc-tiep/']")
            detail_path = link_el.get("href") if link_el else ""
            detail_url = ""
            if detail_path:
                detail_url = detail_path if detail_path.startswith("http") else base_url + detail_path

            # Whitelist match check
            category, comp_name = self.filter_competition(league_name, home_name, away_name)
            if not category:
                return None  # Excluded by whitelist

            return {
                "match_id": fid or f"{home_name}_vs_{away_name}".replace(" ", "_"),
                "home_team": home_name,
                "away_team": away_name,
                "home_logo": home_logo,
                "away_logo": away_logo,
                "category": category,
                "competition": comp_name or league_name,
                "league_raw": league_name,
                "league_logo": league_logo,
                "kickoff_ts": kickoff_ts,
                "kickoff_display": kickoff_display,
                "is_live": is_live,
                "live_status_tag": live_status_tag,
                "score": score,
                "detail_url": detail_url,
                "base_url": base_url
            }
        except Exception as e:
            logger.debug(f"Error parsing match element: {e}")
            return None

    def resolve_streams_for_match(self, match: Dict) -> List[str]:
        """
        Given a match dictionary, resolves direct working HLS (.m3u8) / FLV URLs.
        """
        detail_url = match.get("detail_url")
        if not detail_url:
            return []

        resolved_urls = []
        try:
            r = self.session.get(detail_url, timeout=8)
            r.encoding = "utf-8"
            if r.status_code != 200:
                return []

            # 1. Extract var list_stream = [[...], [...]]
            match_ls = re.search(r'var\s+list_stream\s*=\s*(\[[\s\S]*?\]);', r.text)
            if not match_ls:
                return []

            list_stream = json.loads(match_ls.group(1))

            for server_group in list_stream:
                for embed_url in server_group:
                    try:
                        emb_headers = dict(self.session.headers)
                        emb_headers["Referer"] = detail_url
                        emb_r = self.session.get(embed_url, headers=emb_headers, timeout=6)
                        if emb_r.status_code == 200:
                            stream_m = re.search(r'var\s+urlStream\s*=\s*[\"\']([^\"\']+)[\"\']', emb_r.text)
                            if stream_m:
                                stream_url = stream_m.group(1).replace('\\/', '/')
                                # Generate M3U8 candidate if ends with .flv
                                m3u8_url = stream_url
                                if ".flv" in stream_url:
                                    m3u8_url = stream_url.replace(".flv?", ".m3u8?").replace(".flv", ".m3u8")

                                if CHECK_STREAM_ONLINE and match.get("is_live"):
                                    # Verify connectivity for live streams
                                    if self.verify_stream(m3u8_url, emb_url=embed_url):
                                        resolved_urls.append(m3u8_url)
                                    elif self.verify_stream(stream_url, emb_url=embed_url):
                                        resolved_urls.append(stream_url)
                                else:
                                    # For upcoming matches, keep candidate M3U8
                                    resolved_urls.append(m3u8_url)
                    except Exception as e:
                        logger.debug(f"Error resolving embed {embed_url}: {e}")

        except Exception as e:
            logger.warning(f"Error resolving stream for {match.get('match_id')}: {e}")

        return list(dict.fromkeys(resolved_urls))  # Deduplicate

    def verify_stream(self, stream_url: str, emb_url: str = "") -> bool:
        """
        Quickly tests whether the HLS manifest or stream endpoint responds with HTTP 200.
        """
        try:
            headers = {"User-Agent": DEFAULT_HEADERS["User-Agent"]}
            if emb_url:
                headers["Referer"] = emb_url
            r = self.session.get(stream_url, headers=headers, stream=True, timeout=STREAM_CHECK_TIMEOUT)
            status = r.status_code
            r.close()
            return status in [200, 206]
        except Exception:
            return False
