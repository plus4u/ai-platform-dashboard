import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="데이터 기술통계 & 시각화 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 스타일링
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px 16px;
        border-radius: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] {
            background-color: #1e293b;
            border: 1px solid #334155;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 샘플 데이터 생성 함수
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def generate_sample_data(n_rows: int = 300) -> pd.DataFrame:
    """제조/공정 품질 관리 샘플 데이터셋 생성"""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2026-01-01", periods=n_rows, freq="6h")
    lines = rng.choice(["A라인", "B라인", "C라인"], size=n_rows, p=[0.4, 0.35, 0.25])
    shifts = rng.choice(["주간", "야간"], size=n_rows, p=[0.6, 0.4])
    operators = rng.choice(["김엔지니어", "이엔지니어", "박엔지니어", "최엔지니어"], size=n_rows)

    temp = rng.normal(loc=185.0, scale=6.5, size=n_rows) + np.where(lines == "A라인", 2.5, 0.0)
    pressure = rng.normal(loc=4.2, scale=0.35, size=n_rows) + (temp - 185.0) * 0.02
    vibration = rng.gamma(shape=2.2, scale=1.1, size=n_rows)
    humidity = rng.uniform(35.0, 65.0, size=n_rows)

    # 수율(%) 및 불량 여부 계산
    yield_rate = (
        98.5
        - 0.12 * np.abs(temp - 185.0)
        - 1.8 * np.abs(pressure - 4.2)
        - 0.45 * vibration
        + rng.normal(0, 0.6, size=n_rows)
    )
    yield_rate = np.clip(yield_rate, 82.0, 100.0)
    defect_status = np.where(yield_rate < 95.0, "불량주의", "정상")

    df = pd.DataFrame(
        {
            "측정일시": dates,
            "생산라인": lines,
            "근무조": shifts,
            "담당자": operators,
            "공정온도_C": np.round(temp, 2),
            "공정압력_bar": np.round(pressure, 3),
            "진동수치_mm_s": np.round(vibration, 2),
            "습도_pct": np.round(humidity, 1),
            "수율_pct": np.round(yield_rate, 2),
            "품질상태": defect_status,
        }
    )

    # 일부 결측치 시뮬레이션
    df.loc[rng.choice(n_rows, size=5, replace=False), "진동수치_mm_s"] = np.nan
    df.loc[rng.choice(n_rows, size=3, replace=False), "습도_pct"] = np.nan
    return df


@st.cache_data(show_spinner=False)
def get_excel_sheet_names(file_bytes: bytes) -> list[str]:
    excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
    return excel_file.sheet_names


@st.cache_data(show_spinner=False)
def load_dataframe(
    file_bytes: bytes,
    file_name: str,
    encoding: str = "자동 감지",
    sheet_name: str | int = 0,
    csv_sep: str = ",",
) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        encodings_to_try = (
            ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]
            if encoding == "자동 감지"
            else [encoding]
        )
        last_err = None
        for enc in encodings_to_try:
            try:
                return pd.read_csv(io.BytesIO(file_bytes), encoding=enc, sep=csv_sep)
            except Exception as e:
                last_err = e
        raise ValueError(f"CSV 인코딩 로드 실패: {last_err}")
    elif lower_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    else:
        raise ValueError("지원하지 않는 파일 형식입니다. (.csv, .xlsx, .xls 만 지원)")


