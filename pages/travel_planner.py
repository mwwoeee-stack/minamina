import csv
import html
from datetime import datetime, timedelta
from io import StringIO
from itertools import permutations
from math import factorial

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from tourist_data import TOURIST_DATA

st.set_page_config(page_title="실제 이동 경로 여행 플래너", page_icon="🧭", layout="wide")
st.title("🧭 실제 이동 경로 기반 여행 플래너")
st.caption("도로·보행로 데이터를 이용해 방문 순서를 최적화합니다. 실제 교통 상황 및 대중교통 시간은 반영되지 않습니다.")

API_ROOT = "https://api.openrouteservice.org"
PROFILES = {"🚶 도보": "foot-walking", "🚗 자동차": "driving-car"}


def api_key():
    try:
        return st.secrets.get("ORS_API_KEY", "")
    except (FileNotFoundError, KeyError):
        return ""


@st.cache_data(ttl=3600, show_spinner=False)
def get_matrix(profile, names_and_coords, key):
    """선택 지점 간 실제 이동거리(m)·이동시간(s) 행렬 조회."""
    locations = [[lon, lat] for _, lat, lon in names_and_coords]
    resp = requests.post(
        f"{API_ROOT}/v2/matrix/{profile}",
        headers={"Authorization": key, "Content-Type": "application/json"},
        json={"locations": locations, "metrics": ["distance", "duration"], "resolve_locations": False},
        timeout=45,
    )
    if not resp.ok:
        raise ValueError(f"경로 행렬 조회 실패 (HTTP {resp.status_code}): {resp.text[:350]}")
    data = resp.json()
    distances, durations = data.get("distances"), data.get("durations")
    n = len(locations)
    if not distances or not durations or len(distances) != n or len(durations) != n:
        raise ValueError("경로 API가 완전한 거리·시간 행렬을 반환하지 않았습니다.")
    return distances, durations


@st.cache_data(ttl=3600, show_spinner=False)
def get_road_geometry(profile, start, end, key):
    """한 구간의 실제 도로 경로 좌표 반환 (Folium의 위도, 경도 순서)."""
    resp = requests.post(
        f"{API_ROOT}/v2/directions/{profile}/geojson",
        headers={"Authorization": key, "Content-Type": "application/json"},
        json={"coordinates": [[start[1], start[0]], [end[1], end[0]]]},
        timeout=45,
    )
    if not resp.ok:
        raise ValueError(f"상세 경로 조회 실패 (HTTP {resp.status_code}): {resp.text[:250]}")
    features = resp.json().get("features", [])
    if not features:
        raise ValueError("상세 도로 경로 좌표가 없습니다.")
    coords = features[0]["geometry"]["coordinates"]
    return [[lat, lon] for lon, lat, *rest in coords]


def route_total(route, index, matrix):
    total = 0.0
    for a, b in zip(route, route[1:]):
        value = matrix[index[a]][index[b]]
        if value is None:
            return float("inf")
        total += value
    return total


def optimal_route(names, start, durations, return_to_start):
    """기존 완전탐색 유지: 총 이동시간 최소 경로 탐색."""
    index = {name: i for i, name in enumerate(names)}
    best_route, best_time = None, float("inf")
    for order in permutations(name for name in names if name != start):
        route = [start, *order]
        full = route + [start] if return_to_start else route
        seconds = route_total(full, index, durations)
        if seconds < best_time:
            best_route, best_time = route, seconds
    if best_route is None:
        raise ValueError("선택한 관광지를 모두 연결하는 경로를 찾지 못했습니다. 다른 관광지 또는 이동 수단을 선택해 주세요.")
    return best_route, best_time


def csv_bytes(rows):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return ("\ufeff" + output.getvalue()).encode("utf-8")


country = st.selectbox("국가 선택", list(TOURIST_DATA), key="road_country")
city = st.selectbox("도시 선택", list(TOURIST_DATA[country]), key=f"road_city_{country}")
places = TOURIST_DATA[country][city]
mode = st.radio("이동 수단", list(PROFILES), horizontal=True)
profile = PROFILES[mode]
selected = st.multiselect(
    "방문할 관광지 선택 (2곳 이상)", list(places),
    default=list(places)[:3], key=f"road_places_{country}_{city}",
)

if len(selected) < 2:
    st.info("관광지를 2곳 이상 선택해 주세요.")
    st.stop()

start = st.selectbox("출발 관광지", selected, key=f"road_start_{country}_{city}")
roundtrip = st.checkbox("마지막 관광지 방문 후 출발지로 돌아오기", key=f"road_round_{country}_{city}")

