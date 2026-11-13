
import streamlit as st
import requests
from urllib.parse import urlparse, unquote

# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="세계 관광 명소 탐색",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 세계 관광 명소 탐색 시스템")
st.caption(
    "한국어 소개와 사진이 모두 제공되는 관광지만 추천합니다."
)

# ==========================================
# 2. 국가 및 도시
# ==========================================

CITIES = {
    "대한민국": {
        "서울": (37.5665, 126.9780),
        "부산": (35.1796, 129.0756)
    },
    "일본": {
        "도쿄": (35.6762, 139.6503),
        "교토": (35.0116, 135.7681)
    },
    "중국": {
        "베이징": (39.9042, 116.4074),
        "상하이": (31.2304, 121.4737)
    },
    "미국": {
        "뉴욕": (40.7128, -74.0060),
        "샌프란시스코": (37.7749, -122.4194)
    },
    "프랑스": {
        "파리": (48.8566, 2.3522),
        "니스": (43.7102, 7.2620)
    },
    "아르헨티나": {
        "부에노스아이레스": (-34.6037, -58.3816),
        "멘도사": (-32.8895, -68.8458)
    },
    "호주": {
        "시드니": (-33.8688, 151.2093),
        "멜버른": (-37.8136, 144.9631)
    }
}

# ==========================================
# 3. API 설정
# ==========================================

try:
    API_KEY = st.secrets.get("OPENTRIPMAP_API_KEY", "")
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error("OpenTripMap API 키를 설정해 주세요.")
    st.stop()

BASE = "https://api.opentripmap.com/0.1/en/places"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "WorldTourismExplorer/1.0 "
        "(educational tourism information application)"
    )
}

# ==========================================
# 4. OpenTripMap API
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_places(lat, lon, radius, api_key):
    response = requests.get(
        f"{BASE}/radius",
        params={
            "radius": radius,
            "lon": lon,
            "lat": lat,
            "rate": 3,
            "limit": 100,
            "format": "json",
            "apikey": api_key
        },
        timeout=20
    )
    response.raise_for_status()

    return [
        p for p in response.json()
        if p.get("name", "").strip()
        and p.get("xid")
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def get_detail(xid, api_key):
    response = requests.get(
        f"{BASE}/xid/{xid}",
        params={"apikey": api_key},
        timeout=20
    )
    response.raise_for_status()
    return response.json()

# ==========================================
# 5. Wikipedia 한국어 설명 및 사진
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_data(wikipedia_url):
    if not wikipedia_url:
        return None, None, None

    parsed = urlparse(wikipedia_url)
    hostname = parsed.hostname or ""

    if not hostname.endswith(".wikipedia.org"):
        return None, None, None

    if "/wiki/" not in parsed.path:
        return None, None, None

    title = unquote(parsed.path.split("/wiki/", 1)[1])

    try:
        if hostname == "ko.wikipedia.org":
            korean_title = title.replace("_", " ")
        else:
            response = requests.get(
                f"https://{hostname}/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "langlinks",
                    "titles": title,
                    "lllang": "ko"
                },
                headers=HEADERS,
                timeout=12
            )
            response.raise_for_status()

            pages = response.json().get(
                "query", {}
            ).get("pages", {})

            korean_title = None

            for page in pages.values():
                links = page.get("langlinks", [])
                if links:
                    korean_title = (
                        links[0].get("*")
                        or links[0].get("title")
                    )
                    break

        if not korean_title:
            return None, None, None

        response = requests.get(
            "https://ko.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts|pageimages",
                "exintro": 1,
                "explaintext": 1,
                "pithumbsize": 1000,
                "titles": korean_title
            },
            headers=HEADERS,
            timeout=12
        )
        response.raise_for_status()

        pages = response.json().get(
            "query", {}
        ).get("pages", {})

        for page in pages.values():
            description = page.get(
                "extract", ""
            ).strip()

            image = page.get(
                "thumbnail", {}
            ).get("source")

            korean_name = page.get("title")

            if description:
                return description, image, korean_name

    except (requests.RequestException, ValueError):
        pass

    return None, None, None

# ==========================================
# 6. Wikimedia Commons 사진 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_commons_image(place_name):
    if not place_name:
        return None

    ignored = {
        "the", "and", "of", "de", "del",
        "la", "le", "el", "in", "at"
    }

    words = [
        w.lower()
        for w in place_name.replace("-", " ").split()
        if len(w) >= 4 and w.lower() not in ignored
    ]

    if not words:
        return None

    try:
        response = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f'filetype:bitmap "{place_name}"',
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "iiurlwidth": 1000
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        pages = response.json().get(
            "query", {}
        ).get("pages", {})

        candidates = []

        for page in pages.values():
            title = page.get("title", "").lower()

            if not title.endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                continue

            info = (
                page.get("imageinfo") or [{}]
            )[0]

            if not info.get(
                "mime", ""
            ).startswith("image/"):
                continue

            matches = sum(
                word in title for word in words
            )

            score = matches / len(words)

            if score < 0.6:
                continue

            url = (
                info.get("thumburl")
                or info.get("url")
            )

            if url:
                candidates.append((score, url))

        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    except (requests.RequestException, ValueError):
        pass

    return None

