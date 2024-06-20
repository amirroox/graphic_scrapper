from config import config
from time import sleep
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import mysql.connector


class FlatIcon:
    # inital
    def __init__(self, timeout=config.TIMEOUT_SLEEP):
        self.db_cursor = None
        self.db_connection = None
        self.database_username = config.DATABASE_CONFIG["username"]
        self.database_password = config.DATABASE_CONFIG["password"]
        self.database_name = config.DATABASE_CONFIG["database"]
        self.path_download = os.path.abspath(config.PATH_DOWNLOAD)
        self.timeout_sleep = timeout
        self.driver = None
        self.connect_database()

    # Initial Setup Driver
    def setup_driver(self):
        option = webdriver.ChromeOptions()
        option.add_argument('--no-sandbox')
        option.add_argument('--verbose')
        option.add_argument("--disable-notifications")
        option.add_argument("--start-maximized")
        # AD Blocker Extention
        path_adGuard = ".\\extensions\\adguard\\bgnkhhnnamicmpeenaelnjfhikgbkllg.crx"
        option.add_argument(f"-–load-extension={path_adGuard}")
        option.add_extension(path_adGuard)
        # Zoom Config
        option.add_argument('--force-device-scale-factor=0.5')
        # Download Setup
        option.add_experimental_option("prefs", {
            "download.default_directory": self.path_download,
            "download.prompt_for_download": False})
        driver = webdriver.Chrome(options=option)
        return driver

    # Setup DataBase
    def connect_database(self):
        try:
            db = mysql.connector.connect(
                host="localhost",
                user=self.database_username,
                password=self.database_password,
                database=self.database_name
            )
            self.db_connection = db
            self.db_cursor = db.cursor()
        except Exception as er:
            print(f'SQL Error: {er}')
            exit()

    # Main Scrapper
    def scrape_icons(self, url="https://www.flaticon.com/search"):
        self.driver = self.setup_driver()
        base_url = url
        self.driver.get(base_url)
        self.driver.implicitly_wait(10)

        # Switch To AdBlocker
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.close()

        # Switch To Main Tab
        self.driver.switch_to.window(self.driver.window_handles[0])
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        icons_here = (soup.find('div', {'class': 'list-content'}).find('ul', {'class': 'icons'})
                      .find_all('li', {'class': 'icon--item'}))
        page_icons = [icon for icon in icons_here if icon.get('data-id') is not None]

        # Accept Button Cookies
        try:
            self.driver.find_element(by=By.ID, value='onetrust-accept-btn-handler').click()
        except Exception as error:
            print(error)

        i = 0
        for icon in page_icons:
            # Testing
            i += 1
            if i == 3:
                break
            data_id = icon['data-id']
            data_name = icon['data-name']
            full_name = f"{data_name}_{data_id}"

            # Check Exist Element
            self.db_cursor.execute("SELECT name FROM flaticon WHERE name=%s", (full_name,))
            result = self.db_cursor.fetchone()
            if result is not None:
                continue

            self.driver.find_element(by=By.XPATH, value=f"//a[@data-id='{data_id}']").click()
            sleep(self.timeout_sleep)

            address_link = self.driver.current_url.split('?')[0]
            self.driver.implicitly_wait(5)
            self.driver.find_element(by=By.XPATH, value="//button[@class='popover-button']").click()
            sleep(self.timeout_sleep)
            self.driver.find_element(by=By.XPATH, value="//ul[@class='size']//li//a[@data-size='512']").click()
            sleep(self.timeout_sleep)

            os.chdir(self.path_download)
            if not os.path.exists(full_name):
                os.mkdir(full_name)
            os.chdir('../')

            self.driver.find_element(by=By.XPATH,
                                     value="//button[@id='download-free' and @data-type='icon' and @class='bj-button bj-button--green modal-icon']").click()
            sleep(7)
            os.replace(f'{self.path_download}/{data_name}.png',
                       f'{self.path_download}/{full_name}/{full_name}.png')

            self.db_cursor.execute("INSERT INTO flaticon (name, path) VALUES (%s, %s)", (full_name, ' '))
            self.db_connection.commit()

            self.driver.find_element(by=By.ID, value='detail-close').click()

    def scrape_once(self, url, full_name):
        self.driver = self.setup_driver()
        base_url = url
        data_id = full_name.split('_')[-1]
        data_name = full_name.split('_')[0]
        self.driver.get(base_url)
        self.driver.implicitly_wait(10)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        sleep(5)

        try:
            self.driver.find_element(by=By.ID, value='onetrust-accept-btn-handler').click()
        except Exception as error:
            print(error)

        self.driver.find_element(by=By.XPATH, value=f"//a[@data-id='{data_id}']").click()
        sleep(self.timeout_sleep)

        address_link = self.driver.current_url.split('?')[0]
        self.driver.implicitly_wait(5)
        self.driver.find_element(by=By.XPATH, value="//button[@class='popover-button']").click()
        sleep(self.timeout_sleep)
        self.driver.find_element(by=By.XPATH, value="//ul[@class='size']//li//a[@data-size='512']").click()
        sleep(self.timeout_sleep)

        os.chdir(self.path_download)
        if not os.path.exists(full_name):
            os.mkdir(full_name)
        os.chdir('../')

        self.driver.find_element(by=By.XPATH,
                                 value="//button[@id='download-free' and @data-type='icon' and"
                                       " @class='bj-button bj-button--green modal-icon']").click()
        sleep(10)
        os.replace(f'{self.path_download}{data_name}.png',
                   f'{self.path_download}/{full_name}/{full_name}.png')

        # Add To DataBase
        self.db_cursor.execute("INSERT INTO flaticon (name, path) VALUES (%s, %s)", (full_name, ' '))
        self.db_connection.commit()

    # Close Driver
    def close_driver(self):
        self.driver.close()

    # Search In DB
    def search(self, name):
        self.db_cursor.execute("SELECT name FROM flaticon WHERE name=%s", (name,))
        result = self.db_cursor.fetchone()
        if result is not None:
            return True
        return False
