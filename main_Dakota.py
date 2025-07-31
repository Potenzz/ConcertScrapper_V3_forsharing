from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time
import re
import os
import pandas as pd
from datetime import datetime
import tempfile

class Scraper:      
    def __init__(self):
        self.headless = False
        self.driver = None
        self.shows_data = []

    def config_driver(self):
        options = uc.ChromeOptions()

        profile_dir = tempfile.mkdtemp()

        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-blink-features=AutomationControlled')

        if self.headless:
            options.add_argument("--headless")

        driver = uc.Chrome(options=options)
        self.driver = driver

    def scrap_page(self, target_year, target_month, current_day=None):
        wait_show = WebDriverWait(self.driver, 15)
        date_scraped = datetime.now().strftime('%Y%m%d')  

        # Define current date components early so they can be used as fallback
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        if current_day is None:
            current_day = today.day

        # Default to current month if not given
        if target_year is None:
            target_year = current_year
        if target_month is None:
            target_month = current_month
        
        # will help to return none if no data found in pages any dates.
        found_events = False  
        try:
            shows_container = wait_show.until(
                EC.presence_of_all_elements_located((By.XPATH, "//td[contains(@class, 'wicked-has-events')]"))
            )
        except:
            print(f"No more data")
            return "NO DATA"


        if len(shows_container) == 0:
            return "NO DATA"
        
        def clean_string(s):
                if isinstance(s, list):
                    s = ' '.join(s)  
                
                if s is None:  
                    return ""
                
                return ' '.join(re.sub(r'\s+', ' ', s.replace(',',';').replace('\n', ' ').strip()).split())

        def extract_date(datetime_str):
            try:
                if not datetime_str or len(datetime_str.strip()) < 10:
                    raise ValueError("Empty or short date string")
                dt = datetime.fromisoformat(datetime_str.strip())
                return {
                    "Year": dt.year,
                    "Month": dt.month,
                    "Day": dt.day
                }
            except Exception:
                print(f"Date parse error: Invalid datetime format: '{datetime_str}'")
                return {"Year": "", "Month": "", "Day": ""}



        for show in shows_container:
            try:
                date = show.get_attribute("data-date")
                dt = datetime.fromisoformat(date)
            except:
                date = ""

            try:
                event = show.find_element(By.XPATH, ".//div[contains(@class, 'wicked-events')]/div[contains(@class, 'wicked-event')]/div[contains(@class, 'wicked-event-title')]/a")
                Band_Line1 = event.text.strip()
                if Band_Line1:
                    found_events = True
            except:
                Band_Line1 = ""
            
            if dt.year != target_year or dt.month != target_month:
                continue
            if target_year == current_year and target_month == current_month:
                if dt.day < current_day:
                    continue

            formatted_date = extract_date(date)
            date_scraped = datetime.now().strftime('%Y%m%d')  

            data = {
                'Date Scraped': date_scraped,
                'Year': formatted_date['Year'],
                'Month': formatted_date['Month'],
                'Day': formatted_date['Day'],
                'Venue': "Dakota",
                'Band Line 1': clean_string(Band_Line1),
            }
            print(data)
            self.shows_data.append(data) 
        
        if found_events:
            return "success"
        else:
            return "NO DATA"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_Dakota.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_Dakota_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://www.dakotacooks.com/events/#"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        time.sleep(4)

        today = datetime.today()
        current_year = today.year
        current_month = today.month
        current_day = today.day

        # getting first page
        value = self.scrap_page(current_year, current_month, current_day)
        if value == "NO DATA":
            print("absoulute no data")
            return
        
        time.sleep(1)
        # clicking next month button and then getting that pages.
        wait = WebDriverWait(self.driver, 15)
        flag = True
        popupFlag = True

        # Track next month's date
        target_month = current_month + 1
        target_year = current_year

        # Adjust if we cross into January of next year
        if target_month > 12:
            target_month = 1
            target_year += 1

        while flag:
            try:
                next_month_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/main/div[1]/div/div[2]/div/div/div/div[2]/div[2]/a"))
                ).click()
                time.sleep(3)

                if popupFlag:
                    try: 
                        popup_close_button = WebDriverWait(self.driver, 7).until(
                            EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/a"))
                        ).click()
                        popupFlag = False
                    except: 
                        pass


                value = self.scrap_page(target_year, target_month)
                if value=="NO DATA":
                    flag = False

                # Prepare for next iteration
                target_month += 1
                if target_month > 12:
                    target_month = 1
                    target_year += 1

            except Exception as e:
                print(f"Error locating next button: {e}")
                flag = False

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()