# -----------------------------------------------------------------------------
# 3. 기술통계 계산 함수
# -----------------------------------------------------------------------------
def compute_numeric_stats(df: pd.DataFrame, num_cols: list[str]) -> pd.DataFrame:
    """수치형 변수의 상세 기술통계량 계산"""
    if not num_cols:
        return pd.DataFrame()

    desc = df[num_cols].describe().T
    stats_df = pd.DataFrame(index=num_cols)
    stats_df["유효건수(Count)"] = desc["count"].astype(int)
    stats_df["결측치(Missing)"] = df[num_cols].isna().sum()
    stats_df["결측비율(%)"] = (df[num_cols].isna().mean() * 100).round(2)
    stats_df["평균(Mean)"] = desc["mean"].round(4)
    stats_df["표준편차(Std)"] = desc["std"].round(4)
    stats_df["분산(Var)"] = df[num_cols].var().round(4)
    stats_df["변동계수(CV)"] = (
        (desc["std"] / desc["mean"].replace(0, np.nan)).abs().round(4)
    )
    stats_df["최솟값(Min)"] = desc["min"].round(4)
    stats_df["1사분위수(25%)"] = desc["25%"].round(4)
    stats_df["중앙값(50%)"] = desc["50%"].round(4)
    stats_df["3사분위수(75%)"] = desc["75%"].round(4)
    stats_df["최댓값(Max)"] = desc["max"].round(4)
    stats_df["IQR(Q3-Q1)"] = (desc["75%"] - desc["25%"]).round(4)
    stats_df["왜도(Skewness)"] = df[num_cols].skew().round(4)
    stats_df["첨도(Kurtosis)"] = df[num_cols].kurt().round(4)
    stats_df.index.name = "변수명"
    return stats_df.reset_index()


def compute_categorical_stats(df: pd.DataFrame, cat_cols: list[str]) -> pd.DataFrame:
    """범주형/문자열 변수의 기술통계량 계산"""
    if not cat_cols:
        return pd.DataFrame()

    records = []
    total_len = len(df)
    for col in cat_cols:
        s = df[col]
        non_null = s.dropna()
        count = len(non_null)
        missing = s.isna().sum()
        unique_cnt = non_null.nunique()
        if count > 0:
            vc = non_null.value_counts()
            top_val = str(vc.index[0])
            top_freq = int(vc.iloc[0])
            top_ratio = round((top_freq / count) * 100, 2)
        else:
            top_val, top_freq, top_ratio = "-", 0, 0.0

        records.append(
            {
                "변수명": col,
                "데이터타입": str(s.dtype),
                "유효건수(Count)": count,
                "결측치(Missing)": int(missing),
                "결측비율(%)": round((missing / total_len) * 100, 2) if total_len else 0.0,
                "고유값수(Unique)": int(unique_cnt),
                "최빈값(Top)": top_val,
                "최빈값빈도(Freq)": top_freq,
                "최빈값비율(%)": top_ratio,
            }
        )
    return pd.DataFrame(records)


def convert_df_to_excel_bytes(
    raw_df: pd.DataFrame, num_stats: pd.DataFrame, cat_stats: pd.DataFrame
) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not num_stats.empty:
            num_stats.to_excel(writer, sheet_name="수치형_기술통계", index=False)
        if not cat_stats.empty:
            cat_stats.to_excel(writer, sheet_name="범주형_기술통계", index=False)
        raw_df.head(1000).to_excel(writer, sheet_name="데이터_샘플(최대1000행)", index=False)
    return output.getvalue()


