import yfinance as yf
import pandas as pd

def get_current_prices(stock_codes):
    """
    yfinance를 사용하여 리스트에 담긴 모든 종목의 현재가를 
    딕셔너리 형태로 반환합니다.
    """
    price_dict = {}
    
    if not stock_codes:
        return price_dict

    for code in stock_codes:
        try:
            # Ticker 객체 생성
            ticker = yf.Ticker(code)
            
            # history(period="1d")는 현재 시장의 가장 최신 봉 데이터를 가져옵니다.
            # 실시간 가격(또는 15분 지연된 현재가)을 가져오는 가장 안정적인 방법입니다.
            data = ticker.history(period="1d")
            
            if not data.empty:
                # 'Close' 열의 마지막 행 값이 현재가입니다.
                current_price = data['Close'].iloc[-1]
                price_dict[code] = float(current_price)
                print(f"✅ {code} 조회 성공: {current_price:.2f}")
            else:
                print(f"⚠️ {code}: 데이터를 찾을 수 없습니다.")
                price_dict[code] = 0.0
                
        except Exception as e:
            print(f"❌ {code} 조회 중 오류 발생: {e}")
            price_dict[code] = 0.0
            
    return price_dict

# --- 테스트 코드 ---
if __name__ == "__main__":
    # 테스트하고 싶은 종목들을 리스트에 넣으세요.
    test_list = ["AAPL", "005930.KS", "NVDA", "TSLA"]
    results = get_current_prices(test_list)
    print("\n[최종 결과]")
    for code, price in results.items():
        print(f"{code}: {price:,.2f}")