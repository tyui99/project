# logic.py
import datetime
import re # re模块在extract_date_and_tz中被使用，如果该函数被移除或重构，可以考虑移除此导入
from data import conference_data_list, user_preferences, sent_reminders
from pachong import convert_to_beijing_time # pachong.py 现在有增强的 convert_to_beijing_time

def update_conference_data(new_data):
    """
    用爬取到的新数据更新全局会议列表。
    """
    global conference_data_list
    conference_data_list = new_data
    print(f"会议数据已更新，共有 {len(conference_data_list)} 条记录。")

def parse_and_store_deadlines(conference_list_from_pachong):
    """
    解析从 pachong.py 获取的会议列表中的 'extracted_deadlines',
    将其转换为北京时间并存储在 'parsed_deadlines' 字段中。
    :param conference_list_from_pachong: 从 pachong.py 的 fetch_conferences 返回的列表。
    :return: 更新了 'parsed_deadlines' 的会议列表。
    """
    updated_list = []
    for conf in conference_list_from_pachong:
        parsed_deadlines_for_conf = {}
        # conf['extracted_deadlines'] 的结构是: 
        # {'submission_deadline': {'date_str': '...', 'tz_str': '...'}, ...}
        if 'extracted_deadlines' in conf and isinstance(conf['extracted_deadlines'], dict):
            for deadline_type, details in conf['extracted_deadlines'].items():
                date_str = details.get('date_str')
                tz_str = details.get('tz_str') # Might be None if dateparser is to auto-detect
                
                if date_str:
                    beijing_dt = convert_to_beijing_time(date_str, tz_str)
                    if beijing_dt:
                        parsed_deadlines_for_conf[deadline_type] = beijing_dt
                    else:
                        print(f"警告: 无法转换会议 {conf.get('acronym', 'N/A')} 的截止日期 {deadline_type}: {date_str} (TZ: {tz_str})")
                else:
                    # 不显示缺少日期字符串的警告，因为很多会议确实没有摘要截止日期
                    # print(f"警告: 会议 {conf.get('acronym', 'N/A')} 的截止日期 {deadline_type} 缺少日期字符串.")
                    pass
        
        conf['parsed_deadlines'] = parsed_deadlines_for_conf
        updated_list.append(conf)
    return updated_list

def add_user(email):
    """
    添加新用户，使用默认偏好。
    """
    if email not in user_preferences:
        user_preferences[email] = {
            'user_email': email,
            'subscribed_conferences': [],
            'reminder_days_before': { 
                'submission_deadline': 7, 
                'abstract_deadline': 7,
                'notification_date': 3,
                'camera_ready': 5
                # 可以根据pachong.py中extract_deadline_details_from_text的类型扩展
            },
            'custom_reminder_days': False
        }
        print(f"用户 {email} 已添加。")
        return True
    else:
        print(f"用户 {email} 已存在。")
        return False

def subscribe_conference(email, conference_acronym):
    """
    用户订阅特定会议。
    """
    if email in user_preferences:
        if conference_acronym not in user_preferences[email]['subscribed_conferences']:
            if any(conf['acronym'] == conference_acronym for conf in conference_data_list):
                user_preferences[email]['subscribed_conferences'].append(conference_acronym)
                print(f"用户 {email} 已订阅会议 {conference_acronym}。")
            else:
                print(f"错误: 会议 {conference_acronym} 未找到。")
        else:
            print(f"用户 {email} 已订阅会议 {conference_acronym}。")
    else:
        print(f"错误: 用户 {email} 未找到。")

def unsubscribe_conference(email, conference_acronym):
    """
    用户取消订阅特定会议。
    """
    if email in user_preferences:
        if conference_acronym in user_preferences[email]['subscribed_conferences']:
            user_preferences[email]['subscribed_conferences'].remove(conference_acronym)
            print(f"用户 {email} 已取消订阅会议 {conference_acronym}。")
        else:
            print(f"用户 {email} 未订阅会议 {conference_acronym}。")
    else:
        print(f"错误: 用户 {email} 未找到。")