# -----------------------------------------------------------------------------
# 4. 사이드바: 데이터 업로드 및 필터 설정
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📂 데이터 업로드 및 설정")
    st.caption("CSV 또는 Excel(XLSX/XLS) 파일을 업로드하여 기술통계와 시각화를 즉시 확인하세요.")

    uploaded_file = st.file_uploader(
        "파일 선택 (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        help="한글 CSV(UTF-8, CP949, EUC-KR) 및 다중 시트 Excel 파일을 지원합니다.",
    )

    use_sample = False
    if uploaded_file is None:
        st.info("💡 업로드된 파일이 없습니다. 아래 옵션을 켜면 샘플 제조/품질 데이터로 대시보드를 체험할 수 있습니다.")
        use_sample = st.checkbox("샘플 제조 공정 데이터 사용하기", value=True)

    df_raw = None
    source_label = ""

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        source_label = f"업로드 파일: `{file_name}`"

        if file_name.lower().endswith(".csv"):
            with st.expander("⚙️ CSV 읽기 옵션", expanded=False):
                encoding_opt = st.selectbox(
                    "인코딩",
                    ["자동 감지", "utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"],
                )
                sep_label = st.selectbox(
                    "구분자 (Delimiter)",
                    ["쉼표 (,)", "세미콜론 (;)", "탭 (\\t)", "파이프 (|)"],
                )
                sep_map = {
                    "쉼표 (,)": ",",
                    "세미콜론 (;)": ";",
                    "탭 (\\t)": "\t",
                    "파이프 (|)": "|",
                }
            try:
                df_raw = load_dataframe(
                    file_bytes,
                    file_name,
                    encoding=encoding_opt,
                    csv_sep=sep_map[sep_label],
                )
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        else:
            try:
                sheet_names = get_excel_sheet_names(file_bytes)
                selected_sheet = (
                    st.selectbox("📑 분석할 엑셀 시트 선택", sheet_names)
                    if len(sheet_names) > 1
                    else sheet_names[0]
                )
                df_raw = load_dataframe(
                    file_bytes, file_name, sheet_name=selected_sheet
                )
                source_label += f" (시트: `{selected_sheet}`)"
            except Exception as e:
                st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")

    elif use_sample:
        df_raw = generate_sample_data(300)
        source_label = "샘플 데이터: `제조 공정 품질 모니터링 (300행)`"

    # 날짜 컬럼 자동 변환 옵션 및 데이터 필터링
    if df_raw is not None and not df_raw.empty:
        st.divider()
        st.subheader("🛠️ 전처리 및 필터링")

        auto_parse_dates = st.checkbox(
            "날짜 형식 문자열 자동 변환",
            value=True,
            help="날짜/시간 형태의 문자열 컬럼을 자동으로 datetime 타입으로 변환합니다.",
        )

        df = df_raw.copy()
        if auto_parse_dates:
            for col in df.select_dtypes(include=["object", "string"]).columns:
                sample_vals = df[col].dropna().head(20)
                if len(sample_vals) > 0:
                    try:
                        parsed = pd.to_datetime(sample_vals, errors="raise")
                        if parsed.notna().all():
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                    except Exception:
                        pass

        na_action = st.selectbox(
            "결측치(NaN) 처리 방식",
            [
                "원본 유지 (기본)",
                "결측치 포함 행 제거 (Drop NA)",
                "수치형 평균값 / 범주형 최빈값 대체",
            ],
        )
        if na_action == "결측치 포함 행 제거 (Drop NA)":
            df = df.dropna().reset_index(drop=True)
        elif na_action == "수치형 평균값 / 범주형 최빈값 대체":
            for c in df.select_dtypes(include=[np.number]).columns:
                df[c] = df[c].fillna(df[c].mean())
            for c in df.select_dtypes(exclude=[np.number]).columns:
                mode_series = df[c].mode()
                if not mode_series.empty:
                    df[c] = df[c].fillna(mode_series.iloc[0])

        # 범주형 빠른 필터
        cat_candidates = [
            c
            for c in df.select_dtypes(include=["object", "category", "string"]).columns
            if 1 < df[c].nunique() <= 30
        ]
        if cat_candidates:
            with st.expander("🔍 범주형 조건 필터", expanded=False):
                filter_col = st.selectbox("필터링할 범주형 변수", ["선택 안 함"] + cat_candidates)
                if filter_col != "선택 안 함":
                    unique_vals = df[filter_col].dropna().unique().tolist()
                    selected_vals = st.multiselect(
                        f"'{filter_col}' 포함 값 선택",
                        options=unique_vals,
                        default=unique_vals,
                    )
                    if selected_vals:
                        df = df[df[filter_col].isin(selected_vals)].reset_index(drop=True)
    else:
        df = None


# -----------------------------------------------------------------------------
# 5. 메인 화면 헤더 및 안내
# -----------------------------------------------------------------------------
st.title("📊 데이터 기술통계 & 시각화 분석 대시보드")

if df is None or df.empty:
    st.warning("👈 왼쪽 사이드바에서 **CSV 또는 XLSX 파일**을 업로드하거나 **샘플 데이터 사용하기**를 체크해 주세요.")
    st.stop()

st.markdown(f"**현재 분석 대상:** {source_label}")

# 컬럼 타입 분류
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category", "bool", "string"]).columns.tolist()
dt_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

