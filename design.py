import streamlit as st


def apply_design():
    st.markdown("""
    <style>

    /* 전체 배경 */
    .stApp {
        background-color: #FFFFFF;
    }

    /* 메인 제목 */
    h1 {
        color: #1E3A8A !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #2563EB;
        padding-bottom: 16px !important;
    }

    /* 소제목 */
    h2, h3, h4 {
        color: #1E3A8A !important;
        font-weight: 700 !important;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #EFF6FF;
        border-right: 1px solid #BFDBFE;
    }

    [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        transition: background-color 0.2s;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: #DBEAFE;
    }

    /* 일반 버튼 및 다운로드 버튼 */
    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: background-color 0.2s;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stLinkButton > a:hover {
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
    }

    /* 선택창 및 입력창 */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
    }

    /* 주요 수치 카드 */
    [data-testid="stMetric"] {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.06);
    }

    [data-testid="stMetricValue"] {
        color: #1E3A8A !important;
        font-weight: 700;
    }

    /* 관광지 사진 */
    [data-testid="stImage"] img {
        border-radius: 14px;
    }

    /* 데이터 표 */
    [data-testid="stDataFrame"] {
        border: 1px solid #BFDBFE;
        border-radius: 12px;
    }

    /* 펼치기 메뉴 */
    [data-testid="stExpander"] {
        border-radius: 12px;
        border-color: #BFDBFE;
    }

    /* 구분선 */
    hr {
        border-color: #DBEAFE !important;
    }

    </style>
    """, unsafe_allow_html=True)
