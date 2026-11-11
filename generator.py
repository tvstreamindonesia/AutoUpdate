"""
Playlist Generator Module for Xoilac M3U8.
Constructs standard M3U/M3U8 playlists conforming strictly to the requested specification:
#EXTM3U

#EXTINF:-1 tvg-id="match_id" tvg-name="Team A vs Team B" tvg-logo="TEAM_A_LOGO_URL" group-title="LIVE | COMPETITION",Team A vs Team B
STREAM_URL
"""

import os
from typing import List, Dict
import logging
from config import (
    DEFAULT_STANDBY_STREAM,
    USE_COMPETITION_LOGO,
    SPLIT_SERVERS_INTO_ITEMS,
    CUSTOM_CHANNELS_FILE,
    CUSTOM_CHANNELS_POSITION,
    XOILAC_GROUP_TITLE,
)

logger = logging.getLogger(__name__)


class PlaylistGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def _load_custom_channels(self) -> List[str]:
        """
        Loads manual/custom M3U channel entries from CUSTOM_CHANNELS_FILE if present.
        Strips redundant #EXTM3U headers, converts invalid separator lines to comments,
        and ensures every channel entry is valid with an active stream URL so that
        IPTV players like TiviMate and OTT Navigator never crash or fail to load.
        """
        if not CUSTOM_CHANNELS_FILE:
            return []

        if not os.path.isabs(CUSTOM_CHANNELS_FILE):
            custom_path = os.path.join(os.path.dirname(os.path.abspath(self.output_path)), CUSTOM_CHANNELS_FILE)
        else:
            custom_path = CUSTOM_CHANNELS_FILE

        if not os.path.exists(custom_path):
            return []

        try:
            with open(custom_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                content = f.read()

            raw_lines = content.splitlines()
            valid_entries = []
            channel_props_before = []
            current_channel_lines = []
            in_channel = False

            for line in raw_lines:
                s = line.strip()
                if not s:
                    continue

                if s.startswith("#EXTM3U"):
                    continue

                # Convert decorative section dividers (e.g. <=== ... ===>) into comments
                if s.startswith("<") or s.startswith("="):
                    if not in_channel:
                        valid_entries.append(f"## {line}")
                    continue

                # Directives that may appear BEFORE #EXTINF (#KODIPROP, #EXTVLCOPT, etc.)
                if s.startswith("#KODIPROP:") or s.startswith("#EXTVLCOPT:") or s.startswith("#EXTHTTP:"):
                    if in_channel:
                        current_channel_lines.append(line)
                    else:
                        channel_props_before.append(line)
                    continue

                # Channel header #EXTINF
                if s.startswith("#EXTINF:"):
                    # Discard any previous channel that had no stream URL
                    current_channel_lines = channel_props_before + [line]
                    channel_props_before = []
                    in_channel = True
                    continue

                # Stream URL
                if s.startswith("http://") or s.startswith("https://") or s.startswith("rtmp://") or s.startswith("rtsp://"):
                    if in_channel:
                        current_channel_lines.append(line)
                        valid_entries.extend(current_channel_lines)
                        valid_entries.append("")
                        current_channel_lines = []
                        channel_props_before = []
                        in_channel = False
                    continue

                # Other comments
                if s.startswith("#"):
                    if not in_channel:
                        valid_entries.append(line)

            if valid_entries:
                logger.info(f"Loaded manual channels from {custom_path} ({len(valid_entries)} clean lines)")
                return valid_entries
            return []
        except Exception as e:
            logger.warning(f"Gagal membaca file custom channels {custom_path}: {e}")
            return []

    def _load_livesports_channels(self) -> List[str]:
        """
        Loads scraped LiveSports808 M3U channel entries from livesports.m3u if present.
        """
        livesports_path = os.path.join(os.path.dirname(os.path.abspath(self.output_path)), "livesports.m3u")
        if not os.path.exists(livesports_path):
            return []

        try:
            with open(livesports_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                content = f.read()

            raw_lines = content.splitlines()
            result = []
            for line in raw_lines:
                stripped = line.strip()
                if stripped.startswith("#EXTM3U"):
                    continue
                result.append(line)

            if any(l.strip() and not l.strip().startswith("#") for l in result):
                logger.info(f"Loaded LiveSports808 channels ({len(result)} lines)")
                return result
            return []
        except Exception as e:
            logger.warning(f"Gagal membaca file livesports.m3u: {e}")
            return []

    def build_m3u(self, matches: List[Dict]) -> str:
        """
        Builds M3U playlist string separating LIVE and UPCOMING matches,
        grouped by competition, and seamlessly merging custom/manual channels
        as well as LiveSports808 streams.
        """
        lines = [
            "#EXTM3U x-tvg-url=\"\" url-tvg=\"\" tvg-shift=\"0\"",
            ""
        ]

        custom_entries = self._load_custom_channels()

        # Injeksi saluran manual di bagian ATAS jika posisi = "top"
        if custom_entries and CUSTOM_CHANNELS_POSITION == "top":
            lines.extend(custom_entries)
            lines.append("")

        live_matches = [m for m in matches if m.get("is_live")]
        upcoming_matches = [m for m in matches if not m.get("is_live")]

        # Sort matches by kickoff timestamp
        live_matches.sort(key=lambda x: x.get("kickoff_ts", 0))
        upcoming_matches.sort(key=lambda x: x.get("kickoff_ts", 0))

        # ----------------------------------------------------
        # 1. LIVE MATCHES SECTION (XOILAC)
        # ----------------------------------------------------
        if live_matches:
            lines.append("########################################################")
            lines.append("## [LIVE] PERTANDINGAN SEDANG BERLANGSUNG")
            lines.append("########################################################")
            lines.append("")

            for m in live_matches:
                entries = self._format_match_entries(m, status_prefix="LIVE")
                lines.extend(entries)

        # ----------------------------------------------------
        # 2. LIVESPORTS808 SECTION (FOOTBALL & BADMINTON)
        # ----------------------------------------------------
        livesports_entries = self._load_livesports_channels()
        if livesports_entries:
            lines.append("########################################################")
            lines.append("## [LIVESPORTS808] SEPAK BOLA & BADMINTON LIVE")
            lines.append("########################################################")
            lines.append("")
            lines.extend(livesports_entries)
            lines.append("")

        # ----------------------------------------------------
        # 3. UPCOMING MATCHES SECTION (XOILAC)
        # ----------------------------------------------------
        if upcoming_matches:
            lines.append("########################################################")
            lines.append("## [JADWAL] PERTANDINGAN MENDATANG")
            lines.append("########################################################")
            lines.append("")

            for m in upcoming_matches:
                entries = self._format_match_entries(m, status_prefix="UPCOMING")
                lines.extend(entries)

        # Injeksi saluran manual di bagian BAWAH jika posisi = "bottom"
        if custom_entries and CUSTOM_CHANNELS_POSITION == "bottom":
            lines.append("")
            lines.extend(custom_entries)

        content = "\n".join(lines)
        return content

    def _format_match_entries(self, match: Dict, status_prefix: str) -> List[str]:
        """
        Formats a single match into #EXTINF block and stream URL.
        """
        match_id = match.get("match_id", "")
        home = match.get("home_team", "")
        away = match.get("away_team", "")

        # Prioritize Competition Logo instead of Club Logo
        if USE_COMPETITION_LOGO:
            match_logo = match.get("league_logo") or match.get("home_logo") or ""
        else:
            match_logo = match.get("home_logo") or match.get("league_logo") or ""

        competition = match.get("competition", "Sepak Bola")
        kickoff_str = match.get("kickoff_display", "")
        streams = match.get("streams", [])

        # Format group-title: e.g. "LIVE EVENT" or "LIVE | Premier League"
        if XOILAC_GROUP_TITLE:
            group_title = XOILAC_GROUP_TITLE
        else:
            group_title = f"{status_prefix} | {competition}"

        match_title = f"{home} vs {away}"

        # Display name with context (including Extra Time & Adu Penalti)
        if status_prefix == "LIVE":
            live_tag = match.get("live_status_tag", "LIVE")
            score_val = match.get("score", "")
            score_str = f" [{score_val}]" if score_val and score_val != "VS" else ""

            if live_tag in ["Extra Time", "Adu Penalti"]:
                display_title = f"{home} vs {away} (LIVE - {live_tag}{score_str})"
            elif live_tag != "LIVE":
                display_title = f"{home} vs {away} (LIVE - {live_tag}{score_str})"
            else:
                display_title = f"{home} vs {away} (LIVE{score_str})"
        else:
            time_tag = f"[{kickoff_str}] " if kickoff_str else ""
            comp_tag = f"[{competition}] " if (XOILAC_GROUP_TITLE and competition) else ""
            display_title = f"{time_tag}{comp_tag}{home} vs {away}"

        # Determine target streams
        if not SPLIT_SERVERS_INTO_ITEMS and streams:
            urls_to_emit = [streams[0]]
            emit_server_label = False
        else:
            urls_to_emit = streams if streams else [DEFAULT_STANDBY_STREAM]
            emit_server_label = len(urls_to_emit) > 1

        entries = []
        for idx, url in enumerate(urls_to_emit):
            # If multiple servers, append server label
            server_suffix = f" (Server {idx + 1})" if (emit_server_label and len(urls_to_emit) > 1) else ""
            item_display = f"{display_title}{server_suffix}"
            item_id = f"{match_id}_srv{idx+1}" if (emit_server_label and len(urls_to_emit) > 1) else match_id

            # Standard #EXTINF with attributes
            extinf = (
                f'#EXTINF:-1 tvg-id="{item_id}" '
                f'tvg-name="{match_title}" '
                f'tvg-logo="{match_logo}" '
                f'logo="{match_logo}" '
                f'group-title="{group_title}" '
                f'tvg-country="ID" '
                f'tvg-language="Indonesian" '
                f'catchup="false",'
                f'{item_display}'
            )

            entries.append(extinf)
            if match.get("referrer"):
                entries.append(f'#EXTVLCOPT:http-referrer={match["referrer"]}')
            if match.get("user_agent"):
                entries.append(f'#EXTVLCOPT:http-user-agent={match["user_agent"]}')
            entries.append(url)
            entries.append("")

        return entries

    def save_to_file(self, content: str) -> str:
        """
        Writes the playlist content to the destination M3U file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Playlist successfully written to {self.output_path}")
        return self.output_path
