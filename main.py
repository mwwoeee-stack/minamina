
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
    "OpenTripMap · Wikipedia · Wikimedia Commons 기반 관광 정보 서비스"
)

# ==========================================
# 2. 국가 및 도시 설정
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
# 3. API 키 설정
# ==========================================

try:
    API_KEY = st.secrets.get("OPENTRIPMAP_API_KEY", "")
except Exception:
    API_KEY = ""

if not API_KEY:
    st.warning(
        "Streamlit Cloud의 App settings → Secrets에 "
        "OPENTRIPMAP_API_KEY를 등록해 주세요."
    )
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
# 4. OpenTripMap 데이터 조회
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_places(lat, lon, radius, limit, api_key):
    response = requests.get(
        f"{BASE}/radius",
        params={
            "radius": radius,
            "lon": lon,
            "lat": lat,
            "rate": 2,
            "limit": limit,
            "format": "json",
            "apikey": api_key
        },
        timeout=20
    )
    response.raise_for_status()

    data = response.json()

    return [
        place for place in data
        if place.get("name", "").strip()
        and place.get("xid")
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
# 5. Wikipedia 사진 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_image(wikipedia_url):
    if not wikipedia_url:
        return None

    parsed = urlparse(wikipedia_url)
    hostname = parsed.hostname or ""

    if not hostname.endswith(".wikipedia.org"):
        return None

    if "/wiki/" not in parsed.path:
        return None

    title = unquote(parsed.path.split("/wiki/", 1)[1])

    try:
        response = requests.get(
            f"https://{hostname}/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": title,
                "pithumbsize": 1000
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        pages = response.json().get(
            "query", {}
        ).get("pages", {})

        for page in pages.values():
            image_url = page.get(
                "thumbnail", {}
            ).get("source")

            if image_url:
                return image_url

    except (requests.RequestException, ValueError):
        pass

    return None

# ==========================================
# 6. 한국어 Wikipedia 설명 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_korean_description(wikipedia_url):
    """
    관광지의 한국어 Wikipedia 문서를 찾아
    한국어 소개글을 가져옵니다.
    """

    if not wikipedia_url:
        return None

    parsed = urlparse(wikipedia_url)
    hostname = parsed.hostname or ""

    if not hostname.endswith(".wikipedia.org"):
        return None

    if "/wiki/" not in parsed.path:
        return None

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
                    "lllang": "ko",
                    "lllimit": 1
                },
                headers=HEADERS,
                timeout=15
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
            return None

        response = requests.get(
            "https://ko.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "titles": korean_title
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        pages = response.json().get(
            "query", {}
        ).get("pages", {})

        for page in pages.values():
            description = page.get(
                "extract", ""
            ).strip()

            if description:
                return description

    except (requests.RequestException, ValueError):
        pass

    return None

# ==========================================
# 7. Wikimedia Commons 사진 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_commons_image(place_name, city_name):
    if not place_name:
        return None

    queries = [
        f'"{place_name}" "{city_name}"',
        f'"{place_name}"'
    ]

    ignored_words = {
        "the", "and", "of", "in", "at",
        "de", "del", "la", "le", "el",
        "a", "an"
    }

    place_words = [
        word.lower()
        for word in place_name.replace("-", " ").split()
        if len(word) >= 4
        and word.lower() not in ignored_words
    ]

    if not place_words:
        return None

    for query in queries:
        try:
            response = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {query}",
                    "gsrnamespace": 6,
                    "gsrlimit": 15,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "iiurlwidth": 1000
                },
                headers=HEADERS,
                timeout=20
            )
            response.raise_for_status()

            pages = response.json().get(
                "query", {}
            ).get("pages", {})

            candidates = []

            for page in pages.values():
                title = page.get("title", "")
                title_lower = title.lower()

                if not title_lower.endswith(
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

                match_count = sum(
                    word in title_lower
                    for word in place_words
                )

                if match_count == 0:
                    continue

                score = match_count / len(place_words)

                if score < 0.5:
                    continue

                image_url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if image_url:
                    candidates.append({
                        "score": score,
                        "url": image_url,
                        "page_url": info.get("descriptionurl")
                    })

            if candidates:
                candidates.sort(
                    key=lambda item: item["score"],
                    reverse=True
                )
                return candidates[0]

        except (requests.RequestException, ValueError):
            continue

    return None

# ==========================================
# 8. 사진 자동 선택
# ==========================================

def find_place_image(detail, place_name, city_name):
    image_url = (
        detail.get("preview") or {}
    ).get("source")

    if image_url:
        return {
            "url": image_url,
            "source": "OpenTripMap",
            "source_url": detail.get("otm")
        }

    image_url = get_wikipedia_image(
        detail.get("wikipedia")
    )

    if image_url:
        return {
            "url": image_url,
            "source": "Wikipedia",
            "source_url": detail.get("wikipedia")
        }

    commons_image = get_commons_image(
        place_name,
        city_name
    )

    if commons_image:
        return {
            "url": commons_image["url"],
            "source": "Wikimedia Commons",
            "source_url": commons_image["page_url"]
        }

    return None

# ==========================================
# 9. 국가와 도시 선택
# ==========================================

st.subheader("🔎 국가와 도시 선택")

col1, col2, col3 = st.columns(3)

with col1:
    country = st.selectbox(
        "국가",
        list(CITIES.keys())
    )

with col2:
    city = st.selectbox(
        "도시",
        list(CITIES[country].keys())
    )

with col3:
    radius_km = st.slider(
        "검색 반경 (km)",
        min_value=3,
        max_value=30,
        value=10
    )

lat, lon = CITIES[country][city]

st.map(
    [{"lat": lat, "lon": lon}],
    zoom=10
)

# ==========================================
# 10. 관광지 목록 검색
# ==========================================

try:
    with st.spinner("관광지 정보를 불러오는 중..."):
        places = get_places(
            lat,
            lon,
            radius_km * 1000,
            100,
            API_KEY
        )
except (requests.RequestException, ValueError, TypeError) as e:
    st.error(f"관광지 데이터 연결 오류: {e}")
    st.stop()

st.subheader(f"📍 {city} 관광 명소")

keyword = st.text_input(
    "관광지 이름 검색",
    placeholder="관광지 이름을 입력하세요"
)

if keyword:
    places = [
        place for place in places
        if keyword.casefold()
        in place.get("name", "").casefold()
    ]

if not places:
    st.warning(
        "검색 결과가 없습니다. "
        "검색어 또는 검색 반경을 변경해 보세요."
    )
    st.stop()

# ==========================================
# 11. 관광지 선택
# ==========================================

names = [
    f"{place['name']} ({place['xid']})"
    for place in places
]

selected = st.selectbox(
    "자세히 볼 관광지 선택",
    range(len(places)),
    format_func=lambda index: names[index]
)

place = places[selected]

try:
    detail = get_detail(
        place["xid"],
        API_KEY
    )
except (requests.RequestException, ValueError, TypeError) as e:
    st.error(f"상세 정보 조회 오류: {e}")
    st.stop()

# ==========================================
# 12. 관광지 상세 정보
# ==========================================

st.divider()

place_name = detail.get("name") or place["name"]

st.header(place_name)

left, right = st.columns([1, 1])

# ==========================================
# 13. 관광지 사진
# ==========================================

with left:
    st.markdown("#### 📸 관광지 대표 사진")

    with st.spinner("사진을 검색하는 중..."):
        image_data = find_place_image(
            detail,
            place_name,
            city
        )

    if image_data:
        try:
            st.image(
                image_data["url"],
                caption=(
                    f"{place_name} | "
                    f"출처: {image_data['source']}"
                ),
                use_container_width=True
            )

            if image_data.get("source_url"):
                st.link_button(
                    "사진 출처 확인",
                    image_data["source_url"]
                )

        except Exception:
            st.info(
                "검색된 사진을 표시할 수 없습니다."
            )
    else:
        st.info(
            "해당 관광지의 대표 사진을 찾지 못했습니다."
        )

# ==========================================
# 14. 한국어 관광지 소개
# ==========================================

with right:
    st.markdown("#### 🇰🇷 관광지 소개")

    with st.spinner("한국어 소개를 불러오는 중..."):
        description = get_korean_description(
            detail.get("wikipedia")
        )

    if description:
        st.write(description)
    else:
        st.info(
            "이 관광지의 한국어 소개 자료가 "
            "아직 등록되어 있지 않습니다."
        )

    kinds = detail.get("kinds", "정보 없음")

    st.write(
        "**관광지 유형(원본 분류):**",
        kinds.replace(",", ", ")
    )

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
# 15. 관광지 위치 지도
# ==========================================

coords = detail.get("point") or {}

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
# 16. 데이터 출처
# ==========================================

st.divider()

st.caption(
    "데이터 출처: OpenTripMap API · Wikipedia · "
    "Wikimedia Commons | "
    "일부 관광지에는 한국어 소개나 사진이 "
    "제공되지 않을 수 있습니다."
)
