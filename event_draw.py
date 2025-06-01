import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="이벤트 추첨기", page_icon="🎁")

st.title("🎁 이벤트 무작위 추첨기")
st.markdown("""
이 도구는 **공정한 이벤트 추첨**을 위해 만들어졌습니다.  
CSV 파일을 업로드하면 다음과 같은 기능이 자동 적용됩니다:

- ✅ 텔레그램 핸들 유효성 검사 (영문/숫자/밑줄만 허용)
- ✅ 트위터 아이디 유효성 검사 (입력한 경우만 적용)
- 🔁 중복 참가자 자동 제거
- 🎲 추첨은 **단 1회만 가능**
- 📤 당첨자 발표용/운영자용 결과 파일 따로 제공
""")

st.markdown("⚠️ **한 번 추첨하면 다시 돌릴 수 없습니다.**")
st.markdown("추첨은 단 1회만 가능하며, 이후에는 재추첨이 불가능합니다.")

# 샘플 CSV 다운로드
sample_df = pd.DataFrame({
    "이 열은 텔레그램 핸들을 입력하세요": ["@sample1", "@sample2"],
    "트위터 아이디 입력 (선택사항)": ["@twitter1", ""],
    "기프티콘 받을 전화번호 입력": ["010-1234-5678", "010-9876-5432"]
})
sample_csv = sample_df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📄 샘플 CSV 파일 다운로드",
    data=sample_csv,
    file_name='sample_participants.csv',
    mime='text/csv'
)

st.markdown("📝 **CSV 형식 안내**")
st.markdown("""
- **1행**: 설명용 텍스트 (프로그램에서 자동 건너뜁니다)
- **2행부터** 실제 참가자 정보
- 열 순서: `텔레그램 핸들`, `트위터 아이디 (선택사항)`, `전화번호`
""")

uploaded_file = st.file_uploader("📂 참가자 CSV 업로드", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, skiprows=1, names=["telegram", "twitter", "phone"])

    # === 텔레그램 유효성 검사 ===
    st.markdown("🔎 **1단계: 텔레그램 핸들 유효성 검사**")
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
    else:
        st.info("✅ 모든 텔레그램 핸들이 유효합니다.")

    # === 트위터 유효성 검사 (선택사항) ===
    st.markdown("🔎 **2단계: 트위터 아이디 유효성 검사 (선택사항)**")
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
    else:
        st.info("✅ 모든 트위터 아이디가 유효하거나 입력되지 않았습니다.")

    # === 중복 제거 ===
    st.markdown("🔁 **3단계: 중복 참가자 제거**")
    original_count = len(df)
    duplicates = df[df.duplicated()]
    df = df.drop_duplicates()
    removed = original_count - len(df)

    if removed > 0:
        st.warning(f"⚠️ 중복 참가자 {removed}명 제거 완료")
        with st.expander("📋 중복 제거된 참가자 목록"):
            st.dataframe(duplicates)
    else:
        st.info("👍 중복된 참가자는 없었습니다.")

    st.subheader(f"🎯 최종 유효 참가자 수: {len(df)}명")
    st.dataframe(df)

    # === 추첨: 단 1회 ===
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

        st.download_button("📥 당첨자 발표용 (텔레그램만)", data=csv_public, file_name="winners_public.csv", mime="text/csv")
        st.download_button("🔒 운영자용 전체 정보 다운로드", data=csv_full, file_name="winners_full.csv", mime="text/csv")

    elif st.session_state.drawn:
        st.warning("⚠️ 이미 추첨이 완료되었습니다. 추첨은 한 번만 가능합니다.")
        st.dataframe(st.session_state.winners)
