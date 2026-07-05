#!/usr/bin/env python3
"""
Tamil & English IPTV Playlist Builder
--------------------------------------
Consolidated, fixed version. Combines the best logic from all previous
script iterations and fixes:
  1. Category mismatches (longest-keyword-first matching, single source of truth)
  2. Dead link removal (deep byte-level validation, geo-block awareness)
  3. True deduplication (one working link per normalized channel name)
  4. Custom/local channel priority handling
  5. Clean, strictly-ordered category output + README generation

Run: python build_playlist.py
Output: master_playlist.m3u, README.md
"""

import requests
import re
import json
import datetime
import concurrent.futures

# ==========================================================================
# 1. CUSTOM HARDCODED CHANNELS  (always included, bypass strict filtering)
# ==========================================================================
USER_CUSTOM_CHANNELS = """
#EXTINF:-1 group-title="Local Channels",Sana TV
https://galaxyott.live/hls/sanatv.m3u8
#EXTINF:-1 group-title="Local Channels",Sana Plus
https://galaxyott.live/hls/sanaplus.m3u8
#EXTINF:-1 group-title="Local Channels",UTV
https://stream.galaxyott.live/live/utv/index.m3u8
#EXTINF:-1 group-title="Local Channels",NTV
https://galaxyott.live/hls/ntv.m3u8
#EXTINF:-1 group-title="Local Channels",Surya TV
https://galaxyott.live/hls/suryatv.m3u8
#EXTINF:-1 group-title="Local Channels",Subin TV
https://stream.galaxyott.live/live/subintv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Sakthi TV
https://live.sscloud7.in/live/sakthitv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Prime TV
https://live.applelive.in/primetv/primetv/index.m3u8
#EXTINF:-1 group-title="Local Channels",7 Green
https://account33.livebox.co.in/7GREEN4Khls/live.m3u8
#EXTINF:-1 group-title="Local Channels",Yet TV
https://live.yettelevision.com:5443/LiveApp/streams/yettv.m3u8
#EXTINF:-1 group-title="Local Channels",Riya TV
https://play.applelive.in/riyatv/riyatv.m3u8
#EXTINF:-1 group-title="Local Channels",Dark TV
https://play.applelive.in/darktv/darktv.m3u8
#EXTINF:-1 group-title="Local Channels",Phoenix TV
https://stream.onecloudlive.in/phoenixtv/phoenixtv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Nila TV
https://live.olidigital.in/nilatv/nilatv/index.m3u8
#EXTINF:-1 group-title="Local Channels",SMCV TV
https://singamcloud.in/smcvtv/smcvtv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Shalini TV
https://ipcloud.live/shalinitv/shalinitv/index.m3u8
#EXTINF:-1 group-title="Local Channels",JCV TV
https://play.applelive.in/jcvtv/jcvtv.m3u8
#EXTINF:-1 group-title="Local Channels",JCV Musix
https://play.applelive.in/jcvtv/jcvmusix.m3u8
#EXTINF:-1 group-title="Local Channels",Anbu TV HD
https://ipcloud.live/anbutv/anbutvhd/index.m3u8
#EXTINF:-1 group-title="Local Channels",Nellai TV
https://stream.onecloudlive.in/nellaitv/nellaitv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Akash TV
https://account2.livebox.co.in/AkashTvhls/live.m3u8
#EXTINF:-1 group-title="Local Channels",Apple TV
https://play.applelive.in/appletv/appletv.m3u8
#EXTINF:-1 group-title="Local Channels",Jeyson TV
https://play.applelive.in/jeysontv/jeysontv.m3u8
#EXTINF:-1 group-title="Local Channels",JJ Max
https://play.applelive.in/jjmax/jjmax.m3u8
#EXTINF:-1 group-title="Local Channels",JC TV
https://play.applelive.in/jctv/jctv.m3u8
#EXTINF:-1 group-title="Local Channels",Digital TV
https://play.applelive.in/digitaltv/digitaltv.m3u8
#EXTINF:-1 group-title="Local Channels",Oscar TV
https://account21.livebox.co.in/oscartvhls/live.m3u8
#EXTINF:-1 group-title="Local Channels",Vidyal TV
https://account11.livebox.co.in/vidyaltvhls/live.m3u8?psk=stream
#EXTINF:-1 group-title="Local Channels",Sky TV
https://sscloud7.com/live/skytv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Boys TV
https://rtmp.applelive.in/boystv/boystv/index.m3u8
#EXTINF:-1 group-title="Local Channels",King TV
https://server.sscloud7.in/kingtv/kingtv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Udhayam TV
https://view.rcserver.in/tmp_hls8/udhayamtv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Bharathi TV
https://server.sscloud7.in/live/bharathitv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Irattipaathai TV
https://account31.livebox.co.in/IRATTAIPAATHAITVhls/live.m3u8
#EXTINF:-1 group-title="Local Channels",MCN TV
https://play.applelive.in/mcntv/mcntv.m3u8
#EXTINF:-1 group-title="Local Channels",STN TV
https://play.applelive.in/stntv/stntv.m3u8
#EXTINF:-1 group-title="Local Channels",Vasanth TV
https://play.applelive.in/vasanthtv/vasanthtv.m3u8
#EXTINF:-1 group-title="Local Channels",Eesan TV
https://live.singamcloud.in/eesantv/eesantv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Jeyam TV
https://live.sscloud7.in/live/jeyamtv/index.m3u8
#EXTINF:-1 group-title="Local Channels",Solai TV HD
https://ipcloud.live/solaitv/solaihd/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Chithiram TV
https://cdn-6.pishow.tv/live/1243/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",DD Tamil
https://d2lk5u59tns74c.cloudfront.net/out/v1/abf46b14847e45499f4a47f3a9afe93d/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",EET Live
https://eu.streamjo.com/eetlive/eettv.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Isaiaruvi
https://segment.yuppcdn.net/140622/isaiaruvi/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Murasu
https://segment.yuppcdn.net/050522/murasu/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Kalaignar TV
https://segment.yuppcdn.net/240122/kalaignartv/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Mathimugam
https://cdn-3.pishow.tv/live/1476/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Makkal TV
https://5k8q87azdy4v-hls-live.wmncdn.net/MAKKAL/271ddf829afeece44d8732757fba1a66.sdp/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Malai Murasu
https://cdn-3.pishow.tv/live/1606/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",News7 Tamil
https://segment.yuppcdn.net/240122/news7/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",News18 Tamil Nadu
https://n18syndication.akamaized.net/bpk-tv/News18_Tamil_Nadu_NW18_MOB/output01/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",News J
https://cdn-3.pishow.tv/live/1279/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Polimer News
https://segment.yuppcdn.net/110322/polimernews/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Polimer TV
https://cdn-2.pishow.tv/live/1241/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Puthiya Thalaimurai
https://segment.yuppcdn.net/240122/puthiya/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Raj TV
https://d3qs3d2rkhfqrt.cloudfront.net/out/v1/2839e3d1e0f84a2e821c1708d5fdfdf0/index.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Sirippoli
https://segment.yuppcdn.net/240122/siripoli/playlist.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Thanthi TV
https://cdn-3.pishow.tv/live/1612/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Vendhar TV
https://cdn-3.pishow.tv/live/1271/master.m3u8
#EXTINF:-1 group-title="Tamil IPTV Channels",Win News
https://cdn-4.pishow.tv/live/1531/master.m3u8
"""

