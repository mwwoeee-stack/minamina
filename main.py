import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(
    page_title="화학 시약 혼합 위험성 & 열역학 자발성 판별 시스템",
    page_icon="🧪",
    layout="wide"
)

# ---------------------------------------------------------
# 1. 반응 데이터베이스 (열역학 데이터 및 연출 효과)
# ---------------------------------------------------------
REACTIONS = [
    {
        "id": "hydrogen_explosion",
        "name": "수소-산소 폭명기 급격 연소",
        "reactants": {"수소 (H₂)", "산소 (O₂)", "점화 불꽃 (Activation Energy)"},
        "products": ["수증기 (H₂O)", "강한 충격파"],
        "enthalpy": "ΔH = -483.6 kJ/mol (극단적 발열)",
        "entropy": "열역학적 몰수는 감소하나, 발생한 열로 급격한 부피 팽창 유발",
        "spontaneity": "초자발적 반응 (점화 즉시 연쇄 폭발)",
        "phenomenon": "귀가 먹먹할 정도의 굉음과 섬광을 일으키며 순식간에 폭발합니다! (실험실 안전 주의)",
        "type": "explosion",
        "icon": "💥"
    },
    {
        "id": "sodium_water",
        "name": "나트륨과 물의 격렬한 산화·환원",
        "reactants": {"금속 나트륨 (Na)", "물 (H₂O)"},
        "products": ["수산화 나트륨 (NaOH)", "수소 기체 (H₂)", "다량의 반응열"],
        "enthalpy": "ΔH = -368.6 kJ/mol (격렬한 발열)",
        "entropy": "ΔS > 0 (고체+액체에서 수용액 및 수소 기체 발생)",
        "spontaneity": "매우 자발적 (상온 접촉 즉시 반응)",
        "phenomenon": "나트륨 덩어리가 물 위를 빠르게 회전하며 노란 불꽃을 내뿜고, '퍽!' 하는 소리와 함께 폭발합니다.",
        "type": "explosion",
        "icon": "💥"
    },
    {
        "id": "photosynthesis",
        "name": "광합성 (포도당 합성 반응)",
        "reactants": {"이산화 탄소 (CO₂)", "물 (H₂O)", "태양광 (Light)"},
        "products": ["포도당 (C₆H₁₂O₆)", "산소 (O₂)"],
        "enthalpy": "ΔH = +2803 kJ/mol (흡열 반응)",
        "entropy": "ΔS = -259 J/(mol·K) (기체 분자가 정돈된 유기물로 합성되어 감소)",
        "spontaneity": "비자발적 반응 (외부 빛 에너지 지속 공급 필수)",
        "phenomenon": "빛 에너지를 흡수하여 무기물로부터 화학 에너지를 축적합니다. 외부 에너지 공급 없이는 절대 자발적으로 일어나지 않습니다.",
        "type": "normal",
        "icon": "🌱"
    },
    {
        "id": "cellular_respiration",
        "name": "세포 호흡 및 완전 연소",
        "reactants": {"포도당 (C₆H₁₂O₆)", "산소 (O₂)"},
        "products": ["이산화 탄소 (CO₂)", "물 (H₂O)"],
        "enthalpy": "ΔH = -2803 kJ/mol (발열 반응)",
        "entropy": "ΔS = +259 J/(mol·K) (무질서도 증가)",
        "spontaneity": "항상 자발적 (ΔH < 0, ΔS > 0)",
        "phenomenon": "유기물이 산화 분해되며 다량의 열과 에너지를 방출합니다.",
        "type": "normal",
        "icon": "🔥"
    },
    {
        "id": "baking_soda_vinegar",
        "name": "탄산수소나트륨과 아세트산의 중화·분해",
        "reactants": {"탄산수소 나트륨 (NaHCO₃)", "식초 (CH₃COOH)"},
        "products": ["아세트산 나트륨 (CH₃COONa)", "물 (H₂O)", "이산화 탄소 (CO₂)"],
        "enthalpy": "ΔH > 0 (흡열 반응, 주변 열 흡수)",
        "entropy": "ΔS >> 0 (고체-액체 반응 후 다량의 이산화 탄소 기체 생성)",
        "spontaneity": "자발적 반응 (엔트로피 증가 효과가 흡열 불리성을 극복)",
        "phenomenon": "플라스크 표면이 눈에 띄게 차가워지며 격렬하게 기포(CO₂)가 뿜어져 나옵니다.",
        "type": "normal",
        "icon": "❄️"
    }
]

AVAILABLE_ITEMS = [
    "이산화 탄소 (CO₂)",
    "물 (H₂O)",
    "태양광 (Light)",
    "포도당 (C₆H₁₂O₆)",
    "산소 (O₂)",
    "수소 (H₂)",
    "점화 불꽃 (Activation Energy)",
    "금속 나트륨 (Na)",
    "탄산수소 나트륨 (NaHCO₃)",
    "식초 (CH₃COOH)"
]

