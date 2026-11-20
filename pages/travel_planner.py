import streamlit as st
from math import radians, sin, cos, asin, sqrt, factorial
from itertools import permutations
from datetime import datetime, timedelta
from io import StringIO
import csv
import folium
from streamlit_folium import st_folium
from tourist_data import TOURIST_DATA

st.set_page_config(page_title="최적 여행 경로 탐색", page_icon="🧭", layout="wide")
st.title("🧭 최적 여행 경로 탐색")

country = st.selectbox("국가 선택", list(TOURIST_DATA.keys()), key="planner_country")
city = st.selectbox("도시 선택", list(TOURIST_DATA[country].keys()), key=f"planner_city_{country}")
places = TOURIST_DATA[country][city]

def schedule_to_csv(rows):
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")

# -------------------------
# 최적 여행 경로 계산 함수
# -------------------------

def haversine_km(point_a, point_b):
    """두 관광지 사이의 대권거리 계산"""
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


def route_distance(
    route,
    coordinates,
    return_to_start=False
):
    """방문 경로의 총거리 계산"""

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


def find_shortest_route(
    selected,
    coordinates,
    start,
    return_to_start=False
):
    """순열과 완전탐색을 이용한 최적 경로 계산"""

    remaining = [
        name for name in selected
        if name != start
    ]

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

    # 지도 클릭 등으로 Streamlit이 재실행되어도 계산 결과 유지
    route_state_key = f"calculated_route_{country}_{city}"
    current_route_settings = (
        tuple(selected_places), start_place, return_to_start
    )

    if st.button(
        "🔍 최단 경로 계산하기",
        type="primary"
    ):
        st.session_state[route_state_key] = current_route_settings

    if st.session_state.get(route_state_key) == current_route_settings:
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
            distance = haversine_km(
                places[a],
                places[b]
            )

            st.write(
                f"{i}. {a} → {b}: "
                f"**{distance:.2f} km**"
            )

        # 클릭 가능한 깃발 마커가 있는 최적 경로 지도
        st.subheader("🗺️ 최적 경로 지도")

        center_lat = sum(places[name][0] for name in best_route) / len(best_route)
        center_lon = sum(places[name][1] for name in best_route) / len(best_route)

        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
            control_scale=True
        )

        # 최적 경로를 파란색 선으로 연결
        route_coordinates = [
            [places[name][0], places[name][1]]
            for name in display_route
        ]
        folium.PolyLine(
            locations=route_coordinates,
            color="#1473e6",
            weight=5,
            opacity=0.85,
            tooltip="최적 여행 경로"
        ).add_to(route_map)

        # 각 관광지에 깃발을 꽂고 클릭 시 장소 정보 표시
        for order, name in enumerate(best_route, start=1):
            point_lat, point_lon = places[name]
            popup_html = (
                f"<div style='font-size:15px; min-width:150px;'>"
                f"<b>🚩 {name}</b><br>"
                f"방문 순서: {order}번째"
                f"</div>"
            )
            folium.Marker(
                location=[point_lat, point_lon],
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{order}. {name} (클릭해서 확인)",
                icon=folium.Icon(color="red", icon="flag", prefix="fa")
            ).add_to(route_map)

        # 모든 깃발이 지도에 들어오도록 자동 확대 범위 설정
        route_map.fit_bounds([
            [places[name][0], places[name][1]]
            for name in best_route
        ], padding=(35, 35))

        st_folium(
            route_map,
            height=500,
            use_container_width=True,
            key=f"optimal_route_map_{country}_{city}",
            returned_objects=[]
        )

        st.caption(
            "빨간 깃발을 클릭하면 관광지 이름과 방문 순서를 확인할 수 있습니다. "
            "파란 선은 계산된 최적 경로를 나타냅니다."
        )

        # -------------------------
        # 일반 경로와 최적 경로 비교 분석
        # -------------------------
        st.divider()
        st.subheader("📊 일반 경로와 최적 경로 비교")
        st.caption("일반 경로는 선택 목록에 표시된 순서대로 출발지를 먼저 방문한 경로입니다.")

        normal_route = [start_place] + [
            name for name in selected_places if name != start_place
        ]
        normal_distance = route_distance(
            normal_route, places, return_to_start
        )
        saved_km = max(0.0, normal_distance - best_distance)
        saved_percent = (
            saved_km / normal_distance * 100
            if normal_distance > 0 else 0.0
        )

        comparison_col1, comparison_col2, comparison_col3 = st.columns(3)
        comparison_col1.metric("일반 경로", f"{normal_distance:.2f} km")
        comparison_col2.metric("최적 경로", f"{best_distance:.2f} km")
        comparison_col3.metric("절약 거리", f"{saved_km:.2f} km")
        st.write(f"**거리 절약률: {saved_percent:.1f}%**")
        st.bar_chart(
            {"일반 경로": normal_distance, "최적 경로": best_distance},
            horizontal=True
        )
        st.write("**일반 방문 순서:** " + " → ".join(
            normal_route + ([normal_route[0]] if return_to_start else [])
        ))
        st.write("**최적 방문 순서:** " + " → ".join(display_route))
        if saved_km < 0.001:
            st.info("선택한 일반 경로도 최단 경로입니다. 방문 순서를 바꾸면 차이가 생길 수 있습니다.")

        # -------------------------
        # 최적 경로를 이용한 자동 여행 일정표
        # -------------------------
        st.divider()
        st.subheader("📅 자동 여행 일정표")
        st.caption(
            "선택한 출발 시간, 평균 이동 속도, 관광지별 관람 시간을 바탕으로 "
            "예상 도착 및 출발 시각을 계산합니다. 실제 교통시간과는 다릅니다."
        )

        schedule_col1, schedule_col2 = st.columns(2)
        with schedule_col1:
            departure_time = st.time_input(
                "여행 시작 시각",
                value=datetime.strptime("09:00", "%H:%M").time(),
                key=f"departure_time_{country}_{city}"
            )
        with schedule_col2:
            speed_kmh = st.number_input(
                "가정할 평균 이동 속도 (km/h)",
                min_value=1.0,
                max_value=300.0,
                value=30.0,
                step=5.0,
                key=f"speed_kmh_{country}_{city}"
            )

        default_stay = st.number_input(
            "관광지별 기본 관람 시간 (분)",
            min_value=0,
            max_value=600,
            value=60,
            step=10,
            key=f"default_stay_{country}_{city}"
        )
        with st.expander("관광지별 관람 시간 개별 설정 (선택)"):
            stays = {}
            for name in best_route:
                stays[name] = st.number_input(
                    f"{name} 관람 시간 (분)",
                    min_value=0,
                    max_value=600,
                    value=int(default_stay),
                    step=10,
                    key=f"stay_{country}_{city}_{name}_{default_stay}"
                )

        current_time = datetime.combine(datetime.today().date(), departure_time)
        schedule_rows = []
        previous_name = None
        total_move_minutes = 0.0
        for idx, name in enumerate(best_route, start=1):
            if previous_name is None:
                move_km = 0.0
                move_minutes = 0.0
            else:
                move_km = haversine_km(places[previous_name], places[name])
                move_minutes = move_km / speed_kmh * 60
                current_time += timedelta(minutes=move_minutes)
            total_move_minutes += move_minutes
            arrival = current_time
            current_time += timedelta(minutes=stays[name])
            schedule_rows.append({
                "방문 순서": idx,
                "관광지": name,
                "이전 장소에서 거리(km)": round(move_km, 2),
                "이동 시간(분)": round(move_minutes),
                "도착 시각": arrival.strftime("%m/%d %H:%M"),
                "관람 시간(분)": stays[name],
                "출발 시각": current_time.strftime("%m/%d %H:%M")
            })
            previous_name = name

        if return_to_start:
            back_km = haversine_km(
                places[best_route[-1]], places[best_route[0]]
            )
            back_minutes = back_km / speed_kmh * 60
            total_move_minutes += back_minutes
            current_time += timedelta(minutes=back_minutes)
            schedule_rows.append({
                "방문 순서": len(best_route) + 1,
                "관광지": f"{best_route[0]} (복귀)",
                "이전 장소에서 거리(km)": round(back_km, 2),
                "이동 시간(분)": round(back_minutes),
                "도착 시각": current_time.strftime("%m/%d %H:%M"),
                "관람 시간(분)": 0,
                "출발 시각": "-"
            })

        st.dataframe(schedule_rows, use_container_width=True, hide_index=True)
        st.write(
            f"**예상 종료 시각:** {current_time.strftime('%m/%d %H:%M')} · "
            f"**총 이동 시간:** 약 {total_move_minutes:.0f}분 · "
            f"**총 관람 시간:** {sum(stays.values())}분"
        )
        st.download_button(
            "📥 일정표 CSV 다운로드",
            data=schedule_to_csv(schedule_rows),
            file_name=f"{city}_여행일정표.csv",
            mime="text/csv",
            key=f"download_schedule_{country}_{city}"
        )

        with st.expander(
            "📐 경로 계산에 사용한 수학 원리"
        ):
            st.write(
                "하버사인 공식을 사용해 "
                "두 지점의 위도와 경도로 "
                "대권거리를 계산합니다."
            )

            st.latex(
                r"d=2R\arcsin\left("
                r"\sqrt{\sin^2\frac{\Delta\phi}{2}"
                r"+\cos\phi_1\cos\phi_2"
                r"\sin^2\frac{\Delta\lambda}{2}}"
                r"\right)"
            )

            st.write(
                "R = 6371 km, φ = 위도, λ = 경도"
            )

            st.write(
                "출발지를 고정한 뒤 나머지 관광지의 "
                "모든 방문 순서를 비교하는 "
                "완전탐색 방식입니다."
            )

            count = factorial(
                len(selected_places) - 1
            )

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