# 상단 핵심 KPI 카드
total_cells = df.shape[0] * df.shape[1]
missing_cells = int(df.isna().sum().sum())
missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
dup_rows = int(df.duplicated().sum())

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("전체 행 (Rows)", f"{df.shape[0]:,}개")
kpi2.metric("전체 열 (Columns)", f"{df.shape[1]:,}개")
kpi3.metric("수치형 / 범주형 변수", f"{len(num_cols)} / {len(cat_cols)}개")
kpi4.metric("총 결측치 (Missing)", f"{missing_cells:,}개 ({missing_pct:.1f}%)")
kpi5.metric("중복 행 (Duplicates)", f"{dup_rows:,}개")

st.divider()

# -----------------------------------------------------------------------------
# 6. 탭 구성: 데이터 탐색 / 기술통계 / 시각화 / 상관관계 & 시계열
# -----------------------------------------------------------------------------
tab_overview, tab_stats, tab_viz, tab_corr = st.tabs(
    [
        "🗂️ 1. 데이터 미리보기 & 품질",
        "📐 2. 기술통계 분석 (Descriptive Stats)",
        "📈 3. 인터랙티브 시각화 (Visualizations)",
        "🔗 4. 상관관계 & 시계열 분석",
    ]
)

# =============================================================================
# TAB 1: 데이터 미리보기 & 품질
# =============================================================================
with tab_overview:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🔎 데이터 테이블 미리보기")
        search_col1, search_col2 = st.columns([2, 1])
        with search_col1:
            selected_view_cols = st.multiselect(
                "표시할 컬럼 선택 (비워두면 전체 표시)",
                options=df.columns.tolist(),
                default=[],
            )
        with search_col2:
            n_preview = st.slider("표시 행 수", min_value=5, max_value=min(500, len(df)), value=min(50, len(df)))

        display_df = df[selected_view_cols] if selected_view_cols else df
        st.dataframe(display_df.head(n_preview), use_container_width=True, height=400)

    with col_right:
        st.subheader("📋 컬럼별 타입 및 결측 현황")
        col_info = pd.DataFrame(
            {
                "컬럼명": df.columns,
                "데이터타입": df.dtypes.astype(str).values,
                "유효값수": df.notna().sum().values,
                "결측치수": df.isna().sum().values,
                "결측율(%)": (df.isna().mean().values * 100).round(2),
                "고유값수": [df[c].nunique(dropna=True) for c in df.columns],
            }
        )
        st.dataframe(col_info, use_container_width=True, height=400, hide_index=True)

    if missing_cells > 0:
        st.subheader("⚠️ 컬럼별 결측치 비율 시각화")
        missing_df = col_info[col_info["결측치수"] > 0].sort_values("결측율(%)", ascending=True)
        fig_missing = px.bar(
            missing_df,
            x="결측율(%)",
            y="컬럼명",
            orientation="h",
            text="결측치수",
            color="결측율(%)",
            color_continuous_scale="Reds",
            title="결측치가 존재하는 변수 현황",
        )
        fig_missing.update_layout(height=max(260, len(missing_df) * 45))
        st.plotly_chart(fig_missing, use_container_width=True)


