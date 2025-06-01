import streamlit as st
import pandas as pd
import re
import io
import requests

st.set_page_config(page_title="이벤트 추첨기", page_icon="🎁")

st.title("🎁 이벤트 무작위 추첨기")
st.markdown("""
이 도구는 **공정한 이벤트 추첨**을 위해 만들어졌습니다.  
다음과 같은 기능이 자동 적용됩니다:

- ✅ 텔레그램 핸들 유효성 검사 (영문/숫자/밑줄만 허용)
- ✅ 트위터 아이디 유효성 검사 (입력한 경우만 적용)
- 🔁 중복 참가자 자동 제거
- 🖼️ 업로드 데이터 미리보기 및 정제 상태 시각화
- 🎲 추첨은 단 1회만 가능
- 📤 당첨자 발표용 / 운영자용 파일 제공
""")

st.markdown("⚠️ **한 번 추첨하면 다시 돌릴 수 없습니다.**")

# 샘플 CSV 다운로드
sample_df = pd.DataFrame({
    "이 열은 텔레그램 핸들을 입력하세요": ["@sample1", "@sample2"],
    "트위터 아이디 입력 (선택사항)": ["@twitter1", ""],
    "기프티콘 받을 전화번호 입력": ["010-1234-5678", "010-9876-5432"]
})
sample_csv = sample_df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📄 샘플 CSV 파일 다운로드", sample_csv, "sample.csv", "text/csv")

upload_mode = st.radio("📤 데이터를 어떻게 불러올까요?", ["CSV 업로드", "Google Sheets 사용"])

df, raw_df = None, None
state_message = "⚠️ 아직 데이터를 불러오지 않았습니다."

if upload_mode == "CSV 업로드":
    uploaded_file = st.file_uploader("📂 참가자 CSV 업로드", type="csv")
    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file)
        try:
            df = pd.read_csv(uploaded_file, skiprows=1, names=["telegram", "twitter", "phone"])
            state_message = "✅ CSV 데이터 업로드 및 변환 완료!"
        except:
            st.error("CSV 파일 형식이 올바르지 않습니다.")

elif upload_mode == "Google Sheets 사용":
    sheet_url = st.text_input("🔗 Google Sheets 공유 링크 입력")
    if sheet_url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
        if match:
            sheet_id = match.group(1)
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            try:
                response = requests.get(export_url)
                response.encoding = 'utf-8'
                raw_df = pd.read_csv(io.StringIO(response.text))
                df = pd.read_csv(io.StringIO(response.text), skiprows=1, names=["telegram", "twitter", "phone"])
                state_message = "✅ Google Sheets 데이터 불러오기 완료!"
            except:
                st.error("❌ 데이터를 불러오는 데 실패했습니다.")
        else:
            st.warning("⚠️ 유효한 Google Sheets 링크를 입력해주세요.")

# ✅ 상태 표시
st.info(f"📌 현재 상태: {state_message}")

# ✅ 업로드 원본 미리보기
if raw_df is not None:
    st.subheader("🔍 업로드한 원본 데이터 미리보기 (상위 10개)")
    st.dataframe(raw_df.head(10))