# ==========================================
# 7. 관광지 검증
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def verify_place(xid, original_name, api_key):
    """
    한국어 설명과 사진이 모두 있는지 확인합니다.
    두 조건을 만족하지 않으면 제외합니다.
    """

    try:
        detail = get_detail(xid, api_key)
    except (requests.RequestException, ValueError, TypeError):
        return None

    description, wiki_image, korean_name = (
        get_wikipedia_data(
            detail.get("wikipedia")
        )
    )

    # 한국어 설명이 없으면 제외
    if not description:
        return None

    # 사진 검색
    image = (
        (detail.get("preview") or {}).get("source")
        or wiki_image
    )

    image_source = (
        "OpenTripMap"
        if (detail.get("preview") or {}).get("source")
        else "Wikipedia"
    )

    if not image:
        image = get_commons_image(
            detail.get("name") or original_name
        )
        image_source = "Wikimedia Commons"

    # 사진이 없으면 제외
    if not image:
        return None

    return {
        "xid": xid,
        "name": korean_name or original_name,
        "original_name": original_name,
        "description": description,
        "image": image,
        "image_source": image_source,
        "detail": detail
    }

# ==========================================
# 8. 국가 및 도시 선택
# ==========================================

st.subheader("🔎 국가와 도시 선택")

col1, col2, col3 = st.columns(3)

with col1:
    country = st.selectbox(
        "국가",
        list(CITIES)
    )

with col2:
    city = st.selectbox(
        "도시",
        list(CITIES[country])
    )

with col3:
    radius_km = st.slider(
        "검색 반경 (km)",
        3, 30, 10
    )

lat, lon = CITIES[country][city]

st.map(
    [{"lat": lat, "lon": lon}],
    zoom=10
)

# ==========================================
# 9. 관광지 검색 및 자동 필터링
# ==========================================

st.subheader(f"📍 {city} 관광 명소")

try:
    with st.spinner("관광지 목록을 불러오는 중..."):
        places = get_places(
            lat, lon,
            radius_km * 1000,
            API_KEY
        )
except (requests.RequestException, ValueError, TypeError) as e:
    st.error(f"관광지 검색 오류: {e}")
    st.stop()

keyword = st.text_input(
    "관광지 이름 검색",
    placeholder="관광지 이름을 입력하세요"
)

if keyword:
    places = [
        p for p in places
        if keyword.casefold()
        in p.get("name", "").casefold()
    ]

# 최대 30개 검사
candidates = places[:30]

verified_places = []

progress = st.progress(0)

with st.spinner(
    "한국어 소개와 사진이 있는 관광지를 확인하는 중..."
):
    for index, place in enumerate(candidates):
        result = verify_place(
            place["xid"],
            place["name"],
            API_KEY
        )

        if result:
            verified_places.append(result)

        progress.progress(
            (index + 1) / len(candidates)
        )

        if len(verified_places) >= 10:
            break

progress.empty()

# ==========================================
# 10. 검증된 관광지 목록
# ==========================================

if not verified_places:
    st.warning(
        "현재 검색 범위에서 한국어 소개와 사진이 "
        "모두 있는 관광지를 찾지 못했습니다. "
        "검색 반경을 넓히거나 다른 도시를 선택해 주세요."
    )
    st.stop()

st.success(
    f"한국어 설명과 사진이 있는 관광지 "
    f"{len(verified_places)}곳을 찾았습니다!"
)

selected_index = st.selectbox(
    "관광지 선택",
    range(len(verified_places)),
    format_func=lambda i: verified_places[i]["name"]
)

selected_place = verified_places[selected_index]

# ==========================================
# 11. 관광지 상세 정보
# ==========================================

st.divider()

st.header(selected_place["name"])

left, right = st.columns(2)

with left:
    st.markdown("#### 📸 관광지 사진")

    st.image(
        selected_place["image"],
        caption=(
            f"사진 출처: "
            f"{selected_place['image_source']}"
        ),
        use_container_width=True
    )

with right:
    st.markdown("#### 🇰🇷 관광지 소개")

    st.write(
        selected_place["description"]
    )

    detail = selected_place["detail"]

    address = detail.get("address") or {}

    address_text = ", ".join(
        str(value)
        for value in address.values()
        if value
    )

    st.write(
        "**주소:**",
        address_text or "정보 없음"
    )

    if detail.get("wikipedia"):
        st.link_button(
            "Wikipedia 원문 보기",
            detail["wikipedia"]
        )

    if detail.get("otm"):
        st.link_button(
            "OpenTripMap 원문 보기",
            detail["otm"]
        )

# ==========================================
# 12. 관광지 위치
# ==========================================

coords = (
    selected_place["detail"].get("point")
    or {}
)

if "lat" in coords and "lon" in coords:
    st.markdown("#### 🗺️ 관광지 위치")

    st.map(
        [{
            "lat": coords["lat"],
            "lon": coords["lon"]
        }],
        zoom=13
    )

# ==========================================
# 13. 출처
# ==========================================

st.divider()

st.caption(
    "자료 출처: OpenTripMap API · "
    "한국어 Wikipedia · Wikimedia Commons"
)
