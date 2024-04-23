import imaplib
import email
import json
import time
import subprocess
import base64
import requests

WEBHOOK_URL = ""

def notify_discord(message):
    data = {
        "content": message,
        
    }
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:  # 204表示请求成功/204 means request was successful
        print("Message sent to Discord successfully!")
    else:
        print(f"Failed to send message to Discord. Response code: {response.status_code}, Response: {response.text}")

def update_config_with_detected_code(config_path, email_content):
    # 读取配置文件/Read the config file
    with open(config_path, 'r') as file:
        config = json.load(file)

    # 从配置中获取两个检查代码/Get the two check codes from the config
    check_code1 = config.get('check_code1')
    check_code2 = config.get('check_code2')

    # 检查邮件内容是否包含这些代码，并更新配置/Check if the email content contains these codes and update the config
    if check_code1 and check_code1 in email_content:
        config['check_code'] = check_code1
    elif check_code2 and check_code2 in email_content:
        config['check_code'] = check_code2

    # 将更新后的配置写回文件/Write the updated config back to the file
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)



def check_new_emails(user, password):
   
    #在Gmail中检查新的邮件/Check for new emails in Gmail
    
    # 连接到Gmail的IMAP服务器/Connect to Gmail's IMAP server
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(user, password)
    mail.select('inbox')

    # 搜索所有未读邮件/Search for all unread emails
    result, data = mail.search(None, '(UNSEEN)')
    mail_ids = data[0]
    id_list = mail_ids.split()

    emails = []
    for num in id_list:
        typ, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        emails.append(email_message)

    mail.logout()
    return emails

def parse_email_for_waitlist_update(email_message, check_code1, check_code2):
    """
    解析邮件内容，检查是否包含特定的 check_code/Parse the email content and check if it contains the specific check_code.
    """
    # 尝试从Base64解码邮件内容
    try:
        # 检查email_message是否是多部分邮件/Check if email_message is a multipart email
        if email_message.is_multipart():
            # 如果是多部分，获取所有部分的payload（可能有多个部分）/If it is multipart, get the payload of all parts (there may be multiple parts)
            parts = email_message.get_payload()
            # 将所有部分的内容解码并连接起来/Decode and concatenate the content of all parts
            decoded_content = ""
            for part in parts:
                try:
                    # 解码每个部分的内容/Decode the content of each part
                    part_content = part.get_payload(decode=True).decode('utf-8')
                except:
                    # 如果解码失败，使用原始内容/If decoding fails, use the original content
                    part_content = part.get_payload()
                decoded_content += part_content
        else:
            # 如果不是多部分，直接解码内容/If it is not multipart, decode the content directly
            decoded_content = email_message.get_payload(decode=True).decode('utf-8')
    except Exception as e:
        # 如果有任何异常，打印异常并使用原始邮件内容/If there is any exception, print the exception and use the original email content
        print("An error occurred while decoding the email content:", e)
        decoded_content = email_message.get_payload()
    
    # 检查解码后的内容是否包含 check_code1 或 check_code2（不区分大小写）/Check if the decoded content contains check_code1 or check_code2 (case-insensitive)
    if (check_code1.lower() in decoded_content.lower() or 
    check_code2.lower() in decoded_content.lower()):
        return True
    else:
        return False



def load_config(file_path):
    """
    从给定的配置文件路径加载配置/Load the configuration from the given config file path.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def get_email_content(email_message):
    """
    提取邮件的内容，无论是多部分还是单部分邮件/Extract the content of the email, whether it is a multipart or single part email.
    """
    try:
        if email_message.is_multipart():
            parts = email_message.get_payload()
            decoded_content = ""
            for part in parts:
                try:
                    part_content = part.get_payload(decode=True).decode('utf-8')
                except:
                    part_content = part.get_payload()
                decoded_content += part_content
        else:
            decoded_content = email_message.get_payload(decode=True).decode('utf-8')
    except Exception as e:
        print("An error occurred while decoding the email content:", e)
        decoded_content = email_message.get_payload()
    return decoded_content


def main():
    # 加载配置/Load the configuration
    config = load_config("config.txt") 
    user = config["email"]
    password = config["email_password"]
    check_code1 = config["check_code1"]  # 确保这个值在配置文件中
    check_code2 = config["check_code2"]  # 确保这个值在配置文件中

    while True:  # 此循环将使脚本持续运行/This loop will keep the script running
        print("正在检查新邮件...")
        emails = check_new_emails(user, password)
        print(f"检测到 {len(emails)} 封新邮件.")
        for email_message in emails:
            # 直接在条件语句中调用函数，并传递正确的参数
            if parse_email_for_waitlist_update(email_message, check_code1, check_code2):
                # 获取邮件内容/Get the email content
                email_content = get_email_content(email_message)  # 获取邮件内容
                print("邮件内容 (前100个字符):", email_content[:100])
                print("检测到Waitlist更新! 正在执行自动化任务...")
                # 更新配置文件中的check_code/Update the check_code in the config file
                update_config_with_detected_code("config.txt", email_content)
                # 重新加载配置文件以获取更新后的check_code/Reload the config file to get the updated check_code
                config = load_config("config.txt")
                updated_check_code = config["check_code"]
                notify_discord(f"检测到Waitlist更新! 正在添加课程{updated_check_code}")
                subprocess.run(["python", "loginv8.py"])
                # 检测到相关邮件后，退出检测循环/Exit the detection loop after detecting the relevant email
                return

        # 等待 (1秒) 再次检查/Wait (1 second) before checking again
        time.sleep(1)

if __name__ == "__main__":
    main()

