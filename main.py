    if return_to_start and len(route) > 1:
        total += haversine_km(coordinates[route[-1]], coordinates[route[0]])
    return total


def find_shortest_route(selected, coordinates, start, return_to_start=False):
    """출발지를 고정하고 가능한 모든 방문 순서를 완전탐색"""
    remaining = [name for name in selected if name != start]
    best_route = None
    best_distance = float("inf")
    for order in permutations(remaining):
        candidate = (start,) + order
        distance = route_distance(candidate, coordinates, return_to_start)
        if distance < best_distance:
            best_distance = distance
            best_route = candidate
    return list(best_route), best_distance


st.divider()
st.header("🧭 최적 여행 경로 추천")
st.write("방문할 관광지를 선택하면 이동 거리의 합이 가장 짧은 순서를 계산합니다.")

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
            selected_places, places, start_place, return_to_start
        )
        display_route = best_route + [best_route[0]] if return_to_start else best_route
        st.success("최적 경로 계산이 완료되었습니다!")
        st.metric("총 직선(대권) 거리", f"{best_distance:.2f} km")
        st.subheader("📌 추천 방문 순서")
        st.write(" → ".join(display_route))

        st.subheader("📏 구간별 거리")
        for i, (a, b) in enumerate(zip(display_route, display_route[1:]), start=1):
            distance = haversine_km(places[a], places[b])
            st.write(f"{i}. {a} → {b}: **{distance:.2f} km**")

        # 지도용 좌표는 pydeck의 [경도, 위도] 순서로 변환
        route_points = [
            {"name": name, "order": str(i + 1),
             "lat": places[name][0], "lon": places[name][1]}
            for i, name in enumerate(best_route)
        ]
        line_points = [
            {"source": [places[a][1], places[a][0]],
             "target": [places[b][1], places[b][0]]}
            for a, b in zip(display_route, display_route[1:])
        ]
        center_lat = sum(p["lat"] for p in route_points) / len(route_points)
        center_lon = sum(p["lon"] for p in route_points) / len(route_points)

        layers = [
            pdk.Layer(
                "LineLayer", line_points,
                get_source_position="source",
                get_target_position="target",
                get_color=[20, 115, 230, 220],
                get_width=5, width_min_pixels=3,
                pickable=False
            ),
            pdk.Layer(
                "ScatterplotLayer", route_points,
                get_position="[lon, lat]",
                get_fill_color=[230, 65, 65, 230],
                get_radius=100, radius_min_pixels=9,
                pickable=True
            ),
            pdk.Layer(
                "TextLayer", route_points,
                get_position="[lon, lat]",
                get_text="order", get_size=17,
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
        st.caption("지도에서 빨간 원의 숫자는 방문 순서이며, 파란 선은 관광지 사이를 연결합니다.")

        with st.expander("📐 경로 계산에 사용한 수학 원리"):
            st.write("**하버사인 공식**을 사용해 두 지점의 위도·경도로 대권거리를 계산했습니다.")
            st.latex(r"d=2R\arcsin\left(\sqrt{\sin^2\frac{\Delta\phi}{2}+\cos\phi_1\cos\phi_2\sin^2\frac{\Delta\lambda}{2}}\right)")
            st.write("R = 6371 km, φ = 위도, λ = 경도")
            st.write("출발지를 고정한 뒤 나머지 관광지의 모든 방문 순서를 비교하는 "
                     "완전탐색 방식으로 최소 거리 경로를 찾습니다.")
            st.write(f"이번 계산에서 비교한 방문 순서는 **{__import__('math').factorial(len(selected_places) - 1):,}개**입니다.")

        st.warning(
            "이 경로는 지구 표면의 최단 거리(대권거리)를 최소화한 결과입니다. "
            "실제 도로·도보 경로, 교통수단, 바다·강 등의 장애물과 이동 시간은 "
            "반영되지 않습니다."