# ==========================================================================
# 2. REMOTE SOURCES
# ==========================================================================
SOURCES = [
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u",
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/jio.m3u",
    "https://raw.githubusercontent.com/Tamilwebcast/Tamilwebcast.github.io/main/TWCIPTV.m3u",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/main/output/india_iptv.m3u",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/main/output/india_general.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/jtv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/pishow.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/yupptvfast.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/tangotv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/neotv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
    "https://iptv-org.github.io/iptv/languages/tam.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u",
]

# Only these sources are allowed to populate "Tamil Local Channels"
LOCAL_SOURCES = [
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/main/live/channels.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u",
    "https://raw.githubusercontent.com/amazeyourself/tamil-local-iptv/refs/heads/main/channels.m3u",
]

# ==========================================================================
# 3. LANGUAGE BLOCKLIST  (word-boundary safe: "KTV Bangla" is blocked,
#    "Bangalore TV" is NOT falsely blocked)
# ==========================================================================
BLOCKED_WORDS = [
    "bangla", "bengali", "telugu", "hindi", "kannada", "malayalam",
    "marathi", "punjabi", "gujarati", "bhojpuri", "urdu", "oriya", "odia",
    "assamese", "arabic", "spanish", "french", "german", "italian",
    "portuguese", "russian", "chinese", "japanese", "korean",
    "indonesian", "nepali",
]

