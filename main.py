
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

# 국가별 관광지와 좌표
from tourist_data import TOURIST_DATA

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

# 영어 위키백과 사진 대체 검색
EN_WIKI_TITLES = {
    "해동용궁사": "Haedong Yonggungsa",
    "아라시야마 대나무숲": "Arashiyama",
    "롬바드 스트리트": "Lombard Street (San Francisco)",
    "팰리스 오브 파인 아츠": "Palace of Fine Arts",
    "노트르담 대성당": "Notre-Dame de Paris",
    "플린더스 스트리트역": "Flinders Street railway station",
    "왕립 식물원": "Royal Botanic Gardens Victoria"
}

# 한국어 보충 설명
FALLBACK_DESCRIPTIONS = {
    "해동용궁사": "해동용궁사는 부산광역시 기장군의 바닷가에 자리한 사찰입니다. 바다와 맞닿은 절벽과 해안 풍경이 특징이며, 해돋이를 감상하기 위해 찾는 방문객도 많습니다.",
    "아라시야마 대나무숲": "아라시야마 대나무숲은 일본 교토 서쪽 아라시야마 지역의 대표적인 산책 명소입니다. 높게 자란 대나무 사이로 이어지는 길과 특유의 고요한 풍경으로 알려져 있습니다.",
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


# 위키백과 정보 조회
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


@st.cache_data(ttl=86400, show_spinner=False)
def get_wikipedia_data(place_name):
    title = WIKI_TITLES.get(place_name, place_name)

    image_url, description, page_url = query_wikipedia(
        title, "ko"
    )

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


def schedule_to_csv(rows):
    import csv
    output = BytesIO()
    from io import StringIO
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


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
    image_url, description, page_url = get_wikipedia_data(
        place_name
    )
    image_data = download_image(image_url)


# -------------------------
# 사진과 소개글 좌우 배치
# -------------------------

photo_col, info_col = st.columns(
    [1, 1.6],
    gap="large"
)

# 왼쪽: 작은 관광지 사진
with photo_col:
    st.subheader("📸 관광지 사진")

    if image_data:
        st.image(
            image_data,
            caption=place_name,
            use_container_width=True
        )
        st.caption(
            "사진 출처: 위키백과 / Wikimedia Commons"
        )
    else:
        st.info(
            "현재 이 관광지의 사진을 불러올 수 없습니다."
        )

# 오른쪽: 한국어 관광지 설명
with info_col:
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


# -------------------------
# 관광지 위치 지도
# -------------------------

st.divider()
st.subheader("🗺️ 관광지 위치")

st.map(
    [{"lat": lat, "lon": lon}],
    zoom=13
)

st.caption(
    "관광지 위치는 등록된 좌표를 기준으로 표시됩니다. "
    "사진은 위키백과 자료를 활용하며, "
    "일부 소개글은 보충 설명입니다."
)
