import streamlit as st
import requests
import pandas as pd

# 소수점 포맷팅 함수 정의 (둘째자리까지 있거나, 정수거나)
def format_number(val):
    if val == int(val):
        return f"{int(val):,}" # 정수면 쉼표만 찍음
    return f"{val:,.2,}" # 소수점이 있으면 둘째자리까지

st.set_page_config(page_title="Stock Asset Web", layout="centered")
API_URL = "http://127.0.0.1:8000"

st.title("🚀 주식 자산 관리 웹 대시보드")

# 탭 생성
tab_wallet, tab_market, tab_buy = st.tabs(["📊 내 잔고 현황", "🔍 전체 종목 시세", "🛒 종목 쇼핑 & 매수"])

# --- Tab 1: 내 자산 대시보드 ---
with tab_wallet:
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.subheader("나의 실시간 포트폴리오")
    with col_btn:
        if st.button("🔄 새로고침", key="refresh_final"):
            st.rerun()

    # 1. 기초 데이터 로드 (보유종목, 전체종목리스트, 환율)
    res = requests.get(f"{API_URL}/holdings")
    market_res = requests.get(f"{API_URL}/market/list")
    ex_res = requests.get(f"{API_URL}/market/exchange-rate")

    if res.status_code == 200 and res.json():
        holdings = res.json()
        # DB 종목명 매칭용 딕셔너리 생성 { '005930.KS': '삼성전자' }
        stock_name_map = {s['code']: s['name'] for s in market_res.json()} if market_res.status_code == 200 else {}
        # 환율 데이터
        ex_data = ex_res.json() if ex_res.status_code == 200 else {"rate": 1350.0, "source": "default"}
        exchange_rate = ex_data['rate']

        # 2. 실시간 시세 일괄 가져오기
        all_symbols = ",".join([h['stock_code'] for h in holdings])
        with st.spinner('시세 로딩 중...'):
            prices_res = requests.get(f"{API_URL}/market/prices?symbols={all_symbols}")
            all_prices = prices_res.json() if prices_res.status_code == 200 else {}

        rows = []
        for h in holdings:
            code = h['stock_code']
            p_data = all_prices.get(code, {"price": 0, "prev_close": 0})
            
            # [핵심] 이름은 우리 DB(stock_name_map)에서 먼저 찾고, 없으면 서버 데이터 사용
            db_name = stock_name_map.get(code)  # 1순위: 우리 DB에 있는 한글명
            yf_name = p_data.get('name')        # 2순위: 야후 파이낸스에서 가져온 이름
            
            if db_name:
                display_name = db_name
            elif yf_name and yf_name != code:   # 야후 이름이 코드(숫자)와 다를 때만 사용
                display_name = yf_name
            else:
                display_name = code             # 마지막 수단: 종목 코드 그대로 노출
            
            cur_p = p_data['price']
            prev_p = p_data['prev_close']
            buy_p = h['avg_buy_price']
            qty = h['total_quantity']
            
            eval_amt = cur_p * qty
            buy_amt = buy_p * qty
            pnl = eval_amt - buy_amt
            pnl_r = (pnl / buy_amt * 100) if buy_amt != 0 else 0
            day_r = ((cur_p - prev_p) / prev_p * 100) if prev_p != 0 else 0

            rows.append({
                "종목명": display_name, "평가손익": pnl, "수익률(%)": pnl_r,
                "보유수량": qty, "평가금액": eval_amt, "매입단가": buy_p,
                "현재가": cur_p, "전일가": prev_p, "등락률(%)": day_r, "통화": h['currency']
            })

        df = pd.DataFrame(rows)

        # 1. 통화별 출력 우선순위 정의 (숫자가 작을수록 위에 나옵니다)
        priority = {'KRW': 0, 'USD': 1}
        
        # 2. 현재 보유 중인 통화들을 정의한 순서대로 정렬
        sorted_currencies = sorted(df['통화'].unique(), key=lambda x: priority.get(x, 99))

        # 3. 정렬된 순서대로 요약 및 테이블 출력
        for curr in sorted_currencies:
            curr_df = df[df['통화'] == curr].copy()
            
            t_buy = (curr_df['매입단가'] * curr_df['보유수량']).sum()
            t_eval = curr_df['평가금액'].sum()
            
            # USD일 경우 요약만 원화 환산 (문구는 제거하고 계산만 수행)
            if curr == "USD":
                t_buy *= exchange_rate
                t_eval *= exchange_rate
            
            t_pnl = t_eval - t_buy
            t_pnl_rate = (t_pnl / t_buy * 100) if t_buy != 0 else 0
            pnl_color = "#ef5350" if t_pnl >= 0 else "#42a5f5"

            # 요약 카드 출력
            st.markdown(f"#### 💰 {curr} 자산 요약") # 'KRW 환산' 문구 제거함
            st.markdown(f"""
                <div style="background-color: #fcfcfc; padding: 15px; border-radius: 10px; border: 1px solid #eeeeee;">
                    <p style="margin:0; font-size:13px; color:gray;">총 평가손익</p>
                    <h2 style="margin:0; color:{pnl_color};">{t_pnl:,.0f} 원 <span style="font-size:18px;">({t_pnl_rate:+.2f}%)</span></h2>
                </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div style="margin-top:10px; padding:10px; background:#f8f9fa; border-radius:8px; border: 1px solid #eeeeee;">
                    <p style="margin:0; font-size:12px; color:gray;">총 평가금액</p>
                    <h4 style="margin:0;">{t_eval:,.0f} 원</h4></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div style="margin-top:10px; padding:10px; background:#f8f9fa; border-radius:8px; border: 1px solid #eeeeee;">
                    <p style="margin:0; font-size:12px; color:gray;">총 매입금액</p>
                    <h4 style="margin:0;">{t_buy:,.0f} 원</h4></div>""", unsafe_allow_html=True)

            # 상세 테이블
            def color_pnl(val):
                if isinstance(val, (int, float)):
                    if val > 0: return 'color: #ef5350; font-weight: bold;'
                    elif val < 0: return 'color: #42a5f5; font-weight: bold;'
                return 'color: black;'

            fmt = "{:,.0f}" if curr == "KRW" else "{:,.2f}"
            styled_df = curr_df.style.map(color_pnl, subset=['평가손익', '수익률(%)', '등락률(%)']) \
                .format({
                    "평가손익": fmt, "평가금액": fmt, "매입단가": fmt, 
                    "현재가": fmt, "전일가": fmt, "수익률(%)": "{:+.2f}%", "등락률(%)": "{:+.2f}%"
                })
            st.dataframe(styled_df, width='stretch', hide_index=True)
            st.divider()
    else:
        st.info("보유 종목이 없습니다.")

