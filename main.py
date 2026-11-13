
import streamlit as st
import requests

from urllib.parse import urlparse, unquote
from io import BytesIO
from PIL import Image

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
    "OpenTripMap · Wikipedia · Wikimedia Commons 기반 "
    "한국어 관광 정보 서비스"
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
    API_KEY = st.secrets.get(
        "OPENTRIPMAP_API_KEY", ""
    )
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error(
        "OpenTripMap API 키를 설정해 주세요."
    )
    st.stop()

BASE = "https://api.opentripmap.com/0.1/en/places"

COMMONS_API = (
    "https://commons.wikimedia.org/w/api.php"
)

HEADERS = {
    "User-Agent": (
        "WorldTourismExplorer/1.0 "
        "(educational tourism application)"
    )
}

# ==========================================
# 4. OpenTripMap 관광지 검색
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

    data = response.json()

    return [
        place
        for place in data
        if place.get("name", "").strip()
        and place.get("xid")
    ]


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

# ==========================================
# 5. 한국어 Wikipedia 설명 및 사진
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

    title = unquote(
        parsed.path.split("/wiki/", 1)[1]
    )

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
                timeout=12
            )

            response.raise_for_status()

            pages = response.json().get(
                "query", {}
            ).get("pages", {})

            korean_title = None

            for page in pages.values():

                links = page.get(
                    "langlinks", []
                )

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

            image_url = page.get(
                "thumbnail", {}
            ).get("source")

            name = page.get("title")

            if description:

                return (
                    description,
                    image_url,
                    name
                )

    except (requests.RequestException, ValueError):
        pass

    return None, None, None

# ==========================================
# 6. Wikimedia Commons 사진 검색
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_commons_images(place_name, city_name):

    if not place_name:
        return []

    ignored_words = {
        "the", "and", "of", "in", "at",
        "de", "del", "la", "le", "el",
        "a", "an"
    }

    words = [
        word.lower()
        for word in place_name.replace("-", " ").split()
        if len(word) >= 4
        and word.lower() not in ignored_words
    ]

    if not words:
        return []

    queries = [
        f'"{place_name}" "{city_name}"',
        f'"{place_name}"'
    ]

    candidates = []
    seen_urls = set()

    for query in queries:

        try:

            response = requests.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": (
                        f"filetype:bitmap {query}"
                    ),
                    "gsrnamespace": 6,
                    "gsrlimit": 15,
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

            for page in pages.values():

                title = page.get(
                    "title", ""
                ).lower()

                if not title.endswith(
                    (
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".webp"
                    )
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
                    word in title
                    for word in words
                )

                score = (
                    match_count / len(words)
                )

                if score < 0.6:
                    continue

                image_url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if image_url and image_url not in seen_urls:

                    seen_urls.add(image_url)

                    candidates.append({
                        "score": score,
                        "url": image_url
                    })

        except (requests.RequestException, ValueError):
            continue

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        item["url"]
        for item in candidates
    ]

# ==========================================
# 7. 실제 이미지 파일 검증
# ==========================================

