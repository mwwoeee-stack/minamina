
import streamlit as st
import requests
from urllib.parse import urlparse, unquote

# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="세계 관광 명소 탐색",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 세계 관광 명소 탐색 시스템")
st.caption("OpenTripMap 관광지 데이터와 Wikipedia 정보를 활용합니다.")

# --------------------------------------------------
# 2. 국가 및 도시 데이터
# --------------------------------------------------

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

# --------------------------------------------------
# 3. OpenTripMap API 키
# --------------------------------------------------

try:
    API_KEY = st.secrets.get("OPENTRIPMAP_API_KEY", "")
except Exception:
    API_KEY = ""

if not API_KEY:
    st.info(
        "OpenTripMap API 키를 설정해 주세요. "
        "Streamlit Cloud의 App settings → Secrets에 "
        'OPENTRIPMAP_API_KEY = "발급받은키"를 입력하세요.'
    )
    st.stop()

BASE = "https://api.opentripmap.com/0.1/en/places"

# --------------------------------------------------
# 4. Wikipedia 대표 사진 검색 함수
# --------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_image(wikipedia_url):
    """
    Wikipedia 문서에서 대표 사진을 검색합니다.
    """

    if not wikipedia_url:
        return None

    parsed = urlparse(wikipedia_url)

    hostname = parsed.hostname or ""

    if not (
        hostname == "wikipedia.org"
        or hostname.endswith(".wikipedia.org")
    ):
        return None

    if "/wiki/" not in parsed.path:
        return None

    title = unquote(
        parsed.path.split("/wiki/", 1)[-1]
    )

    if not title:
        return None

    api_url = f"https://{hostname}/w/api.php"

    try:
        response = requests.get(
            api_url,
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": title,
                "pithumbsize": 900
            },
            headers={
                "User-Agent": (
                    "WorldTourismExplorer/1.0 "
                    "(educational tourism information project)"
                )
            },
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        pages = data.get(
            "query", {}
        ).get("pages", {})

        for page in pages.values():

            image_url = page.get(
                "thumbnail", {}
            ).get("source")

            if image_url:
                return image_url

    except (requests.RequestException, ValueError):
        return None

    return None


# --------------------------------------------------
# 5. 관광지 목록 가져오기
# --------------------------------------------------

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
        place
        for place in data
        if place.get("name", "").strip()
        and place.get("xid")
    ]


# --------------------------------------------------
# 6. 관광지 상세 정보 가져오기
# --------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def get_detail(xid, api_key):

    response = requests.get(
        f"{BASE}/xid/{xid}",
        params={
            "apikey": api_key
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# 7. 국가 및 도시 선택
# --------------------------------------------------

st.subheader("🔎 국가와 도시 선택")

a, b, c = st.columns([1, 1, 1])

with a:
    country = st.selectbox(
        "국가",
        list(CITIES)
    )

with b:
    city = st.selectbox(
        "도시",
        list(CITIES[country])
    )

with c:
    radius_km = st.slider(
        "검색 반경 (km)",
        3,
        30,
        10
    )

lat, lon = CITIES[country][city]

st.map(
    [{"lat": lat, "lon": lon}],
    zoom=10
)


# --------------------------------------------------
# 8. 관광지 데이터 검색
# --------------------------------------------------

try:

    with st.spinner("관광지 정보를 불러오는 중..."):

        places = get_places(
            lat,
            lon,
            radius_km * 1000,
            100,
            API_KEY
        )

except requests.RequestException as e:

    st.error(
        f"OpenTripMap 연결 오류: {e}"
    )

    st.stop()

except (ValueError, TypeError) as e:

    st.error(
        f"데이터 처리 오류: {e}"
    )

    st.stop()


# --------------------------------------------------
# 9. 관광지 검색 및 선택
# --------------------------------------------------

st.subheader(f"📍 {city} 관광 명소")

keyword = st.text_input(
    "관광지 이름 검색",
    placeholder="관광지 이름을 입력하세요 (영어 이름도 검색 가능)"
)

if keyword:

    places = [
        place
        for place in places
        if keyword.casefold()
        in place.get("name", "").casefold()
    ]

if not places:

    st.warning(
        "검색된 관광지가 없습니다. "
        "검색어 또는 검색 반경을 바꿔 보세요."
    )

    st.stop()


names = [
    f"{place['name']} ({place['xid']})"
    for place in places
]

selected = st.selectbox(
    "자세히 볼 관광지 선택",
    range(len(places)),
    format_func=lambda i: names[i]
)

place = places[selected]


# --------------------------------------------------
# 10. 관광지 상세 정보 조회
# --------------------------------------------------

try:

    detail = get_detail(
        place["xid"],
        API_KEY
    )

except (requests.RequestException, ValueError, TypeError) as e:

    st.error(
        f"상세 정보 연결 오류: {e}"
    )

    st.stop()


# --------------------------------------------------
# 11. 관광지 상세 화면
# --------------------------------------------------

st.divider()

place_name = detail.get("name") or place["name"]

st.header(place_name)

left, right = st.columns([1, 1])


# --------------------------------------------------
# 12. 관광지 대표 사진
# --------------------------------------------------

with left:

    st.markdown("#### 📸 관광지 대표 사진")

    # 1순위: OpenTripMap 사진
    image_url = (
        detail.get("preview") or {}
    ).get("source")

    image_source = "OpenTripMap"

    # 2순위: Wikipedia 사진
    if not image_url:

        image_url = get_wikipedia_image(
            detail.get("wikipedia")
        )

        image_source = "Wikipedia"

    # 사진 출력
    if image_url:

        try:

            st.image(
                image_url,
                caption=f"{place_name} | 출처: {image_source}",
                use_container_width=True
            )

        except Exception:

            st.info(
                "대표 사진을 불러오지 못했습니다."
            )

    else:

        st.info(
            "해당 관광지의 대표 사진을 찾지 못했습니다."
        )


# --------------------------------------------------
# 13. 관광지 설명
# --------------------------------------------------

with right:

    st.markdown("#### 관광지 소개")

    description = (
        (detail.get("wikipedia_extracts") or {}).get("text")
        or
        (detail.get("info") or {}).get("descr")
    )

    st.write(
        description
        or
        "제공된 설명이 없습니다. 아래 원문 링크를 확인해 보세요."
    )

    kinds = detail.get(
        "kinds",
        "정보 없음"
    )

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


# --------------------------------------------------
# 14. 관광지 위치 지도
# --------------------------------------------------

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


# --------------------------------------------------
# 15. 데이터 출처
# --------------------------------------------------

st.divider()

st.caption(
    "자료 출처: OpenTripMap API · Wikipedia | "
    "관광지별로 제공되는 정보와 사진은 다를 수 있습니다."
)
