import sys
import requests  # 서버와 통신하기 위해 필요합니다
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, 
                             QTableWidgetItem, QVBoxLayout, QWidget, QLabel, QPushButton)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QLineEdit, QFormLayout, QMessageBox
from scraper import get_current_prices

class MyAssetManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("나의 실시간 자산 관리자 (v2.0 - API 연결됨)")
        self.resize(1000, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 상단 요약 정보
        self.summary_label = QLabel("서버에서 데이터를 불러오는 중...")
        self.summary_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(self.summary_label)

        # 주식 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["종목", "수량", "평단가", "현재가", "평가금액(원)", "수익률", "통화"])
        layout.addWidget(self.table)

        # 데이터 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_btn)

        self.market_btn = QPushButton("🛍️ 종목 구경하고 매수하기")
        self.market_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.market_btn.clicked.connect(self.open_market_window)
        layout.addWidget(self.market_btn)

        self.load_data()

    def open_market_window(self):
        self.market_win = MarketWindow(self)
        self.market_win.show()    

    def load_data(self):
        try:
            # 1. API 서버에서 잔고 데이터 가져오기
            response = requests.get("http://127.0.0.1:8000/holdings")
            if response.status_code != 200:
                print("서버 연결 실패")
                return
            
            holdings = response.json() # JSON 데이터를 파이썬 리스트로 변환

            # 2. 실시간 주가 가져오기 (Scraper 활용)
            stock_codes = [h['stock_code'] for h in holdings]
            current_prices = get_current_prices(stock_codes)

            # 3. 화면 업데이트
            self.table.setRowCount(len(holdings))
            total_eval_krw = 0
            
            # (임시) 환율 설정 - 나중에 이것도 API로 가져올 수 있습니다.
            ex_rates = {"USD": 1450.0, "KRW": 1.0}

            for row, data in enumerate(holdings):
                code = data['stock_code']
                qty = float(data['total_quantity'])
                avg_price = float(data['avg_buy_price'])
                curr = data['currency']
                
                curr_price = current_prices.get(code, 0)
                rate = ex_rates.get(curr, 1.0)

                eval_krw = qty * curr_price * rate
                total_eval_krw += eval_krw
                profit_rate = ((curr_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

                self.table.setItem(row, 0, QTableWidgetItem(code))
                self.table.setItem(row, 1, QTableWidgetItem(f"{qty:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{avg_price:,.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{curr_price:,.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(f"{int(eval_krw):,}원"))
                
                profit_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
                if profit_rate > 0: profit_item.setForeground(QColor("red"))
                elif profit_rate < 0: profit_item.setForeground(QColor("blue"))
                self.table.setItem(row, 5, profit_item)
                self.table.setItem(row, 6, QTableWidgetItem(curr))

            self.summary_label.setText(f"💰 총 자산 가치: {int(total_eval_krw):,} 원")

        except Exception as e:
            print(f"오류 발생: {e}")
            self.summary_label.setText("데이터를 불러오지 못했습니다.")

# 매수 수량을 입력받는 팝업창 클래스
class BuyDialog(QDialog):
    def __init__(self, stock_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{stock_code} 매수")
        layout = QFormLayout(self)
        
        self.qty_input = QLineEdit()
        self.price_input = QLineEdit()
        layout.addRow("매수 수량:", self.qty_input)
        layout.addRow("매수 가격:", self.price_input)
        
        self.buy_btn = QPushButton("확인")
        self.buy_btn.clicked.connect(self.accept)
        layout.addWidget(self.buy_btn)

# 종목 구경하기(카탈로그) 창 클래스
class MarketWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("전체 종목 구경하기")
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        self.label = QLabel("관심 있는 종목을 클릭하여 매수하세요.")
        layout.addWidget(self.label)
        
        self.market_table = QTableWidget()
        self.market_table.setColumnCount(2)
        self.market_table.setHorizontalHeaderLabels(["종목코드", "종목명"])
        self.market_table.cellDoubleClicked.connect(self.order_stock) # 더블클릭 시 주문
        layout.addWidget(self.market_table)
        
        self.load_market_list()

    def load_market_list(self):
        # API 서버에서 카탈로그 목록 가져오기
        res = requests.get("http://127.0.0.1:8000/market-list")
        if res.status_code == 200:
            stocks = res.json()
            self.market_table.setRowCount(len(stocks))
            for i, stock in enumerate(stocks):
                self.market_table.setItem(i, 0, QTableWidgetItem(stock['code']))
                self.market_table.setItem(i, 1, QTableWidgetItem(stock['name']))

    def order_stock(self, row, col):
        stock_code = self.market_table.item(row, 0).text()
        
        # 매수 팝업 띄우기
        dialog = BuyDialog(stock_code, self)
        if dialog.exec():
            qty = dialog.qty_input.text()
            price = dialog.price_input.text()
            
            # API 서버에 매수 기록 전송 (POST 요청)
            trade_data = {
                "stock_code": stock_code,
                "quantity": float(qty),
                "price": float(price),
                "currency": "USD" if ".KS" not in stock_code else "KRW"
            }
            res = requests.post("http://127.0.0.1:8000/trades", json=trade_data)
            if res.status_code == 200:
                QMessageBox.information(self, "완료", f"{stock_code} 매수 기록이 저장되었습니다!")
                self.parent().load_data() # 메인 화면 새로고침        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyAssetManager()
    window.show()
    sys.exit(app.exec())