import appdaemon.plugins.hass.hassapi as hass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from datetime import datetime
from typing import List, Optional
import time

class Account:
    def __init__(self, name: str, username: str, password: str, input_boolean: str, input_datetime: str):
        self.name = name
        self.username = username
        self.password = password
        self.input_boolean = input_boolean
        self.input_datetime = input_datetime

class HeiliLibraryAgent(hass.Hass):

    def initialize(self):
        self.log("HeiliLibraryAgent initialized")
        self.setup_accounts()
        
        for account in self.accounts:
            self.listen_state(self.trigger_script, account.input_boolean)

        # TEMP do not fetch when debugging
        # Run fetch_due_date for all accounts on initialization
        self.log("should fetch all on startup")
        # 3 second delay
        self.run_in(self.fetch_all_due_dates, 3)

        # Call fetch_all_due_dates daily
        time = self.parse_time(self.args.get("update_time", "03:00:00"))
        self.run_daily(self.fetch_all_due_dates, time)

    def setup_accounts(self):
        self.accounts: List[Account] = []
        account_names = self.args.get("account_names", [])
        for name in account_names:
            account = Account(
                name=name,
                username=self.args[f"heili_{name}_username"],
                password=self.args[f"heili_{name}_password"],
                input_boolean=f"input_boolean.run_webscrape_heili_renew_all_{name}",
                input_datetime=f"input_datetime.webscrape_heili_date_{name}"
            )
            self.accounts.append(account)

    def trigger_script(self, entity, attribute, old, new, kwargs):
        if new == "on":
            account = next((acc for acc in self.accounts if acc.input_boolean == entity), None)
            if account:
                self.log(f"Starting renewal process for {account.name}...")
                self.run_in(self.renew_all_books, 0, account=account)

    @staticmethod
    def setup_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")

        custom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
        }

        driver = webdriver.Chrome(options=chrome_options)

        for key, value in custom_headers.items():
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": custom_headers["User-Agent"]})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {"headers": custom_headers})

        return driver

    def login_to_website(self, driver: webdriver.Chrome, account: Account) -> bool:
        try:
            self.log(f"Logging in for {account.name}...")
            driver.get("https://heilikirjastot.fi/protected/my-account/overview")
            WebDriverWait(driver, 20).until(lambda d: d.find_element(By.NAME, "openTextUsernameContainer:openTextUsername"))
            self.log(f"Username field found")

            username_field = driver.find_element(By.ID, "id__patronLogin__WAR__arenaportlet____4")
            
            
            # make it visible
            driver.execute_script("document.querySelector('#p_p_id_patronLogin_WAR_arenaportlet_').style.display = 'block';")
            
            password_field = driver.find_element(By.NAME, "textPassword")
            if username_field and password_field:
                self.log(f"Username and password fields found")
            
            
            #self.log(f"Element state: visible={username_field.is_displayed()}, enabled={username_field.is_enabled()}")
            
            username_field.send_keys(account.username)
            #self.log(f"username sent")
            password_field.send_keys(account.password)
            #self.log(f"password sent")

            submit_button = driver.find_element(By.CLASS_NAME, "js-new-login-button")

            if submit_button:
                self.log(f"Sending submit...")
                submit_button.click()
                self.log(f"Submit sent")
                return True
            else:
                self.log(f"Login form submit button not found for {account.name}.")
                return False
        except WebDriverException as ex:
            self.log(f"Error during login for {account.name}: {ex}")
            return False

    def renew_all_books(self, kwargs):
        account = kwargs['account']
        self.log(f"Starting 'Renew All' for {account.name}...")
        with self.setup_driver() as driver:
            if not self.login_to_website(driver, account):
                return

            try:

                WebDriverWait(driver, 20).until(lambda d: d.find_element(By.CLASS_NAME, "portlet-content"))

                # make Lainani section visible
                driver.execute_script("document.querySelector('#portlet_loansWicket_WAR_arenaportlet > div > div').style.display = 'block';")