key = api_key()
if not key:
    st.error("OpenRouteService API 키가 없습니다. Streamlit Cloud → App settings → Secrets에 ORS_API_KEY를 등록해 주세요.")
    st.code('ORS_API_KEY = "여기에_발급받은_API_키"', language="toml")
    st.stop()

settings = (country, city, mode, tuple(selected), start, roundtrip)
if st.button("🔍 실제 이동 경로 최적화하기", type="primary"):
    st.session_state["road_requested"] = settings

if st.session_state.get("road_requested") != settings:
    st.info("조건을 선택한 다음 '실제 이동 경로 최적화하기'를 눌러 주세요.")
    st.stop()

names_and_coords = tuple((name, *places[name]) for name in selected)
try:
    with st.spinner("실제 도로·보행로 거리와 시간을 조회하고 있습니다..."):
        distances, durations = get_matrix(profile, names_and_coords, key)
        best, best_seconds = optimal_route(selected, start, durations, roundtrip)
except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
    st.error(f"실제 경로를 계산하지 못했습니다: {exc}")
    st.info("일부 국가나 섬 관광지는 도보·자동차로 연결되지 않을 수 있습니다. 다른 장소나 이동 수단을 선택해 주세요.")
    st.stop()

index = {name: i for i, name in enumerate(selected)}
best_full = best + [start] if roundtrip else best
normal = [start] + [name for name in selected if name != start]
normal_full = normal + [start] if roundtrip else normal
best_m = route_total(best_full, index, distances)
normal_m = route_total(normal_full, index, distances)
normal_s = route_total(normal_full, index, durations)

st.success("실제 이동 경로를 기반으로 최적 방문 순서를 계산했습니다.")
a, b = st.columns(2)
a.metric("최적 경로 실제 이동거리", f"{best_m / 1000:.2f} km")
b.metric("예상 총 이동시간", f"{best_seconds / 60:.0f}분")
st.subheader("📌 추천 방문 순서")
st.write(" → ".join(best_full))
st.caption("총 이동시간 최소 기준으로 최적화합니다. 최단 거리 경로와는 다를 수 있습니다.")

st.subheader("📏 구간별 실제 이동거리 및 시간")
for a_name, b_name in zip(best_full, best_full[1:]):
    d = distances[index[a_name]][index[b_name]]
    t = durations[index[a_name]][index[b_name]]
    st.write(f"{a_name} → {b_name}: **{d / 1000:.2f} km · 약 {t / 60:.0f}분**")