def set_reminder_days(email, deadline_type, days):
    """
    用户设置特定类型截止日期的提前提醒天数。
    """
    if email in user_preferences:
        if not user_preferences[email]['custom_reminder_days']:
            user_preferences[email]['custom_reminder_days'] = True
        user_preferences[email]['reminder_days_before'][deadline_type] = int(days)
        print(f"用户 {email} 的 {deadline_type} 提醒已设置为提前 {days} 天。")
    else:
        print(f"错误: 用户 {email} 未找到。")

def get_reminders_for_user(email):
    """
    为指定用户生成需要发送的提醒列表。
    """
    reminders_to_send = []
    if email not in user_preferences:
        return reminders_to_send

    user_prefs = user_preferences[email]
    # 获取当前的北京时间日期
    beijing_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    today_beijing_date = beijing_now.date()

    for conf_acronym in user_prefs['subscribed_conferences']:
        conference = next((c for c in conference_data_list if c.get('acronym') == conf_acronym), None)
        if not conference or not conference.get('parsed_deadlines'):
            continue

        for deadline_type, deadline_datetime_obj in conference['parsed_deadlines'].items():
            if not deadline_datetime_obj: 
                continue
            
            # deadline_datetime_obj 已经是北京时区的 datetime 对象
            deadline_date_beijing = deadline_datetime_obj.date()

            # 获取该类型截止日期的提醒天数，如果用户未特定设置，则从默认中获取，再没有则用通用默认值
            default_reminder_days_for_type = user_preferences[email]['reminder_days_before'].get(deadline_type, 7) 
            reminder_days = int(user_prefs['reminder_days_before'].get(deadline_type, default_reminder_days_for_type))
            
            reminder_trigger_date = deadline_date_beijing - datetime.timedelta(days=reminder_days)

            if reminder_trigger_date <= today_beijing_date <= deadline_date_beijing:
                reminder_key = (email, conf_acronym, deadline_type, deadline_date_beijing.strftime('%Y-%m-%d'))
                if reminder_key not in sent_reminders: 
                    days_to_deadline = (deadline_date_beijing - today_beijing_date).days
                    # 只在截止日期当天或之前提醒，并且剩余天数大于等于0
                    if days_to_deadline >= 0:
                        reminders_to_send.append({
                            'email': email,
                            'conference_name': conference.get('full_name', conf_acronym),
                            'conference_acronym': conf_acronym,
                            'deadline_type': deadline_type,
                            'deadline_date': deadline_date_beijing.strftime('%Y-%m-%d'),
                            'days_to_deadline': days_to_deadline
                        })
    return reminders_to_send

def mark_reminder_sent(email, conference_acronym, deadline_type, deadline_date_str):
    """
    标记提醒已发送。使用截止日期字符串确保唯一性，以防同一类型日期变动。
    """
    sent_reminders[(email, conference_acronym, deadline_type, deadline_date_str)] = datetime.datetime.now()

# 移除旧的 extract_date_and_tz 函数，因为它已被 pachong.py 中的新逻辑取代
# def extract_date_and_tz(raw_deadline_info): ... 

