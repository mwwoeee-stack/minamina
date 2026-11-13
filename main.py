
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
    "OpenTripMap · Wikipedia · Wikimedia Commons 데이터를 활용합니다."
)

CITIES = {
    "대한민국": {
        "서울": (37.5665, 126.9780),
        "부산": (35.1796, 129.0756)
    },
    "일본": {
        "도쿄": (35.6762, 139.6503),
        "교토": (35.0116, 135.7681)
    },
    "프랑스": {
        "파리": (48.8566, 2.3522),
        "니스": (43.7102, 7.2620)
    },
    "이탈리아": {
        "로마": (41.9028, 12.4964),
        "피렌체": (43.7696, 11.2558)
    },
    "영국": {
        "런던": (51.5072, -0.1276)
    },
    "미국": {
        "뉴욕": (40.7128, -74.0060),
        "샌프란시스코": (37.7749, -122.4194)
    },
    "스페인": {
        "바르셀로나": (41.3874, 2.1686),
        "마드리드": (40.4168, -3.7038)
    },
    "태국": {
        "방콕": (13.7563, 100.5018)
    },
    "호주": {
        "시드니": (-33.8688, 151.2093)
    }
}

# ==========================================
# 2. API 설정
# ==========================================

try:
    API_KEY = st.secrets.get("OPENTRIPMAP_API_KEY", "")
except Exception:
    API_KEY = ""

if not API_KEY:
    st.warning(
        "Streamlit Cloud의 App settings → Secrets에서 "
        "OPENTRIPMAP_API_KEY를 설정해 주세요."
    )
    st.stop()

BASE = "https://api.opentripmap.com/0.1/en/places"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "WorldTourismExplorer/1.0 "
        "(educational project; Wikimedia API image lookup)"
    )
}

# ==========================================
# 3. OpenTripMap 관광지 검색
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
# 4. Wikipedia 대표 사진 검색
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
# 5. Wikimedia Commons 사진 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_commons_image(place_name, city_name):
    """
    관광지 이름과 도시명을 이용해
    Wikimedia Commons에서 사진을 검색합니다.

    검색 결과의 파일명과 관광지 이름을 비교하여
    관련성이 낮은 이미지는 제외합니다.
    """

    if not place_name:
        return None

    search_queries = [
        f'"{place_name}" "{city_name}"',
        f'"{place_name}"'
    ]

    # 이미지 파일만 검색
    allowed_extensions = (
        ".jpg", ".jpeg", ".png", ".webp"
    )

    # 지나치게 일반적인 단어는 비교에서 제외
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

    for search_query in search_queries:
        try:
            response = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": (
                        f"filetype:bitmap {search_query}"
                    ),
                    "gsrnamespace": 6,
                    "gsrlimit": 15,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime|extmetadata",
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
                    allowed_extensions
                ):
                    continue

                image_info = (
                    page.get("imageinfo") or [{}]
                )[0]

                mime = image_info.get("mime", "")

                if not mime.startswith("image/"):
                    continue

                # 파일명에 관광지 이름이 얼마나 포함되는지 확인
                match_count = sum(
                    word in title_lower
                    for word in place_words
                )

                # 관광지 이름과 일치하는 단어가 없으면 제외
                if match_count == 0:
                    continue

                score = match_count / len(place_words)

                # 이름의 절반 이상 일치해야 사용
                if score < 0.5:
                    continue

                image_url = (
                    image_info.get("thumburl")
                    or image_info.get("url")
                )

                if not image_url:
                    continue

                candidates.append({
                    "score": score,
                    "url": image_url,
                    "title": title,
                    "page_url": (
                        image_info.get("descriptionurl")
                    )
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
# 6. 사진 자동 선택
# ==========================================

def find_place_image(detail, place_name, city_name):
    """
    1. OpenTripMap
    2. Wikipedia
    3. Wikimedia Commons
    순서로 사진을 검색합니다.
    """

    preview = detail.get("preview") or {}
    image_url = preview.get("source")

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
# 7. 국가와 도시 선택
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
# 8. 관광지 목록 불러오기
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
# 9. 관광지 선택
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
# 10. 관광지 상세 정보
# ==========================================

st.divider()

place_name = detail.get("name") or place["name"]

st.header(place_name)

left, right = st.columns([1, 1])

# ==========================================
# 11. 사진 표시
# ==========================================

with left:
    st.markdown("#### 📸 관광지 대표 사진")

    with st.spinner("관광지 사진 검색 중..."):
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
                    f"사진 출처: {image_data['source']}"
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
            "해당 관광지와 일치하는 사진을 찾지 못했습니다."
        )

# ==========================================
# 12. 관광지 설명 및 주소
# ==========================================

with right:
    st.markdown("#### 관광지 소개")

    description = (
        (detail.get("wikipedia_extracts") or {}).get("text")
        or
        (detail.get("info") or {}).get("descr")
    )

    st.write(
        description
        or "제공된 관광지 설명이 없습니다."
    )

    kinds = detail.get("kinds", "정보 없음")

    st.write(
        "**유형:**",
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
# 13. 관광지 위치 지도
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
# 14. 출처
# ==========================================

st.divider()

st.caption(
    "데이터 출처: OpenTripMap API · Wikipedia · "
    "Wikimedia Commons | "
    "사진은 자동 검색 결과이므로 실제 관광지와 "
    "일치하는지 확인이 필요합니다."
)