#                WebDriverWait(driver, 10).until(lambda d: d.find_element(By.NAME, "renewAll"))
                
                select_all_box = self.find_element_safe(driver, By.NAME, "loansCheckboxGroup:selectAll")
                renew_all_button = self.find_element_safe(driver, By.NAME, "renewLoansSubmit")
                if select_all_box and renew_all_button:

                    self.log(f"Selecting all loans for {account.name}...")

                    # Klikkaa checkbox valituksi
                    select_all_box.click()

                    # Pieni viive, jotta JS ehtii käsitellä valinnan
                    time.sleep(1)

                    # Varmista, että Renew-painike on nyt aktiivinen
                    self.log(f"Clicking 'Renew' for {account.name}...")
                    renew_all_button = self.find_element_safe(driver, By.NAME, "renewLoansSubmit")
                    renew_all_button.click()

                    # Odota vahvistusviesti tai onnistumisen tunniste
                    WebDriverWait(driver, 20).until(
                        lambda d: d.find_element(By.ID, "renewalsuccess")
                    )
                    self.log(f"Renew for {account.name} success")


                    # self.log(f"Selected all and clicking 'Renew' for {account.name}...")
                    # renew_all_button.click()
                    # WebDriverWait(driver, 20).until(lambda d: d.find_element(By.ID, "renewalsuccess"))
                    # self.log(f"Renew for {account.name} success")


                    #renew_all_yes_button = self.find_element_safe(driver, By.ID, "confirm_renew_all_yes")
                    #if renew_all_yes_button:
                    #    self.log(f"Confirming 'Renew All' for {account.name}...")
                    #    renew_all_yes_button.click()
                    #    self.run_in(self.fetch_due_date, 0, account=account)
                    #else:
                    #    self.log(f"'Renew All YES' button not found for {account.name}.")
                else:
                    self.log(f"'Renew All' button not found for {account.name}.")
                    if select_all_box:
                        self.log(f"select_all_box ok")
                    if renew_all_button:
                        self.log(f"renew_all_button ok")
            except TimeoutException:
                self.log(f"Timeout while renewing books for {account.name}.")
        
        self.turn_off(account.input_boolean)
        self.log(f"Renewal process for {account.name} completed.")
        self.run_in(self.fetch_due_date, 2, account=account)

    @staticmethod
    def find_element_safe(driver: webdriver.Chrome, by: By, value: str) -> Optional[webdriver.remote.webelement.WebElement]:
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            #self.log(f"'find_element_safe' failed for {value} by {by}.")
            return None

    # def fetch_all_due_dates(self, kwargs):
    #     self.log("fetch_all_due_dates")
    #     for account in self.accounts:
    #         self.run_in(self.fetch_due_date, 0, account=account)

    def fetch_all_due_dates(self, kwargs):
        self.log("fetch_all_due_dates")
        for i, account in enumerate(self.accounts):
            delay = i * 60
            self.run_in(self.fetch_due_date, delay, account=account)
            self.log(f"Fetch for {account.name} scheduled after {delay}s")


    def fetch_due_date(self, kwargs):
        account = kwargs['account']
        self.log(f"Fetching due date for {account.name}...")
        with self.setup_driver() as driver:
            if not self.login_to_website(driver, account):
                return
            
            self.log(f"Login success")

            try:
                #WebDriverWait(driver, 50).until(lambda d: d.find_element(By.XPATH, '//*[@id="content"]'))
                WebDriverWait(driver, 20).until(lambda d: d.find_element(By.CLASS_NAME, "portlet-content"))
                #due_date_element = self.find_element_safe(driver, By.CSS_SELECTOR, "td.checkedout-status-information > div.status-column > strong")
                #due_date_element = self.find_element_safe(driver, By.CSS_SELECTOR, "span.arena-renewal-date-value > span")

                

                # make Lainani section visible
                driver.execute_script("document.querySelector('#portlet_loansWicket_WAR_arenaportlet > div > div').style.display = 'block';")
            

                #due_date_element = driver.find_element(By.CSS_SELECTOR, 'td.arena-renewal-date > span.arena-renewal-date-value[aria-label^="Eräpäivä:"]')
                due_date_element = self.find_element_safe(driver, By.CSS_SELECTOR, 'td.arena-renewal-date > span.arena-renewal-date-value[aria-label^="Eräpäivä:"]')
                #self.find_element_safe(driver, By.NAME, "processLogin")
                
                if due_date_element:
                    due_date_text = due_date_element.text
                    self.log(f"Due date element found: {due_date_text}")
                    due_date_parts = due_date_text.split(": ")
                    if len(due_date_parts) == 2:
                        due_date = due_date_parts[1]
                        due_date_ymd = self.parse_date(due_date).strftime("%Y-%m-%d")
                        self.log(f"Due date fetched for {account.name}: {due_date}")
                        self.call_service("input_datetime/set_datetime", 
                            entity_id=account.input_datetime,
                            date=due_date_ymd) 
                    elif len(due_date_parts) == 1:
                        due_date = due_date_parts[0]
                        #self.log(f"Due {due_date}")
                        due_date_ymd = self.parse_date(due_date).strftime("%Y-%m-%d")
                        self.log(f"Due date fetched for {account.name}: {due_date}")
                        self.call_service("input_datetime/set_datetime", 
                            entity_id=account.input_datetime,
                            date=due_date_ymd)
                        
                    else:
                        self.log(f"Failed to parse due date for {account.name}. Unexpected format: {due_date_text}")
                else:
                    self.log(f"Due date element not found for {account.name}. Setting to 1.1.2000")
                    self.call_service("input_datetime/set_datetime", 
                            entity_id=account.input_datetime,
                            date='2000-01-01')
            except TimeoutException:
                self.log(f"Timeout while fetching due date for {account.name}.")
            except NoSuchElementException:
                self.log(f"NoSuchElementException while fetching due date for {account.name}.")
            self.log(f"Fetch end {account.name}")
            return True

    @staticmethod
    def parse_date(date_string: str) -> datetime:
        return datetime.strptime(date_string, "%d.%m.%Y")