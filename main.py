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
# Open-Meteo 날씨 조회
# -------------------------

WEATHER_DESCRIPTIONS = {
    0: "☀️ 맑음", 1: "🌤️ 대체로 맑음", 2: "⛅ 구름 조금", 3: "☁️ 흐림",
    45: "🌫️ 안개", 48: "🌫️ 서리 안개", 51: "🌦️ 약한 이슬비",
    53: "🌦️ 이슬비", 55: "🌧️ 강한 이슬비", 56: "🌧️ 어는 이슬비",
    57: "🌧️ 강한 어는 이슬비", 61: "🌦️ 약한 비", 63: "🌧️ 비",
    65: "🌧️ 강한 비", 66: "🌧️ 어는 비", 67: "🌧️ 강한 어는 비",
    71: "🌨️ 약한 눈", 73: "❄️ 눈", 75: "❄️ 강한 눈", 77: "🌨️ 눈 알갱이",
    80: "🌦️ 약한 소나기", 81: "🌧️ 소나기", 82: "⛈️ 강한 소나기",
    85: "🌨️ 약한 눈 소나기", 86: "❄️ 강한 눈 소나기",
    95: "⛈️ 뇌우", 96: "⛈️ 우박 동반 뇌우", 99: "⛈️ 강한 우박 동반 뇌우"
}


@st.cache_data(ttl=600, show_spinner=False)
def get_weather(lat, lon):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "weather_code,wind_speed_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "timezone": "auto",
            "forecast_days": 3
        },
        timeout=15
    )
    response.raise_for_status()
    data = response.json()
    if "current" not in data or "daily" not in data:
        raise ValueError("날씨 응답에 필요한 데이터가 없습니다.")
    return data


def weather_text(code):
    return WEATHER_DESCRIPTIONS.get(code, "🌡️ 날씨 정보")


# -------------------------
# 날씨에 따른 관광 적합도 분석
# -------------------------
# 실내 활동이 가능한 관광지를 별도로 분류합니다.
# 미분류 관광지는 야외 중심으로 간주하며, 이는 간단한 추천용 분류입니다.
INDOOR_PLACES = {
    "루브르 박물관", "롯데월드타워", "상하이 타워",
    "퀸 빅토리아 마켓", "플린더스 스트리트역"
}
MIXED_PLACES = {
    "창덕궁", "경복궁", "자금성", "금각사", "니조성",
    "노트르담 대성당", "사크레쾨르 대성당", "센소지",
    "메이지 신궁", "기요미즈데라", "후시미 이나리 신사",
    "남산서울타워", "도쿄 타워", "도쿄 스카이트리",
    "시드니 오페라 하우스", "타롱가 동물원"
}


def place_category(name):
    if name in INDOOR_PLACES:
        return "실내 중심"
    if name in MIXED_PLACES:
        return "실내·야외 혼합"
    return "야외 중심"


def suitability_score(name, rain, low_temp, high_temp, wind=None):
    """날씨 예보와 관광지 유형을 조합한 교육용 휴리스틱 점수."""
    category = place_category(name)
    score = 100
    reasons = []

    if rain is not None:
        if rain >= 70:
            penalty = {"실내 중심": 5, "실내·야외 혼합": 20, "야외 중심": 40}[category]
            reasons.append("강수확률이 매우 높음")
        elif rain >= 40:
            penalty = {"실내 중심": 0, "실내·야외 혼합": 10, "야외 중심": 25}[category]
            reasons.append("비가 올 가능성이 있음")
        else:
            penalty = 0
        score -= penalty

    # 하루 최고/최저기온은 시간별 체감온도와 다르므로 보수적으로 반영합니다.
    if high_temp is not None and high_temp >= 33:
        score -= 5 if category == "실내 중심" else 20
        reasons.append("폭염 가능성")
    if low_temp is not None and low_temp <= -5:
        score -= 5 if category == "실내 중심" else 15
        reasons.append("추위 주의")

    if wind is not None and wind >= 35:
        score -= 5 if category == "실내 중심" else 15
        reasons.append("강한 바람")

    return max(0, min(100, score)), reasons


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

# -------------------------
# 선택한 관광지의 현재 날씨 및 3일 예보
# -------------------------

st.divider()
st.subheader("🌤️ 관광지 날씨")
st.caption(f"{country} · {city} · {place_name}의 현지 날씨 (Open-Meteo 제공)")

