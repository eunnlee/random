# 파일명 예시: event_draw.py

import streamlit as st
import pandas as pd
import re
import io
import requests

st.set_page_config(page_title="이벤트 추첨기", page_icon="🎁")

st.title("🎁 이벤트 무작위 추첨기")
st.markdown("""
이 도구는 **공정한 이벤트 추첨**을 위해 만들어졌습니다.

- ✅ 텔레그램 핸들 유효성 검사 (영문/숫자/밑줄만 허용, 공백 자동 제거)
- ✅ 트위터 아이디 유효성 검사 (입력 시만 적용)
- ✅ 전화번호는 숫자만 추출 후, 11자리만 허용 (010xxxxxxxx 형식)
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
    if uploaded_file:
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
    # 정리 및 유효성 검사
    def is_valid_telegram(s):
        if not isinstance(s, str):
            return False
        s = s.strip().lstrip('@')
        return bool(re.fullmatch(r'[a-zA-Z0-9_]+', s))

    def is_valid_or_empty_twitter(s):
        if not isinstance(s, str) or s.strip() == "":
            return True
        s = s.strip().lstrip('@')
        return bool(re.fullmatch(r'[A-Za-z0-9_]{1,15}', s))

    def format_and_validate_phone(p):
        if not isinstance(p, str):
            return False
        digits = re.sub(r'\D', '', p)
        if len(digits) == 10 and digits.startswith("10"):
            digits = "0" + digits
        return digits if len(digits) == 11 else False

    df["telegram_valid"] = df["telegram"].apply(is_valid_telegram)
    invalid_telegram = df[df["telegram_valid"] == False]
    df = df[df["telegram_valid"] == True].drop(columns=["telegram_valid"])

    df["twitter_valid"] = df["twitter"].apply(is_valid_or_empty_twitter)
    invalid_twitter = df[df["twitter_valid"] == False]
    df = df[df["twitter_valid"] == True].drop(columns=["twitter_valid"])

    df["phone"] = df["phone"].apply(format_and_validate_phone)
    invalid_phone = df[df["phone"] == False]
    df = df[df["phone"] != False]

    # 중복 제거
    original_count = len(df)
    duplicates = df[df.duplicated()]
    df = df.drop_duplicates()
    removed = original_count - len(df)

    # 안내 메시지
    if not invalid_telegram.empty:
        st.warning(f"🚫 유효하지 않은 텔레그램 핸들 {len(invalid_telegram)}명 제외")
        with st.expander("❌ 제외된 텔레그램 참가자"):
            st.dataframe(invalid_telegram)
    if not invalid_twitter.empty:
        st.warning(f"🚫 유효하지 않은 트위터 아이디 {len(invalid_twitter)}명 제외")
        with st.expander("❌ 제외된 트위터 참가자"):
            st.dataframe(invalid_twitter)
    if not invalid_phone.empty:
        st.warning(f"🚫 유효하지 않은 전화번호 {len(invalid_phone)}명 제외")
        with st.expander("❌ 제외된 전화번호 참가자"):
            st.dataframe(invalid_phone)
    if removed > 0:
        st.warning(f"⚠️ 중복 참가자 {removed}명 제거 완료")
        with st.expander("📋 중복 제거된 참가자 목록"):
            st.dataframe(duplicates)

    st.subheader(f"🎯 최종 유효 참가자 수: {len(df)}명")
    st.dataframe(df)

    # 추첨 상품별 인원 설정
    st.subheader("🎁 추첨 상품과 인원 설정")
    reward_count = st.number_input("추첨할 상품 개수", min_value=1, value=1, step=1)
    rewards = {}

    for i in range(reward_count):
        col1, col2 = st.columns([2, 1])
        with col1:
            prize = st.text_input(f"상품 {i+1} 이름", key=f"prize_{i}")
        with col2:
            count = st.number_input(f"{prize} 당첨자 수", min_value=1, max_value=len(df), value=1, key=f"count_{i}")
        if prize:
            rewards[prize] = count

    if "drawn" not in st.session_state:
        st.session_state.drawn = False

    if st.button("🎲 당첨자 추첨하기") and not st.session_state.drawn:
        drawn = []
        remaining_df = df.copy()

        for prize, count in rewards.items():
            count = min(count, len(remaining_df))
            selected = remaining_df.sample(n=count)
            selected["상품"] = prize
            drawn.append(selected)
            remaining_df = remaining_df.drop(selected.index)

        winners_df = pd.concat(drawn)
        st.session_state.winners = winners_df
        st.session_state.drawn = True

        st.success("🎉 아래는 무작위로 추첨된 당첨자 목록입니다!")
        st.dataframe(winners_df)

        csv_public = winners_df[["telegram", "상품"]].to_csv(index=False).encode("utf-8-sig")
        csv_full = winners_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button("📥 당첨자 발표용 (텔레그램+상품)", csv_public, "winners_public.csv", "text/csv")
        st.download_button("🔒 운영자용 전체 정보 다운로드", csv_full, "winners_full.csv", "text/csv")

    elif st.session_state.drawn:
        st.warning("⚠️ 이미 추첨이 완료되었습니다. 추첨은 한 번만 가능합니다.")
        st.dataframe(st.session_state.winners)