# --- Tab : 전체 종목 시세 ---
with tab_market:
    st.subheader("🔥 Yahoo Finance 실시간 트렌딩 종목")
    
    with st.spinner('글로벌 인기 종목 정보를 불러오는 중...'):
        # 1. 서버에서 트렌딩 티커 가져오기
        trending_res = requests.get(f"{API_URL}/market/trending")
        trending_codes = trending_res.json() if trending_res.status_code == 200 else []
        
        # 한국 주식도 항상 보고 싶다면 여기에 추가
        kr_codes = ["005930.KS", "000660.KS", "035420.KS", "005380.KS", "035720.KS"]
        total_codes = list(set(trending_codes + kr_codes))
        
        # 2. 상세 정보 호출
        all_symbols = ",".join(total_codes)
        prices_res = requests.get(f"{API_URL}/market/prices?symbols={all_symbols}")
        live_data = prices_res.json() if prices_res.status_code == 200 else {}

    # 데이터 정리
    rows = []
    for code, info in live_data.items():
        # 이름이 비어있거나 티커와 같다면 재확인 (서버 보완 버전 활용)
        display_name = info.get('name') or code
        
        cur_p = info['price']
        prev_p = info['prev_close']
        change_rate = ((cur_p - prev_p) / prev_p * 100) if prev_p != 0 else 0
        currency = "KRW" if ".KS" in code or ".KQ" in code else "USD"
        
        rows.append({
            "Official Name": display_name,
            "Ticker": code,
            "Price": cur_p,
            "Change (%)": change_rate,
            "Currency": currency
        })
    
    df_market = pd.DataFrame(rows)

    # 3. 출력 (KRW와 USD를 각각 확실히 출력)
    for curr in ["KRW", "USD"]:
        curr_df = df_market[df_market['Currency'] == curr].sort_values(by="Change (%)", ascending=False)
        
        if not curr_df.empty:
            st.markdown(f"### 🚩 {curr} Market")
            fmt = "{:,.0f}" if curr == "KRW" else "{:,.2f}"
            
            styled_df = curr_df.style.map(lambda x: f"color: {'#ef5350' if x > 0 else '#42a5f5' if x < 0 else 'black'}; font-weight: bold;", subset=['Change (%)']) \
                .format({"Price": fmt, "Change (%)": "{:+.2f}%"})
            
            st.dataframe(styled_df, width='stretch', hide_index=True)
        else:
            # USD가 안 나올 경우를 대비한 디버깅용 메시지
            if curr == "USD":
                st.warning("⚠️ 미국 주식 데이터를 가져오지 못했습니다. 서버 상태를 확인해 주세요.")

