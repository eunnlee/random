import streamlit as st
import pandas as pd
import random

st.title("🎉 이벤트 무작위 추첨기")
st.write("CSV 파일을 업로드하고, 원하는 인원 수를 정해 추첨하세요!")

# CSV 업로드
uploaded_file = st.file_uploader("참가자 명단 CSV 업로드", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 참가자 리스트 보여주기
    st.subheader("참가자 목록")
    st.write(df)

    # 추첨 인원 수 설정
    max_participants = len(df)
    num_winners = st.number_input("당첨자 수를 입력하세요", min_value=1, max_value=max_participants, value=1, step=1)

    # 추첨 버튼
    if st.button("🎲 당첨자 추첨하기"):
        winners = df.sample(n=num_winners)
        st.success("🎉 당첨자 목록")
        st.dataframe(winners)

        # 다운로드 버튼
        csv = winners.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 당첨자 CSV 다운로드",
            data=csv,
            file_name='winners.csv',
            mime='text/csv'
        )
