import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sys, os, requests

# 부모 폴더의 common 폴더를 참조하기 위한 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.database import get_stock_holdings, add_trade

app = FastAPI(title="Stock Asset Manager API")

# 매수 요청을 받을 때 사용할 데이터 규격
class TradeCreate(BaseModel):
    stock_code: str
    quantity: float
    price: float
    currency: str

@app.get("/")
def root():
    return {"message": "자산 관리 API 서버가 가동 중입니다."}

# 1. 전체 종목 리스트 (필요하신 전체 리스트를 여기 정의하세요)
@app.get("/market/list")
def get_market_list():
    return [
        {"code": "AAPL", "name": "애플 (Apple)", "currency": "USD"},
        {"code": "NVDA", "name": "엔비디아 (Nvidia)", "currency": "USD"},
        {"code": "TSLA", "name": "테슬라 (Tesla)", "currency": "USD"},
        {"code": "005930.KS", "name": "삼성전자", "currency": "KRW"},
        {"code": "000660.KS", "name": "SK하이닉스", "currency": "KRW"},
        {"code": "035420.KS", "name": "NAVER", "currency": "KRW"}
    ]

# 2. 실시간 현재가 가져오기
# 2-1. 단일 종목 조회 (쇼핑 탭에서 사용)
@app.get("/market/price/{symbol}")
def get_current_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        # 종목명 가져오기 (없으면 심볼로 대체)
        stock_name = ticker.info.get('longName') or ticker.info.get('shortName') or symbol
        
        data = ticker.history(period="2d")
        if data.empty:
            return {"symbol": symbol, "name": stock_name, "price": 0, "prev_close": 0}
        
        current_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
        
        return {
            "symbol": symbol,
            "name": stock_name, # 종목명 추가
            "price": round(float(current_price), 2),
            "prev_close": round(float(prev_close), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2-2. 다중 종목 조회 (잔고 탭 성능 최적화용 - 새로 추가)
@app.get("/market/prices")
def get_multiple_prices(symbols: str):
    symbol_list = symbols.split(",")
    tickers = yf.Tickers(symbol_list)
    result = {}
    
    for symbol in symbol_list:
        try:
            t = tickers.tickers[symbol]
            # info에서 이름을 못 가져올 경우를 대비해 fast_info나 기본 name 탐색
            name = t.info.get('shortName') or t.info.get('longName') or symbol
            
            result[symbol] = {
                "name": name,
                "price": t.fast_info.last_price,
                "prev_close": t.fast_info.previous_close
            }
        except:
            result[symbol] = {"name": symbol, "price": 0, "prev_close": 0}
    return result

# 달러/원 환율 가져오기
@app.get("/market/exchange-rate")
def get_exchange_rate():
    # 1단계: yfinance (메인 소스)
    try:
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="1d")
        if not data.empty:
            rate = round(float(data['Close'].iloc[-1]), 2)
            return {"rate": rate, "status": "success", "source": "yfinance"}
    except Exception as e:
        print(f"yfinance error: {e}")

    # 2단계: Frankfurter API (백업 소스)
    try:
        # 무료이며 인증키가 필요 없는 오픈 API입니다.
        res = requests.get("https://api.frankfurter.app/latest?from=USD&to=KRW", timeout=3)
        if res.status_code == 200:
            rate = res.json()['rates']['KRW']
            return {"rate": round(rate, 2), "status": "success", "source": "backup_api"}
    except Exception as e:
        print(f"Backup API error: {e}")

    # 3단계: 최후의 보루 (하드코딩된 기본값)
    # 1, 2단계 모두 실패할 경우에만 작동합니다.
    return {"rate": 1400.0, "status": "fallback", "source": "default"}


@app.get("/holdings")
def fetch_holdings():
    """DB에서 현재 잔고 목록을 가져옵니다."""
    try:
        data = get_stock_holdings()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trades")
def record_trade(trade: TradeCreate):
    """새로운 주식 매수 기록을 DB에 저장합니다."""
    try:
        add_trade(
            trade.stock_code, 
            trade.quantity, 
            trade.price, 
            trade.currency
        )
        return {"status": "success", "message": f"{trade.stock_code} 매수 기록 완료"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/trades/sell")
def record_sell_trade(trade: TradeCreate):
    """주식 매도 기록을 DB에 저장합니다. (수량을 음수로 변환)"""
    try:
        # 매도이므로 수량을 음수(negative)로 강제로 변환
        # abs()를 써서 양수로 만든 뒤 -를 붙이는 방식
        sell_quantity = -abs(trade.quantity)

        add_trade(
            trade.stock_code, 
            sell_quantity, 
            trade.price, 
            trade.currency
        )
        return {"status": "success", "message": f"{trade.stock_code} {trade.quantity}주 매도 기록 완료"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/market-list")
def get_market_catalog():
    """구경하기 화면에서 보여줄 전체 종목 리스트"""
    # 나중에는 DB에서 가져오게 확장 가능합니다.
    return [
        {"code": "AAPL", "name": "Apple"},
        {"code": "NVDA", "name": "Nvidia"},
        {"code": "TSLA", "name": "Tesla"},
        {"code": "005930.KS", "name": "삼성전자"},
        {"code": "000660.KS", "name": "SK하이닉스"}
    ]

@app.get("/market/search")
def search_global_stocks(query: str):  # 'q' 대신 'query'로 변경하여 웹 앱과 매칭
    try:
        search = yf.Search(query, max_results=10)
        
        results = []
        for quote in search.quotes:
            if quote.get('quoteType') in ['EQUITY', 'ETF']:
                symbol = quote['symbol']
                # 웹 앱에서 기대하는 'currency' 필드를 여기서 생성
                currency = "KRW" if (".KS" in symbol or ".KQ" in symbol) else "USD"
                
                results.append({
                    "code": symbol,
                    "name": quote.get('shortname') or quote.get('longname') or symbol,
                    "currency": currency  # 이 필드가 있어야 웹 앱의 'Currency' 섹션이 작동함
                })
        return results
    except Exception as e:
        print(f"Search Error: {e}")
        return []


    
@app.get("/market/trending")
def get_trending_stocks():
    try:
        # 1. 'stocks' 키워드로 검색하여 실제 활발한 종목들 추출
        search = yf.Search("stocks", max_results=30)
        trending_tickers = [q['symbol'] for q in search.quotes if q.get('quoteType') == 'EQUITY' or q.get('quoteType') == 'ETF']
        
        # 2. 만약 검색 결과가 적다면 미국 우량주 강제 포함 (보험용)
        top_us = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]
        
        # 중복 제거 후 리턴
        return list(set(trending_tickers + top_us))
    except Exception as e:
        # 에러 발생 시 미국 대표 종목 리턴
        return ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"]