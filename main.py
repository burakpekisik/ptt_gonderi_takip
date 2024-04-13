import sys
import json
import time
import asyncio
import requests
import datetime
from selenium.common.exceptions import TimeoutException
from database import insert_to_database, connect_to_database, close_database_connection, get_all_data
from userInfo import order_api
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TrackOrder:
    def __init__(self):
        self.order_api = order_api
        self.filtered_data = []
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("window-size=1024,768")
        self.chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.implicitly_wait(40)

    def get_track_ids(self):
        print("Getting Track IDs From API")
        max_retries = 5
        retries = 0

        while retries < max_retries:
            try:
                self.filtered_data.clear()
                response_API = requests.get(self.order_api)
                print(response_API.status_code)

                if response_API.status_code == 200:
                    data = response_API.text
                    parse_json = json.loads(data)
                    
                    self.filtered_data = [item for item in parse_json if 'trackId' in item]
                    break
                else:
                    retries += 1
                    print(f"Retrying... Attempt {retries}/{max_retries}")
                    time.sleep(1)  # Wait for 1 second before retrying

            except Exception as e:
                retries += 1
                print(f"Error While Fetching Data From API: {str(e)}")
                print(f"Retrying... Attempt {retries}/{max_retries}")
                time.sleep(1)  # Wait for 1 second before retrying

        if retries == max_retries:
            print("Max retries reached. Exiting.")
            sys.exit()

    async def check_status(self):  # Make the method asynchronous
        print("Checking Status of Track IDs")
        mycol = connect_to_database()
        
        all_data = get_all_data(mycol)
        delivered_orders = {data["ID"] for data in all_data if data["status"] == "TESLİM EDİLDİ"}

        all_data = get_all_data(mycol)
        false_tracks = {data_false["ID"] for data_false in all_data if data_false["status"] == "Hatalı Takip Kodu"}
        filtered_orders = delivered_orders.union(false_tracks)

        self.filtered_data = [data for data in self.filtered_data if data["ID"] not in filtered_orders]

        print("Filtered Data: ", self.filtered_data)

        # for database_data in all_data:
        #     for filter_data in self.filtered_data:
        #         if database_data["status"] == "TESLİM EDİLDİ":
        #             if database_data["ID"] == filter_data["ID"]:
        #                 print("Order Already Delivered: ", filter_data["trackId"])
        #                 self.filtered_data.remove(filter_data)

        for data in self.filtered_data:
            try:
                print("Checking Status of Order with Track ID: " + data["trackId"])
                self.driver.get("https://gonderitakip.ptt.gov.tr/")
                input_field = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#search-area"))
                )

                input_field.send_keys(data["trackId"])

                search_button = WebDriverWait(self.driver, 40).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#searchButton"))
                )
                time.sleep(2)
                search_button.click()

                # try:
                #     error_text = self.driver.find_element(By.XPATH, "/html/body/div/div/div[2]/span").get_attribute("innerHTML")
                #     # error_text = WebDriverWait(self.driver, 5).until(
                #     #     EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[2]/span"))
                #     # ).get_attribute("innerHTML")

                #     if error_text != "":
                #         print("Invalid Track ID: " + data["trackId"])
                #         data["status"] = "Hatalı Takip Kodu"
                #         await insert_to_database(data, mycol)
                #         continue

                #     print("Error Text: " + error_text)
                # except:
                #     pass

                transport_status = WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/main/div/div[1]/div[2]/b/h8/span"))
                )

                data["status"] = transport_status.text
                print(data)
                
                # Await the asynchronous function call
                await insert_to_database(data, mycol)

            except Exception as e:
                print("Error While Fetching Data From PTT Website: " + str(e))
                print("Invalid Track ID: " + data["trackId"])
                data["status"] = "Hatalı Takip Kodu"
                await insert_to_database(data, mycol)
                continue

        close_database_connection()

    def close(self):
        self.driver.quit()

async def main():
    while True:  # Sonsuz bir döngü başlatıyoruz
        # Şu anki tarihi ve saati al
        now = datetime.datetime.now()

        #Eğer şu anki gün Cumartesi veya Pazar ise döngüyü bekleme
        if now.weekday() >= 5:
            print("Bugün Cumartesi veya Pazar, döngü bekleme.")
            await asyncio.sleep(3600)  # 1 saat bekleme
            continue

        #Eğer şu anki saat 10:00 ile 19:00 arası değilse döngüyü bekleme
        if now.hour < 10 or now.hour >= 19:
            print("Şu anki saat 10:00 ile 19:00 arası değil, döngü bekleme.")
            await asyncio.sleep(3600)  # 1 saat bekleme
            continue

        trackOrder = TrackOrder()
        trackOrder.get_track_ids()
        await trackOrder.check_status()

        # 1 dakika (60 saniye) bekle
        remaining_time = 30  # Başlangıçta 30 dakika kalan süre
        for _ in range(remaining_time):
            print(f"Kalan süre: {remaining_time} dakika")
            await asyncio.sleep(60)
            remaining_time -= 1

# Run the asyncio event loop
# if __name__ == "__main__":
#     asyncio.run(main())

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Scanning stopped by user.")
    finally:
        TrackOrder.close()
        loop.close()