from config import config
from config import account_list
from time import sleep
import os
from selenium.webdriver.common.by import By

from scraperModules.BaseClass import BaseClass


class FreePik(BaseClass):
    # inital
    def __init__(self, timeout=config.TIMEOUT_SLEEP):
        super().__init__(timeout)

    # ---------- Vector FreePic ----------

    # Main Scrapper (Vector Scrapper)
    def scrape_vectors(self, url="https://www.freepik.com/search?format=search&type=vector", account=False, premium=False):
        if premium:
            this_url = f"{url}&last_filter=premium&last_value=1&premium=1"
        else:
            this_url = f"{url}&last_filter=selection&last_value=1&selection=1"

        self.driver = self.setup_driver()
        self.driver.get('https://www.freepik.com/log-in?client_id=freepik&lang=en')  # Sign In Link
        sleep(5)

        # Switch To AdBlocker
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.close()

        # Switch To Main Tab
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Accept Button Cookies
        try:
            self.driver.find_element(by=By.ID, value='onetrust-accept-btn-handler').click()
        except Exception as error:
            print(error)

        # Sign In
        # self.driver.find_element(by=By.XPATH, value='//a[@data-cy="login-button"]').click()
        self.driver.find_elements(by=By.XPATH, value='//button[@class="main-button button button--outline button--with-icon"]')[-1].click()
        sleep(5)
        # List Account
        myAccount = account_list.account_list['Freepik'][0]
        self.driver.find_element(by=By.XPATH, value='//input[@name="email"]').send_keys(myAccount['email'])
        sleep(5)
        self.driver.find_element(by=By.XPATH, value='//input[@name="password"]').send_keys(myAccount['password'])
        sleep(5)
        self.driver.find_element(by=By.ID, value='submit').click()
        sleep(60)  # For Manual Captcha Check

        # Go To Main Scrap
        self.driver.get(this_url)
        self.driver.implicitly_wait(20)
        vetors_page = self.driver.find_elements(by=By.XPATH, value='//figure[@data-cy="resource-thumbnail"]//a')

        for vector in vetors_page:
            href_vector = vector.get_attribute('href')
            full_name = href_vector.replace('//', '/').split('/')[3].split('.')[0]
            title_vector = full_name.split('_')[0].replace('-', ' ')
            id_vector = full_name.split('_')[1]

            # Check Exist Element
            self.db_cursor.execute("SELECT title FROM freepik_vectors WHERE title=%s", (title_vector,))
            result = self.db_cursor.fetchone()
            if result is not None:
                continue

            # Open Vector New Tab
            self.driver.get(href_vector)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            sleep(self.timeout_sleep)
            self.driver.implicitly_wait(5)

            os.chdir(f'{self.path_download}/Freepik')
            if not os.path.exists(full_name):
                os.mkdir(full_name)
            os.chdir('../../')

            # Details
            try:  # File
                file_details = self.driver.find_elements(by=By.XPATH, value="//ul[@class='_1286nb11a9']//li//span//span")[0].text
                file_list = file_details.replace(':', '').split('/')
                file_size = file_list[0].strip()
                file_format = file_list[1].strip()
            except Exception as ex:
                print("Size Or Format None")
                print(ex)
                file_size, file_format = 'unknown', 'unknown'
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
            for tag in all_tags_list:
                file_tags = file_tags + str(tag.text.split()) + ', '

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
                    if new_files:
                        full_path = os.path.join(self.path_download, new_files[0])
                        if os.path.isfile(full_path):
                            # file_extension = os.path.splitext(filename)[1]
                            new_filename = f"{full_name}.{formating}"
                            new_file_path = os.path.join(self.path_download, 'Freepik', full_name, new_filename)
                            os.replace(full_path, new_file_path)
                    list_pass.append(str(formating))
                    self.db_cursor.execute("INSERT INTO freepik_vectors (title, path_zip, formats, size, license, tags) "
                                           "VALUES (%s, %s, %s, %s, %s, %s)",
                                           (title_vector, f'Freepik/{full_name}/{full_name}.zip',
                                            file_format, file_size, file_license, file_tags))
                    self.db_connection.commit()
                    if 'jpg' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_jpg = %s WHERE title = %s",
                                               (f'Freepik/{full_name}/{full_name}.jpg', title_vector))
                    if 'eps' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_eps = %s WHERE title = %s",
                                               (f'Freepik/{full_name}/{full_name}.eps', title_vector))
                    if 'ai' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_ai = %s WHERE title = %s",
                                               (f'Freepik/{full_name}/{full_name}.ai', title_vector))
                    if 'svg' in list_pass:
                        self.db_cursor.execute("UPDATE freepik_vectors SET path_svg = %s WHERE title = %s",
                                               (f'Freepik/{full_name}/{full_name}.svg', title_vector))
                    self.db_connection.commit()
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
                        new_file_path = os.path.join(self.path_download, 'Freepik', full_name, new_filename)
                        os.replace(full_path, new_file_path)
                self.db_cursor.execute("INSERT INTO freepik_vectors (title, path_zip, formats, size, license, tags) "
                                       "VALUES (%s, %s, %s, %s, %s, %s)",
                                       (title_vector, f'Freepik/{full_name}/{full_name}.zip',
                                        file_format, file_size, file_license, file_tags))
                self.db_connection.commit()

            self.driver.back()
            # Test
            print("Done")
            return

    # Alone Scrapper (Vector Scrapper)
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

    # Search In DB (Vector)
    def search(self, name):
        self.db_cursor.execute("SELECT name FROM flaticon WHERE name=%s", (name,))
        result = self.db_cursor.fetchone()
        if result is not None:
            return True
        return False

    # ---------- Vector FreePic ----------
