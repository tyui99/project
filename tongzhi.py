# tongzhi.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# SMTP 服务器配置 (用户需要根据自己的邮箱服务商修改这些设置)
# 警告：请勿将密码硬编码到代码中。实际应用中应使用更安全的方式管理凭据，
# 例如环境变量、配置文件或GUI输入。
SMTP_SERVER = 'smtp.example.com'  # 例如：'smtp.qq.com', 'smtp.gmail.com'
SMTP_PORT = 587  # TLS常用端口，或者 465 (SSL)
SMTP_USERNAME = 'your_email@example.com' # 您的发件邮箱
SMTP_PASSWORD = 'your_email_password'    # 您的邮箱密码或授权码
SENDER_EMAIL = 'your_email@example.com'  # 发件人邮箱地址

def send_email(receiver_email, subject, message_html):
    """
    发送邮件。
    :param receiver_email: 收件人邮箱地址
    :param subject: 邮件主题
    :param message_html: HTML格式的邮件内容
    :return: True 如果发送成功, False 如果失败
    """
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]) or SMTP_SERVER == 'smtp.example.com':
        print("错误: SMTP配置不完整或使用的是示例配置。请在 tongzhi.py 中正确配置SMTP服务器信息。")
        return False

    msg = MIMEText(message_html, 'html', 'utf-8')
    msg['From'] = Header(f"会议提醒助手 <{SENDER_EMAIL}>", 'utf-8')
    msg['To'] = Header(receiver_email, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        print(f"尝试连接到SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        
        print("尝试登录SMTP服务器...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("SMTP登录成功。正在发送邮件...")
        server.sendmail(SENDER_EMAIL, [receiver_email], msg.as_string())
        server.quit()
        print(f"邮件已成功发送给 {receiver_email}，主题: {subject}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP认证失败: {e}. 请检查用户名和密码/授权码。")
    except smtplib.SMTPServerDisconnected as e:
        print(f"SMTP服务器意外断开连接: {e}")
    except smtplib.SMTPConnectError as e:
        print(f"无法连接到SMTP服务器 {SMTP_SERVER}:{SMTP_PORT} : {e}")
    except smtplib.SMTPException as e:
        print(f"发送邮件时发生SMTP错误: {e}")
    except Exception as e:
        print(f"发送邮件给 {receiver_email} 失败: {e}")
    return False

def format_reminder_email(reminder_details):
    """
    格式化提醒邮件的主题和内容。
    :param reminder_details: 包含提醒信息的字典
    :return: (subject, message_html) 元组
    """
    conf_name = reminder_details.get('conference_name', reminder_details.get('conference_acronym', 'N/A'))
    deadline_type_str = reminder_details.get('deadline_type', '未知类型').replace('_', ' ').title()
    deadline_date = reminder_details.get('deadline_date', 'N/A')
    days_left = reminder_details.get('days_to_deadline')

    subject = f"会议提醒: {conf_name} - {deadline_type_str} 即将截止"

    if days_left == 0:
        time_left_str = "就是今天！"
    elif days_left == 1:
        time_left_str = "仅剩 1 天！"
    else:
        time_left_str = f"还有 {days_left} 天。"

    message_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }}
            h2 {{ color: #0056b3; }}
            p {{ line-height: 1.6; }}
            strong {{ color: #d9534f; }}
            .footer {{ font-size: 0.9em; color: #777; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>会议截止日期提醒</h2>
            <p>您好！</p>
            <p>这是一个关于会议 <strong>{conf_name}</strong> 的提醒：</p>
            <ul>
                <li>截止类型：<strong>{deadline_type_str}</strong></li>
                <li>截止日期：<strong>{deadline_date}</strong> (北京时间)</li>
                <li>剩余时间：<strong>{time_left_str}</strong></li>
            </ul>
            <p>请及时处理相关事宜。</p>
            <p class="footer">此邮件由Python论文投稿定时提醒系统自动发送。</p>
        </div>
    </body>
    </html>
    """
    return subject, message_html

if __name__ == '__main__':
    print("测试邮件发送功能...")
    print("重要: 请务必在 tongzhi.py 文件顶部修改 SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL 为您的真实邮箱配置。")
    
    test_receiver_email = input("请输入测试接收邮箱地址 (例如 your_receive_email@example.com): ").strip()
    if not test_receiver_email:
        print("未输入接收邮箱，测试取消。")
    else:
        sample_reminder = {
            'conference_name': '示例会议 (Test Conference)',
            'conference_acronym': 'TESTCONF24',
            'deadline_type': 'submission_deadline',
            'deadline_date': '2024-12-31',
            'days_to_deadline': 5
        }
        subject, message_html = format_reminder_email(sample_reminder)
        print(f"\n将发送以下测试邮件给 {test_receiver_email}:")
        print(f"主题: {subject}")

        confirm = input("是否确认发送测试邮件? (yes/no): ").strip().lower()
        if confirm == 'yes':
            if SMTP_SERVER == 'smtp.example.com' or not SMTP_USERNAME or not SMTP_PASSWORD:
                print("\n错误：无法发送测试邮件，因为 tongzhi.py 中的SMTP配置不正确或仍为示例值。")
                print("请打开 e:\\python大作业\\project\\tongzhi.py 文件并更新SMTP配置信息。")
            elif send_email(test_receiver_email, subject, message_html):
                print("\n测试邮件已尝试发送。请检查您的邮箱。")
            else:
                print("\n测试邮件发送失败。请检查控制台错误信息和SMTP配置。")
        else:
            print("测试邮件发送已取消。")