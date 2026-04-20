import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# [설정] 본인의 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M0Nid5bSfsrxyBEe0r-4HmQnl9Zl3lqgP-0FhMrrKwQ/export?format=csv"

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # 문자열로 된 값을 숫자로 변환 (천단위 콤마 등이 있을 경우 대비)
        return dict(zip(df['code'], df['value']))
    except:
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
            st.error("비밀번호 오류")
    return False

if check_password():
    st.set_page_config(page_title="26년 1번 포트", layout="wide")
    data = load_data()
    
    # 구글 시트에서 예산과 일수 가져오기 (없으면 기본값)
    total_budget = int(data.get('budget', 5930509))
    days_left = int(data.get('days', 30))

    st.markdown('<p style="font-size:24px; font-weight:bold;"> 26년 1번 포트</p>', unsafe_allow_html=True)

    # 종목 설정 (100% 실존 코드 확인 완료)
    portfolio_config = {
        "KODEX 반도체": "091160",
        "TIGER 미국MSCI리츠(H)": "182480",
        "KODEX 부동산리츠인프라": "477380",
        "SOL 조선 TOP3": "475250",
        "KODEX AI전력설비": "48720",
        "PLUS K-방산": "461580",
        "현금(KOFR)": "449170"
    }
    
    # 비중 설정 (총합 1.0)
    weights = {
        "091160": 0.25, 
        "182480": 0.15, 
        "477380": 0.15, 
        "475250": 0.15, 
        "487240": 0.10, 
        "461580": 0.10, 
        "449170": 0.10
    }

    def get_analysis():
        results = []
        total_buy_val = 0
        total_eval_val = 0

        for name, code in portfolio_config.items():
            # 1. 구글 시트에서 수동 현재가 확인
            manual_price = int(data.get(f"{code}_price", 0))
            
            curr = 0
            if manual_price > 0:
                curr = manual_price
            else:
                try:
                    # 주말이나 공휴일 대비 7일치 데이터를 가져와서 마지막 종가 사용
                    df = fdr.DataReader(code, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
                    curr = int(df['Close'].iloc[-1])
                except:
                    curr = 0

            qty = int(data.get(f"{code}_qty", 0))
            avg = int(data.get(f"{code}_avg", 0))
            
            buy_amt = qty * avg
            eval_amt = qty * curr
            total_buy_val += buy_amt
            total_eval_val += eval_amt

            profit_pct = ((curr - avg) / avg * 100) if avg > 0 else 0
            
            # 오늘 살 금액 계산 (남은 예산 / 남은 일수 * 비중)
            remaining_budget = total_budget - total_buy_val
            target_today = (remaining_budget / days_left * weights[code]) if days_left > 0 else 0

            results.append({
                "종목명": name, 
                "현재가": f"{curr:,}원" if curr > 0 else "가격 입력 필요", 
                "내 평단": f"{avg:,}원",
                "수량": f"{qty:,}", 
                "수익률": f"{profit_pct:+.2f}%", 
                "오늘 살 금액": f"{int(target_today):,}원"
            })
        return pd.DataFrame(results), total_buy_val, total_eval_val

    res_df, t_buy, t_eval = get_analysis()

    # 상단 대시보드 메트릭
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 매입액", f"{t_buy:,}원")
    m2.metric("총 평가액", f"{t_eval:,}원")
    
    p_rate = ((t_eval - t_buy) / t_buy * 100) if t_buy > 0 else 0
    m3.metric("전체 수익률", f"{p_rate:.2f}%")
    
    cash_left = max(0, total_budget - t_buy)
    m4.metric("남은 목표예산", f"{cash_left:,}원")

    st.divider()
    
    # 데이터 표 출력
    st.dataframe(res_df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 데이터 새로고침"):
        st.rerun()
