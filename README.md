# 📈 실시간 주식 자산 관리 시스템 (Full-Stack Architecture)

이 프로젝트는 단순한 자산 기록기를 넘어, **현대적인 소프트웨어 아키텍처(3-Tier)**를 이해하고 구현하기 위한 교육 및 실습용 프로젝트입니다.

## 🏗️ 시스템 아키텍처 (System Architecture)

본 시스템은 데이터 보안, 확장성 및 유지보수성을 위해 세 개의 계층으로 분리되어 설계되었습니다.

1. **Presentation Tier (Client):** `PyQt6` 기반의 데스크톱 애플리케이션. 사용자의 입력을 받고 API 서버와 HTTP 통신을 통해 데이터를 시각화합니다.
2. **Logic Tier (API Server):** `FastAPI` 기반의 백엔드 서버. 비즈니스 로직 처리, 데이터 검증 및 데이터베이스와의 가교 역할을 수행합니다.
3. **Data Tier (Database):** `PostgreSQL` 관계형 데이터베이스. 모든 거래 기록(`trades`), 기초 자산 정보 및 환율 데이터를 안전하게 저장합니다.

---

## 🛠️ 기술 스택 (Tech Stack)

### **Backend & API**

* **Python 3.13+**
* **FastAPI**: 고성능 비동기 웹 프레임워크 (RESTful API 구현)
* **Uvicorn**: ASGI 서버
* **SQLAlchemy / psycopg2**: 데이터베이스 연동 및 ORM

### **Frontend (Desktop)**

* **PyQt6**: 데스크톱 GUI 프레임워크
* **Requests**: API 서버와의 통신을 위한 HTTP 라이브러리
* **yfinance**: 실시간 금융 데이터 크롤링

### **Database & Automation**

* **PostgreSQL**: 관계형 데이터베이스 시스템
* **n8n**: 환율 데이터 자동 수집 및 DB 동기화 워크플로우

---

## 📂 프로젝트 구조 (Directory Structure)

```text
stock-asset-manager/
├── api/                # API 서버 로직
│   ├── main.py         # FastAPI 진입점 (api_server.py)
│   └── schemas.py      # 데이터 요청/응답 규격 (Pydantic)
├── client/             # GUI 애플리케이션
│   ├── main.py         # PyQt6 메인 화면
│   ├── scraper.py      # 실시간 시세 조회 모듈
│   └── api_client.py   # API 서버 통신 전용 모듈
├── common/             # 공통 DB 유틸리티
│   └── database.py     # DB 연결 및 쿼리 관리
├── .env                # 환경 변수 (DB 접속 정보 등)
├── requirements.txt    # 의존성 라이브러리 목록
└── README.md           # 프로젝트 문서

```

---

## 🚀 시작 가이드 (Getting Started)

### 1. 가상환경 설정 및 라이브러리 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

```

### 2. 서버 실행 (Backend)

```bash
# 프로젝트 루트에서 실행
uvicorn api.main:app --reload

```

* API 문서 확인: `http://127.0.0.1:8000/docs`

### 3. 클라이언트 실행 (Frontend)

```bash
python client/main.py
streamlit run client/web_app.py
```

---