def is_blocked(name: str) -> bool:
    if not name:
        return True
    n = name.lower()
    return any(re.search(r"\b" + w + r"\b", n) for w in BLOCKED_WORDS)


# ==========================================================================
# 4. SINGLE SOURCE OF TRUTH CATEGORY MAP
#    Structure: category -> { "Proper Display Name": [keywords...] }
#    Matching uses LONGEST keyword first, so "Star Vijay Super" never
#    gets swallowed by the shorter "Star Vijay" / "Vijay TV" keywords.
# ==========================================================================
CATEGORY_ORDER = [
    "Tamil GEC", "Tamil Movies", "Tamil News", "Tamil Comedy", "Tamil Music",
    "Tamil Infotainment & Lifestyle", "Tamil Spiritual & Devotional", "Tamil Kids",
    "Sports",
    "English GEC", "English Movies", "English National News",
    "English International News", "English Business News", "English Infotainment",
    "English Lifestyle & Travel", "English Kids",
    "Local Channels", "Tamil Local Channels", "Tamil IPTV Channels",
]

CATEGORIES_MAP = {
    "Tamil GEC": {
        "Sun TV": ["sun tv"], "Star Vijay": ["star vijay", "vijay tv"],
        "Zee Tamil": ["zee tamil"], "Colors Tamil": ["colors tamil"],
        "Kalaignar TV": ["kalaignar tv", "kalaignar"], "Jaya TV": ["jaya tv"],
        "Raj TV": ["raj tv"], "Polimer TV": ["polimer tv"],
        "Makkal TV": ["makkal tv", "makkal"], "Vasanth TV": ["vasanth tv", "vasanth"],
        "Puthuyugam TV": ["puthuyugam tv", "puthuyugam"], "Mega TV": ["mega tv"],
        "Captain TV": ["captain tv"], "Vendhar TV": ["vendhar tv", "vendhar"],
    },
    "Tamil Movies": {
        "Star Vijay Super": ["star vijay super", "vijay super"],
        "KTV": ["ktv"], "Zee Thirai": ["zee thirai"],
        "J Movies": ["j movie", "jaya movie"],
        "Raj Digital Plus": ["raj digital plus"], "Murasu": ["murasu"],
        "Mega 24": ["mega 24"], "Sun Action": ["sun action"],
    },
    "Tamil News": {
        "Sun News": ["sun news"], "Puthiya Thalaimurai": ["puthiya thalaimurai"],
        "Thanthi TV": ["thanthi tv", "thanthi"],
        "News18 Tamil Nadu": ["news18 tamil", "news 18 tamil"],
        "Polimer News": ["polimer news"],
        "News7 Tamil": ["news7 tamil", "news 7 tamil"],
        "Sathiyam TV": ["sathiyam tv", "sathiyam"], "News J": ["news j", "newsj"],
        "Jaya Plus": ["jaya plus"], "Kalaignar Seithigal": ["kalaignar seithigal"],
        "Raj News Tamil": ["raj news tamil", "raj news"], "Captain News": ["captain news"],
    },
    "Tamil Comedy": {
        "Adithya TV": ["adithya tv", "adithya"], "Sirippoli": ["sirippoli"],
    },
    "Tamil Music": {
        "Sun Music": ["sun music"], "Star Vijay Music": ["star vijay music", "vijay music"],
        "Isaiaruvi": ["isaiaruvi", "isai aruvi"], "Jaya Max": ["jaya max"],
        "Raj Musix Tamil": ["raj musix tamil", "raj musix"], "Mega Musiq": ["mega musiq"],
    },
    "Tamil Infotainment & Lifestyle": {
        "Sun Life": ["sun life"], "Discovery Tamil": ["discovery tamil"],
        "Nat Geo Tamil": ["nat geo tamil", "national geographic tamil"],
        "Sony BBC Earth Tamil": ["sony bbc earth tamil", "bbc earth tamil"],
    },
    "Tamil Spiritual & Devotional": {
        "Madha TV": ["madha tv"], "Angel TV": ["angel tv"],
        "Nambikkai TV": ["nambikkai tv", "nambikkai"], "Vaanavil TV": ["vaanavil"],
        "Jothi TV": ["jothi tv"], "Velicham TV": ["velicham tv"],
        "Sri Sankara TV": ["sri sankara tv", "sri sankara", "sankara tv"],
    },
    "Tamil Kids": {
        "Chutti TV": ["chutti tv", "chutti"],
        "Chithiram TV": ["chithiram tv", "chithiram"],
        "Cartoon Network Tamil": ["cartoon network tamil"],
        "Pogo Tamil": ["pogo tamil"], "Discovery Kids Tamil": ["discovery kids tamil"],
        "Sony Yay Tamil": ["sony yay tamil"], "Disney Channel Tamil": ["disney channel tamil"],
        "Kochu TV": ["kochu tv"],
    },
    "Sports": {
        "Star Sports 1 Tamil": ["star sports 1 tamil"],
        "Star Sports 2 Tamil": ["star sports 2 tamil"],
        "Star Sports Select 1": ["star sports select 1"],
        "Star Sports Select 2": ["star sports select 2"],
        "Star Sports 1": ["star sports 1"], "Star Sports 2": ["star sports 2"],
        "Sony Sports Ten 1": ["sony sports ten 1", "sony ten 1"],
        "Sony Sports Ten 2": ["sony sports ten 2", "sony ten 2"],
        "Sony Sports Ten 5": ["sony sports ten 5", "sony ten 5", "sony sports ten 6"],
        "Eurosport": ["eurosport"], "Sports18": ["sports18", "sports 18"],
    },
    "English GEC": {
        "Colors Infinity": ["colors infinity"], "Comedy Central": ["comedy central"],
        "Disney International HD": ["disney international"], "Zee Cafe": ["zee cafe"],
    },
    "English Movies": {
        "Star Movies Select": ["star movies select"], "Star Movies": ["star movies"],
        "Sony PIX": ["sony pix"], "Movies Now": ["movies now"], "MNX": ["mnx"],
        "Romedy Now": ["romedy now"], "HBO": ["hbo"], "WB": ["wb"],
    },
    "English National News": {
        "Times Now": ["times now"], "Republic TV": ["republic tv"],
        "India Today": ["india today"], "NDTV 24x7": ["ndtv 24x7"],
        "Mirror Now": ["mirror now"], "WION": ["wion"],
        "CNN-News18": ["cnn-news18", "cnn news18"],
    },
    "English International News": {
        "BBC News": ["bbc news"], "CNN International": ["cnn international"],
        "Al Jazeera English": ["al jazeera english", "al jazeera"],
        "RT (Russia Today)": ["russia today", "rt news", "rt arabic", "rt india"],
    },
    "English Business News": {
        "CNBC-TV18": ["cnbc-tv18", "cnbc tv18"], "NDTV Profit": ["ndtv profit"],
    },
    "English Infotainment": {
        "Discovery Channel": ["discovery channel"],
        "National Geographic": ["national geographic"],
        "History TV18": ["history tv18"], "Animal Planet": ["animal planet"],
        "Sony BBC Earth": ["sony bbc earth"],
    },
    "English Lifestyle & Travel": {
        "Travelxp": ["travelxp"], "Goodtimes": ["goodtimes", "ndtv goodtimes"],
    },
    "English Kids": {
        "Disney Channel": ["disney channel"], "Disney Junior": ["disney junior"],
        "Nickelodeon": ["nickelodeon"],
    },
}

