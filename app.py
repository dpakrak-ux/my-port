import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="26년 1번 포트", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; margin-bottom: 20px; }
    div[data-testid="stMetricValue"] { font-size: 22px !important; color: #00FFCC; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">26년 1번 포트</p>', unsafe_allow_html=True)

# 2. 사이드바: 자산 설정 및 종목별 수동 데이터 입력
st.sidebar.header("💰 자산 및 매수 설정")
total_budget = st.sidebar.number_input("총 투자 목표 예산 (원)", value=10000000, step=1000000)
days_left = st.sidebar.slider("남은 분할 매수 일수", 1, 30, 20)

st.sidebar.divider()
st.sidebar.subheader("📝 종목별 상세 관리")

portfolio_config = {
    "KODEX 반도체": {"code": "091160", "weight": 0.25},
    "TIGER 미국배당리츠": {"code": "456370", "weight": 0.15},
    "KODEX 부동산리츠": {"code": "472290", "weight": 0.15},
    "SOL 조선 TOP3(L)": {"code": "475250", "weight": 0.15},
    "KODEX AI전력": {"code": "482060", "weight": 0.10},
    "PLUS K-방산": {"code": "461580", "weight": 0.10},
    "현금(KOFR)": {"code": "449170", "weight": 0.10}
}

user_data = {}
for name, info in portfolio_config.items():
    with st.sidebar.expander(f"{name}", expanded=False):
        qty = st.number_input(f"보유 수량", key=f"qty_{info['code']}", value=0)
        avg = st.number_input(f"평단가", key=f"avg_{info['code']}", value=0)
        manual_price = st.number_input(f"현재가 수동 입력 (오류 시)", key=f"manual_{info['code']}", value=0)
        user_data[name] = {"qty": qty, "avg": avg, "manual": manual_price}

# 3. 데이터 분석 로직
def get_analysis():
    results = []
    total_buy_val = 0
    total_eval_val = 0

    for name, info in portfolio_config.items():
        try:
            # 실시간 데이터 시도
            df = fdr.DataReader(info['code'], (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
            current_price = int(df['Close'].iloc[-1])
        except:
            # 연결 오류 시 사용자가 입력한 수동 가격 사용
            current_price = user_data[name]['manual']

        qty = user_data[name]['qty']
        avg = user_data[name]['avg']
        
        buy_amt = qty * avg
        eval_amt = qty * current_price
        profit_pct = ((current_price - avg) / avg * 100) if avg > 0 else 0
        
        total_buy_val += buy_amt
        total_eval_val += eval_amt

        # 매수 가이드 (남은 예산 기준)
        remaining = total_budget - total_buy_val
        target_buy = (remaining / days_left * info['weight']) if days_left > 0 else 0

        results.append({
            "종목명": name,
            "현재가": f"{current_price:,}원" if current_price > 0 else "가격 입력 필요",
            "내 평단가": f"{avg:,}원",
            "보유수량": f"{qty:,}",
            "수익률": f"{profit_pct:+.2f}%",
            "권장 매수액": f"{int(target_buy):,}원"
        })
            
    return pd.DataFrame(results), total_buy_val, total_eval_val

result_df, total_buy, total_eval = get_analysis()

# 4. 메인 화면 출력
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 매입금액", f"{total_buy:,}원")
c2.metric("총 평가금액", f"{total_eval:,}원")
profit_pct = ((total_eval - total_buy) / total_buy * 100) if total_buy > 0 else 0
c3.metric("전체 수익률", f"{profit_pct:.2f}%")
c4.metric("남은 예수금", f"{max(0, total_budget - total_buy):,}원")

st.divider()
st.subheader("투자현황 및 매수 가이드")
st.dataframe(result_df, use_container_width=True, hide_index=True)

# 5. 투자 달력 및 기록 섹션
st.divider()
st.subheader("📅 투자 기록 달력")

col_cal, col_log = st.columns([1, 1])

with col_cal:
    selected_date = st.date_input("투자 날짜 선택", datetime.now())
    invest_amt = st.number_input("오늘 투자한 금액(원)", value=0, step=10000)
    memo = st.text_input("메모", placeholder="예: KODEX 반도체 10주 추매")
    if st.button("기록 저장"):
        if 'invest_log' not in st.session_state:
            st.session_state.invest_log = []
        st.session_state.invest_log.append({"날짜": selected_date, "금액": invest_amt, "내용": memo})
        st.success("기록되었습니다!")

with col_log:
    st.write("📂 최근 투자 로그")
    if 'invest_log' in st.session_state and st.session_state.invest_log:
        log_df = pd.DataFrame(st.session_state.invest_log)
        # 금액에 콤마 적용하여 표시
        log_df['금액'] = log_df['금액'].apply(lambda x: f"{x:,}원")
        st.table(log_df.tail(5)) # 최근 5개 기록만 표시
    else:
        st.info("아직 기록된 투자 내역이 없습니다.")