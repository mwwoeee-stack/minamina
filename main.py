
import streamlit as st
import requests

st.set_page_config(page_title='세계 관광 명소 탐색', page_icon='🌏', layout='wide')
st.title('🌏 세계 관광 명소 탐색 시스템')
st.caption('OpenTripMap 관광지 데이터와 Wikipedia 설명을 활용합니다.')

CITIES = {
    '대한민국': {'서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756)},
    '일본': {'도쿄': (35.6762, 139.6503), '교토': (35.0116, 135.7681)},
    '프랑스': {'파리': (48.8566, 2.3522), '니스': (43.7102, 7.2620)},
    '이탈리아': {'로마': (41.9028, 12.4964), '피렌체': (43.7696, 11.2558)},
    '영국': {'런던': (51.5072, -0.1276)},
    '미국': {'뉴욕': (40.7128, -74.0060), '샌프란시스코': (37.7749, -122.4194)},
    '스페인': {'바르셀로나': (41.3874, 2.1686), '마드리드': (40.4168, -3.7038)},
    '태국': {'방콕': (13.7563, 100.5018)},
    '호주': {'시드니': (-33.8688, 151.2093)},
}

try:
    API_KEY = st.secrets.get('OPENTRIPMAP_API_KEY', '')
except Exception:
    API_KEY = ''

if not API_KEY:
    st.info('먼저 OpenTripMap API 키를 설정해 주세요. Streamlit Cloud의 App settings → Secrets에 OPENTRIPMAP_API_KEY = "발급받은키"를 입력하면 됩니다.')
    st.stop()

BASE = 'https://api.opentripmap.com/0.1/en/places'

@st.cache_data(ttl=3600, show_spinner=False)
def get_places(lat, lon, radius, limit, api_key):
    response = requests.get(f'{BASE}/radius', params={
        'radius': radius, 'lon': lon, 'lat': lat,
        'rate': 2, 'limit': limit, 'format': 'json', 'apikey': api_key,
    }, timeout=20)
    response.raise_for_status()
    data = response.json()
    return [p for p in data if p.get('name', '').strip() and p.get('xid')]

@st.cache_data(ttl=3600, show_spinner=False)
def get_detail(xid, api_key):
    response = requests.get(f'{BASE}/xid/{xid}', params={'apikey': api_key}, timeout=20)
    response.raise_for_status()
    return response.json()

st.subheader('🔎 국가와 도시 선택')
a, b, c = st.columns([1, 1, 1])
with a:
    country = st.selectbox('국가', list(CITIES))
with b:
    city = st.selectbox('도시', list(CITIES[country]))
with c:
    radius_km = st.slider('검색 반경 (km)', 3, 30, 10)

lat, lon = CITIES[country][city]
st.map([{'lat': lat, 'lon': lon}], zoom=10)

try:
    with st.spinner('관광지 정보를 불러오는 중...'):
        places = get_places(lat, lon, radius_km * 1000, 100, API_KEY)
except requests.RequestException as e:
    st.error(f'OpenTripMap 연결 오류: {e}')
    st.stop()
except (ValueError, TypeError) as e:
    st.error(f'데이터 처리 오류: {e}')
    st.stop()

st.subheader(f'📍 {city} 관광 명소')
keyword = st.text_input('관광지 이름 검색', placeholder='관광지 이름을 입력하세요 (영어 이름도 검색 가능)')
if keyword:
    places = [p for p in places if keyword.casefold() in p.get('name', '').casefold()]

if not places:
    st.warning('검색된 관광지가 없습니다. 검색어 또는 검색 반경을 바꿔 보세요.')
    st.stop()

names = [f"{p['name']} ({p['xid']})" for p in places]
selected = st.selectbox('자세히 볼 관광지 선택', range(len(places)), format_func=lambda i: names[i])
place = places[selected]
try:
    detail = get_detail(place['xid'], API_KEY)
except (requests.RequestException, ValueError, TypeError) as e:
    st.error(f'상세 정보 연결 오류: {e}')
    st.stop()

st.divider()
st.header(detail.get('name') or place['name'])
left, right = st.columns([1, 1])
with left:
    image_url = detail.get('preview', {}).get('source')
    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.info('제공된 대표 사진이 없습니다.')
with right:
    st.markdown('#### 관광지 소개')
    description = detail.get('wikipedia_extracts', {}).get('text') or detail.get('info', {}).get('descr')
    st.write(description or '제공된 설명이 없습니다. 아래 원문 링크를 확인해 보세요.')
    st.write('**유형:**', detail.get('kinds', '정보 없음').replace(',', ', '))
    address = detail.get('address') or {}
    address_text = ', '.join(str(v) for v in address.values() if v)
    st.write('**주소:**', address_text or '정보 없음')
    if detail.get('wikipedia'):
        st.link_button('Wikipedia 원문 보기', detail['wikipedia'])
    if detail.get('otm'):
        st.link_button('OpenTripMap 원문 보기', detail['otm'])

coords = detail.get('point') or {}
if 'lat' in coords and 'lon' in coords:
    st.markdown('#### 🗺️ 관광지 위치')
    st.map([{'lat': coords['lat'], 'lon': coords['lon']}], zoom=13)

st.caption('자료 출처: OpenTripMap API · Wikipedia (장소별 정보 제공 여부는 다를 수 있습니다.)')