# Flatten + sort longest-keyword-first (fixes "Star Vijay Super" vs "Star Vijay")
FLAT_RULES = []
for cat, channels in CATEGORIES_MAP.items():
    for proper_name, keywords in channels.items():
        for kw in keywords:
            FLAT_RULES.append((len(kw), kw, proper_name, cat))
FLAT_RULES.sort(reverse=True, key=lambda x: x[0])

TAMIL_LOCAL_HINTS = ["tv", "media", "vision", "tamil", "network", "cable", "channel"]


def get_category_and_name(raw_name: str):
    """Returns (category, proper_display_name) or (None, None)."""
    if is_blocked(raw_name):
        return None, None
    n = raw_name.lower()
    for _, kw, proper_name, cat in FLAT_RULES:
        if kw in n:
            return cat, proper_name
    return None, None


def clean_name(name: str) -> str:
    name = re.sub(r"\s*\[.*?\]\s*", "", name)
    name = re.sub(r"\s*\(.*?\)\s*", "", name)
    name = re.sub(r"\b(HD|SD|FHD|4K|UHD|HEVC|HDR|1080p|720p|Premium)\b", "", name, flags=re.I)
    return " ".join(name.split()).strip().title()


def get_core_key(name: str) -> str:
    """Normalized dedup key: 'Sun TV HD' -> 'suntv'."""
    n = re.sub(r"\s*\[.*?\]\s*", "", name)
    n = re.sub(r"\s*\(.*?\)\s*", "", n)
    n = re.sub(r"\b(HD|SD|FHD|4K|UHD|HEVC|HDR|1080p|720p|Premium|IN)\b", "", n, flags=re.I)
    n = re.sub(r"[^a-zA-Z0-9]", "", n)
    return n.lower()


