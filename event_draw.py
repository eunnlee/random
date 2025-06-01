import streamlit as st
import pandas as pd

st.set_page_config(page_title="이벤트 추첨기", page_icon="🎁")

st.title("🎁 이벤트 무작위 추첨기")
st.markdown("""
이 도구는 **공정한 이벤트 추첨**을 위해 만들어졌습니다.  
CSV로 참가자 명단을 업로드하면, 중복된 사람을 자동으로 제거하고 무작위로 당첨자를 추첨합니다.  
""")

uploaded_file = st.file_uploader("📄 참가자 명단 CSV 업로드", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.markdown("✅ **중복 참가자 자동 제거 기능이 적용됩니다.**")
    st.markdown("같은 이름이나 ID가 여러 번 들어 있어도, 1회만 인정돼요. **공정성 확보**를 위해 필수입니다.")

    # 중복 제거 전후 비교
    original_count = len(df)
    duplicates = df[df.duplicated()]
    df = df.drop_duplicates()
    unique_count = len(df)
    duplicates_removed = original_count - unique_count

    # 중복 안내 메시지
    if duplicates_removed > 0:
        st.warning(f"⚠️ 중복된 참가자 {duplicates_removed}명이 자동 제거되었습니다.")
        with st.expander("👀 제거된 중복 참가자 보기"):
            st.dataframe(duplicates)
    else:
        st.info("👍 중복된 참가자는 없었습니다.")

    st.subheader(f"🎯 최종 유효 참가자 수: {unique_count}명")
    st.dataframe(df)

    # 추첨 인원 수 입력
    num_winners = st.number_input("추첨할 당첨자 수를 입력하세요", min_value=1, max_value=unique_count, value=1, step=1)

    # 추첨 버튼
    if st.button("🎲 당첨자 추첨하기"):
        winners = df.sample(n=num_winners)
        st.success("🎉 당첨자 목록입니다!")
        st.dataframe(winners)

        # CSV 다운로드 버튼
        csv = winners.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 당첨자 CSV 다운로드",
            data=csv,
            file_name='winners.csv',
            mime='text/csv'
        )

else:
    st.info("👆 먼저 참가자 CSV 파일을 업로드해 주세요.")