# --- Tab 2: 실시간 종목 쇼핑 (매수) ---
with tab_buy:
    st.subheader("🛍️ 종목 통합 검색 및 매수")
    
    # 1. 통합 검색창
    search_query = st.text_input("종목명 또는 티커를 입력하세요", placeholder="예: QQQ, 삼성, NVDA", key="total_search")

    if search_query:
        with st.spinner(f"'{search_query}' 관련 종목을 찾는 중..."):
            # A. DB에서 검색
            market_res = requests.get(f"{API_URL}/market/list")
            db_stocks = market_res.json() if market_res.status_code == 200 else []
            filtered_db = [s for s in db_stocks if search_query.lower() in s['name'].lower() or search_query.upper() in s['code'].upper()]

            # B. 외부 API(yfinance)에서 연관 검색
            api_res = requests.get(f"{API_URL}/market/search?query={search_query}")
            api_stocks = api_res.json() if api_res.status_code == 200 else []

            # C. 두 결과 합치기 (중복 제거)
            combined_results = {s['code']: s for s in (filtered_db + api_stocks)}.values()

        if combined_results:
            # 사용자가 선택할 수 있게 Selectbox로 제공
            options = {f"[{s['code']}] {s['name']}": s for s in combined_results}
            selected_key = st.selectbox(f"검색 결과 ({len(combined_results)}건)", options=list(options.keys()))
            selected_info = options[selected_key]

            # 2. 선택된 종목의 현재가 자동 로딩
            with st.spinner('실시간 시세 확인 중...'):
                p_res = requests.get(f"{API_URL}/market/price/{selected_info['code']}")
                if p_res.status_code == 200:
                    price_data = p_res.json()
                    live_price = price_data['price']
                    
                    st.markdown("---")
                    col_info, col_val = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"### {selected_info['name']}")
                        st.caption(f"티커: {selected_info['code']} | 통화: {selected_info['currency']}")
                    
                    with col_val:
                        # 1. KRW일 때 소수점 삭제 / 2. USD일 때 KRW 환산가 병기
                        if selected_info['currency'] == "KRW":
                            st.metric("현재가", f"{live_price:,.0f} 원")
                        else:
                            # USD 현재가 표시
                            st.metric("현재가", f"{live_price:,.2f} USD")
                            # 환율 적용한 KRW 가격 계산 및 표시 (작은 글씨)
                            krw_price = live_price * exchange_rate
                            st.caption(f"≈ {krw_price:,.0f} 원 (환율 적용)")

                    # 3. 매수 폼 (가독성을 위해 숫자 입력칸도 포맷 변경)
                    with st.form("buy_form_final"):
                        # 통화별로 입력창 소수점 단위 조절
                        step_val = 1.0 if selected_info['currency'] == "KRW" else 0.01
                        format_val = "%.0f" if selected_info['currency'] == "KRW" else "%.2f"
                        
                        price_input = st.number_input("매수 가격", value=float(live_price), step=step_val, format=format_val)
                        qty_input = st.number_input("매수 수량", min_value=0, value=0, step=1)
                        
                        if st.form_submit_button("🔥 매수 주문 실행"):
                            if qty_input > 0:
                                trade_data = {
                                    "stock_code": selected_info['code'],
                                    "quantity": qty_input,
                                    "price": price_input,
                                    "currency": selected_info['currency']
                                }
                                order_res = requests.post(f"{API_URL}/trades", json=trade_data)
                                if order_res.status_code == 200:
                                    st.success(f"✅ {selected_info['name']} 매수 완료!")
                                    st.balloons()
                            else:
                                st.warning("수량을 입력하세요.")
                else:
                    st.error("시세를 가져올 수 없는 종목입니다.")
        else:
            st.warning("검색 결과가 없습니다.")