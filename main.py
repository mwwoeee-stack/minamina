import streamlit as st
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(
    page_title="세계 관광 명소 탐색",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 세계 관광 명소 탐색 시스템")
st.write("국가와 도시를 선택하여 주요 관광지를 탐색해 보세요.")

# 국가별 관광지 및 좌표
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
        },
        "니스": {
            "영국인 산책로": (43.6954, 7.2653),
            "니스 구시가지": (43.6975, 7.2755),
            "캐슬 힐": (43.6956, 7.2808),
            "마세나 광장": (43.6972, 7.2701),
            "니스 항구": (43.6959, 7.2865)
        }
    },
    "아르헨티나": {
        "부에노스아이레스": {
            "오벨리스코": (-34.6037, -58.3816),
            "카사 로사다": (-34.6081, -58.3702),
            "라 보카 카미니토": (-34.6383, -58.3625),
            "레콜레타 묘지": (-34.5875, -58.3930),
            "콜론 극장": (-34.6010, -58.3832)
        },
        "멘도사": {
            "독립광장": (-32.8895, -68.8458),
            "산마르틴 공원": (-32.8898, -68.8700),
            "세로 데 라 글로리아": (-32.8904, -68.8910),
            "에스파냐 광장": (-32.8934, -68.8438),
            "멘도사 중앙시장": (-32.8857, -68.8396)
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

# 관광지와 한국어 위키백과 문서 연결
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
    "영국인 산책로": "영국인 산책로",
    "니스 구시가지": None,
    "캐슬 힐": None,
    "마세나 광장": "마세나 광장",
    "니스 항구": None,
    "오벨리스코": "부에노스아이레스 오벨리스크",
    "카사 로사다": "카사 로사다",
    "라 보카 카미니토": "카미니토",
    "레콜레타 묘지": "레콜레타 묘지",
    "콜론 극장": "콜론 극장",
    "독립광장": None,
    "산마르틴 공원": "헤네랄 산마르틴 공원",
    "세로 데 라 글로리아": None,
    "에스파냐 광장": None,
    "멘도사 중앙시장": None,
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

HEADERS = {
    "User-Agent": "WorldTouristExplorer/1.0 (educational Streamlit project)",
    "Accept": "application/json"
}


@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_data(place_name):
    """
    한국어 위키백과에서 관광지의
    대표 사진, 한국어 설명, 문서 주소를 조회
    """

    title = WIKI_TITLES.get(place_name, place_name)

    # 정확히 대응하는 문서가 없는 관광지는
    # 다른 도시의 사진이나 설명을 잘못 가져오지 않음
    if title is None:
        return None, None, None

    api_url = "https://ko.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages|extracts|info",
        "titles": title,
        "pithumbsize": 900,
        "exintro": 1,
        "explaintext": 1,
        "exsectionformat": "plain",
        "inprop": "url",
        "redirects": 1
    }

    try:
        response = requests.get(
            api_url,
            params=params,
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page in pages.values():
            if "missing" in page:
                continue

            image_url = page.get(
                "thumbnail", {}
            ).get("source")

            description = page.get("extract", "").strip()

            # 너무 긴 소개는 앞부분만 사용
            if description:
                paragraphs = [
                    p.strip()
                    for p in description.split("\n")
                    if p.strip()
                ]

                description = "\n\n".join(paragraphs)

                if len(description) > 700:
                    shortened = description[:700]
                    last_space = shortened.rfind(" ")

                    if last_space > 400:
                        shortened = shortened[:last_space]

                    description = shortened.rstrip() + "…"

            page_url = page.get("fullurl")

            return image_url, description, page_url

    except (requests.RequestException, ValueError):
        pass

    return None, None, None


@st.cache_data(ttl=86400, show_spinner=False)
def download_image(image_url):
    """사진을 다운로드하고 정상 이미지인지 검사"""

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

    except (
        requests.RequestException,
        OSError,
        ValueError
    ):
        return None


# -------------------------
# 사용자 화면
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

# 위키백과 정보 가져오기
with st.spinner("관광지 정보를 불러오는 중입니다..."):
    image_url, description, page_url = get_wikipedia_data(
        place_name
    )

    image_data = download_image(image_url)

# 관광지 사진
st.subheader("📸 관광지 사진")

if image_data:
    st.image(
        image_data,
        caption=f"{place_name} - 위키백과",
        width="stretch"
    )
    st.caption("사진 출처: 위키백과 / Wikimedia Commons")
else:
    st.info(
        "현재 이 관광지의 사진을 불러올 수 없습니다."
    )

# 한국어 관광지 설명
st.subheader("📖 관광지 소개")

if description:
    st.write(description)

    if page_url:
        st.link_button(
            "📚 위키백과에서 자세히 보기",
            page_url
        )
else:
    st.info(
        "현재 이 관광지의 한국어 소개를 "
        "불러올 수 없습니다."
    )

# 지도
st.subheader("🗺️ 관광지 위치")

st.map(
    [{"lat": lat, "lon": lon}],
    zoom=13
)

st.caption(
    "관광지 위치는 등록된 좌표를 기준으로 표시됩니다. "
    "소개와 사진은 한국어 위키백과 자료를 활용합니다."
)
