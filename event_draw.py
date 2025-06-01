import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="이벤트 추첨기", page_icon="🎁")

st.title("🎁 이벤트 무작위 추첨기")
st.markdown("""
이 도구는 **공정한 이벤트 추첨**을 위해 만들어졌습니다.  
CSV로 참가자 명단을 업로드하면, 유효성 검사 및 중복 제거 후 신뢰할 수 있는 무작위 추첨을 도와줍니다.  
""")

# 📄 샘플 CSV 생성
sample_df = pd.DataFrame({
    "이 열은 텔레그램 핸들을 입력하세요": ["@sample1", "@sample2"],
    "트위터 아이디 입력": ["@tw1", "@tw2"],
    "기프티콘 받을 전화번호 입력": ["010-1234-5678", "010-9876-5432"]
})
sample_csv = sample_df.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📄 샘플 CSV 파일 다운로드",
    data=sample_csv,
    file_name='sample_participants.csv',
    mime='text/csv'
)

# 📥 CSV 업로드 안내
st.markdown("📝 **CSV 형식 안내**")
st.markdown("""
- **첫 번째 행**: 안내용 문구 (예: '이 열은 텔레그램 핸들을 입력하세요')  
- **두 번째 행부터** 실제 데이터가 들어가야 합니다.
- 열 순서: 텔레그램 핸들 / 트위터 아이디 / 전화번호
""")

uploaded_file = st.file_uploader("📂 참가자 CSV 파일 업로드", type="csv")

if uploaded_file is not None:
    # 1️⃣ CSV 읽기 (첫 행은 설명이므로 skip)
    df = pd.read_csv(uploaded_file, skiprows=1, names=["telegram", "twitter", "phone"])

    # 2️⃣ 유효성 검사: telegram 핸들
    st.markdown("🔎 **유효성 검사: 텔레그램 핸들**")
    st.markdown("영문자/숫자로만 구성된 핸들만 유효하며, `@`로 시작해도 괜찮습니다.")

    def is_valid_handle(s):
        if not isinstance(s, str):
            return False
        s = s.lstrip('@')
        return bool(re.fullmatch(r'[a-zA-Z0-9]+', s))

    df['valid'] = df['telegram'].apply(is_valid_handle)
    invalid_entries = df[df['valid'] == False]
    df = df[df['valid'] == True].drop(columns=['valid'])

    if not invalid_entries.empty:
        st.warning(f"🚫 유효하지 않아 제외된 참가자 수: {len(invalid_entries)}명")
        with st.expander("❌ 제외된 참가자 보기"):
            st.dataframe(invalid_entries)
    else:
        st.info("✅ 모든 텔레그램 핸들이 유효합니다.")

    # 3️⃣ 중복 제거
    st.markdown("🔁 **중복 제거**")
    original_count = len(df)
    duplicates = df[df.duplicated()]
    df = df.drop_duplicates()
    unique_count = len(df)
    removed = original_count - unique_count

    if removed > 0:
        st.warning(f"⚠️ 중복 참가자 {removed}명 제거 완료")
        with st.expander("📋 중복 제거된 참가자 목록"):
            st.dataframe(duplicates)
    else:
        st.info("👍 중복된 참가자는 없었습니다.")

    st.subheader(f"🎯 최종 유효 참가자 수: {unique_count}명")
    st.dataframe(df)

    # 4️⃣ 추첨
    num_winners = st.number_input("🎁 추첨할 당첨자 수", min_value=1, max_value=unique_count, value=1, step=1)

    if st.button("🎲 당첨자 추첨하기"):
        winners = df.sample(n=num_winners)
        st.success("🎉 당첨자 추첨 완료!")

        # 📤 결과 파일: 공개용 (telegram만)
        public = winners[["telegram"]].copy()
        csv_public = public.to_csv(index=False).encode('utf-8-sig')

        # 📤 결과 파일: 운영자용 (전체 정보)
        csv_full = winners.to_csv(index=False).encode('utf-8-sig')

        st.download_button(
            label="📥 당첨자 발표용 (텔레그램만)",
            data=csv_public,
            file_name="winners_public.csv",
            mime="text/csv"
        )

        st.download_button(
            label="🔒 운영자용 전체 정보 다운로드",
            data=csv_full,
            file_name="winners_full.csv",
            mime="text/csv"
        )