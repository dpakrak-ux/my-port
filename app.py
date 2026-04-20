import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# [설정] 본인의 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M0Nid5bSfsrxyBEe0r-4HmQnl9Zl3lqgP-0FhMrrKwQ/export?format=csv"

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # 시트의 code열과 value열을 매칭하여 딕셔너리로 변환
        return dict(zip(df['code'].astype(str), df['value']))
    except Exception as e:
        return {}

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: 
        return True
    
    st.title("🔒 Portfolio Access")
    pwd = st.text_input("비밀번호 (****)", type="password")
    if st.button("접속"):
        if pwd == "1222":
            st.session_state["password_correct"] = True
            st.rerun()
        else: 
            st.error("비밀번호가 틀렸습니다.")
    return False

if check_password():
    st.set_page_config(page_title="26년 1번 포트", layout="wide")
    data = load_data()
    
    # 구글 시트에서 예산과 일수 가져오기
    total_budget = int(data.get('budget', 5930509))
    days_left = int(data.get('days', 30))

    st.markdown('<p style="font-size:24px; font-weight:bold;">26년 1번 포트 (Final Sync)</p>', unsafe_allow_html=True)

    # [검증 완료] 100% 실존하는 종목 코드 리스트
    portfolio_config = {
        "KODEX 반도체": "091160",
        "TIGER 미국MSCI리츠(H)": "182480",
        "KODEX 부동산리츠인프라": "476800",
        "SOL 조선 TOP3 레버리지": "0080Y0",
        "KODEX AI전력설비": "487240",
        "PLUS K-방산": "449450",
        "현금(KOFR)": "449170"
    }
    
    # 목표 비중 설정
    weights = {
        "091160": 0.25, "182480": 0.15, "476800": 0.15, 
        "0080Y0": 0.15, "487240": 0.10, "449450": 0.10, "449170": 0.10
    }

    def get_analysis():
        results = []
        total_buy_val = 0
        total_eval_val = 0

        for name, code in portfolio_config.items():
            # 1. 시트에서 수동 현재가(_price) 확인
            m_price = data.get(f"{code}_price", 0)
            manual_price = int(m_price) if str(m_price).isdigit() else 0
            
            curr = 0
            if manual_price > 0:
                curr = manual_price
            else:
                try:
                    # 최근 7일 데이터 중 가장 마지막 종가 사용
                    df = fdr.DataReader(code, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
                    curr = int(df['Close'].iloc[-1])
                except:
                    curr = 0

            # 2. 시트에서 수량(_qty)과 평단(_avg) 확인
            q = data.get(f"{code}_qty", 0)
            a = data.get(f"{code}_avg", 0)
            qty = int(q) if str(q).isdigit() else 0
            avg = int(a) if str(a).isdigit() else 0
            
            buy_amt = qty * avg
            eval_amt = qty * curr
            total_buy_val += buy_amt
            total_eval_val += eval_amt

            profit_pct = ((curr - avg) / avg * 100) if avg > 0 else 0
            
            # 3. 오늘 살 금액 계산
            remaining_target = total_budget - total_buy_val
            daily_target = (remaining_target / days_left * weights[code]) if days_left > 0 else 0

            results.append({
                "종목명": name, 
                "현재가": f"{curr:,}원" if curr > 0 else "시세 대기", 
                "내 평단": f"{avg:,}원",
                "수량": f"{qty:,}", 
                "수익률": f"{profit_pct:+.2f}%", 
                "오늘 살 금액": f"{max(0, int(daily_target)):,}원"
            })
        return pd.DataFrame(results), total_buy_val, total_eval_val

    res_df, t_buy, t_eval = get_analysis()

    # 상단 대시보드
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 매입액", f"{t_buy:,}원")
    m2.metric("총 평가액", f"{t_eval:,}원")
    p_rate = ((t_eval - t_buy) / t_buy * 100) if t_buy > 0 else 0
    m3.metric("전체 수익률", f"{p_rate:.2f}%")
    m4.metric("남은 목표예산", f"{max(0, total_budget - t_buy):,}원")

    st.divider()
    st.dataframe(res_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 데이터 새로고침"):
        st.rerun()
