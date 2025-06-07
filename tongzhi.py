# tongzhi.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
from email_config import SMTP_CONFIG, EMAIL_TEMPLATES, is_email_configured

def send_email(receiver_email, subject, message_html):
    """
    发送邮件。
    :param receiver_email: 收件人邮箱地址
    :param subject: 邮件主题
    :param message_html: HTML格式的邮件内容
    :return: True 如果发送成功, False 如果失败
    """
    if not is_email_configured():
        print("错误: SMTP配置不完整。请在 email_config.py 中正确配置SMTP服务器信息。")
        return False

    config = SMTP_CONFIG
    msg = MIMEText(message_html, 'html', 'utf-8')
    msg['From'] = config['sender_email']
    msg['To'] = receiver_email
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        print(f"尝试连接到SMTP服务器: {config['server']}:{config['port']}")
        
        if config['use_tls']:
            server = smtplib.SMTP(config['server'], config['port'], timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
        
        print("尝试登录SMTP服务器...")
        server.login(config['username'], config['password'])
        print("SMTP登录成功。正在发送邮件...")
        server.sendmail(config['sender_email'], [receiver_email], msg.as_string())
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

def send_conference_reminder(receiver_email, conference_info, reminder_type, days_left):
    """
    发送会议提醒邮件
    :param receiver_email: 收件人邮箱
    :param conference_info: 会议信息字典
    :param reminder_type: 提醒类型 ('submission_reminder', 'notification_reminder', 'camera_ready_reminder')
    :param days_left: 距离截止日期的天数
    :return: True 如果发送成功, False 如果失败
    """
    if not is_email_configured():
        print("错误: 邮件配置未完成，无法发送提醒邮件。")
        return False
    
    if reminder_type not in EMAIL_TEMPLATES:
        print(f"错误: 未知的提醒类型: {reminder_type}")
        return False
    
    template = EMAIL_TEMPLATES[reminder_type]
    
    # 准备邮件内容变量
    conference_name = f"{conference_info.get('acronym', 'N/A')} - {conference_info.get('full_name', 'Unknown Conference')}"
    location = conference_info.get('location', '未知地点')
    conference_date = conference_info.get('when', '未知时间')
    
    # 获取相关日期
    deadlines = conference_info.get('extracted_deadlines', {})
    submission_deadline = deadlines.get('submission_deadline', {}).get('date_str', '未知')
    notification_date = deadlines.get('notification_date', {}).get('date_str', '未知')
    camera_ready_deadline = deadlines.get('camera_ready', {}).get('date_str', '未知')
    
    # 格式化邮件内容
    subject = template['subject'].format(
        conference_name=conference_name
    )
    
    message_html = template['template'].format(
        conference_name=conference_name,
        submission_deadline=submission_deadline,
        notification_date=notification_date,
        camera_ready_deadline=camera_ready_deadline,
        conference_date=conference_date,
        location=location,
        days_left=days_left
    )
    
    return send_email(receiver_email, subject, message_html)

def send_submission_reminder(receiver_email, conference_info, days_left):
    """发送投稿截止提醒"""
    return send_conference_reminder(receiver_email, conference_info, 'submission_reminder', days_left)

def send_notification_reminder(receiver_email, conference_info, days_left):
    """发送通知时间提醒"""
    return send_conference_reminder(receiver_email, conference_info, 'notification_reminder', days_left)

def send_camera_ready_reminder(receiver_email, conference_info, days_left):
    """发送终稿提交提醒"""
    return send_conference_reminder(receiver_email, conference_info, 'camera_ready_reminder', days_left)

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