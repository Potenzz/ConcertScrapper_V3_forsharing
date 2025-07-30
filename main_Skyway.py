from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
import pandas as pd
from datetime import datetime


class Scraper:      
    def __init__(self):
        self.headless = False
        self.driver = None
        self.shows_data = []

    def config_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        s = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options=options)
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
                EC.presence_of_all_elements_located((By.XPATH, "//td[@role='gridcell' and @data-date]"))
            )
        except Exception as e:
            print(f"Error locating event container: {e}")
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
                dt = datetime.fromisoformat(datetime_str)
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
                date_str = show.get_attribute("data-date")
                dt = datetime.fromisoformat(date_str)
            except:
                continue


            formatted_date = extract_date(date_str)

            try:
                event_blocks = show.find_elements(
                    By.XPATH,
                    ".//div[contains(@class, 'fc-daygrid-event-harness')]"
                )
                if event_blocks:
                    found_events = True
            except:
                event_blocks = []

            if dt.year != target_year or dt.month != target_month:
                continue
            if target_year == current_year and target_month == current_month:
                if dt.day < current_day:
                    continue

            for block in event_blocks:
                try:
                    time = block.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'fc-event-time')]"
                    ).text.strip()
                except:
                    time = ""

                try:
                    Band_Line1 = block.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'fc-event-title')]"
                    ).text.strip()
                except:
                    Band_Line1 = ""

           
                data = {
                    'Date Scraped': date_scraped,
                    'Year': formatted_date['Year'],
                    'Month': formatted_date['Month'],
                    'Day': formatted_date['Day'],
                    'Venue': "Skyway",
                    'Time':time,
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
        file_name = f"Data_{today}_SkyWay.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_SkyWay_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://skywaytheatre.com/events/"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        time.sleep(3)

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
                    EC.element_to_be_clickable((By.XPATH, "/html/body/main/section/div/div/div/div[1]/div[1]/div[2]/button[3]"))
                ).click()
                time.sleep(3)

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