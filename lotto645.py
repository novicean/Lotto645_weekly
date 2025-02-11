import time
import random
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta


# 사용자 설정ls

USER_ID = "novicean"
USER_PW = "ehdgksla00!"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1337762943458218045/QhjxPlepexySGT7XFSgRsY51HXo3xzwSv0mgMLwQw6u0ELLNQDh3GNDGrIbxVbMP7i-r"

# 웹 드라이버 설정 (ChromeDriver 경로 수정 필요)
chrome_options = Options()
chrome_options.add_argument("--headless")  # 백그라운드 실행
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())  # ✅ ChromeDriver 자동 설치
driver = webdriver.Chrome(service=service, options=chrome_options)

def login():
    """로그인 함수"""
    driver.get("https://www.dhlottery.co.kr/user.do?method=login")
    time.sleep(2)

    driver.find_element(By.ID, "userId").send_keys(USER_ID)
    driver.find_element(By.NAME, "password").send_keys(USER_PW)
    driver.find_element(By.XPATH, '//a[@href="javascript:check_if_Valid3();"]').click()
    time.sleep(3)

    handle_popup()  # 팝업 제거 시도

def handle_popup():
    """팝업창이 있으면 자동으로 닫기"""
    try:
        time.sleep(1)  # 팝업이 뜨는 시간 기다리기
        driver.switch_to.alert.accept()  # JavaScript alert 창 닫기
        print("팝업(alert) 창을 닫았습니다.")
    except:
        print("팝업(alert) 창이 없습니다.")

    try:
        # 팝업이 새로운 윈도우로 열렸는지 확인
        main_window = driver.current_window_handle
        for window in driver.window_handles:
            if window != main_window:
                driver.switch_to.window(window)
                driver.close()  # 팝업 창 닫기
                driver.switch_to.window(main_window)
                print("새로운 팝업 창을 닫았습니다.")
    except:
        print("새로운 팝업 창이 없습니다.")

def generate_lotto_numbers():
    """랜덤으로 로또 번호 6개 생성"""
    numbers = sorted(random.sample(range(1, 46), 6))
    print(f"🎲 선택된 로또 번호: {numbers}")
    return numbers

def select_numbers(numbers):
    """웹페이지에서 지정된 로또 번호를 선택"""
    
    iframe_element = driver.find_element(By.ID, "ifrm_tab")  # iframe의 id를 사용하여 찾는 예시
    driver.switch_to.frame(iframe_element)  # iframe 내부로 전환
    
    for num in numbers:
        button = driver.find_element(By.XPATH, f'//label[@for="check645num{num}"]')
        button.click()
        time.sleep(0.5)
        
    driver.switch_to.default_content()  # 원래의 컨텍스트로 복귀

def buy_lotto():
    """로또 자동 구매 (동일한 번호로 5게임)"""
    login()
    driver.get("https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40")
    time.sleep(3)
    
    iframe_element = driver.find_element(By.ID, "ifrm_tab")  # iframe의 id를 사용하여 찾는 예시
    driver.switch_to.frame(iframe_element)  # iframe 내부로 전환

    lotto_numbers = generate_lotto_numbers()  # 랜덤 번호 생성

    #for i in range(5):  # 5게임 동일한 번호로 선택
        #game_button = driver.find_element(By.XPATH, f'//div[@id="numView"]//li[{i+1}]')
        #game_button.click()
        #time.sleep(1)

        #select_numbers(lotto_numbers)  # 번호 선택
        # time.sleep(1)
        
    for num in lotto_numbers:
        button = driver.find_element(By.XPATH, f'//label[@for="check645num{num}"]')
        button.click()
        time.sleep(0.5)
    
    Select(driver.find_element(By.XPATH, f'//select[@id="amoundApply"]')).select_by_value("5")
    driver.find_element(By.XPATH, f'//input[@id="btnSelectNum"]').click()

    driver.find_element(By.ID, "btnBuy").click()
    time.sleep(3)
    
    driver.switch_to.default_content()  # 원래의 컨텍스트로 복귀

    alert = driver.switch_to.alert
    alert.accept()

    print("✅ 로또 구매 완료")
    send_discord_message(f"✅ 로또 6/45 5000원어치 자동 구매 완료! 🎟️ 번호: {lotto_numbers}")

def check_balance():
    """예치금 확인 및 알림"""
    login()
    driver.get("https://dhlottery.co.kr/payment.do?method=payment")
    time.sleep(3)

    balance = driver.find_element(By.XPATH, '//a[@href="/myPage.do?method=depositListView"]').text
    balance = int(balance.replace(",", "").replace("원", ""))

    if balance < 5000:
        send_discord_message(f"⚠️ 예치금 부족: 현재 {balance}원 남음. 충전 필요!")
    else:
        send_discord_message(f"⚠️ 예치금 충분: 현재 {balance}원 남음.")

def check_lotto_results():
    """당첨 여부 확인"""
    login()
    driver.get("https://dhlottery.co.kr/userSsl.do?method=myPage")
    time.sleep(3)

    today = datetime.today()
    seven_days_ago = today - timedelta(days=7)

    rows = driver.find_elements(By.XPATH, '//table[contains(@class, "tbl_data")]/tbody/tr')
    found = False

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 5:
            continue  # 데이터가 부족한 행은 건너뜀

        # 날짜 추출
        purchase_date_str = cols[0].text.strip()
        try:
            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")  # 날짜 포맷 변환
        except ValueError:
            continue  # 날짜가 잘못된 경우 건너뜀

        # 7일 이내인지 확인
        if purchase_date >= seven_days_ago:
            found = True
            game_round = cols[1].text.strip()  # 게임 회차
            game_info = cols[2].text.strip()  # 게임 종류 (로또 6/45 등)
            purchse_num = cols[3].text.strip()  # 구매 번호
            game_num = cols[4].text.strip()  # 구매 갯수
            result = cols[5].text.strip()  # 당첨 여부 (당첨 / 낙첨)
            prize_amount = cols[6].text.strip()  # 당첨금

            if result == "낙첨":
                send_discord_message(f"❌ {purchase_date_str} ({game_info}): 낙첨")
            else:
                send_discord_message(f"🎉 {purchase_date_str} ({game_info}): 당첨! 회차: {game_round} 당첨금: {prize_amount}")

    if not found:
        send_discord_message("📌 최근 7일 이내의 구입 내역이 없습니다.")

def send_discord_message(message):
    """디스코드 알림 전송"""
    data = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lotto Bot")
    parser.add_argument("--buy_lotto", action="store_true", help="로또 구매 실행")
    parser.add_argument("--check_balance", action="store_true", help="잔액 확인 실행")
    parser.add_argument("--check_lotto_results", action="store_true", help="당첨 확인 실행")
    args = parser.parse_args()

    if args.buy_lotto:
        buy_lotto()
    elif args.check_balance:
        check_balance()
    elif args.check_lotto_results:
        check_lotto_results()

    driver.quit()