# ==========================================================================
# 5. PARSERS
# ==========================================================================
def parse_m3u(content: str):
    """Yields (name, logo, url, group_title) for each entry."""
    lines = content.splitlines()
    current_name, current_logo, current_cat = None, "", None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            logos = re.findall(r'tvg-logo="(.*?)"', line)
            current_logo = logos[0] if logos else ""
            cats = re.findall(r'group-title="(.*?)"', line)
            current_cat = cats[0] if cats else None
            current_name = line.rsplit(",", 1)[1].strip() if "," in line else None
        elif line and not line.startswith("#") and current_name:
            # strip any trailing |User-Agent=... pipe (keep base URL only)
            url = line.split("|")[0].strip()
            yield current_name, current_logo, url, current_cat
            current_name, current_cat = None, None


# ==========================================================================
# 6. STREAM VALIDATION  (deep byte inspection + geo-block awareness)
# ==========================================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

# Geo-blocked-but-alive: Indian CDNs commonly 403 GitHub Actions' US IPs.
# Treat these as PASS rather than dead, or every local channel gets purged.
ALIVE_EVEN_IF_BLOCKED = {403, 401, 451, 429}


def stream_is_alive(url: str, timeout=(5.0, 8.0)) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, stream=True, allow_redirects=True)

        if r.status_code in ALIVE_EVEN_IF_BLOCKED:
            return True
        if r.status_code not in (200, 206, 302):
            return False

        ctype = r.headers.get("Content-Type", "").lower()
        if "text/html" in ctype or "application/json" in ctype:
            return False

        chunk = r.raw.read(1500)
        if not chunk:
            return False
        text = chunk.decode("utf-8", errors="ignore").lower().strip()

        # Reject disguised error/HTML/JSON pages
        if "<html" in text or "<!doctype" in text or "<body" in text:
            return False
        if text.startswith("{") or text.startswith("["):
            return False

        is_media = any(v in ctype for v in
                        ["video/", "audio/", "mpegurl", "octet-stream", "mp2t"])
        is_m3u8 = "#extm3u" in text or "#ext-x" in text

        return is_media or is_m3u8
    except Exception:
        return False


def resolve_channel(item):
    """item = (proper_name, {'category', 'logo', 'urls': [..]})
    Tests backup URLs in order; returns first working one."""
    proper_name, data = item
    for url in data["urls"]:
        if stream_is_alive(url):
            return (data["category"], proper_name, data["logo"], url)
    return None