# ---------------------------------------------------------
# 2. 세션 상태 관리
# ---------------------------------------------------------
if "flask" not in st.session_state:
    st.session_state.flask = set()

def add_to_flask(item):
    st.session_state.flask.add(item)

def clear_flask():
    st.session_state.flask.clear()

# ---------------------------------------------------------
# 3. 폭발 애니메이션 삽입 컴포넌트 (CSS Shake + Flash)
# ---------------------------------------------------------
def trigger_explosion_effect():
    html_code = """
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // 1. 기존 폭발 오버레이가 남아있다면 제거 (재실행 대응)
        const oldOverlay = parentDoc.getElementById('chem-explosion-overlay');
        if (oldOverlay) oldOverlay.remove();
        const oldStyle = parentDoc.getElementById('chem-explosion-style');
        if (oldStyle) oldStyle.remove();

        // 2. 부모 창(전체 Streamlit 앱) 흔들림 & 섬광 CSS 주입
        const style = parentDoc.createElement('style');
        style.id = 'chem-explosion-style';
        style.innerHTML = `
            @keyframes appShake {
                0%, 100% { transform: translate(0, 0) rotate(0deg); }
                10% { transform: translate(-12px, -8px) rotate(-1.5deg); }
                20% { transform: translate(12px, 6px) rotate(1.5deg); }
                30% { transform: translate(-10px, 8px) rotate(-1deg); }
                40% { transform: translate(10px, -6px) rotate(1deg); }
                50% { transform: translate(-8px, -4px) rotate(-0.8deg); }
                60% { transform: translate(8px, 4px) rotate(0.8deg); }
                70% { transform: translate(-5px, 2px) rotate(-0.5deg); }
                80% { transform: translate(5px, -2px) rotate(0.5deg); }
            }
            .stApp {
                animation: appShake 0.75s cubic-bezier(.36,.07,.19,.97) both !important;
            }
        `;
        parentDoc.head.appendChild(style);

        // 3. 전체 화면을 덮는 투명 Canvas 생성
        const canvas = parentDoc.createElement('canvas');
        canvas.id = 'chem-explosion-overlay';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100vw';
        canvas.style.height = '100vh';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '999999';
        canvas.width = window.parent.innerWidth;
        canvas.height = window.parent.innerHeight;
        parentDoc.body.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        const centerX = canvas.width * 0.65; // 우측 반응계 영역 중심
        const centerY = canvas.height * 0.45;

        // 4. 화염 파티클 및 연기 생성
        const particles = [];
        const colors = ['#ffffff', '#fff200', '#ff9f1a', '#ff3838', '#4b4b4b'];

        for (let i = 0; i < 160; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 18 + 3;
            particles.push({
                x: centerX,
                y: centerY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                radius: Math.random() * 18 + 5,
                color: colors[Math.floor(Math.random() * colors.length)],
                alpha: 1,
                decay: Math.random() * 0.02 + 0.015
            });
        }

        let shockwaveRadius = 10;
        let flashAlpha = 0.85;

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 초기 섬광 효과
            if (flashAlpha > 0) {
                ctx.fillStyle = `rgba(255, 100, 50, ${flashAlpha})`;
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                flashAlpha -= 0.05;
            }

            // 충격파 링 확산
            if (shockwaveRadius < canvas.width * 0.8) {
                ctx.beginPath();
                ctx.arc(centerX, centerY, shockwaveRadius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(255, 220, 120, ${1 - shockwaveRadius / (canvas.width * 0.8)})`;
                ctx.lineWidth = 14;
                ctx.stroke();
                shockwaveRadius += 28;
            }

            // 불꽃 파티클 업데이트
            let alive = false;
            for (let p of particles) {
                if (p.alpha > 0) {
                    alive = true;
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vx *= 0.94; // 공기 저항 감속
                    p.vy *= 0.94;
                    p.vy += 0.15; // 미세 중력
                    p.alpha -= p.decay;

                    ctx.save();
                    ctx.globalAlpha = Math.max(0, p.alpha);
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                    ctx.fillStyle = p.color;
                    ctx.fill();
                    ctx.restore();
                }
            }

            if (alive || flashAlpha > 0) {
                requestAnimationFrame(animate);
            } else {
                canvas.remove();
            }
        }

        animate();
    })();
    </script>
    <div style="text-align:center; padding:15px; background:#ff3333; color:white; font-weight:800; font-size:20px; border-radius:8px; box-shadow:0 0 20px rgba(255,51,51,0.8);">
        ⚠️ 위험: 급격한 연소·폭발 반응 조건이 감지되었습니다!
    </div>
    """
    components.html(html_code, height=85)

