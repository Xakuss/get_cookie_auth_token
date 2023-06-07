import csv
import zipfile
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import json
import tempfile
import shutil


def click_button(driver, button) -> None:
    "нажатие на кнопку"
    wait = WebDriverWait(driver, 10)
    next_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, button)))
    ActionChains(driver).move_to_element(next_button).click().perform()


def get_chromedriver_with_proxy(proxy_ip: str, proxy_port: str, proxy_user: str, proxy_pass: str, user_agent: str):
    "получить хром драйвер с прокси для работы с селениумом"

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"76.0.0"
    }
    """

    background_js = """
    let config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }
    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_ip, proxy_port, proxy_user, proxy_pass)

    chrome_options = webdriver.ChromeOptions()

    plugin_file = 'proxy_auth_plugin.zip'

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr('manifest.json', manifest_json)
        zp.writestr('background.js', background_js)

    chrome_options.add_extension(plugin_file)

    chrome_options.add_argument(f'--user-agent={user_agent}')

    s = Service(
        executable_path='path_to_chromedriver'
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )

    return driver


def twitter_auth(driver, login: str, password: str, reserve_mail: str):
    "Заходит в твиттер"
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://twitter.com/i/flow/login")
        sleep(2)
        driver.find_element(By.NAME,
                            "text").send_keys(login)
        print("ввожу логин")
        sleep(1)
        click_button(driver,
                     "div[class='css-18t94o4 css-1dbjc4n r-sdzlij r-1phboty r-rs99b7 r-ywje51 r-usiww2 r-2yi16 r-1qi8awa r-1ny4l3l r-ymttw5 r-o7ynqc r-6416eg r-lrvibr r-13qz1uu'")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "Input[type='password']"))).send_keys(password)
        print("ввожу пароль")
        click_button(driver,
                     "div[class = 'css-18t94o4 css-1dbjc4n r-sdzlij r-1phboty r-rs99b7 r-19yznuf r-64el8z r-1ny4l3l r-1dye5f7 r-o7ynqc r-6416eg r-lrvibr']")
        sleep(2)
        if driver.current_url == "https://twitter.com/home":
            print("зашел без резрвной почты")
        else:
            print("ввожу резервную")
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "Input[type='email']"))).send_keys(
                reserve_mail)
            click_button(driver,
                         "div[class = 'css-18t94o4 css-1dbjc4n r-sdzlij r-1phboty r-rs99b7 r-19yznuf r-64el8z r-1ny4l3l r-1dye5f7 r-o7ynqc r-6416eg r-lrvibr']")
        return json.dumps(driver.get_cookie("auth_token"))
        # with open("cookie", "a") as file:
        #     file.write(json.dumps(driver.get_cookie("auth_token")))
        #     file.write(",\n")
        #     print("успешно записал токен")
    except Exception:
        print("что то не так")
    finally:
        driver.close()
        driver.quit()


if __name__ == '__main__':

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    with open("data.csv",
              "r") as f, temp_file:  # блок для очистки с помощью временных файлов, чтобы при каждом новом запуске кода все, кроме 1 строки стиралось
        reader = csv.reader(f)
        writer = csv.writer(temp_file)
        try:
            header = next(reader)
            writer.writerow(header)
        except StopIteration:
            print("Файл CSV пуст или содержит только заголовки столбцов.")
    shutil.move(temp_file.name, "data.csv")
    temp_file.close()

    with open("data.csv", "w", newline="") as f, open("data1.csv", "r") as f1:
        reader_1 = csv.DictReader(f1)
        writer_1 = csv.DictWriter(f,
                                  ["proxy_ip", "proxy_port", "proxy_login", "proxy_password", "user_agent", "tw_cookie",
                                   "tw_user",
                                   "tw_url"])
        writer_1.writeheader()  # запись заголовков, без нее в файл будут записаны только значения
        for row in reader_1:
            data = {
                "proxy_ip": row["proxy_ip"],
                "proxy_port": row["proxy_port"],
                "proxy_login": row["proxy_login"],
                "proxy_password": row["proxy_password"],
                "user_agent": row["user_agent"],
                "tw_cookie":
                    twitter_auth(get_chromedriver_with_proxy(row["proxy_ip"], row["proxy_port"], row["proxy_login"],
                                                             row["proxy_password"], row["user_agent"]),
                                 row["tw_login"], row["tw_password"], row["tw_reserve_mail"])
            }
            writer_1.writerow(data)
# with open("cookie", "w") as file:
#     file.truncate(0)
# with open("cookie", "a") as file:
#     file.write("[")
# with open("data.csv", "r") as file:
#     reader = csv.DictReader(file)
#     for row in reader:
#         try:
#             twitter_auth(get_chromedriver_with_proxy(row["proxy_ip"], row["proxy_port"], row["proxy_login"],
#                                                      row["proxy_password"], row["user_agent"]),
#                          row["tw_login"], row["tw_password"], row["tw_reserve_mail"])
#         except Exception as ex:
#             print(ex, "где то ошибка")
# with open("cookie", "a") as file:
#     file.write("{}]")
