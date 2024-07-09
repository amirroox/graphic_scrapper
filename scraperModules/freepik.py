import json
import random
import re
import zipfile

from selenium.webdriver.support.wait import WebDriverWait

from config import config
from config import account_list
from time import sleep
import os
from selenium.webdriver.common.by import By

from scraperModules.BaseClass import BaseClass


class FreePik(BaseClass):
    # inital
    def __init__(self, timeout=config.TIMEOUT_SLEEP, AD_BLOCKER=True, ftp_send=True):
        super().__init__(timeout, AD_BLOCKER, ftp_send)
        self.name = "Freepik"

    # Sign In
    def _sign_in(self):
        self.driver.get('https://www.freepik.com/log-in?client_id=freepik&lang=en')  # Sign In Link

        # if os.path.exists(f'cookies/{self.name}/cookies.pkl'):
        #     cookies = pickle.load(open(f"cookies/{self.name}/cookies.pkl", "rb"))
        #     for cookie in cookies:
        #         self.driver.add_cookie(cookie)
        #     return

        # Wait To LOAD
        wait = WebDriverWait(self.driver, 30)
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

        # Accept Button Cookies
        sleep(3)
        try:
            self.driver.find_element(by=By.ID, value='onetrust-accept-btn-handler').click()
        except Exception as error:
            print(error)

        # Sign In
        # self.driver.find_element(by=By.XPATH, value='//a[@data-cy="login-button"]').click()
        buttons = self.driver.find_elements(by=By.XPATH,
                                            value='//button[@class="main-button button button--outline button--with-icon"]')
        buttons[-1].click()
        sleep(5)  # For Not Robot
        # List Account
        myAccount = account_list.account_list[self.name][0]
        self.driver.find_element(by=By.XPATH, value='//input[@name="email"]').send_keys(myAccount['email'])
        sleep(5)  # For Not Robot
        self.driver.find_element(by=By.XPATH, value='//input[@name="password"]').send_keys(myAccount['password'])
        sleep(5)  # For Not Robot
        self.driver.find_element(by=By.ID, value='submit').click()
        sleep(60 + random.randint(5, 15))  # For Manual Captcha Check
        # pickle.dump(self.driver.get_cookies(), open(f"cookies/{self.name}/cookies.pkl", "wb"))
        print("Sign In Complate! - Cookies Save!")

    # ---------- Vector FreePic ----------

    # Main Scrapper (Vector Scrapper)
    def scrape_vectors(self, url="https://www.freepik.com/search?format=search&type=vector",
                       query=None, account=False, premium=False):
        self._initial_open()  # Open
        try_count = 3  # Default Try
        if query:
            url = f'{url}&query={query}'

        if account:  # Sign In
            self._sign_in()
            try_count = 10

        # Free Or Premium
        if premium:
            this_url = f"{url}&last_filter=premium&last_value=1&premium=1"
            try_count = 100
        else:
            this_url = f"{url}&last_filter=selection&last_value=1&selection=1"

        # Go To Main Scrap
        self.driver.get(this_url)
        # Wait To LOAD
        wait = WebDriverWait(self.driver, 30)
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        vectors_page = self.driver.find_elements(by=By.XPATH, value='//figure[@data-cy="resource-thumbnail"]//a')
        vectors_page = [href.get_attribute('href') for href in vectors_page]

        # Check Folder
        os.chdir(f'{self.path_download}')
        if not os.path.exists(self.name):
            os.mkdir(self.name)
        os.chdir('../')

        try_temp = 1
        while True:
            for vector in vectors_page:
                href_vector = vector
                pure_href = href_vector.split('#')[0]
                full_name = href_vector.replace('//', '/').split('/')[3].split('.')[0]
                title_vector = full_name.split('_')[0].replace('-', ' ')
                id_vector = full_name.split('_')[1]
                new_file_path = None  # New Raname File

                # Check Exist Element
                self.db_cursor.execute("SELECT title FROM freepik_vectors WHERE title=%s", (title_vector,))
                result = self.db_cursor.fetchone()
                if result is not None:
                    continue

                # Chcek try Limit Download
                if try_temp > try_count:
                    print("Try Done")
                    sleep(86500)  # Wait For Tomorrow
                    try_temp = 1

                # Open Vector
                self.driver.get(href_vector)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                sleep(self.timeout_sleep)
                self.driver.implicitly_wait(5)
                # Scroll 200px Bottom
                self.driver.execute_script("window.scrollBy(0, 200);")

                os.chdir(f'{self.path_download}/{self.name}')
                if not os.path.exists(full_name):
                    os.mkdir(full_name)
                os.chdir('../../')

                # Details
                try:  # File
                    file_details = self.driver.find_elements(by=By.XPATH, value="//ul[@class='_1286nb11a9']//li//span//span")[0].text
                    file_list = file_details.replace(':', '').split('/')
                    file_size = file_list[0].strip()
                    file_formats = file_list[1].strip()
                except Exception as ex:
                    print("Size Or Format None")
                    print(ex)
                    file_size, file_formats = 'unknown', 'unknown'
                current_url = self.driver.current_url.replace('//', '/').split('/')[2]  # License
                file_license = 0  # Free
                if 'premium' in current_url:
                    file_license = 1  # Premium
                # Related Tags
                try:  # Check All Tags
                    file_all_tags = self.driver.find_element(by=By.XPATH, value="//div[@style='grid-area:keywords']//button").click()
                except Exception as ex:
                    print("Tags Less...")
                    print(ex)
                all_tags_list = self.driver.find_elements(by=By.XPATH, value="//div[@style='grid-area:keywords']//ul//li//a")
                file_tags = ''

                # Seve Search Tags For Searching
                os.chdir(f'search/')
                if not os.path.exists(self.name):
                    os.mkdir(self.name)
                tags_save_search_file = {}
                file_name_json = f'{self.name}/{self.name}_Vector.json'
                if os.path.exists(file_name_json):
                    with open(file_name_json, 'r') as json_file:
                        tags_save_search_file = json.load(json_file)  # Dict
                else:
                    with open(file_name_json, 'w') as json_file:
                        tags_save_search_file = {}
                        json.dump(tags_save_search_file, json_file)
                for tag in all_tags_list:
                    tag = tag.text.strip()
                    if tag not in tags_save_search_file.keys():  # Check Exists Tag
                        tags_save_search_file[tag] = 0
                    file_tags = file_tags + str(tag) + ', '
                with open(file_name_json, 'w') as outfile:
                    json.dump(tags_save_search_file, outfile)  # Save To Json
                os.chdir('../')

                # Download Try
                self.driver.find_element(by=By.XPATH, value='//button[@data-cy="wrapper-download-free"]').click()
                sleep(self.timeout_sleep)
                try:
                    # Multi File
                    format_list = ['jpg', 'eps', 'ai', 'svg', 'zip']
                    list_pass = []
                    for formating in format_list:
                        self.driver.find_element(by=By.XPATH, value='//button[@data-cy="dropdown-download-type"]').click()
                        sleep(self.timeout_sleep)
                        # Find Formats
                        try:
                            file_format = self.driver.find_element(by=By.XPATH,
                                                                   value=f'//a[@data-cy="download-type-{formating}"]')
                            # Downlaod
                            before_download = os.listdir(self.path_download)
                            file_format.click()
                        except Exception as ex:
                            print(ex)
                            continue
                        sleep(10)
                        after_download = os.listdir(self.path_download)
                        new_files = [f for f in after_download if f not in before_download]
                        # pattern_search = rf"^{id_vector}_\d+\.{formating}$"
                        while True:
                            try:
                                if new_files:
                                    if '.crdownload' in new_files[0]:  # Temp Download TimeOut
                                        sleep(10)
                                    full_path = os.path.join(self.path_download, new_files[0])
                                    if os.path.isfile(full_path):
                                        # file_extension = os.path.splitext(filename)[1]
                                        new_filename = f"{full_name}.{formating}"
                                        new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                                        os.replace(full_path, new_file_path)
                                        if self.ftp is not None:
                                            upload_to_host(self, full_name, new_file_path, new_filename)
                                break
                            except Exception as ex:  # For Complate Download
                                print(ex)
                                sleep(30)
                        list_pass.append(str(formating))
                    self.db_cursor.execute("INSERT INTO freepik_vectors (title, link, path_zip, formats, size, license, tags) "
                                           "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                           (title_vector, pure_href, f'{self.name}/{full_name}/{full_name}.zip',
                                            file_formats, file_size, file_license, file_tags))
                    self.db_connection.commit()
                    if 'jpg' not in list_pass:  # Download JPG (picodl.ir)
                        img_jpg = self.driver.find_element(by=By.XPATH, value="//div[@class='_1286nb19f']//img")
                        href_img = img_jpg.get_attribute('src')
                        try:
                            self.driver.get('https://picodl.com')
                            # Wait To LOAD
                            wait = WebDriverWait(self.driver, 5)
                            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                            sleep(15)
                            self.driver.find_element(by=By.ID, value="image-url").send_keys(f'{href_img}?w=5000')
                            self.driver.find_element(by=By.ID, value="download-btn").click()
                            # Wait To LOAD
                            wait = WebDriverWait(self.driver, 60)
                            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                            # Downlaod
                            before_download = os.listdir(self.path_download)
                            self.driver.find_element(by=By.XPATH, value="//div[@class='card-body']//a[@download]").click()
                            sleep(10)
                            after_download = os.listdir(self.path_download)
                            new_files = [f for f in after_download if f not in before_download]
                            if new_files:
                                full_path = os.path.join(self.path_download, new_files[0])
                                if os.path.isfile(full_path):
                                    new_filename = f"{full_name}.jpg"
                                    new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                                    os.replace(full_path, new_file_path)
                                    if self.ftp is not None:
                                        upload_to_host(self, full_name, new_file_path, new_filename)
                        except Exception as ex:
                            print('JPG DOWNLOAD FAILED!')
                            print(ex)
                            with zipfile.ZipFile(new_file_path, 'r') as fileZip:
                                allFileInZip = fileZip.namelist()  # List
                                for extFileHere in allFileInZip:
                                    if re.fullmatch(f'\w+\.(jpg|png)', extFileHere):
                                        oldJPG = fileZip.extract(extFileHere,
                                                                 f'{self.path_download}/{self.name}/{full_name}')
                                        new_file_path = os.path.join(self.path_download, self.name, full_name,
                                                                     f'{full_name}.jpg')
                                        os.replace(oldJPG, new_file_path)
                                        self.db_cursor.execute(
                                            "UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                            (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                                        self.db_connection.commit()
                                        break
                    self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                           (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                    if 'eps' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_eps = %s WHERE title = %s",
                                               (f'{self.name}/{full_name}/{full_name}.eps', title_vector))
                    if 'ai' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_ai = %s WHERE title = %s",
                                               (f'{self.name}/{full_name}/{full_name}.ai', title_vector))
                    if 'svg' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_svg = %s WHERE title = %s",
                                               (f'{self.name}/{full_name}/{full_name}.svg', title_vector))
                    self.db_connection.commit()
                    try_temp += 1  # Check Try
                except Exception as ex:  # Just Zip File
                    # Zip File
                    print(ex)
                    # Downlaod
                    before_download = os.listdir(self.path_download)
                    self.driver.find_element(by=By.XPATH, value='//a[@data-cy="download-button"]').click()
                    sleep(10)
                    after_download = os.listdir(self.path_download)
                    new_files = [f for f in after_download if f not in before_download]
                    # pattern_search = rf"^{id_vector}_\d+\.{formating}$"
                    if new_files:
                        full_path = os.path.join(self.path_download, new_files[0])
                        if os.path.isfile(full_path):
                            # file_extension = os.path.splitext(filename)[1]
                            new_filename = f"{full_name}.zip"
                            new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                            os.replace(full_path, new_file_path)
                            if self.ftp is not None:
                                upload_to_host(self, full_name, new_file_path, new_filename)
                    self.db_cursor.execute("INSERT INTO freepik_vectors (title, link, path_zip, formats, size, license, tags) "
                                           "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                           (title_vector, pure_href, f'{self.name}/{full_name}/{full_name}.zip',
                                            file_formats, file_size, file_license, file_tags))
                    self.db_connection.commit()
                    img_jpg = self.driver.find_element(by=By.XPATH, value="//div[@class='_1286nb19f']//img")
                    href_img = img_jpg.get_attribute('src')
                    try:
                        self.driver.get('https://picodl.com')
                        # Wait To LOAD
                        wait = WebDriverWait(self.driver, 5)
                        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                        sleep(15)
                        self.driver.find_element(by=By.ID, value="image-url").send_keys(f'{href_img}?w=5000')
                        self.driver.find_element(by=By.ID, value="download-btn").click()
                        # Wait To LOAD
                        wait = WebDriverWait(self.driver, 60)
                        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                        # Downlaod
                        before_download = os.listdir(self.path_download)
                        self.driver.find_element(by=By.XPATH, value="//div[@class='card-body']//a[@download]").click()
                        sleep(10)
                        after_download = os.listdir(self.path_download)
                        new_files = [f for f in after_download if f not in before_download]
                        if new_files:
                            full_path = os.path.join(self.path_download, new_files[0])
                            if os.path.isfile(full_path):
                                new_filename = f"{full_name}.jpg"
                                new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                                os.replace(full_path, new_file_path)
                                if self.ftp is not None:
                                    upload_to_host(self, full_name, new_file_path, new_filename)
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                               (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                        self.db_connection.commit()
                        try_temp += 1  # Check Try
                    except Exception as ex:
                        print('JPG DOWNLOAD FAILED!')
                        print(ex)
                        with zipfile.ZipFile(new_file_path, 'r') as fileZip:
                            allFileInZip = fileZip.namelist()  # List
                            for extFileHere in allFileInZip:
                                if re.fullmatch(f'\w+\.(jpg|png)', extFileHere):
                                    oldJPG = fileZip.extract(extFileHere,
                                                             f'{self.path_download}/{self.name}/{full_name}')
                                    new_file_path = os.path.join(self.path_download, self.name, full_name,
                                                                 f'{full_name}.jpg')
                                    os.replace(oldJPG, new_file_path)
                                    self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                                           (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                                    self.db_connection.commit()
                                    break
            self.driver.get(this_url)
            # Wait To LOAD
            wait = WebDriverWait(self.driver, 30)
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            self.driver.find_element(by=By.XPATH, value="//a[@title='Next Page']").click()
            # Wait To LOAD
            sleep(random.randint(10, 20))
            vectors_page = self.driver.find_elements(by=By.XPATH, value='//figure[@data-cy="resource-thumbnail"]//a')
            if not vectors_page:
                file_name_json = f'{self.name}/{self.name}_Vector.json'
                check_here = False
                with open(file_name_json, 'w+') as json_file:
                    tags_save_search_file = json.load(json_file)  # Dict
                    for tag_here in tags_save_search_file.keys():
                        if tags_save_search_file[tag_here] == 0:
                            tags_save_search_file[tag_here] = 1
                            if re.search(r'query=\w+', this_url) is not None:
                                re.sub(r'query=\w+', 'query=hello', this_url)
                            else:
                                re.sub(r'last_filter=\w+', 'last_filter=query', this_url)
                                re.sub(r'last_value=\w+', f'last_value={tag_here}', this_url)
                                this_url = f"{this_url}&query={tag_here}"
                            check_here = True
                            break
                if not check_here:
                    print('No Scrapping File More!')
                else:
                    self.driver.get(this_url)
                    # Wait To LOAD
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                    vectors_page = self.driver.find_elements(by=By.XPATH,
                                                             value='//figure[@data-cy="resource-thumbnail"]//a')
                    json.dump(tags_save_search_file, json_file)  # Save To Json

    # Alone Scrapper (Vector Scrapper)
    def scrape_vector(self, url, account=False):
        self._initial_open()  # Open

        if account:  # Sign In
            self._sign_in()

        # Check Folder
        os.chdir(f'{self.path_download}')
        if not os.path.exists(self.name):
            os.mkdir(self.name)
        os.chdir('../')

        # Open Vector
        self.driver.get(url)
        # Wait To LOAD
        wait = WebDriverWait(self.driver, 30)
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        # Scroll 200px Bottom
        self.driver.execute_script("window.scrollBy(0, 200);")

        href_vector = url
        pure_href = href_vector.split('#')[0]
        full_name = href_vector.replace('//', '/').split('/')[3].split('.')[0]
        title_vector = full_name.split('_')[0].replace('-', ' ')
        id_vector = full_name.split('_')[1]
        new_file_path = None  # New Raname File

        os.chdir(f'{self.path_download}/{self.name}')
        if not os.path.exists(full_name):
            os.mkdir(full_name)
        os.chdir('../../')

        # Details
        try:  # File
            file_details = self.driver.find_elements(by=By.XPATH, value="//ul[@class='_1286nb11a9']//li//span//span")[
                0].text
            file_list = file_details.replace(':', '').split('/')
            file_size = file_list[0].strip()
            file_formats = file_list[1].strip()
        except Exception as ex:
            print("Size Or Format None")
            print(ex)
            file_size, file_formats = 'unknown', 'unknown'
        current_url = self.driver.current_url.replace('//', '/').split('/')[2]  # License
        file_license = 0  # Free
        if 'premium' in current_url:
            file_license = 1  # Premium
        # Related Tags
        try:  # Check All Tags
            file_all_tags = self.driver.find_element(by=By.XPATH,
                                                     value="//div[@style='grid-area:keywords']//button").click()
        except Exception as ex:
            print("Tags Less...")
            print(ex)
        all_tags_list = self.driver.find_elements(by=By.XPATH, value="//div[@style='grid-area:keywords']//ul//li//a")
        file_tags = ''
        for tag in all_tags_list:
            file_tags = file_tags + str(tag.text.strip()) + ', '

        # Download Try
        self.driver.find_element(by=By.XPATH, value='//button[@data-cy="wrapper-download-free"]').click()
        sleep(self.timeout_sleep)
        try:
            # Multi File
            format_list = ['jpg', 'eps', 'ai', 'svg', 'zip']
            list_pass = []
            for formating in format_list:
                self.driver.find_element(by=By.XPATH, value='//button[@data-cy="dropdown-download-type"]').click()
                sleep(self.timeout_sleep)
                # Find Formats
                try:
                    file_format = self.driver.find_element(by=By.XPATH,
                                                           value=f'//a[@data-cy="download-type-{formating}"]')
                    # Downlaod
                    before_download = os.listdir(self.path_download)
                    file_format.click()
                except Exception as ex:
                    print(ex)
                    continue
                sleep(10)
                after_download = os.listdir(self.path_download)
                new_files = [f for f in after_download if f not in before_download]
                # pattern_search = rf"^{id_vector}_\d+\.{formating}$"
                while True:
                    try:
                        if new_files:
                            if '.crdownload' in new_files[0]:  # Temp Doanload TimeOut
                                sleep(10)
                            full_path = os.path.join(self.path_download, new_files[0])
                            if os.path.isfile(full_path):
                                # file_extension = os.path.splitext(filename)[1]
                                new_filename = f"{full_name}.{formating}"
                                new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                                os.replace(full_path, new_file_path)
                                if self.ftp is not None:
                                    upload_to_host(self, full_name, new_file_path, new_filename)
                        break
                    except Exception as ex:  # For Complate Download
                        print(ex)
                        sleep(30)
                list_pass.append(str(formating))
            self.db_cursor.execute("INSERT INTO freepik_vectors (title, link, path_zip, formats, size, license, tags) "
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                   (title_vector, pure_href, f'{self.name}/{full_name}/{full_name}.zip',
                                    file_formats, file_size, file_license, file_tags))
            self.db_connection.commit()
            if 'jpg' not in list_pass:  # Download JPG (picodl.ir)
                img_jpg = self.driver.find_element(by=By.XPATH, value="//div[@class='_1286nb19f']//img")
                href_img = img_jpg.get_attribute('src')
                try:
                    self.driver.get('https://picodl.com')
                    # Wait To LOAD
                    wait = WebDriverWait(self.driver, 5)
                    wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                    sleep(15)
                    self.driver.find_element(by=By.ID, value="image-url").send_keys(f'{href_img}?w=5000')
                    self.driver.find_element(by=By.ID, value="download-btn").click()
                    # Wait To LOAD
                    wait = WebDriverWait(self.driver, 60)
                    wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                    # Downlaod
                    before_download = os.listdir(self.path_download)
                    self.driver.find_element(by=By.XPATH, value="//div[@class='card-body']//a[@download]").click()
                    sleep(10)
                    after_download = os.listdir(self.path_download)
                    new_files = [f for f in after_download if f not in before_download]
                    if new_files:
                        full_path = os.path.join(self.path_download, new_files[0])
                        if os.path.isfile(full_path):
                            new_filename = f"{full_name}.jpg"
                            new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                            os.replace(full_path, new_file_path)
                            if self.ftp is not None:
                                upload_to_host(self, full_name, new_file_path, new_filename)
                except Exception as ex:
                    print('JPG DOWNLOAD FAILED!')
                    print(ex)
                    with zipfile.ZipFile(new_file_path, 'r') as fileZip:
                        allFileInZip = fileZip.namelist()  # List
                        for extFileHere in allFileInZip:
                            if re.fullmatch(f'\w+\.(jpg|png)', extFileHere):
                                oldJPG = fileZip.extract(extFileHere,
                                                         f'{self.path_download}/{self.name}/{full_name}')
                                new_file_path = os.path.join(self.path_download, self.name, full_name,
                                                             f'{full_name}.jpg')
                                os.replace(oldJPG, new_file_path)
                                self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                                       (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                                self.db_connection.commit()
                                break
            self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                   (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
            if 'eps' in list_pass:
                self.db_cursor.execute("UPDATE freepik_vectors SET path_eps = %s WHERE title = %s",
                                       (f'{self.name}/{full_name}/{full_name}.eps', title_vector))
            if 'ai' in list_pass:
                self.db_cursor.execute("UPDATE freepik_vectors SET path_ai = %s WHERE title = %s",
                                       (f'{self.name}/{full_name}/{full_name}.ai', title_vector))
            if 'svg' in list_pass:
                self.db_cursor.execute("UPDATE freepik_vectors SET path_svg = %s WHERE title = %s",
                                       (f'{self.name}/{full_name}/{full_name}.svg', title_vector))
            self.db_connection.commit()
            # Fetch Result
            self.db_cursor.execute("SELECT * FROM freepik_vectors WHERE title = %s", (title_vector,))
            result = self.db_cursor.fetchone()
            return result
        except Exception as ex:
            # Zip File
            print(ex)
            # Downlaod
            before_download = os.listdir(self.path_download)
            self.driver.find_element(by=By.XPATH, value='//a[@data-cy="download-button"]').click()
            sleep(10)
            after_download = os.listdir(self.path_download)
            new_files = [f for f in after_download if f not in before_download]
            # pattern_search = rf"^{id_vector}_\d+\.{formating}$"
            if new_files:
                full_path = os.path.join(self.path_download, new_files[0])
                if os.path.isfile(full_path):
                    # file_extension = os.path.splitext(filename)[1]
                    new_filename = f"{full_name}.zip"
                    new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                    os.replace(full_path, new_file_path)
                    if self.ftp is not None:
                        upload_to_host(self, full_name, new_file_path, new_filename)
            self.db_cursor.execute("INSERT INTO freepik_vectors (title, link, path_zip, formats, size, license, tags) "
                                   "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                   (title_vector, pure_href, f'{self.name}/{full_name}/{full_name}.zip',
                                    file_formats, file_size, file_license, file_tags))
            self.db_connection.commit()
            img_jpg = self.driver.find_element(by=By.XPATH, value="//div[@class='_1286nb19f']//img")
            href_img = img_jpg.get_attribute('src')
            try:
                self.driver.get('https://picodl.com')
                # Wait To LOAD
                wait = WebDriverWait(self.driver, 5)
                wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                sleep(15)
                self.driver.find_element(by=By.ID, value="image-url").send_keys(f'{href_img}?w=5000')
                self.driver.find_element(by=By.ID, value="download-btn").click()
                # Wait To LOAD
                wait = WebDriverWait(self.driver, 60)
                wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                # Downlaod
                before_download = os.listdir(self.path_download)
                self.driver.find_element(by=By.XPATH, value="//div[@class='card-body']//a[@download]").click()
                sleep(10)
                after_download = os.listdir(self.path_download)
                new_files = [f for f in after_download if f not in before_download]
                if new_files:
                    full_path = os.path.join(self.path_download, new_files[0])
                    if os.path.isfile(full_path):
                        new_filename = f"{full_name}.jpg"
                        new_file_path = os.path.join(self.path_download, self.name, full_name, new_filename)
                        os.replace(full_path, new_file_path)
                        if self.ftp is not None:
                            upload_to_host(self, full_name, new_file_path, new_filename)
                self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                       (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                self.db_connection.commit()
            except Exception as ex:
                print('JPG DOWNLOAD FAILED!')
                print(ex)
                with zipfile.ZipFile(new_file_path, 'r') as fileZip:
                    allFileInZip = fileZip.namelist()  # List
                    for extFileHere in allFileInZip:
                        if re.fullmatch(f'\w+\.(jpg|png)', extFileHere):
                            oldJPG = fileZip.extract(extFileHere,
                                                     f'{self.path_download}/{self.name}/{full_name}')
                            new_file_path = os.path.join(self.path_download, self.name, full_name,
                                                         f'{full_name}.jpg')
                            os.replace(oldJPG, new_file_path)
                            self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                                   (f'{self.name}/{full_name}/{full_name}.jpg', title_vector))
                            self.db_connection.commit()
                            break
            # Fetch Result
            self.db_cursor.execute("SELECT * FROM freepik_vectors WHERE title = %s", (title_vector,))
            result = self.db_cursor.fetchone()
            return result

    # Search In DB (Vector)
    def search_vector(self, link=None, title=None, size=None, formats=None, license_=None, tags=None, transfer=None,
                      max_limit=25):
        query = "SELECT * FROM freepik_vectors "
        params = []
        conditions = []

        search_params = {
            'link': link,
            'title': title,
            'size': size,
            'license': license_,
            'transfer': transfer
        }

        for key, value in search_params.items():
            if value is not None:
                conditions.append(f"{key} = %s")
                params.append(value)

        if tags:
            conditions.append("tags LIKE %s")
            params.append(f'%{tags}%')

        if formats:
            conditions.append("formats LIKE %s")
            params.append(f'%{formats}%')

        if not conditions:
            return False

        query += 'WHERE '
        query += " AND ".join(conditions)
        query += f" LIMIT {max_limit}"

        self.db_cursor.execute(query, tuple(params))

        if link:
            result = self.db_cursor.fetchone()
        else:
            result = self.db_cursor.fetchmany(max_limit)

        return result if result else False

    # ---------- Vector FreePic ----------


# Upload To Ftp
def upload_to_host(self: FreePik, full_name, new_file_path, new_filename):
    try:
        try:
            self.ftp.cwd(self.name)
        except Exception as ex:
            print(ex)
            self.ftp.mkd(self.name)
            self.ftp.cwd(self.name)
        try:
            self.ftp.cwd(full_name)
        except Exception as ex:
            print(ex)
            self.ftp.mkd(full_name)
            self.ftp.cwd(full_name)
        with open(new_file_path, 'rb') as file:
            self.ftp.storbinary(f'STOR {new_filename}', file)
    except Exception as ex:
        print(f'FTP Error\n{ex}')
    self.close_fpt()
