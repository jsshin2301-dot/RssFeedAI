# 개발 세션 리포트: RssFeedAI 문제 해결 및 구현 로그

이 문서는 본 세션에서 발생한 오류, 사용자의 요청(질문), 그리고 해결을 위해 수행한 행동들을 순서대로 기록합니다.

## 1. 초기 실행 및 데이터 로딩 에러

### 🚨 발생한 에러
**오류 메시지:** `Error loading data/feeds.json: This repository is empty.: 404 ...`
*   **상황:** `streamlit run app.py` 실행 직후 발생.
*   **원인:** `utils.py`의 `load_json` 메서드가 GitHub 저장소(PyGithub)에서 직접 파일을 읽어오려 했으나, 저장소가 비어있거나 초기화되지 않아 404 에러를 반환함. 로컬 파일 시스템에 대한 Fallback(대비책) 로직이 없었음.

### ✅ 해결 조치
*   **분석:** `utils.py` 및 데이터 디렉토리 확인 결과, 로컬에는 `feeds.json`이 존재함을 확인.
*   **수정:** `utils.py`를 수정하여 GitHub API 호출 실패 시 로컬 파일(`data/` 경로)을 읽어오도록 Fallback 로직 추가. 또한 저장(`save_json`) 시에도 로컬에 우선 저장하도록 변경하여 안정성 확보.

---

## 2. Admin Dashboard Feed 추가 버그

### 🐛 발생한 문제
**사용자 리포트:** "Admin Dashboard에서 Feed 주소를 넣고 Add 버튼을 눌러도 반응이 없다(빈 상태). 두 번 눌러야 추가된다."
*   **원인:** Streamlit의 `st.text_input`과 `st.button`의 상태 동기화 문제. 텍스트 입력 후 엔터나 포커스 이동 없이 바로 버튼을 누르면, 첫 번째 렌더링에서 입력값이 바인딩되지 않거나 초기화되는 현상 발생 (Double-click issue).

### ✅ 해결 조치
*   **수정:** Feed 추가 UI를 `st.form`으로 감싸서 처리 (`st.form_submit_button` 사용).
*   **결과:** 폼 제출 방식을 통해 데이터 입력과 제출이 한 번의 액션으로 원자적으로 처리되도록 개선하여, 한 번 클릭으로 정상 추가되도록 수정.

---

## 3. Google Gemini API 모델 오류 (404 Not Found)

### 🚨 발생한 에러
**오류 메시지:** `404 models/gemini-1.5-flash is not found ...`
*   **원인:** 코드에 하드코딩된 모델명 `gemini-1.5-flash`가 현재 사용 중인 API 환경에서 제공되지 않음.

### ✅ 해결 조치
*   **진단:** `list_models.py` 스크립트를 작성 및 실행하여 사용 가능한 모델 목록 조회.
*   **결과:** `gemini-1.5-flash` 부재. `gemini-2.0-flash`, `gemini-2.5-flash` 등 존재 확인.
*   **수정:** 사용자와 협의 후 `gemini-2.0-flash`로 코드 변경.

---

## 4. Google Gemini API 할당량 초과 (429 Quota Exceeded)

### 🚨 발생한 에러
**오류 메시지:** `429 You exceeded your current quota ... limit: 0, model: gemini-2.0-flash`
*   **원인:** 변경한 `gemini-2.0-flash` 모델에 대해 현재 API 키(계정)의 무료 사용량(Free Tier)이 0으로 설정되어 있어 사용 불가.

### ✅ 해결 조치
*   **분석:** 에러 메시지의 `limit: 0`을 통해 해당 모델이 무료 티어를 지원하지 않음을 파악.
*   **제안:** 무료 사용이 가능할 확률이 높은 Lite 모델 제안.
*   **수정:** `gemini-2.0-flash-lite`로 모델 변경.

---

## 5. 모델 재변경 요청

### 🗣️ 사용자 요청
**요청 내용:** "gemini-2.5-Flash-lite로 변경해줘"

### ✅ 해결 조치
*   **수정:** `utils.py`의 모델 설정을 `gemini-2.5-flash-lite`로 업데이트.

---

## 6. GitHub 코드 저장 (Push) 실패 및 해결

### 🗣️ 사용자 요청
**요청 내용:** "이거를 github로 코드 저장 해 줄 수 잇니?"

### 🚨 발생한 문제 (연속적)
1.  **초기 시도:** `git init` 후 Push 시도 -> `403 Permission Denied` (권한 없음).
    *   **원인:** `secrets.toml`에 있던 토큰이 해당 저장소에 대한 쓰기 권한이 없었음.
2.  **2차 시도:** 사용자가 토큰 업데이트 후 재시도 -> 실패.
    *   **원인:** 사용자가 파일을 저장하지 않았거나 업데이트가 제대로 안 되어, `secrets.toml` 내의 토큰 값이 이전과 **동일**했음.
3.  **3차 시도:** 토큰 재업데이트 후 재시도 -> 실패 (Push 에러).
    *   **원인:** `secrets.toml` 파일이 Git에 추적(Tracked)되고 있어 보안 문제 및 충돌 발생 가능성.

### ✅ 해결 조치 (최종)
*   **보안 조치:** `git rm --cached .streamlit/secrets.toml` 명령어로 비밀 파일의 추적 해제 및 `.gitignore`에 추가.
*   **History 정리:** `git commit --amend`로 이전 커밋에서 비밀 파일 포함 내역 수정.
*   **강제 푸시:** `git push -u origin main --force`로 GitHub에 최종 코드 업로드 성공.

---

## 요약
본 세션에서는 **데이터 로딩 안정성 확보 -> UI UX 개선(Double Click 방지) -> AI 모델 호환성 및 할당량 문제 해결 -> GitHub 저장소 연동 및 보안 처리** 순으로 개발 및 문제 해결을 진행했습니다.
