import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai
from PIL import Image
import io

# [설정] 1. 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1M0Nid5bSfsrxyBEe0r-4HmQnl9Zl3lqgP-0FhMrrKwQ/export?format=csv"

# [설정] 2. Gemini API 설정 (보내주신 키 적용)
GOOGLE_API_KEY = "AIzaSyAjz_EqarM_9fvSVLYW2goir4avL0kq6Wg"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return dict(zip(df['code'].astype(str), df['value']))
    except:
        return {}

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.title("🔒 Portfolio Access")
    pwd = st.text_input("비밀번호 (****)", type="password")
    if st.button("접속"):
        if pwd == "1222":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("비밀번호 오류")
    return False

if check_password():
    st.set_page_config(page_title="26년 1번 포트", layout="wide")
    data = load_data()
    
    st.markdown('<p style="font-size:24px; font-weight:bold;">26년 1번 포트 </p>', unsafe_allow_html=True)

    # 포트폴리오 설정 (스크린샷 기반 코드 매칭)
    portfolio_config = {
        "KODEX 반도체": "091160",
        "TIGER 미국MSCI리츠(H)": "182480",
        "KODEX 부동산리츠인프라": "476800",
        "SOL 조선 TOP3 레버리지": "0080Y0",
        "KODEX AI전력설비": "487240",
        "PLUS K-방산": "449450",
        "현금(KOFR)": "449170"
    }

    # 📸 스크린샷 업로드 섹션
    with st.expander("📷 계좌 스크린샷으로 데이터 업데이트", expanded=False):
        uploaded_files = st.file_uploader("삼성증권 잔고 스크린샷을 모두 선택하세요 (최대 3장)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if st.button("AI 분석 및 데이터 추출") and uploaded_files:
            all_extracted_data = []
            with st.spinner("AI가 이미지를 분석하여 데이터를 추출 중입니다..."):
                for uploaded_file in uploaded_files:
                    img = Image.open(uploaded_file)
                    # 프롬프트: 삼성증권 UI에 최적화된 추출 명령
                    prompt = """
                    이 이미지는 삼성증권 주식 잔고 화면입니다. 
                    각 종목의 '종목명', '보유수량', '수익률(%)', '평가금액'을 찾아줘.
                    결과는 반드시 JSON 형식으로만 답해줘. 예: [{"name": "KODEX 반도체", "qty": 10, "profit_pct": 5.2, "eval_amt": 350000}]
                    """
                    response = model.generate_content([prompt, img])
                    try:
                        # JSON 텍스트만 추출하는 로직
                        import json
                        clean_json = response.text.replace('```json', '').replace('```', '').strip()
                        all_extracted_data.extend(json.loads(clean_json))
                    except:
                        st.error(f"이미지 분석 중 오류가 발생했습니다.")

                if all_extracted_data:
                    st.write("### 🔍 추출된 데이터 확인")
                    st.dataframe(pd.DataFrame(all_extracted_data))
                    st.info("💡 이 데이터를 바탕으로 구글 시트 양식에 맞게 값을 복사하여 업데이트하세요. (자동 쓰기는 구글 권한 설정이 필요하므로 현재는 데이터 확인용입니다.)")

    # 기존 대시보드 로직 (이전 코드와 동일)
    # ... (생략된 분석 및 출력 코드) ...
    
    if st.button("🔄 데이터 새로고침"):
        st.rerun()
