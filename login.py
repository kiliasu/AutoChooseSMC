from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.support.ui import Select
import subprocess
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import requests

# Discord Webhook URL
WEBHOOK_URL = ""

def notify_discord(message):
    data = {
        "content": message,
        
        
    }
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:  # 204表示请求成功
        print("Message sent to Discord successfully!")
    else:
        print(f"Failed to send message to Discord. Response code: {response.status_code}, Response: {response.text}")

# Load credentials from config.txt 加载凭据
with open("config.txt", "r") as f:
    config_data = eval(f.read())
    username = config_data["username"]
    password = config_data["password"]

def init_chrome_driver():
    try:
        # try to use the chromedriver from PATH/尝试使用 PATH 中的 chromedriver
        browser = webdriver.Chrome()
    except WebDriverException:
        print("Failed to use chromedriver from PATH. Trying the integrated one...")
        # 指定项目内部的 chromedriver 路径/Specify the path to the chromedriver within the project
        chrome_driver_path = './drivers/chromedriver'
        browser = webdriver.Chrome(executable_path=chrome_driver_path)
    return browser

# 使用函数来初始化 Chrome/Use a function to initialize Chrome
browser = init_chrome_driver()

# Navigate to the login page/导航到登录页面
browser.get("https://smccis.smc.edu/smcweb/f?p=20240325:LOGIN_DESKTOP::::::")
print("Logging in...")

# Enter the username and password/输入用户名和密码
username_field = browser.find_element(By.ID, "P9999_USERNAME")
username_field.send_keys(username)
password_field = browser.find_element(By.ID, "P9999_PASSWORD")
password_field.send_keys(password)

# Click the Sign In button/点击登录按钮
sign_in_button = browser.find_element(By.ID, "B7242879295214351318")
sign_in_button.click()

# Wait for the login process to complete/等待登录过程完成
time.sleep(2)

# Locate the semester dropdown/定位下拉学期菜单
semester_dropdown = browser.find_element(By.ID, "P0_SEMCODE")

# Create a Select object/创建一个 Select 对象
select = Select(semester_dropdown)

# Select by visible text/按可见文本选择学期
select.select_by_visible_text(config_data["semester"])
print("Selecting semester...")

# Refresh the page after selecting the semester/选择学期后刷新页面
browser.refresh()
time.sleep(1)

# Use WebDriverWait to ensure that the page has loaded after the refresh/使用 WebDriverWait 确保刷新后页面已加载
wait_creation_code = "wait = WebDriverWait(browser, 20)"
wait = WebDriverWait(browser, 20)
wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div[1]/div[2]/div[2]/div[2]/div/div[3]/div/div/div/div/div/div/div/div/div[3]/button')))

# Use WebDriverWait to ensure that the "Add Classes" button is present and clickable before interacting with it/使用 WebDriverWait 确保“添加课程”按钮在与之交互之前存在并可点击
add_classes_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/form/div[1]/div[2]/div[2]/div[2]/div/div[3]/div/div/div/div/div/div/div/div/div[3]/button')))
add_classes_button.click()
print("Trying to get the choose classes page...")

# Wait for the course selection page to load/等待课程选择页面加载
wait = WebDriverWait(browser, 20)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#P301_ADDSCTNUM")))

MAX_RETRIES = 1
for attempt in range(MAX_RETRIES):
    try:
        # Input the course code and try to add the class/输入课程代码并尝试添加课程
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#P301_ADDSCTNUM")))
        course_code_input = browser.find_element(By.CSS_SELECTOR, "#P301_ADDSCTNUM")
        course_code_input.send_keys(config_data["check_code"])
        print("Adding class " + config_data["check_code"])
        add_the_class_button = browser.find_element(By.CSS_SELECTOR, "#B7210995900197509441")
        add_the_class_button.click()
        
        # Check for the second confirmation window/检查前置课程pass二次确认窗口
        try:
            continue_add_button = browser.find_element(By.ID, "B7212605618119480274")
            continue_add_button.click()
        except:
            # If not found, continue with the original logic/如果未找到，继续使用原始逻辑
            pass

        # 等待选课状态消息元素出现并变为可见/Wait for the status message element to appear and become visible
        status_message_element = WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#P301_MESSAGE > table > tbody > tr > td:nth-child(2) > font > b"))
    )

        # Locate the status message after trying to add the class/尝试添加课程后找到状态消息
        status_message_element = browser.find_element(By.CSS_SELECTOR, "#P301_MESSAGE > table > tbody > tr > td:nth-child(2) > font > b")
        status_message_text = status_message_element.text

        if "success" in status_message_text.lower():
            print("Course added successfully!")
            notify_discord(f"Course {check_code} added successfully!")
            break
        elif "cannot add section" in status_message_text.lower():
            print(f"Failed to add the course on attempt {attempt + 1}: {status_message_text}")
            # 关闭弹窗/Close the popup
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#B6591218527447274516")))
            ok_button = browser.find_element(By.CSS_SELECTOR, "#B6591218527447274516")
            browser.execute_script("arguments[0].click();", ok_button)

            # 点击重置按钮/Click the reset button
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#B7210995973172509442")))
            reset_button = browser.find_element(By.CSS_SELECTOR, "#B7210995973172509442")
            reset_button.click()
            # 等待页面刷新/Wait for the page to refresh

            browser.refresh()
            time.sleep(1)
            raise Exception("Failed to add the course, retrying...")
        else:
            print(f"Received status on attempt {attempt + 1}: {status_message_text}")
            raise Exception("Unexpected status, retrying...")
    except Exception as e:
        print(f"Attempt {attempt + 1} failed due to: {str(e)}. Retrying...")
else:
    print(f"Failed to add the class after {MAX_RETRIES} attempts.")
    print("now try running waitlist_detector.py")
    subprocess.run(["python", "waitlist_detector.py"])
    #激活等待列表检测器/Activate the waitlist detector

time.sleep(10)
# Close the browser
browser.close()