try:
    with st.spinner("날씨 정보를 불러오는 중입니다..."):
        weather = get_weather(lat, lon)

    current = weather["current"]
    daily = weather["daily"]

    st.write(f"**현재 날씨:** {weather_text(current.get('weather_code'))}")
    col_temp, col_feels, col_humidity, col_wind = st.columns(4)
    col_temp.metric("현재 기온", f"{current['temperature_2m']} °C")
    col_feels.metric("체감 기온", f"{current['apparent_temperature']} °C")
    col_humidity.metric("습도", f"{current['relative_humidity_2m']} %")
    col_wind.metric("풍속", f"{current['wind_speed_10m']} km/h")

    st.caption(
        f"현지 관측·모델 기반 현재 날씨 기준: {current.get('time', '시간 정보 없음')} "
        f"({weather.get('timezone_abbreviation', '현지 시간')})"
    )

    st.markdown("#### 📅 3일간 날씨 예보")
    forecast_rows = []
    for i, date in enumerate(daily["time"]):
        rain = daily["precipitation_probability_max"][i]
        forecast_rows.append({
            "날짜 (현지 기준)": date,
            "날씨": weather_text(daily["weather_code"][i]),
            "최고 기온 (°C)": daily["temperature_2m_max"][i],
            "최저 기온 (°C)": daily["temperature_2m_min"][i],
            "최대 강수확률 (%)": rain if rain is not None else "정보 없음"
        })

    st.dataframe(forecast_rows, use_container_width=True, hide_index=True)

    today_rain = daily["precipitation_probability_max"][0]
    if today_rain is not None and today_rain >= 60:
        st.info("☔ 오늘은 강수확률이 높으니 우산과 실내 관광 대안을 준비해 보세요.")
    elif today_rain is not None and today_rain >= 30:
        st.info("🌂 오늘은 비가 올 가능성이 있으니 외출 전 예보를 다시 확인하세요.")
    else:
        st.info("🎒 여행 전 기온과 바람을 확인하고 적절한 복장을 준비하세요.")

    st.caption(
        "날씨는 약 10분간 저장되며 실제 관측과 차이가 있을 수 있습니다. "
        "강수확률은 해당 날짜의 시간별 예보 중 최댓값입니다."
    )

    st.divider()
    st.subheader("🌦️ 날씨 기반 여행 적합도 분석")
    chosen_day = st.selectbox(
        "분석할 날짜 (현지 기준)",
        options=list(range(len(daily["time"]))),
        format_func=lambda i: daily["time"][i],
        key="suitability_day"
    )
    rain = daily["precipitation_probability_max"][chosen_day]
    low = daily["temperature_2m_min"][chosen_day]
    high = daily["temperature_2m_max"][chosen_day]
    # 현재 풍속을 미래 날짜의 풍속으로 잘못 사용하지 않습니다.
    wind = current.get("wind_speed_10m") if chosen_day == 0 else None

    score, reasons = suitability_score(place_name, rain, low, high, wind)
    st.write(f"**관광지 유형:** {place_category(place_name)}")
    st.metric("여행 적합도 (자체 기준)", f"{score} / 100점")
    st.progress(score / 100)
    if score >= 80:
        st.success("👍 날씨 조건이 비교적 양호해 방문을 고려하기 좋아요.")
    elif score >= 60:
        st.info("🌂 방문할 수 있지만 날씨에 맞춘 준비가 필요해요.")
    else:
        st.warning("☔ 날씨의 영향을 받을 수 있어 실내 대안을 고려해 보세요.")

    if reasons:
        st.caption("점수에 반영된 요인: " + ", ".join(reasons))

    if score < 80 and place_category(place_name) != "실내 중심":
        alternatives = [
            name for name in places
            if name != place_name and place_category(name) == "실내 중심"
        ]
        if alternatives:
            st.write("**🏛️ 같은 도시의 실내 관광 대안:** " + ", ".join(alternatives))
        else:
            st.caption("현재 등록된 같은 도시 관광지 중 실내 중심 대안이 없습니다.")

    st.caption(
        "적합도는 강수확률·최고/최저기온·관광지 유형 등을 바탕으로 "
        "직접 정한 규칙으로 계산한 참고 점수입니다. 공식 관광 적합도나 "
        "방문 가능 여부를 의미하지 않습니다. 관광지 운영시간 및 휴관일은 별도 확인이 필요합니다."
    )
except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as error:
    st.warning("현재 날씨 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
    st.caption(f"날씨 조회 오류: {error}")