# =============================================================================
# TAB 2: 기술통계 분석 (Descriptive Statistics)
# =============================================================================
with tab_stats:
    num_stats_df = compute_numeric_stats(df, num_cols)
    cat_stats_df = compute_categorical_stats(df, cat_cols)

    top_bar_left, top_bar_right = st.columns([3, 1])
    with top_bar_left:
        st.subheader("📐 수치형 변수 기술통계표 (Numerical Summary)")
        st.caption("평균, 표준편차, 사분위수(IQR)뿐만 아니라 분포의 비대칭도(왜도)와 뾰족한 정도(첨도), 변동계수(CV)를 함께 제공합니다.")
    with top_bar_right:
        excel_bytes = convert_df_to_excel_bytes(df, num_stats_df, cat_stats_df)
        st.download_button(
            label="📥 기술통계 리포트 다운로드 (.xlsx)",
            data=excel_bytes,
            file_name="descriptive_statistics_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if not num_stats_df.empty:
        st.dataframe(
            num_stats_df.style.background_gradient(
                subset=["평균(Mean)", "표준편차(Std)", "왜도(Skewness)"], cmap="Blues"
            ),
            use_container_width=True,
            hide_index=True,
        )

        # 그룹별 기술통계 비교 기능
        if cat_cols:
            with st.expander("📊 범주(그룹)별 수치형 기술통계 비교 보기", expanded=False):
                g_col1, g_col2, g_col3 = st.columns(3)
                with g_col1:
                    group_by_col = st.selectbox("기준 범주형 변수 (Group By)", cat_cols, key="grp_stat_cat")
                with g_col2:
                    target_num_col = st.selectbox("대상 수치형 변수", num_cols, key="grp_stat_num")
                with g_col3:
                    agg_stat_df = (
                        df.groupby(group_by_col, dropna=False)[target_num_col]
                        .agg(
                            건수="count",
                            평균="mean",
                            표준편차="std",
                            최솟값="min",
                            중앙값="median",
                            최댓값="max",
                        )
                        .reset_index()
                        .round(4)
                    )
                st.dataframe(agg_stat_df, use_container_width=True, hide_index=True)
    else:
        st.info("데이터셋에 수치형(Numeric) 변수가 없습니다.")

    st.divider()
    st.subheader("🏷️ 범주형 / 텍스트 변수 기술통계표 (Categorical Summary)")
    if not cat_stats_df.empty:
        st.dataframe(cat_stats_df, use_container_width=True, hide_index=True)

        with st.expander("🔢 선택한 범주형 변수의 상세 빈도표 (Frequency Table)", expanded=True):
            selected_cat_detail = st.selectbox("상세 빈도를 확인할 범주형 변수", cat_cols, key="cat_freq_sel")
            vc = df[selected_cat_detail].value_counts(dropna=False).reset_index()
            vc.columns = [selected_cat_detail, "빈도수(Count)"]
            vc["비율(%)"] = (vc["빈도수(Count)"] / len(df) * 100).round(2)
            vc["누적비율(%)"] = vc["비율(%)"].cumsum().round(2)
            st.dataframe(vc, use_container_width=True, hide_index=True)
    else:
        st.info("데이터셋에 범주형(Categorical) 변수가 없습니다.")


# =============================================================================
# TAB 3: 인터랙티브 시각화 (Visualizations)
# =============================================================================
with tab_viz:
    st.subheader("📈 변수별 맞춤형 시각화 그래프")

    viz_category = st.radio(
        "시각화 유형 선택",
        [
            "1️⃣ 단변량 분포 (히스토그램 / 박스플롯 / 바이올린)",
            "2️⃣ 이변량 관계 (산점도 & 회귀추세선 / 버블차트)",
            "3️⃣ 범주형 집계 & 비율 (막대그래프 / 파이차트 / 트리맵)",
            "4️⃣ 다변량 분포 비교 (산점도 행렬 Pairplot)",
        ],
        horizontal=True,
    )

    st.markdown("---")

    # 1) 단변량 분포
    if viz_category.startswith("1️⃣"):
        if not num_cols:
            st.warning("수치형 변수가 없어 분포 그래프를 그릴 수 없습니다.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                uni_col = st.selectbox("분석할 수치형 변수 (X축)", num_cols, key="uni_x")
            with c2:
                uni_color = st.selectbox(
                    "그룹 색상 구분 (Color)", ["없음"] + cat_cols, key="uni_color"
                )
            with c3:
                marginal_type = st.selectbox(
                    "보조 분포 모양 (Marginal)",
                    ["box (박스플롯)", "violin (바이올린)", "rug (러그)", "없음"],
                )
            with c4:
                bins_cnt = st.slider("히스토그램 구간 수 (Bins)", 5, 100, 30)

            color_arg = None if uni_color == "없음" else uni_color
            marg_arg = None if marginal_type == "없음" else marginal_type.split(" ")[0]

            col_plot1, col_plot2 = st.columns([3, 2])
            with col_plot1:
                fig_hist = px.histogram(
                    df,
                    x=uni_col,
                    color=color_arg,
                    marginal=marg_arg,
                    nbins=bins_cnt,
                    barmode="overlay",
                    opacity=0.75,
                    title=f"[{uni_col}] 히스토그램 및 분포",
                    template="plotly_white",
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col_plot2:
                box_or_violin = st.radio(
                    "우측 비교 그래프 형태", ["Box Plot (이상치 확인)", "Violin Plot (밀도 확인)"], horizontal=True
                )
                if box_or_violin.startswith("Box"):
                    fig_bv = px.box(
                        df,
                        x=color_arg,
                        y=uni_col,
                        color=color_arg,
                        points="outliers",
                        title=f"[{uni_col}] 박스플롯 (이상치 및 사분위수)",
                        template="plotly_white",
                    )
                else:
                    fig_bv = px.violin(
                        df,
                        x=color_arg,
                        y=uni_col,
                        color=color_arg,
                        box=True,
                        points="outliers",
                        title=f"[{uni_col}] 바이올린 플롯 (밀도 및 사분위수)",
                        template="plotly_white",
                    )
                st.plotly_chart(fig_bv, use_container_width=True)

    # 2) 이변량 관계 (산점도 & 추세선)
    elif viz_category.startswith("2️⃣"):
        if len(num_cols) < 2:
            st.warning("산점도를 그리려면 최소 2개 이상의 수치형 변수가 필요합니다.")
        else:
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            with sc1:
                x_col = st.selectbox("X축 수치형 변수", num_cols, index=0, key="sc_x")
            with sc2:
                y_col = st.selectbox(
                    "Y축 수치형 변수", num_cols, index=min(1, len(num_cols) - 1), key="sc_y"
                )
            with sc3:
                color_sc = st.selectbox(
                    "색상 구분 (Color)", ["없음"] + cat_cols + num_cols, key="sc_color"
                )
            with sc4:
                size_sc = st.selectbox("버블 크기 (Size)", ["없음"] + num_cols, key="sc_size")
            with sc5:
                trend_opt = st.selectbox(
                    "회귀 추세선 (Trendline)",
                    ["ols (선형회귀)", "lowess (비선형 평활)", "없음"],
                )

            c_arg = None if color_sc == "없음" else color_sc
            s_arg = None if size_sc == "없음" else size_sc
            t_arg = None if trend_opt == "없음" else trend_opt.split(" ")[0]

            plot_df = df.copy()
            if s_arg is not None:
                # 음수값이 있을 경우 버블 크기를 최소 0 이상으로 스케일링
                min_val = plot_df[s_arg].min()
                if pd.notna(min_val) and min_val < 0:
                    plot_df[s_arg] = plot_df[s_arg] - min_val + 1.0

            fig_scatter = px.scatter(
                plot_df,
                x=x_col,
                y=y_col,
                color=c_arg,
                size=s_arg,
                trendline=t_arg,
                opacity=0.8,
                title=f"[{x_col}] vs [{y_col}] 산점도 분석",
                template="plotly_white",
            )
            fig_scatter.update_layout(height=520)
            st.plotly_chart(fig_scatter, use_container_width=True)

            # 두 변수 간 상관계수 및 p-value 요약
            valid_pair = df[[x_col, y_col]].dropna()
            if len(valid_pair) >= 3:
                r_val, p_val = stats.pearsonr(valid_pair[x_col], valid_pair[y_col])
                rho_val, sp_pval = stats.spearmanr(valid_pair[x_col], valid_pair[y_col])
                st.info(
                    f"📌 **[{x_col}] ↔ [{y_col}] 상관성 요약 (유효 표본 {len(valid_pair):,}개):** "
                    f"Pearson $r = {r_val:.4f}$ ($p = {p_val:.4e}$) | "
                    f"Spearman $\\rho = {rho_val:.4f}$ ($p = {sp_pval:.4e}$)"
                )

    # 3) 범주형 집계 & 비율
    elif viz_category.startswith("3️⃣"):
        if not cat_cols:
            st.warning("데이터셋에 범주형 변수가 없습니다.")
        else:
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                cat_x = st.selectbox("범주형 기준 변수", cat_cols, key="cat_viz_x")
            with bc2:
                agg_target = st.selectbox(
                    "집계 대상 변수", ["빈도수 (Count)"] + num_cols, key="cat_viz_y"
                )
            with bc3:
                agg_func_label = st.selectbox(
                    "집계 함수",
                    ["평균 (mean)", "합계 (sum)", "중앙값 (median)", "최댓값 (max)", "최솟값 (min)"],
                    disabled=(agg_target == "빈도수 (Count)"),
                )
            with bc4:
                top_n = st.slider("표시할 상위 범주 개수 (Top N)", 3, 30, 15)

            if agg_target == "빈도수 (Count)":
                agg_df = df[cat_x].value_counts(dropna=False).head(top_n).reset_index()
                agg_df.columns = [cat_x, "값"]
                y_label = "빈도수 (Count)"
            else:
                func_name = agg_func_label.split("(")[1].replace(")", "").strip()
                agg_df = (
                    df.groupby(cat_x, dropna=False)[agg_target]
                    .agg(func_name)
                    .reset_index()
                    .rename(columns={agg_target: "값"})
                    .sort_values("값", ascending=False)
                    .head(top_n)
                )
                agg_df["값"] = agg_df["값"].round(4)
                y_label = f"{agg_target} ({agg_func_label})"

            agg_df[cat_x] = agg_df[cat_x].astype(str)

            col_bar, col_pie = st.columns([3, 2])
            with col_bar:
                fig_bar = px.bar(
                    agg_df,
                    x=cat_x,
                    y="값",
                    color=cat_x,
                    text="값",
                    title=f"[{cat_x}] 별 {y_label} (상위 {top_n}개)",
                    labels={"값": y_label},
                    template="plotly_white",
                )
                fig_bar.update_traces(textposition="outside")
                fig_bar.update_layout(height=460, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_pie:
                pie_or_tree = st.radio(
                    "비율 차트 유형", ["도넛 차트 (Donut)", "트리맵 (Treemap)"], horizontal=True
                )
                if pie_or_tree.startswith("도넛"):
                    fig_pie = px.pie(
                        agg_df,
                        names=cat_x,
                        values="값",
                        hole=0.4,
                        title=f"[{cat_x}] 비중 분포",
                        template="plotly_white",
                    )
                else:
                    fig_pie = px.treemap(
                        agg_df,
                        path=[cat_x],
                        values="값",
                        title=f"[{cat_x}] 트리맵 비중",
                        template="plotly_white",
                    )
                fig_pie.update_layout(height=460)
                st.plotly_chart(fig_pie, use_container_width=True)

    # 4) 다변량 산점도 행렬 (Pairplot)
    elif viz_category.startswith("4️⃣"):
        if len(num_cols) < 2:
            st.warning("다변량 산점도 행렬을 그리려면 2개 이상의 수치형 변수가 필요합니다.")
        else:
            p_col1, p_col2 = st.columns([3, 1])
            with p_col1:
                selected_dims = st.multiselect(
                    "비교할 수치형 변수 선택 (2~6개 권장)",
                    options=num_cols,
                    default=num_cols[: min(4, len(num_cols))],
                )
            with p_col2:
                pair_color = st.selectbox(
                    "그룹 색상 변수", ["없음"] + cat_cols, key="pair_color"
                )

            if len(selected_dims) >= 2:
                fig_matrix = px.scatter_matrix(
                    df,
                    dimensions=selected_dims,
                    color=None if pair_color == "없음" else pair_color,
                    opacity=0.7,
                    title="다변량 산점도 행렬 (Scatter Matrix)",
                    template="plotly_white",
                )
                fig_matrix.update_traces(diagonal_visible=True)
                fig_matrix.update_layout(height=650)
                st.plotly_chart(fig_matrix, use_container_width=True)
            else:
                st.info("최소 2개 이상의 수치형 변수를 선택해 주세요.")


# =============================================================================
# TAB 4: 상관관계 히트맵 & 시계열 추세 분석
# =============================================================================
with tab_corr:
    st.subheader("🔗 수치형 변수 상관관계 분석 (Correlation Heatmap)")

    if len(num_cols) >= 2:
        corr_c1, corr_c2 = st.columns([1, 3])
        with corr_c1:
            corr_method_label = st.radio(
                "상관계수 계산 방식",
                [
                    "pearson (선형 상관관계)",
                    "spearman (순위 기반 비모수)",
                    "kendall (켄달 순위 상관계수)",
                ],
            )
            corr_method = corr_method_label.split(" ")[0]
            corr_matrix = df[num_cols].corr(method=corr_method).round(3)

            # 상위 상관 변수 쌍 추출
            pairs = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    c1_name, c2_name = num_cols[i], num_cols[j]
                    val = corr_matrix.loc[c1_name, c2_name]
                    if pd.notna(val):
                        pairs.append(
                            {
                                "변수 1": c1_name,
                                "변수 2": c2_name,
                                "상관계수(r)": val,
                                "절댓값(|r|)": abs(val),
                            }
                        )
            pairs_df = pd.DataFrame(pairs).sort_values("절댓값(|r|)", ascending=False)
            st.markdown("**🔥 상관성 높은 변수 쌍 Top 5**")
            if not pairs_df.empty:
                st.dataframe(
                    pairs_df[["변수 1", "변수 2", "상관계수(r)"]].head(5),
                    use_container_width=True,
                    hide_index=True,
                )

        with corr_c2:
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title=f"변수 간 상관계수 히트맵 ({corr_method.capitalize()})",
            )
            fig_corr.update_layout(height=500)
            st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("상관관계 분석을 위해서는 최소 2개 이상의 수치형 변수가 필요합니다.")

    st.divider()
    st.subheader("⏱️ 시계열 / 순차 추세선 및 이동평균(Moving Average) 분석")

    if num_cols:
        ts_c1, ts_c2, ts_c3 = st.columns([1, 2, 1])
        with ts_c1:
            x_axis_options = dt_cols + ["행 인덱스 (Row Index)"] + [
                c for c in df.columns if c not in dt_cols
            ]
            ts_x = st.selectbox("기준 축 (날짜/시간 또는 순서)", x_axis_options, index=0)
        with ts_c2:
            ts_y_cols = st.multiselect(
                "추세를 확인할 수치형 변수 (복수 선택 가능)",
                options=num_cols,
                default=[num_cols[0]],
            )
        with ts_c3:
            ma_window = st.slider(
                "이동평균 구간 (Moving Average)",
                min_value=1,
                max_value=min(50, max(2, len(df) // 2)),
                value=1,
                help="1보다 크게 설정하면 이동평균 평활선이 함께 표시됩니다.",
            )

        if ts_y_cols:
            ts_df = df.copy()
            if ts_x == "행 인덱스 (Row Index)":
                ts_df["_x_axis_"] = np.arange(len(ts_df))
                x_col_plot = "_x_axis_"
            else:
                ts_df = ts_df.sort_values(by=ts_x).reset_index(drop=True)
                x_col_plot = ts_x

            fig_ts = go.Figure()
            for y_c in ts_y_cols:
                fig_ts.add_trace(
                    go.Scatter(
                        x=ts_df[x_col_plot],
                        y=ts_df[y_c],
                        mode="lines",
                        name=f"{y_c} (원본)",
                        opacity=0.65 if ma_window > 1 else 0.95,
                    )
                )
                if ma_window > 1:
                    ma_series = ts_df[y_c].rolling(window=ma_window, min_periods=1).mean()
                    fig_ts.add_trace(
                        go.Scatter(
                            x=ts_df[x_col_plot],
                            y=ma_series,
                            mode="lines",
                            name=f"{y_c} ({ma_window}구간 이동평균)",
                            line=dict(width=3),
                        )
                    )

            fig_ts.update_layout(
                title=f"추세 분석 그래프 (기준: {ts_x})",
                xaxis_title=ts_x,
                yaxis_title="측정값",
                template="plotly_white",
                height=460,
                hovermode="x unified",
            )
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("추세를 확인할 수치형 변수를 1개 이상 선택해 주세요.")
