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

st.markdown("📝 **CSV/시트 형식 안내**")
st.markdown("""
- **1행**: 설명용 텍스트 (자동 무시됨)
- **2행부터** 실제 참가자 정보
- 열 순서: `텔레그램 핸들`, `트위터 아이디 (선택사항)`, `전화번호`
""")

upload_mode = st.radio("📤 데이터를 어떻게 불러올까요?", ["CSV 업로드", "Google Sheets 사용"])

df = None

if upload_mode == "CSV 업로드":
    uploaded_file = st.file_uploader("📂 참가자 CSV 업로드", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, skiprows=1, names=["telegram", "twitter", "phone"])

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
                df = pd.read_csv(io.StringIO(response.text), skiprows=1, names=["telegram", "twitter", "phone"])
            except Exception:
                st.error("❌ Google Sheets 데이터를 불러오는 데 실패했습니다.")
        else:
            st.warning("⚠️ 유효한 Google Sheets 링크를 입력해주세요.")

if df is not None:
    # 텔레그램 유효성 검사
    def is_valid_telegram(s):
        if not isinstance(s, str):
            return False
        s = s.lstrip('@')
        return bool(re.fullmatch(r'[a-zA-Z0-9_]+', s))

    df['telegram_valid'] = df['telegram'].apply(is_valid_telegram)
    invalid_telegram = df[df['telegram_valid'] == False]
    df = df[df['telegram_valid'] == True].drop(columns=['telegram_valid'])

    if not invalid_telegram.empty:
        st.warning(f"🚫 유효하지 않은 텔레그램 핸들 {len(invalid_telegram)}명 제외")
        with st.expander("❌ 제외된 텔레그램 참가자"):
            st.dataframe(invalid_telegram)

    # 트위터 유효성 검사
    def is_valid_or_empty_twitter(s):
        if not isinstance(s, str) or s.strip() == "":
            return True
        s = s.lstrip('@')
        return bool(re.fullmatch(r'[A-Za-z0-9_]{1,15}', s))

    df['twitter_valid'] = df['twitter'].apply(is_valid_or_empty_twitter)
    invalid_twitter = df[df['twitter_valid'] == False]
    df = df[df['twitter_valid'] == True].drop(columns=['twitter_valid'])

    if not invalid_twitter.empty:
        st.warning(f"🚫 유효하지 않은 트위터 아이디 {len(invalid_twitter)}명 제외")
        with st.expander("❌ 제외된 트위터 참가자"):
            st.dataframe(invalid_twitter)

    # 중복 제거
    original_count = len(df)
    duplicates = df[df.duplicated()]
    df = df.drop_duplicates()
    removed = original_count - len(df)

    if removed > 0:
        st.warning(f"⚠️ 중복 참가자 {removed}명 제거 완료")
        with st.expander("📋 중복 제거된 참가자 목록"):
            st.dataframe(duplicates)

    st.subheader(f"🎯 최종 유효 참가자 수: {len(df)}명")
    st.dataframe(df)

    # 추첨
    num_winners = st.number_input("🎁 추첨할 당첨자 수", min_value=1, max_value=len(df), value=1, step=1)

    if 'drawn' not in st.session_state:
        st.session_state.drawn = False

    if st.button("🎲 당첨자 추첨하기") and not st.session_state.drawn:
        winners = df.sample(n=num_winners)
        st.session_state.winners = winners
        st.session_state.drawn = True
        st.success("🎉 아래는 무작위로 추첨된 당첨자 목록입니다!")
        st.dataframe(winners)

        # 발표용
        csv_public = winners[["telegram"]].to_csv(index=False).encode('utf-8-sig')
        csv_full = winners.to_csv(index=False).encode('utf-8-sig')

        st.download_button("📥 당첨자 발표용 (텔레그램만)", csv_public, "winners_public.csv", "text/csv")
        st.download_button("🔒 운영자용 전체 정보 다운로드", csv_full, "winners_full.csv", "text/csv")

    elif st.session_state.drawn:
        st.warning("⚠️ 이미 추첨이 완료되었습니다. 추첨은 한 번만 가능합니다.")
        st.dataframe(st.session_state.winners)
st.markdown("---")
col1, col2 = st.columns([1, 10])
with col1:
    st.image("logo.png", width=60)
with col2:
    st.markdown("**Powered by INFCL**")