# ==========================================================================
# 7. MAIN BUILD
# ==========================================================================
def main():
    print("Building playlist (fixed categories + dead-link removal)...\n")

    grouped = {}          # core_key -> {category, logo, urls: []}
    seen_urls = set()

    def add_channel(raw_name, logo, url, category):
        url = url.strip()
        if not url.startswith("http") or url in seen_urls:
            return
        seen_urls.add(url)
        display = clean_name(raw_name)
        key = get_core_key(raw_name)
        if key not in grouped:
            grouped[key] = {"category": category, "logo": logo, "urls": [], "display": display}
        grouped[key]["urls"].append(url)
        if not grouped[key]["logo"] and logo:
            grouped[key]["logo"] = logo

    # -- 1. Custom channels first (priority, bypass strict category matcher) --
    print("Loading custom channels...")
    count_custom = 0
    for name, logo, url, group_title in parse_m3u(USER_CUSTOM_CHANNELS):
        if is_blocked(name):
            continue
        cat = group_title if group_title in CATEGORY_ORDER else "Tamil IPTV Channels"
        add_channel(name, logo, url, cat)
        count_custom += 1
    print(f"  -> {count_custom} custom entries loaded\n")

    # -- 2. Remote sources --
    for src in SOURCES:
        print(f"Fetching: {src}")
        try:
            resp = requests.get(src, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  SKIP (fetch failed: {e})")
            continue

        n_added = 0
        for name, logo, url, _ in parse_m3u(resp.text):
            if is_blocked(name):
                continue
            cat, proper_name = get_category_and_name(name)

            if not cat:
                # Fallback: only real "local" sources may populate Tamil Local Channels
                if src in LOCAL_SOURCES and any(h in name.lower() for h in TAMIL_LOCAL_HINTS):
                    cat = "Tamil Local Channels"
                    proper_name = name
                else:
                    continue

            add_channel(proper_name or name, logo, url, cat)
            n_added += 1
        print(f"  -> matched {n_added} channels")

    print(f"\nTotal unique channel groups to validate: {len(grouped)}")
    print("Testing streams concurrently (dead links will be dropped)...\n")

    # -- 3. Concurrent dead-link validation, winner-takes-all dedup --
    final_channels = {cat: [] for cat in CATEGORY_ORDER}
    total_added = 0

    items = [(v["display"], v) for v in grouped.values()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        for result in executor.map(resolve_channel, items):
            if result:
                cat, proper_name, logo, url = result
                if cat not in final_channels:
                    final_channels[cat] = []
                final_channels[cat].append((proper_name, logo, url))
                total_added += 1

    # -- 4. Write output --
    print(f"\nWriting master_playlist.m3u  ({total_added} live channels)...")
    with open("master_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#PLAYLIST:Fixed & Deduplicated Tamil/English IPTV Playlist\n")
        for cat in CATEGORY_ORDER:
            chans = final_channels.get(cat, [])
            if not chans:
                continue
            chans.sort(key=lambda x: x[0].lower())
            f.write(f"\n# --- {cat} ---\n")
            for name, logo, url in chans:
                f.write(
                    f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" '
                    f'group-title="{cat}",{name}\n'
                )
                f.write(f"#EXTVLCOPT:http-user-agent={HEADERS['User-Agent']}\n")
                f.write(f"{url}|User-Agent={HEADERS['User-Agent']}\n")

    print(f"DONE. Total live unique channels: {total_added}")

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# Tamil & English IPTV Playlist\n\n")
        f.write(
            "Auto-checked, correctly categorized, fully deduplicated "
            "(1 working link per channel), dead links removed automatically.\n\n"
        )
        f.write(f"**Total live channels:** {total_added}  \n**Last updated:** {timestamp}\n\n")
        f.write("## Playlist URL\n```text\n")
        f.write(
            "https://raw.githubusercontent.com/nuttle-nuttterr/Tv-by-Claude/main/master_playlist.m3u\n"
        )
        f.write("```\n\n## Channel Breakdown\n| Category | Count |\n|---|---|\n")
        for cat in CATEGORY_ORDER:
            n = len(final_channels.get(cat, []))
            if n:
                f.write(f"| {cat} | {n} |\n")


if __name__ == "__main__":
    main()
