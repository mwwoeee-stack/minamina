
import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from math import radians, sin, cos, asin, sqrt, factorial
from itertools import permutations
import pydeck as pdk

st.set_page_config(
    page_title="세계 관광 명소 탐색",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 세계 관광 명소 탐색 시스템")
st.write("국가와 도시를 선택하여 주요 관광지를 탐색해 보세요.")

# 국가별 관광지와 좌표
TOURIST_DATA = {
    "대한민국": {
        "서울": {
            "경복궁": (37.5796, 126.9770),
            "남산서울타워": (37.5512, 126.9882),
            "롯데월드타워": (37.5125, 127.1025),
            "창덕궁": (37.5794, 126.9910),
            "광화문광장": (37.5729, 126.9769)
        },
        "부산": {
            "해운대해수욕장": (35.1587, 129.1604),
            "광안대교": (35.1477, 129.1288),
            "감천문화마을": (35.0975, 129.0106),
            "해동용궁사": (35.1884, 129.2232),
            "광안리해수욕장": (35.1532, 129.1186)
        }
    },
    "일본": {
        "도쿄": {
            "도쿄 타워": (35.6586, 139.7454),
            "도쿄 스카이트리": (35.7101, 139.8107),
            "센소지": (35.7148, 139.7967),
            "메이지 신궁": (35.6764, 139.6993),
            "시부야 스크램블 교차로": (35.6595, 139.7005)
        },
        "교토": {
            "기요미즈데라": (34.9949, 135.7850),
            "후시미 이나리 신사": (34.9671, 135.7727),
            "금각사": (35.0394, 135.7292),
            "아라시야마 대나무숲": (35.0170, 135.6713),
            "니조성": (35.0142, 135.7481)
        }
    },
    "중국": {
        "베이징": {
            "자금성": (39.9163, 116.3972),
            "천안문광장": (39.9055, 116.3976),
            "천단공원": (39.8822, 116.4065),
            "이화원": (39.9996, 116.2755),
            "팔달령 만리장성": (40.3598, 116.0200)
        },
        "상하이": {
            "동방명주탑": (31.2397, 121.4998),
            "와이탄": (31.2400, 121.4900),
            "예원": (31.2272, 121.4921),
            "상하이 타워": (31.2335, 121.5055),
            "난징루": (31.2348, 121.4745)
        }
    },
    "미국": {
        "뉴욕": {
            "자유의 여신상": (40.6892, -74.0445),
            "타임스 스퀘어": (40.7580, -73.9855),
            "센트럴 파크": (40.7829, -73.9654),
            "엠파이어 스테이트 빌딩": (40.7484, -73.9857),
            "브루클린 브리지": (40.7061, -73.9969)
        },
        "샌프란시스코": {
            "금문교": (37.8199, -122.4783),
            "알카트라즈섬": (37.8267, -122.4230),
            "피어 39": (37.8087, -122.4098),
            "롬바드 스트리트": (37.8021, -122.4187),
            "팰리스 오브 파인 아츠": (37.8029, -122.4484)
        }
    },
    "프랑스": {
        "파리": {
            "에펠탑": (48.8584, 2.2945),
            "루브르 박물관": (48.8606, 2.3376),
            "개선문": (48.8738, 2.2950),
            "노트르담 대성당": (48.8530, 2.3499),
            "사크레쾨르 대성당": (48.8867, 2.3431)
        }
    },
    "호주": {
        "시드니": {
            "시드니 오페라 하우스": (-33.8568, 151.2153),
            "하버 브리지": (-33.8523, 151.2108),
            "본다이 비치": (-33.8915, 151.2767),
            "달링 하버": (-33.8749, 151.2009),
            "타롱가 동물원": (-33.8433, 151.2410)
        },
        "멜버른": {
            "플린더스 스트리트역": (-37.8183, 144.9671),
            "페더레이션 광장": (-37.8179, 144.9690),
            "퀸 빅토리아 마켓": (-37.8076, 144.9568),
            "왕립 식물원": (-37.8304, 144.9803),
            "브라이턴 비치": (-37.9167, 144.9860)
        }
    }
}

# 한국어 위키백과 문서 제목
WIKI_TITLES = {
    "경복궁": "경복궁",
    "남산서울타워": "N서울타워",
    "롯데월드타워": "롯데월드타워",
    "창덕궁": "창덕궁",
    "광화문광장": "광화문광장",
    "해운대해수욕장": "해운대해수욕장",
    "광안대교": "광안대교",
    "감천문화마을": "감천문화마을",
    "해동용궁사": "해동 용궁사",
    "광안리해수욕장": "광안리해수욕장",
    "도쿄 타워": "도쿄 타워",
    "도쿄 스카이트리": "도쿄 스카이트리",
    "센소지": "센소지",
    "메이지 신궁": "메이지 신궁",
    "시부야 스크램블 교차로": "시부야 스크램블 교차로",
    "기요미즈데라": "기요미즈데라",
    "후시미 이나리 신사": "후시미 이나리 신사",
    "금각사": "금각사",
    "아라시야마 대나무숲": "아라시야마",
    "니조성": "니조성",
    "자금성": "자금성",
    "천안문광장": "톈안먼 광장",
    "천단공원": "천단",
    "이화원": "이화원",
    "팔달령 만리장성": "팔달령",
    "동방명주탑": "동방명주탑",
    "와이탄": "와이탄",
    "예원": "예원",
    "상하이 타워": "상하이 타워",
    "난징루": "난징루",
    "자유의 여신상": "자유의 여신상",
    "타임스 스퀘어": "타임스 스퀘어",
    "센트럴 파크": "센트럴 파크",
    "엠파이어 스테이트 빌딩": "엠파이어 스테이트 빌딩",
    "브루클린 브리지": "브루클린 교",
    "금문교": "금문교",
    "알카트라즈섬": "알카트라즈섬",
    "피어 39": "피어 39",
    "롬바드 스트리트": "롬바드 스트리트",
    "팰리스 오브 파인 아츠": "팰리스 오브 파인 아츠",
    "에펠탑": "에펠탑",
    "루브르 박물관": "루브르 박물관",
    "개선문": "에투알 개선문",
    "노트르담 대성당": "파리 노트르담 대성당",
    "사크레쾨르 대성당": "사크레쾨르 대성당",
    "시드니 오페라 하우스": "시드니 오페라 하우스",
    "하버 브리지": "시드니 하버 브리지",
    "본다이 비치": "본다이 비치",
    "달링 하버": "달링 하버",
    "타롱가 동물원": "타롱가 동물원",
    "플린더스 스트리트역": "플린더스 스트리트역",
    "페더레이션 광장": "페더레이션 광장",
    "퀸 빅토리아 마켓": "퀸 빅토리아 마켓",
    "왕립 식물원": "멜버른 왕립 식물원",
    "브라이턴 비치": "브라이턴 비치"
}

# 사진을 영어 위키백과에서 추가로 검색할 관광지
EN_WIKI_TITLES = {
    "해동용궁사": "Haedong Yonggungsa",
    "아라시야마 대나무숲": "Arashiyama",
    "엠파이어 스테이트 빌딩": "Empire State Building",
    "롬바드 스트리트": "Lombard Street (San Francisco)",
    "팰리스 오브 파인 아츠": "Palace of Fine Arts",
    "노트르담 대성당": "Notre-Dame de Paris",
    "플린더스 스트리트역": "Flinders Street railway station",
    "왕립 식물원": "Royal Botanic Gardens Victoria"
}

# 위키백과 설명이 없을 때 사용할 한국어 설명
FALLBACK_DESCRIPTIONS = {
    "해동용궁사": "해동용궁사는 부산광역시 기장군의 바닷가에 자리한 사찰입니다. 바다와 맞닿은 절벽과 해안 풍경이 특징이며, 해돋이를 감상하기 위해 찾는 방문객도 많습니다.",
    "아라시야마 대나무숲": "아라시야마 대나무숲은 일본 교토 서쪽 아라시야마 지역의 대표적인 산책 명소입니다. 높게 자란 대나무 사이로 이어지는 길과 특유의 고요한 풍경으로 알려져 있습니다.",
    "엠파이어 스테이트 빌딩": "엠파이어 스테이트 빌딩은 미국 뉴욕 맨해튼에 있는 대표적인 초고층 건축물입니다. 아르데코 양식의 외관과 도시 전경을 조망할 수 있는 전망대로 유명합니다.",
    "롬바드 스트리트": "롬바드 스트리트는 미국 샌프란시스코에 있는 거리로, 특히 러시안 힐의 급경사 구간에 조성된 여러 개의 굽은 길로 유명합니다.",
    "팰리스 오브 파인 아츠": "팰리스 오브 파인 아츠는 미국 샌프란시스코 마리나 지구에 있는 기념비적인 건축물입니다. 고전적인 원형 돔과 열주, 연못이 어우러져 있습니다.",
    "노트르담 대성당": "파리 노트르담 대성당은 프랑스 파리 시테섬에 자리한 고딕 양식의 대성당입니다. 섬세한 조각과 장미창, 두 개의 종탑으로 유명합니다.",
    "플린더스 스트리트역": "플린더스 스트리트역은 호주 멜버른 도심의 주요 철도역입니다. 노란색 외벽과 돔, 시계가 있는 역사 건물은 멜버른의 상징입니다.",
    "왕립 식물원": "멜버른 왕립 식물원은 호주 멜버른에 위치한 넓은 식물원입니다. 다양한 식물과 정원, 산책로, 호수가 조성되어 있습니다."
}

HEADERS = {
    "User-Agent": "WorldTouristExplorer/1.0 (educational project)",
    "Accept": "application/json"
}


# 위키백과 API
@st.cache_data(ttl=86400, show_spinner=False)
def query_wikipedia(title, language="ko"):
    if not title:
        return None, None, None

    try:
        response = requests.get(
            f"https://{language}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages|extracts|info",
                "titles": title,
                "pithumbsize": 900,
                "exintro": 1,
                "explaintext": 1,
                "inprop": "url",
                "redirects": 1
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", {})

        for page in pages.values():
            if "missing" in page:
                continue

            return (
                page.get("thumbnail", {}).get("source"),
                page.get("extract", "").strip(),
                page.get("fullurl")
            )

    except (requests.RequestException, ValueError):
        pass

    return None, None, None


# 엠파이어 스테이트 빌딩 사진 추가 검색
@st.cache_data(ttl=86400, show_spinner=False)
def get_empire_commons_photo():
    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "titles": "File:The Empire State Building.jpg",
                "iiprop": "url",
                "iiurlwidth": 800
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", {})

        for page in pages.values():
            info = page.get("imageinfo", [])
            if info:
                return info[0].get("thumburl") or info[0].get("url")

    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass

    return None


@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_data(place_name):
    title = WIKI_TITLES.get(place_name, place_name)

    image_url, description, page_url = query_wikipedia(title, "ko")

    if not description:
        description = FALLBACK_DESCRIPTIONS.get(place_name)

    if not image_url and place_name in EN_WIKI_TITLES:
        en_image, _, en_page = query_wikipedia(
            EN_WIKI_TITLES[place_name], "en"
        )
        image_url = en_image

        if not page_url:
            page_url = en_page

    if description and len(description) > 700:
        shortened = description[:700]
        last_space = shortened.rfind(" ")

        if last_space > 400:
            shortened = shortened[:last_space]

        description = shortened.rstrip() + "…"

    return image_url, description, page_url


@st.cache_data(ttl=86400, show_spinner=False)
def download_image(image_url):
    if not image_url:
        return None

    try:
        response = requests.get(
            image_url,
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if not content_type.startswith("image/"):
            return None

        image = Image.open(BytesIO(response.content))
        image.load()

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        output = BytesIO()
        image.save(output, format="PNG")

        return output.getvalue()

    except (requests.RequestException, OSError, ValueError):
        return None


# -------------------------
# 관광지 검색 화면
# -------------------------

st.subheader("🔎 관광지 검색")

col1, col2 = st.columns(2)

with col1:
    country = st.selectbox(
        "국가 선택",
        list(TOURIST_DATA.keys())
    )

with col2:
    city = st.selectbox(
        "도시 선택",
        list(TOURIST_DATA[country].keys()),
        key=f"city_{country}"
    )

places = TOURIST_DATA[country][city]

st.subheader(f"📍 {city}의 주요 관광지")

place_name = st.selectbox(
    "관광지 선택",
    list(places.keys()),
    key=f"place_{country}_{city}"
)

lat, lon = places[place_name]

st.divider()

st.header(f"📍 {place_name}")
st.write(f"**국가:** {country}")
st.write(f"**도시:** {city}")

with st.spinner("관광지 정보를 불러오는 중입니다..."):
    image_url, description, page_url = get_wikipedia_data(place_name)
    image_data = download_image(image_url)

    if not image_data and place_name == "엠파이어 스테이트 빌딩":
        commons_url = get_empire_commons_photo()
        image_data = download_image(commons_url)

        if image_data:
            image_url = commons_url

st.subheader("📸 관광지 사진")

if image_data:
    st.image(
        image_data,
        caption=f"{place_name} - 위키백과 / Wikimedia Commons",
        use_container_width=True
    )
    st.caption("사진 출처: 위키백과 / Wikimedia Commons")
else:
    st.info("현재 이 관광지의 사진을 불러올 수 없습니다.")

st.subheader("📖 관광지 소개")

if description:
    st.write(description)

    if page_url:
        st.link_button(
            "📚 위키백과에서 자세히 보기",
            page_url
        )
else:
    st.info("현재 이 관광지의 한국어 소개를 불러올 수 없습니다.")

st.subheader("🗺️ 관광지 위치")
st.map([{"lat": lat, "lon": lon}], zoom=13)

st.caption(
    "관광지 위치는 등록된 좌표를 기준으로 표시됩니다. "
    "사진은 위키백과 자료를 활용하며, 일부 소개글은 보충 설명입니다."
)


# -------------------------
# 수학적 최적 여행 경로 계산
# -------------------------

def haversine_km(point_a, point_b):
    """두 관광지 사이의 대권거리(km)"""
    lat1, lon1 = point_a
    lat2, lon2 = point_b

    radius = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))

    return 2 * radius * asin(sqrt(a))


def route_distance(route, coordinates, return_to_start=False):
    total = sum(
        haversine_km(coordinates[a], coordinates[b])
        for a, b in zip(route, route[1:])
    )

    if return_to_start and len(route) > 1:
        total += haversine_km(
            coordinates[route[-1]],
            coordinates[route[0]]
        )

    return total


def find_shortest_route(selected, coordinates, start, return_to_start=False):
    """모든 방문 순서를 비교하는 완전탐색 알고리즘"""
    remaining = [name for name in selected if name != start]

    best_route = None
    best_distance = float("inf")

    for order in permutations(remaining):
        candidate = (start,) + order

        distance = route_distance(
            candidate,
            coordinates,
            return_to_start
        )

        if distance < best_distance:
            best_distance = distance
            best_route = candidate

    return list(best_route), best_distance


# -------------------------
# 최적 경로 추천 화면
# -------------------------

st.divider()
st.header("🧭 최적 여행 경로 추천")

st.write(
    "방문할 관광지를 선택하면 "
    "이동 거리의 합이 가장 짧은 순서를 계산합니다."
)

selected_places = st.multiselect(
    "방문할 관광지 선택 (2곳 이상)",
    options=list(places.keys()),
    default=list(places.keys())[:3],
    key=f"route_places_{country}_{city}"
)

if len(selected_places) < 2:
    st.info("관광지를 2곳 이상 선택해 주세요.")

else:
    start_place = st.selectbox(
        "출발 관광지 선택",
        options=selected_places,
        key=f"route_start_{country}_{city}"
    )

    return_to_start = st.checkbox(
        "마지막 관광지 방문 후 출발지로 돌아오기",
        value=False,
        key=f"route_roundtrip_{country}_{city}"
    )

    if st.button("🔍 최단 경로 계산하기", type="primary"):

        best_route, best_distance = find_shortest_route(
            selected_places,
            places,
            start_place,
            return_to_start
        )

        if return_to_start:
            display_route = best_route + [best_route[0]]
        else:
            display_route = best_route

        st.success("최적 경로 계산이 완료되었습니다!")

        st.metric(
            "총 대권거리",
            f"{best_distance:.2f} km"
        )

        st.subheader("📌 추천 방문 순서")
        st.write(" → ".join(display_route))

        st.subheader("📏 구간별 거리")

        for i, (a, b) in enumerate(
            zip(display_route, display_route[1:]),
            start=1
        ):
            distance = haversine_km(places[a], places[b])

            st.write(
                f"{i}. {a} → {b}: **{distance:.2f} km**"
            )

        # 지도에 표시할 관광지 좌표
        route_points = [
            {
                "name": name,
                "order": str(i + 1),
                "lat": places[name][0],
                "lon": places[name][1]
            }
            for i, name in enumerate(best_route)
        ]

        # 관광지 사이를 연결하는 선
        line_points = [
            {
                "source": [places[a][1], places[a][0]],
                "target": [places[b][1], places[b][0]]
            }
            for a, b in zip(display_route, display_route[1:])
        ]

        center_lat = (
            sum(p["lat"] for p in route_points)
            / len(route_points)
        )

        center_lon = (
            sum(p["lon"] for p in route_points)
            / len(route_points)
        )

        layers = [
            pdk.Layer(
                "LineLayer",
                line_points,
                get_source_position="source",
                get_target_position="target",
                get_color=[20, 115, 230, 220],
                get_width=5,
                width_min_pixels=3,
                pickable=False
            ),
            pdk.Layer(
                "ScatterplotLayer",
                route_points,
                get_position="[lon, lat]",
                get_fill_color=[230, 65, 65, 230],
                get_radius=100,
                radius_min_pixels=9,
                pickable=True
            ),
            pdk.Layer(
                "TextLayer",
                route_points,
                get_position="[lon, lat]",
                get_text="order",
                get_size=17,
                get_color=[255, 255, 255],
                get_alignment_baseline="center",
                get_text_anchor="middle",
                pickable=False
            )
        ]

        st.subheader("🗺️ 최적 경로 지도")

        st.pydeck_chart(
            pdk.Deck(
                layers=layers,
                initial_view_state=pdk.ViewState(
                    latitude=center_lat,
                    longitude=center_lon,
                    zoom=10,
                    pitch=0
                ),
                tooltip={"text": "{order}. {name}"},
                map_style="light"
            ),
            use_container_width=True
        )

        st.caption(
            "빨간 원의 숫자는 방문 순서이며, "
            "파란 선은 관광지 사이를 연결합니다."
        )

        with st.expander("📐 경로 계산에 사용한 수학 원리"):
            st.write(
                "하버사인 공식을 사용해 "
                "두 지점의 위도와 경도로 대권거리를 계산합니다."
            )

            st.latex(
                r"d=2R\arcsin\left("
                r"\sqrt{\sin^2\frac{\Delta\phi}{2}"
                r"+\cos\phi_1\cos\phi_2"
                r"\sin^2\frac{\Delta\lambda}{2}}"
                r"\right)"
            )

            st.write("R = 6371 km, φ = 위도, λ = 경도")

            st.write(
                "출발지를 고정한 뒤 나머지 관광지의 "
                "모든 방문 순서를 비교하는 완전탐색 방식입니다."
            )

            count = factorial(len(selected_places) - 1)

            st.write(
                f"이번 계산에서 비교한 방문 순서는 "
                f"**{count:,}개**입니다."
            )

        st.warning(
            "이 경로는 지구 표면의 최단 거리(대권거리)를 "
            "최소화한 결과입니다. 실제 도로·도보 경로, "
            "교통수단, 바다와 강 등의 장애물 및 "
            "이동 시간은 반영되지 않습니다."
        )
