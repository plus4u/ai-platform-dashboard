# 📊 데이터 기술통계 & 시각화 대시보드 (Streamlit)

CSV 또는 Excel(`.xlsx`, `.xls`) 파일을 업로드하면 **데이터 품질 점검, 기술통계 분석(수치형/범주형), 인터랙티브 시각화(분포, 산점도/회귀선, 범주형 집계, 다변량 행렬, 상관관계 히트맵, 시계열 추세)**를 즉시 제공하는 웹 대시보드입니다.

---

## ✨ 주요 기능

1. **파일 업로드 및 전처리**
   - `.csv` (한글 인코딩 `UTF-8`, `CP949`, `EUC-KR` 자동 감지 지원) 및 `.xlsx` / `.xls` (다중 시트 선택 지원) 업로드
   - 업로드 파일이 없을 때 즉시 체험 가능한 **제조 공정 품질 모니터링 샘플 데이터셋** 내장
   - 결측치 처리(원본 유지 / 결측 행 제거 / 평균·최빈값 대체) 및 범주형 조건 필터링

2. **기술통계 분석 (Descriptive Statistics)**
   - **수치형 변수**: 유효건수, 결측치(건수/비율), 평균, 표준편차, 분산, 변동계수(CV), 최솟값, 사분위수(25%, 50%, 75%, IQR), 최댓값, 왜도(Skewness), 첨도(Kurtosis)
   - **범주형 변수**: 유효건수, 결측율, 고유값 수(Unique), 최빈값(Top) 및 빈도/비율, 상세 빈도표(누적 비율 포함)
   - **그룹별 기술통계 비교** 및 **분석 결과 Excel(`.xlsx`) 리포트 원클릭 다운로드**

3. **인터랙티브 시각화 (Plotly 기반)**
   - **단변량 분포**: 히스토그램 + 보조 그래프(Boxplot/Violin/Rug), 박스플롯(이상치 탐지), 바이올린 플롯
   - **이변량 관계**: 산점도(Scatter) + 선형(OLS)/비선형(Lowess) 회귀 추세선 + 상관계수($r$, $\rho$) 및 $p$-value 자동 계산
   - **범주형 집계 & 비율**: 그룹별 집계(빈도/평균/합계/중앙값) 막대그래프, 도넛 차트, 트리맵(Treemap)
   - **다변량 산점도 행렬**: 복수 수치형 변수 간 Pairplot(Scatter Matrix)
   - **상관관계 & 시계열**: Pearson/Spearman/Kendall 상관계수 히트맵, 상위 상관 변수 쌍 Top 5, 시계열 추세선 및 이동평균선(Moving Average)

---

## 💻 로컬 환경 실행 방법

```bash
# 1. 작업 폴더로 이동
cd T:\1_AI_Agent\Manuf_x\AI_Coach\AI_Platform

# 2. 필수 패키지 설치
pip install -r requirements.txt

# 3. Streamlit 앱 실행
streamlit run app.py
```

---

## ☁️ Streamlit Community Cloud 배포 가이드

이 프로젝트는 **Streamlit Community Cloud**에 바로 배포할 수 있도록 모든 설정 파일(`app.py`, `requirements.txt`, `.streamlit/config.toml`, `.gitignore`)이 구성되어 있습니다.

### 1단계: GitHub 저장소(Repository)에 코드 업로드
작업 폴더(`T:\1_AI_Agent\Manuf_x\AI_Coach\AI_Platform`)에서 아래 명령어를 순서대로 실행하여 GitHub에 푸시합니다.

```bash
cd T:\1_AI_Agent\Manuf_x\AI_Coach\AI_Platform
git init
git add .
git commit -m "Initial commit: Streamlit stats and visualization dashboard"
git branch -M main
git remote add origin https://github.com/<본인_GitHub_아이디>/<저장소_이름>.git
git push -u origin main
```

### 2단계: Streamlit Community Cloud 연결 및 배포
1. [Streamlit Community Cloud (share.streamlit.io)](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. 우측 상단의 **`Create app`** (또는 **`New app`**) 버튼을 클릭합니다.
3. 배포 설정 항목에 아래와 같이 입력합니다:
   - **Repository**: 방금 푸시한 `<본인_GitHub_아이디>/<저장소_이름>` 선택
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **`Deploy!`** 버튼을 클릭하면 `requirements.txt`의 패키지가 자동 설치되며 약 1~2분 후 고유 URL(`https://...streamlit.app`)로 대시보드가 배포됩니다.