@st.cache_data(ttl=86400, show_spinner=False)
def download_valid_image(image_url):
    """
    이미지 주소가 아니라 실제 파일을 다운로드하여
    정상적인 이미지인지 검사합니다.
    """

    if not image_url:
        return None

    try:

        response = requests.get(
            image_url,
            headers=HEADERS,
            timeout=12
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if not content_type.startswith("image/"):
            return None

        image_bytes = response.content

        if not image_bytes:
            return None

        # Pillow로 실제 이미지 파일 검사
        with Image.open(BytesIO(image_bytes)) as img:

            img.verify()

        # 검증 후 실제로 읽을 수 있는지도 확인
        with Image.open(BytesIO(image_bytes)) as img:

            img.load()

        return image_bytes

    except Exception:
        return None

# ==========================================
# 8. 관광지 검증
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def verify_place(
    xid,
    original_name,
    city_name,
    api_key
):

    try:

        detail = get_detail(
            xid,
            api_key
        )

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ):

        return None

    # 한국어 설명 검색
    description, wiki_image, korean_name = (
        get_wikipedia_data(
            detail.get("wikipedia")
        )
    )

    # 한국어 설명이 없으면 제외
    if not description:
        return None

    preview_image = (
        detail.get("preview") or {}
    ).get("source")

    image_candidates = [
        ("OpenTripMap", preview_image),
        ("Wikipedia", wiki_image)
    ]

    valid_image = None
    image_source = None

    # OpenTripMap 및 Wikipedia 사진 확인
    for source, image_url in image_candidates:

        image_bytes = download_valid_image(
            image_url
        )

        if image_bytes:

            valid_image = image_bytes
            image_source = source

            break

    # 앞의 사진이 실패하면 Commons에서 검색
    if valid_image is None:

        commons_images = get_commons_images(
            detail.get("name") or original_name,
            city_name
        )

        for image_url in commons_images:

            image_bytes = download_valid_image(
                image_url
            )

            if image_bytes:

                valid_image = image_bytes
                image_source = "Wikimedia Commons"

                break

    # 정상적인 사진이 없으면 관광지 제외
    if valid_image is None:
        return None

    return {
        "xid": xid,
        "name": korean_name or original_name,
        "original_name": original_name,
        "description": description,
        "image": valid_image,
        "image_source": image_source,
        "detail": detail
    }

# ==========================================
# 9. 국가 및 도시 선택
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
    [{
        "lat": lat,
        "lon": lon
    }],
    zoom=10
)

# ==========================================
# 10. 관광지 검색
# ==========================================

st.subheader(
    f"📍 {city} 관광 명소"
)

try:

    with st.spinner(
        "관광지 데이터를 불러오는 중..."
    ):

        places = get_places(
            lat,
            lon,
            radius_km * 1000,
            API_KEY
        )

except (
    requests.RequestException,
    ValueError,
    TypeError
) as e:

    st.error(
        f"관광지 검색 오류: {e}"
    )

    st.stop()

keyword = st.text_input(
    "관광지 이름 검색",
    placeholder="관광지 이름을 입력하세요"
)

if keyword:

    places = [
        place
        for place in places
        if keyword.casefold()
        in place.get(
            "name", ""
        ).casefold()
    ]

# 최대 30개 검사
candidates = places[:30]

verified_places = []

if candidates:

    progress = st.progress(0)

    with st.spinner(
        "한국어 소개와 정상적인 사진을 확인하는 중..."
    ):

        for index, place in enumerate(candidates):

            result = verify_place(
                place["xid"],
                place["name"],
                city,
                API_KEY
            )

            if result:
                verified_places.append(
                    result
                )

            progress.progress(
                (index + 1) / len(candidates)
            )

            if len(verified_places) >= 10:
                break

    progress.empty()

# ==========================================
# 11. 조건을 충족하는 관광지만 표시
# ==========================================

if not verified_places:

    st.warning(
        "현재 검색 범위에서 한국어 소개와 "
        "정상적인 사진이 모두 있는 관광지를 "
        "찾지 못했습니다. "
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
    format_func=lambda i: (
        verified_places[i]["name"]
    )
)

selected_place = verified_places[
    selected_index
]

# ==========================================
# 12. 관광지 상세 정보
# ==========================================

st.divider()

st.header(
    selected_place["name"]
)

left, right = st.columns(2)

# ==========================================
# 13. 관광지 사진 표시
# ==========================================

with left:

    st.markdown(
        "#### 📸 관광지 사진"
    )

    # 검증된 이미지 파일을 직접 표시
    st.image(
        selected_place["image"],
        caption=(
            f"사진 출처: "
            f"{selected_place['image_source']}"
        ),
        use_container_width=True
    )

# ==========================================
# 14. 한국어 관광지 소개
# ==========================================

with right:

    st.markdown(
        "#### 🇰🇷 관광지 소개"
    )

    st.write(
        selected_place["description"]
    )

    detail = selected_place["detail"]

    address = (
        detail.get("address") or {}
    )

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

coords = (
    selected_place["detail"].get("point")
    or {}
)

if "lat" in coords and "lon" in coords:

    st.markdown(
        "#### 🗺️ 관광지 위치"
    )

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
    "자료 출처: OpenTripMap API · "
    "한국어 Wikipedia · Wikimedia Commons"
)
