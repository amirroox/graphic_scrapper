from mysql.connector.abstracts import MySQLCursorAbstract, MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from config import config
import os
from selenium import webdriver
import mysql.connector
import ftplib


# Connect To FTP
def connect_ftp(host=config.FTP_CONFIG['host'], user=config.FTP_CONFIG['user'],
                password=config.FTP_CONFIG['password']):
    return ftplib.FTP(host, user, password)  # return FTP Session


class BaseClass:
    # inital
    def __init__(self, timeout=config.TIMEOUT_SLEEP, AD_BLOCKER=True, ftp_send=True):
        self.name = None
        self.db_cursor: MySQLCursorAbstract | None = None
        self.db_connection: PooledMySQLConnection | MySQLConnectionAbstract | None = None
        self.database_username = config.DATABASE_CONFIG["username"]
        self.database_password = config.DATABASE_CONFIG["password"]
        self.database_name = config.DATABASE_CONFIG["database"]
        self.path_download = os.path.abspath(config.PATH_DOWNLOAD)
        self.timeout_sleep: int | float = timeout
        self.driver: WebDriver | None = None
        self.ad_blocker = AD_BLOCKER
        self.ftp = None
        if ftp_send:
            self.ftp = connect_ftp()
        self.connect_database()

    # Def Driver Open
    def _initial_open(self):
        self.driver = self.setup_driver()
        self.driver.get('https://google.com')
        # Wait To LOAD
        wait = WebDriverWait(self.driver, 30)
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        if self.ad_blocker:
            # Switch To AdBlocker
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.close()
            # Switch To Main Tab
            self.driver.switch_to.window(self.driver.window_handles[0])

    # Initial Setup Driver
    def setup_driver(self):
        option = webdriver.ChromeOptions()
        option.add_argument('--no-sandbox')
        option.add_argument('--verbose')
        option.add_argument("--disable-notifications")
        option.add_argument("--start-maximized")
        # AD Blocker Extention
        if self.ad_blocker:
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
            self.db_cursor = db.cursor(dictionary=True)
        except Exception as er:
            print(f'SQL Error: {er}')
            exit()

    # Close Driver
    def close_driver(self):
        self.driver.close()

    # Clsoe FTP
    def close_fpt(self):
        if self.ftp is not None:
            self.ftp.close()
