import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# .env 파일로드
load_dotenv()

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(db_url)

def get_latest_exchange_rates():
    """DB에서 각 통화별 최신 화율 정보를 가져오기"""
    conn = get_db_connection()
    # RealDictCursor를 사용하면 결과가 {'currency_code': 'USD', 'rate': 1470} 처럼 딕셔너리 형태로 나와서 다루기 편합니다.
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 각 통화(currency_code)별로 날짜(rate_date)가 가장 최신인 것 1개씩만 가져오는 SQL
        query = """
        SELECT DISTINCT ON (currency_code)
                id, currency_code, country_name, rate, rate_date
        FROM exchange_rates
        ORDER BY currency_code, rate_date DESC;
        """
        cur.execute(query)
        rates = cur.fetchall()
        return rates
    
    except Exception as e:
        print(f"환율 데이터 조회 실패 : {e}")
    
    finally:
        cur.close()
        conn.close()

def get_stock_holdings():
    """따로 테이블을 만들지 않고, trades 기록을 즉석에서 합산해 잔고를 계산합니다."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 이 쿼리가 핵심입니다! 
    # SUM(quantity)로 현재 총 수량을 계산하고,
    # 평균 단가(총 매수금액 / 총 수량)를 구합니다.
    query = """
    SELECT 
        stock_code, 
        SUM(quantity) as total_quantity, 
        AVG(price) as avg_buy_price, 
        currency
    FROM trades
    GROUP BY stock_code, currency
    HAVING SUM(quantity) > 0;
    """
    
    try:
        cur.execute(query)
        # 결과값을 딕셔너리 리스트 형태로 변환 (API가 이해하기 쉽게)
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]
        return result
    except Exception as e:
        print(f"데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        cur.close()
        conn.close() 


def add_trade(stock_code, quantity, price, currency):
    """사용자가 매수 버튼을 누르면 호출되어 trades 테이블에 기록을 남깁니다."""
    conn = get_db_connection() # 기존에 만드신 DB 연결 함수 이름 확인!
    cur = conn.cursor()
    
    # trade_date는 현재 시간으로, trade_type은 'BUY'로 저장
    query = """
    INSERT INTO trades (stock_code, quantity, price, currency, trade_type, trade_date)
    VALUES (%s, %s, %s, %s, 'BUY', CURRENT_TIMESTAMP);
    """
    try:
        cur.execute(query, (stock_code, quantity, price, currency))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    lastest_rates = get_latest_exchange_rates()
    print("=== 최신 화율 정보 ===")
    for r in lastest_rates:
        print(f"[{r['country_name']}] 1 {r['currency_code']} = {r['rate']:,}원 (기준일: {r['rate_date']})")


    # 2. 보유 주식 테스트
    holdings = get_stock_holdings()
    print("\n--- 보유 주식 현황 ---")
    for h in holdings:
        print(f"종목: {h['stock_code']}, 수량: {h['total_quantity']}, 평단: {h['avg_buy_price']:.2f} ({h['currency']})")

