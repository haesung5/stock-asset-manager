# 📈 가상 주식 매매 및 자산 관리 프로그램 (Stock Portfolio Manager)

파이썬을 활용하여 실시간 주가 정보를 확인하고, 가상 매매 기록을 관리하는 데스크톱 애플리케이션입니다. 
클라우드 DB를 사용하여 어디서든 내 자산 데이터를 조회할 수 있도록 설계되었습니다.

---

## 🚀 주요 기능
- **실시간 주식 정보 조회**: `yfinance` API를 활용한 국내/해외 주가 데이터 호출
- **가상 매매 시스템**: 주식 매수/매도 기록 저장 및 관리
- **자산 관리 포트폴리오**: 총 자산, 종목별 수익률, 원화 환산 금액 계산
- **환율 자동 연동**: 해외 주식 계산을 위한 실시간 환율 정보 DB 저장 및 업데이트
- **멀티 접속 지원**: Neon(PostgreSQL) 클라우드 DB 연동으로 여러 PC에서 동일 데이터 공유

---

## 🛠 사용 기술 (Tech Stack)
- **Language**: Python 3.13.2
- **n8n** : 2.4.6
- **UI Framework**: PyQt6 (또는 CustomTkinter)
- **Database**: Neon (Serverless PostgreSQL)
- **Libraries**:
  - `psycopg2`: DB 연동
  - `yfinance`: 주식 데이터 수집
  - `python-dotenv`: 환경 변수 보안 관리
  - `pandas`: 데이터 처리 및 계산

---

## 📂 데이터베이스 구조 (Database Schema)
1. **Transactions Table**: 매매 기록 (종목명, 가격, 수량, 날짜 등)
2. **ExchangeRates Table**: 통화별 환율 정보
3. **Assets Table**: 현재 보유 중인 자산 현황

---

## ⚙️ 설치 및 실행 방법
1. 저장소 클론
   ```bash
   git clone [https://github.com/haesung5/stock-asset-manager.git]