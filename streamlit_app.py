#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="타이타닉 생존 분석 대시보드",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>
[data-testid="block-container"] {
    padding: 1rem 2rem 0rem 2rem;
}
[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv')

#######################
# Sidebar
with st.sidebar:
    st.title("🛳 타이타닉 생존 분석 대시보드")
    st.caption("필터를 선택하면 모든 지표와 차트가 실시간으로 업데이트됩니다.")
    st.divider()

    # 색상 테마 선택
    theme = st.selectbox(
        "색상 테마 선택",
        ["blues", "greens", "viridis", "plasma", "magma", "inferno"],
        index=0
    )
    st.session_state["theme"] = theme

    # 필터 옵션 준비
    _df = df_reshaped.copy()
    _df["Embarked_filled"] = _df["Embarked"].fillna("Unknown")

    pclass_options = sorted(_df["Pclass"].dropna().unique())
    sex_options = sorted(_df["Sex"].dropna().unique())
    embarked_options = ["C", "Q", "S", "Unknown"]

    age_min, age_max = int(_df["Age"].min(skipna=True)), int(_df["Age"].max(skipna=True))
    fare_min, fare_max = float(_df["Fare"].min(skipna=True)), float(_df["Fare"].max(skipna=True))

    # --- 필터 ---
    st.subheader("🔍 필터")
    sel_pclass = st.multiselect("객실 등급 (Pclass)", options=pclass_options, default=pclass_options)
    sel_sex = st.multiselect("성별 (Sex)", options=sex_options, default=sex_options)
    sel_embarked = st.multiselect("승선 항구 (Embarked)", options=embarked_options, default=embarked_options)
    age_range = st.slider("나이 범위 (Age)", min_value=age_min, max_value=age_max, value=(age_min, age_max))
    fare_range = st.slider("요금 범위 (Fare)", min_value=fare_min, max_value=fare_max, value=(fare_min, fare_max))

    # 필터 적용
    view = _df[
        (_df["Pclass"].isin(sel_pclass)) &
        (_df["Sex"].isin(sel_sex)) &
        (_df["Embarked_filled"].isin(sel_embarked)) &
        ((_df["Age"].between(age_range[0], age_range[1])) | (_df["Age"].isna())) &
        (_df["Fare"].between(fare_range[0], fare_range[1]))
    ].copy()

    st.session_state["df_view"] = view

    # --- 현재 필터 결과 ---
    st.divider()
    st.subheader("📌 현재 필터 결과")
    total_cnt = len(view)
    survived_cnt = int(view["Survived"].sum())
    survived_rate = (survived_cnt / total_cnt * 100) if total_cnt else 0.0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("탑승객 수", f"{total_cnt:,}")
    kpi2.metric("생존자 수", f"{survived_cnt:,}")
    kpi3.metric("생존률", f"{survived_rate:0.1f}%")

    if st.button("필터 초기화"):
        st.experimental_rerun()

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap="medium")

# --- 왼쪽 컬럼 ---
with col[0]:
    st.subheader("🚢 생존 개요")
    df_view = st.session_state["df_view"]

    if df_view.empty:
        st.info("데이터가 없습니다. 필터를 확인하세요.")
    else:
        # KPI
        total_passengers = len(df_view)
        survived_count = int(df_view["Survived"].sum())
        dead_count = total_passengers - survived_count
        survived_rate = survived_count / total_passengers * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("총 탑승객", f"{total_passengers:,}")
        c2.metric("생존자", f"{survived_count:,}", f"{survived_rate:0.1f}%")
        c3.metric("사망자", f"{dead_count:,}")

        st.divider()

        # 객실 등급별 생존률
        st.markdown("**🎟 객실 등급별 생존률**")
        pclass_stats = df_view.groupby("Pclass")["Survived"].mean().mul(100).round(1).reset_index()
        st.table(pclass_stats.rename(columns={"Survived": "생존률(%)"}))

        st.divider()

        # 성별 생존률
        st.markdown("**⚖ 성별 생존률**")
        sex_stats = df_view.groupby("Sex")["Survived"].mean().mul(100).round(1).reset_index()
        st.table(sex_stats.rename(columns={"Survived": "생존률(%)"}))

# --- 중앙 컬럼 ---
with col[1]:
    st.subheader("📊 분포 & 히트맵")
    df_view = st.session_state["df_view"]

    if df_view.empty:
        st.info("데이터가 없습니다.")
    else:
        # 나이 × 객실 등급 생존률 히트맵
        df_view["AgeGroup"] = pd.cut(df_view["Age"], bins=[0,10,20,30,40,50,60,70,80,90], 
                                     labels=["0-9","10-19","20-29","30-39","40-49","50-59","60-69","70-79","80+"])
        heatmap_data = df_view.groupby(["AgeGroup","Pclass"])["Survived"].mean().reset_index()
        heatmap_data["Survived"] *= 100

        heatmap_chart = alt.Chart(heatmap_data).mark_rect().encode(
            x="Pclass:N",
            y="AgeGroup:N",
            color=alt.Color("Survived:Q", scale=alt.Scale(scheme=st.session_state["theme"]), title="생존률(%)"),
            tooltip=["AgeGroup","Pclass","Survived"]
        ).properties(height=350)
        st.altair_chart(heatmap_chart, use_container_width=True)

        st.divider()

        # 나이 × 요금 산점도
        scatter = px.scatter(
            df_view, x="Age", y="Fare", color="Survived", symbol="Sex",
            hover_data=["Pclass","Embarked"], color_continuous_scale=st.session_state["theme"]
        )
        scatter.update_layout(height=400, margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(scatter, use_container_width=True)

        st.divider()

        # 항구별 승객 수
        embarked_count = df_view["Embarked"].fillna("Unknown").value_counts().reset_index()
        embarked_count.columns = ["승선 항구","탑승객 수"]
        bar_chart = alt.Chart(embarked_count).mark_bar().encode(
            x="승선 항구:N", y="탑승객 수:Q",
            color=alt.Color("승선 항구:N", scale=alt.Scale(scheme=st.session_state["theme"])),
            tooltip=["승선 항구","탑승객 수"]
        ).properties(height=250)
        st.altair_chart(bar_chart, use_container_width=True)

# --- 오른쪽 컬럼 ---
with col[2]:
    st.subheader("🏆 상위 그룹 & 세부 정보")
    df_view = st.session_state["df_view"]

    if df_view.empty:
        st.info("데이터 없음")
    else:
        # 상위 생존 그룹
        st.markdown("**Top 생존 그룹 (객실 등급 × 성별)**")
        top_groups = (
            df_view.groupby(["Pclass","Sex"])["Survived"].sum()
            .reset_index().sort_values("Survived", ascending=False).head(5)
        )
        st.dataframe(top_groups, use_container_width=True, hide_index=True)

        st.divider()

        # 항구별 생존 통계
        st.markdown("**🛳 항구별 생존 통계**")
        embarked_stats = (
            df_view.groupby("Embarked")["Survived"]
            .agg(['count','sum','mean'])
            .rename(columns={'count':'승객 수','sum':'생존자 수','mean':'생존률'})
        )
        embarked_stats["생존률"] = (embarked_stats["생존률"]*100).round(1)
        st.dataframe(embarked_stats, use_container_width=True)

        st.divider()

        # About
        with st.expander("ℹ️ 대시보드 정보"):
            st.markdown("""
            - **데이터:** Titanic dataset (Kaggle)  
            - **필터:** 객실 등급, 성별, 항구, 나이, 요금 범위 적용 가능  
            - **시각화:** 히트맵, 산점도, 막대그래프  
            """)