# ---------------------------------------------------------
# 4. 메인 대시보드 UI
# ---------------------------------------------------------
st.title("🧪 화학 시약 혼합 위험성 & 열역학 자발성 판별 시스템")
st.caption("반응물질과 에너지 조건을 조합하여 생성물을 예측하고, 엔탈피(ΔH)와 엔트로피(ΔS) 변화에 따른 화학적 자발성을 확인하세요.")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📦 화학 시약 및 조건 선택")
    st.write("반응계에 투입할 요소를 클릭하세요:")
    
    btn_cols = st.columns(2)
    for i, item in enumerate(AVAILABLE_ITEMS):
        with btn_cols[i % 2]:
            disabled = item in st.session_state.flask
            if st.button(f"➕ {item}", key=f"btn_{i}", disabled=disabled, use_container_width=True):
                add_to_flask(item)
                st.rerun()

    st.divider()
    if st.button("🔄 반응계 비우기 (초기화)", use_container_width=True):
        clear_flask()
        st.rerun()

with col2:
    st.subheader("🧫 반응계 (Reaction System)")
    
    if not st.session_state.flask:
        st.info("현재 투입된 물질이 없습니다. 왼쪽에서 반응물과 에너지를 선택해 보세요.")
    else:
        st.write("**투입된 화학종 및 에너지:**")
        tags = " ".join([f"`{item}`" for item in st.session_state.flask])
        st.markdown(tags)
        
        # ---------------------------------------------------------
        # 5. 반응 매칭
        # ---------------------------------------------------------
        matched_reaction = None
        for rxn in REACTIONS:
            if rxn["reactants"] == st.session_state.flask:
                matched_reaction = rxn
                break
        
        st.divider()

        if matched_reaction:
            if matched_reaction["type"] == "explosion":
                trigger_explosion_effect()
                st.error(f"### {matched_reaction['icon']} {matched_reaction['name']}")
            else:
                st.success(f"### {matched_reaction['icon']} {matched_reaction['name']}")
            
            st.markdown(f"**생성물:** " + ", ".join([f"**{p}**" for p in matched_reaction['products']]))
            st.info(f"**관찰되는 거시적 현상:** {matched_reaction['phenomenon']}")
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric(label="엔탈피 변화 (ΔH)", value=matched_reaction['enthalpy'])
            with m2:
                st.metric(label="자발성 판정", value=matched_reaction['spontaneity'])
            
            st.caption(f"**엔트로피 거동 (ΔS):** {matched_reaction['entropy']}")
            
        else:
            st.warning("⚠️ 선택된 조합으로는 상온 조건에서 유의미한 화학 반응이 일어나지 않습니다. 다른 시약이나 에너지 조건을 조합해 보세요.")

# 실제 화학 반응 데이터베이스 연결
import requests
import pandas as pd
from io import StringIO

@st.cache_data(ttl=86400)
def load_rhea_data():
    url = "https://www.rhea-db.org/rhea/"

    params = {
        "query": "",
        "columns": "rhea-id,equation",
        "format": "tsv",
        "limit": 1000
    }

    response = requests.get(
        url, params=params, timeout=30
    )
    response.raise_for_status()

    return pd.read_csv(
        StringIO(response.text),
        sep="\t"
    )

st.divider()
st.header("🔬 실제 화학 반응식 검색")

try:
    reactions_df = load_rhea_data()

    search_word = st.text_input(
        "검색할 화학 물질을 입력하세요",
        placeholder="예: ATP, glucose"
    )

    if search_word:
        filtered = reactions_df[
            reactions_df["Equation"].str.contains(
                search_word,
                case=False,
                na=False,
                regex=False
            )
        ]
    else:
        filtered = reactions_df

    st.write(f"검색 결과: {len(filtered)}개")
    st.dataframe(
        filtered,
        use_container_width=True
    )

# Rhea 화학 반응 데이터베이스 연결
import requests
import pandas as pd
from io import StringIO

@st.cache_data(ttl=86400)
def load_rhea_data():
    url = "https://www.rhea-db.org/rhea/"

    params = {
        "query": "",
        "columns": "rhea-id,equation",
        "format": "tsv",
        "limit": 1000
    }

    response = requests.get(
        url, params=params, timeout=30
    )
    response.raise_for_status()

    return pd.read_csv(
        StringIO(response.text),
        sep="\t"
    )

st.divider()
st.header("🔬 실제 화학 반응식 검색")

try:
    reactions_df = load_rhea_data()

    search_word = st.text_input(
        "검색할 화학 물질을 입력하세요",
        placeholder="예: ATP, glucose"
    )

    if search_word:
        filtered = reactions_df[
            reactions_df["Equation"].str.contains(
                search_word,
                case=False,
                na=False,
                regex=False
            )
        ]
    else:
        filtered = reactions_df

    st.write(f"검색 결과: {len(filtered)}개")
    st.dataframe(
        filtered,
        use_container_width=True
    )

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")


except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