if __name__ == '__main__':
    # 模拟从 pachong.py 获取数据并更新
    # pachong.py 的 fetch_conferences 会返回包含 'extracted_deadlines' 的列表
    sample_crawled_data_from_pachong = [
        {
            'acronym': 'CVPR',
            'full_name': 'IEEE/CVF Conference on Computer Vision and Pattern Recognition',
            'rank': 'A',
            'url': 'http://cvpr2024.thecvf.com/',
            'deadlines_raw': 'Submission Deadline: Nov 15, 2024, 23:59 AoE\nNotification: Feb 28, 2025',
            'extracted_deadlines': { 
                'submission_deadline': {'date_str': 'Nov 15, 2024, 23:59', 'tz_str': 'AoE'},
                'notification_date': {'date_str': 'Feb 28, 2025', 'tz_str': None}, # 假设无时区，dateparser会尝试处理
            }
        },
        {
            'acronym': 'ICML',
            'full_name': 'International Conference on Machine Learning',
            'rank': 'A',
            'url': 'https://icml.cc/',
            'deadlines_raw': 'Paper Submission: January 20, 2025 17:00 PST',
            'extracted_deadlines': {
                'submission_deadline': {'date_str': 'January 20, 2025 17:00', 'tz_str': 'PST'},
            }
        }
    ]

    # 1. 解析和存储截止日期 (将 'extracted_deadlines' 转换为 'parsed_deadlines')
    processed_conferences = parse_and_store_deadlines(sample_crawled_data_from_pachong)
    update_conference_data(processed_conferences)

    print("\n--- 更新后的会议数据 (包含 parsed_deadlines) ---")
    for conf in conference_data_list:
        print(f"  会议: {conf['acronym']}")
        if conf.get('parsed_deadlines'):
            for dtype, dt_obj in conf['parsed_deadlines'].items():
                print(f"    {dtype}: {dt_obj.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        else:
            print("    无解析的截止日期。")
    print("-" * 20)

    # 2. 测试用户和订阅功能
    add_user('user1@example.com')
    add_user('user2@example.com')

    subscribe_conference('user1@example.com', 'CVPR')
    subscribe_conference('user1@example.com', 'ICML')
    subscribe_conference('user2@example.com', 'CVPR')

    print("\n--- 用户偏好 ---")
    print(user_preferences)

    # 3. 测试设置提醒时间
    set_reminder_days('user1@example.com', 'submission_deadline', 5) 
    set_reminder_days('user1@example.com', 'notification_date', 2)

    print("\n--- 更新后的用户 user1@example.com 偏好 ---")
    print(user_preferences['user1@example.com'])

    # 4. 测试获取提醒
    # 手动调整一个会议的截止日期为近期以触发提醒
    # 确保 CVPR 的 submission_deadline 是几天后
    cvpr_conf = next((c for c in conference_data_list if c['acronym'] == 'CVPR'), None)
    if cvpr_conf and cvpr_conf['parsed_deadlines'].get('submission_deadline'):
        user1_prefs = user_preferences['user1@example.com']
        reminder_setting_days = user1_prefs['reminder_days_before'].get('submission_deadline', 7)
        
        # 设置截止日期为 reminder_setting_days - 1 天之后 (即今天会触发提醒)
        # 或直接设置为几天后，确保在提醒窗口内
        future_deadline_offset = reminder_setting_days - 1 
        if future_deadline_offset < 0: future_deadline_offset = 1 # 确保是未来

        # 获取当前的北京时区
        beijing_tz = datetime.timezone(datetime.timedelta(hours=8))
        new_deadline_dt = datetime.datetime.now(beijing_tz) + datetime.timedelta(days=future_deadline_offset)
        # 保留原始时间部分，或设置为一天结束
        original_time = cvpr_conf['parsed_deadlines']['submission_deadline'].time()
        new_deadline_dt = new_deadline_dt.replace(hour=original_time.hour, minute=original_time.minute, second=original_time.second, microsecond=original_time.microsecond)
        
        cvpr_conf['parsed_deadlines']['submission_deadline'] = new_deadline_dt
        print(f"\n调整CVPR投稿截止日期为: {cvpr_conf['parsed_deadlines']['submission_deadline'].strftime('%Y-%m-%d %H:%M:%S %Z%z')} 以便测试提醒")
    
    reminders1 = get_reminders_for_user('user1@example.com')
    print("\n--- 给 user1@example.com 的提醒 ---")
    if reminders1:
        for r in reminders1:
            print(f"  - 会议: {r['conference_name']} ({r['conference_acronym']}), 类型: {r['deadline_type']}, 截止: {r['deadline_date']}, {r['days_to_deadline']} 天后")
            mark_reminder_sent(r['email'], r['conference_acronym'], r['deadline_type'], r['deadline_date'])
    else:
        print("  无提醒。")

    reminders1_again = get_reminders_for_user('user1@example.com')
    print("\n--- 再次给 user1@example.com 的提醒 (应为空) ---")
    if not reminders1_again:
        print("  无新提醒，符合预期。")
    else:
        print("  错误，不应有新提醒。", reminders1_again)

    print("\n--- 已发送提醒记录 ---")
    print(sent_reminders)
    print("\nLogic module test completed.")