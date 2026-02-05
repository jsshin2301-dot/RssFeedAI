# 📝 Project Specification: AI IT Newsroom (Antigravity)

## 1. Project Overview
본 프로젝트는 국내 IT 뉴스 RSS 피드를 수집하여 **Gemini 1.5 Flash API**를 통해 분석하고, 사용자에게 주제별로 요약된 **1장 분량의 뉴스 리포트**를 제공하는 웹 애플리케이션이다. 데이터베이스 대신 **GitHub Repository를 JSON 저장소**로 활용하며, **Streamlit Cloud**를 통해 배포한다.

## 2. Tech Stack
- **Frontend/Framework:** Streamlit
- **AI Model:** Google Gemini 1.5 Flash
- **Data Fetching:** Feedparser (RSS parsing)
- **Persistence:** GitHub API (PyGithub) + JSON Files
- **Deployment:** Streamlit Cloud

## 3. Project Structure
```text
/
├── app.py                # Main Streamlit Application (UI & Control)
├── utils.py              # GitHub API Handler (load/save) & AI Logic
├── requirements.txt      # Dependency list
├── data/
│   ├── feeds.json        # List of RSS URLs
│   ├── news_data.json    # AI Analyzed reports indexed by date (YYYY-MM-DD)
│   └── stats.json        # Visitor statistics (total views & daily)
└── .streamlit/
    └── secrets.toml      # API Keys & Credentials (Local testing only)

## 4. Functional Requirements

### 4.1. Data Persistence (GitHub-as-a-DB)
- 모든 데이터는 data/ 디렉토리 내의 JSON 파일에 저장한다.
- PyGithub 라이브러리를 사용하여 데이터 수정 시 GitHub 리포지토리에 즉시 Commit/Push 한다.

### 4.2. Main View: Newsroom
- 접속 시 가장 최신 날짜의 뉴스 리포트를 최상단에 노출한다.
- select_slider 또는 selectbox를 사용하여 사용자가 과거 날짜의 리포트를 선택해 볼 수 있게 한다.
- AI가 생성한 마크다운 리포트를 렌더링하며, 각 토픽별 뉴스 제목과 원본 링크를 포함한다.

### 4.3. Admin Dashboard
- st.secrets["ADMIN_PASSWORD"]에 저장된 패스워드로 인증 후 진입한다.
- RSS 관리: URL 추가 및 삭제 기능.
- AI 분석 실행:
    1) 등록된 피드에서 최근 3일(72시간) 이내의 기사만 추출한다.
    2) Gemini 1.5 Flash를 사용해 기사들을 주제별로 그룹화하고 요약한다.
    3) 기사 제목과 원문 주소([Link])가 포함된 리포트를 생성한다.
    4) 결과를 news_data.json에 YYYY-MM-DD 키값으로 저장한다.
- 통계: stats.json 데이터를 활용하여 누적 방문자 및 일별 접속자 추이를 시각화한다.

### 4.4. Gemini 1.5 Flash Prompting Instruction
- 페르소나: IT 전문 뉴스 큐레이터.
- 지침: 입력된 뉴스를 주제별 분류, 핵심 3문장 요약, 기사 제목과 링크 포함, 가독성 높은 마크다운 형식 사용.

## 5. Security & Environment Variables
Streamlit Cloud Secrets 설정 항목:
- GEMINI_API_KEY: Google AI Studio API 키
- GITHUB_TOKEN: GitHub Personal Access Token
- REPO_NAME: "유저명/리포지토리명"
- ADMIN_PASSWORD: 관리자 접속 암호

## 6. Implementation Instructions for Antigravity
1. utils.py 생성: PyGithub를 이용해 JSON 파일을 읽고 쓰는 GithubDB 클래스를 구현하라.
2. app.py UI 구성: 사이드바 메뉴(뉴스룸/대시보드)와 비밀번호 인증 로직을 작성하라.
3. 수집 기능: feedparser로 최근 3일치 기사만 필터링하는 함수를 작성하라.
4. AI 분석: google-generativeai 라이브러리로 Gemini 1.5 Flash 모델에 요약을 요청하라.
5. 통계 및 저장: 방문자 기록 업데이트 및 분석 결과의 GitHub 커밋 로직을 연결하라.
6. requirements.txt: streamlit, google-generativeai, feedparser, PyGithub, pandas를 포함하라.