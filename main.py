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
except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as error:
    st.warning("현재 날씨 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
    st.caption(f"날씨 조회 오류: {error}")
