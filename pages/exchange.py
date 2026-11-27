import streamlit as st
import requests
import math

st.set_page_config(
    page_title="환율 조회 및 여행 경비 환산",
    page_icon="💱",
    layout="wide"
)

from design import apply_design
apply_design()

st.title("💱 환율 조회 및 여행 경비 환산")
st.caption("최신 기준환율을 활용하여 여행 경비를 계산합니다.")

# 국가별 통화 정보
CURRENCIES = {
    "대한민국": ("KRW", "원"),
    "일본": ("JPY", "엔"),
    "중국": ("CNY", "위안"),
    "미국": ("USD", "달러"),
    "프랑스": ("EUR", "유로"),
    "호주": ("AUD", "호주 달러")
}


# 외부 API를 활용한 최신 기준환율 조회
# 동일한 환율 데이터는 1시간 동안 저장하여 재사용한다.
@st.cache_data(ttl=3600)
def get_exchange_rate(currency):
    url = (
        "https://api.frankfurter.dev/v2/rate/"
        f"{currency}/KRW"
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    data = response.json()
    rate = float(data["rate"])

    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("유효하지 않은 환율")

    return rate, data["date"]


country = st.selectbox(
    "여행 국가 선택",
    list(CURRENCIES)
)

currency, currency_name = CURRENCIES[country]

# 대한민국은 별도의 환율 조회가 필요하지 않다.
if currency == "KRW":
    rate = 1.0
    date = "동일 통화"
else:
    try:
        rate, date = get_exchange_rate(currency)
    except (requests.RequestException, ValueError,
            KeyError, TypeError):
        st.error("환율 정보를 불러오지 못했습니다.")
        st.info("잠시 후 다시 시도해 주세요.")
        st.stop()


st.subheader("📊 최신 기준환율")

col1, col2 = st.columns(2)

col1.metric(
    f"1 {currency_name}당 원화",
    f"{rate:,.4f}원"
)

col2.metric("환율 기준 날짜", date)

st.divider()

st.subheader("🧮 여행 경비 환산기")

direction = st.radio(
    "환산 방향 선택",
    ["현지 통화 → 원화", "원화 → 현지 통화"],
    horizontal=True
)

# 환율과 금액 사이의 비례 관계를 활용한다.
# 원화 금액 = 현지 통화 금액 × 환율
# 현지 통화 금액 = 원화 금액 ÷ 환율
if direction == "현지 통화 → 원화":

    amount = st.number_input(
        f"현지 통화 금액 입력 ({currency})",
        min_value=0.0,
        value=100.0,
        step=10.0
    )

    result = amount * rate

    st.success(
        f"{amount:,.2f} {currency} = "
        f"{result:,.0f}원"
    )

else:

    amount = st.number_input(
        "원화 금액 입력 (KRW)",
        min_value=0.0,
        value=100000.0,
        step=10000.0
    )

    result = amount / rate

    st.success(
        f"{amount:,.0f}원 = "
        f"{result:,.2f} {currency}"
    )


with st.expander("📐 환율 계산에 적용된 수학적 원리"):

    st.write(
        "환율이 일정할 때 현지 통화 금액과 "
        "원화 금액은 정비례 관계를 가진다."
    )

    st.latex(r"y = rx")

    st.write(
        "x: 현지 통화 금액 / "
        "r: 환율 / y: 원화 금액"
    )

    st.write(
        "원화 금액을 현지 통화로 환산할 때는 "
        "위 식을 변형하여 계산한다."
    )

    st.latex(r"x = \frac{y}{r}")


st.divider()

st.caption("환율 데이터 출처: Frankfurter API")
st.warning(
    "제공되는 환율은 참고용 기준환율이며, "
    "실제 환전 수수료 및 은행별 적용 환율과 "
    "차이가 발생할 수 있습니다."
)
