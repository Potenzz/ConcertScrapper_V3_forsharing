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

    def scrap_page(self):

        wait_show = WebDriverWait(self.driver, 15)

        try:
            shows_container = wait_show.until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'chakra-linkbox')]"))
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


        def extract_date():
            current_year = datetime.now().year
            last_month_index = 0  # Jan = 1

            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }

            def extract(month_abbr, day_str):
                nonlocal current_year, last_month_index

                try:
                    month_index = month_map[month_abbr[:3].title()]  
                    day = int(day_str)

                    # Detect year rollover (e.g., Dec to Jan)
                    if last_month_index and month_index < last_month_index:
                        current_year += 1

                    last_month_index = month_index

                    return {
                        "Year": current_year,
                        "Month": month_index,
                        "Day": day
                    }
                except Exception as e:
                    print(f"Date parse error: {e}")
                    return {"Year": "", "Month": "", "Day": ""}

            return extract
        
        date_extractor = extract_date()


        for show in shows_container:
            try:
                # Get Band/Title from the overlay anchor
                band_el = show.find_element(By.XPATH, ".//a[contains(@class, 'chakra-linkbox__overlay')]")
                Band_Line1 = band_el.text.strip()
            except Exception as e:
                Band_Line1 = ""

            try:
                # Get Date from time block
                day_str = show.find_element(By.XPATH, ".//time//p[contains(@class, 'date-box-date')]").text.strip()
                month_str = show.find_elements(By.XPATH, ".//time//p[contains(@class, 'css-81x3ga')]")[1].text.strip()
                formatted_date = date_extractor(month_str, day_str)
            except Exception as e:
                formatted_date = {"Year": "", "Month": "", "Day": ""}


            date_scraped = datetime.now().strftime('%Y%m%d')  

            data = {
                'Date Scraped': date_scraped,
                'Year': formatted_date['Year'],
                'Month': formatted_date['Month'],
                'Day': formatted_date['Day'],
                'Venue': "Fillmore",
                'Band Line 1': clean_string(Band_Line1),
            }
            print(data)
            self.shows_data.append(data) 

        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_Fillmore.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_Fillmore_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://www.fillmoreminneapolis.com/shows"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)


        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()