st.subheader("🗺️ 실제 도로·보행로 최적 경로 지도")
center_lat = sum(places[name][0] for name in best) / len(best)
center_lon = sum(places[name][1] for name in best) / len(best)
route_map = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="OpenStreetMap", control_scale=True)
all_geometry = []
map_errors = []
for a_name, b_name in zip(best_full, best_full[1:]):
    try:
        segment = get_road_geometry(profile, places[a_name], places[b_name], key)
        folium.PolyLine(segment, color="#1473e6", weight=5, opacity=0.85,
                        tooltip=f"{a_name} → {b_name}").add_to(route_map)
        all_geometry.extend(segment)
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        map_errors.append(f"{a_name} → {b_name}: {exc}")
for order, name in enumerate(best, 1):
    lat, lon = places[name]
    popup = f"<b>🚩 {html.escape(name)}</b><br>방문 순서: {order}번째"
    folium.Marker([lat, lon], popup=folium.Popup(popup, max_width=280),
                  tooltip=f"{order}. {name}",
                  icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(route_map)
route_map.fit_bounds(all_geometry or [list(places[name]) for name in best], padding=(35, 35))
st_folium(route_map, height=500, use_container_width=True,
          key=f"road_map_{country}_{city}_{profile}", returned_objects=[])
if map_errors:
    st.warning("일부 구간의 도로 선을 표시하지 못했습니다. 직선으로 대체하지 않았습니다.")
    with st.expander("상세 오류"):
        st.write("\n".join(map_errors))
st.caption("빨간 깃발을 클릭하면 방문 순서를 확인할 수 있습니다. 파란 선은 경로 API에서 받은 실제 도로·보행로 경로입니다.")

st.divider()
st.subheader("📊 일반 경로와 최적 경로 비교")
st.caption("일반 경로는 출발지를 먼저 방문한 뒤, 관광지 선택 목록 순서대로 방문하는 경로입니다.")
if normal_m == float("inf"):
    st.warning("일반 경로의 일부 구간은 이동할 수 없어 거리 비교가 불가능합니다.")
else:
    saved_km = max(0.0, (normal_m - best_m) / 1000)
    saved_pct = saved_km / (normal_m / 1000) * 100 if normal_m else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("일반 경로", f"{normal_m / 1000:.2f} km")
    c2.metric("최적 경로", f"{best_m / 1000:.2f} km")
    c3.metric("거리 차이", f"{(normal_m - best_m) / 1000:+.2f} km")
    st.bar_chart({"일반 경로": normal_m / 1000, "최적 경로": best_m / 1000}, horizontal=True)
    st.write(f"**거리 기준 절약률: {saved_pct:.1f}%**")
    if normal_s != float("inf"):
        st.write(f"**시간 절약:** 약 {max(0, (normal_s - best_seconds) / 60):.0f}분")
    if best_m > normal_m:
        st.info("최적화 기준은 '시간'이므로, 더 빠른 경로의 총 이동거리가 더 길 수도 있습니다.")
st.write("**일반 방문 순서:** " + " → ".join(normal_full))
st.write("**최적 방문 순서:** " + " → ".join(best_full))

st.divider()
st.subheader("📅 실제 예상 이동시간 기반 자동 여행 일정표")
c1, c2 = st.columns(2)
with c1:
    travel_date = st.date_input("여행 날짜", value=datetime.today().date())
with c2:
    departure_time = st.time_input("여행 시작 시각", value=datetime.strptime("09:00", "%H:%M").time())
default_stay = st.number_input("관광지별 기본 관람 시간 (분)", min_value=0, max_value=600, value=60, step=10)
stays = {}
with st.expander("관광지별 관람 시간 개별 설정"):
    for name in best:
        stays[name] = st.number_input(f"{name} 관람 시간 (분)", min_value=0, max_value=600,
                                      value=int(default_stay), step=10,
                                      key=f"road_stay_{country}_{city}_{name}_{default_stay}")

now = datetime.combine(travel_date, departure_time)
rows = []
travel_seconds = 0.0
for order, name in enumerate(best, 1):
    if order == 1:
        distance_m, seconds = 0, 0
    else:
        prev = best[order - 2]
        distance_m = distances[index[prev]][index[name]]
        seconds = durations[index[prev]][index[name]]
        now += timedelta(seconds=seconds)
    travel_seconds += seconds
    arrival = now
    now += timedelta(minutes=stays[name])
    rows.append({"방문 순서": order, "관광지": name, "이전 장소에서 거리(km)": round(distance_m / 1000, 2),
                 "이동 시간(분)": round(seconds / 60), "도착 시각": arrival.strftime("%m/%d %H:%M"),
                 "관람 시간(분)": stays[name], "출발 시각": now.strftime("%m/%d %H:%M")})
if roundtrip:
    last = best[-1]
    back_m = distances[index[last]][index[start]]
    back_s = durations[index[last]][index[start]]
    travel_seconds += back_s
    now += timedelta(seconds=back_s)
    rows.append({"방문 순서": len(best) + 1, "관광지": f"{start} (복귀)",
                 "이전 장소에서 거리(km)": round(back_m / 1000, 2),
                 "이동 시간(분)": round(back_s / 60), "도착 시각": now.strftime("%m/%d %H:%M"),
                 "관람 시간(분)": 0, "출발 시각": "-"})
st.dataframe(rows, use_container_width=True, hide_index=True)
st.write(f"**예상 종료 시각:** {now.strftime('%m/%d %H:%M')} · "
         f"**총 이동시간:** 약 {travel_seconds / 60:.0f}분 · "
         f"**총 관람시간:** {sum(stays.values())}분")
st.download_button("📥 일정표 CSV 다운로드", csv_bytes(rows),
                   file_name=f"{city}_{'도보' if profile == 'foot-walking' else '자동차'}_여행일정표.csv",
                   mime="text/csv")
with st.expander("📐 경로 계산에 사용한 알고리즘"):
    st.write("관광지 좌표로 실제 도로·보행로 이동거리와 이동시간 행렬을 조회합니다. "
             "출발지를 고정한 후 나머지 관광지의 모든 방문 순서를 순열로 생성하고, "
             "각 순서의 총 예상 이동시간을 합산해 가장 작은 경로를 선택하는 완전탐색 알고리즘입니다.")
    st.write(f"**비교한 방문 순서: {factorial(len(selected) - 1):,}개**")
st.warning("이동시간은 도로 데이터 기반 추정치입니다. 실시간 교통량, 신호 대기, 휴관일, "
           "현지 도로 규제 및 대중교통·선박 연결은 반영되지 않을 수 있습니다. "
           "출발 좌표가 도로에서 떨어져 있으면 가까운 도로 지점으로 보정될 수 있습니다.")
