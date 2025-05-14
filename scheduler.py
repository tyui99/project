# scheduler.py
import schedule
import time
import datetime
from logic import get_reminders_for_user, mark_reminder_sent, update_conference_data, parse_and_store_deadlines
from tongzhi import send_email, format_reminder_email
from pachong import fetch_conferences
from data import load_conference_data, save_conference_data, load_user_preferences, save_user_preferences, conference_data_list, user_preferences

# 全局变量，用于存储上一次成功爬取的时间
last_successful_fetch_time = None
FETCH_INTERVAL_HOURS = 24 # 每24小时爬取一次

def job_fetch_and_update_conferences():
    """
    定时任务：爬取最新的会议信息并更新。
    """
    global last_successful_fetch_time
    print(f"[{datetime.datetime.now()}] 开始执行会议信息爬取和更新任务...")
    try:
        categories_to_fetch = ["人工智能"] # 可以扩展到其他类别
        all_new_conferences = []
        for category in categories_to_fetch:
            print(f"  正在爬取类别: {category}")
            new_conf_data = fetch_conferences(category)
            if new_conf_data:
                all_new_conferences.extend(new_conf_data)
            else:
                print(f"  未能从类别 '{category}' 爬取到数据。")
        
        if all_new_conferences:
            print(f"爬取完成，共获得 {len(all_new_conferences)} 条原始会议数据。开始处理和更新...")
            
            # pachong.py的fetch_conferences返回的列表包含'extracted_deadlines'。
            # logic.py的parse_and_store_deadlines会处理这个列表，
            # 将提取的日期转换为北京时间，并存入每个会议的'parsed_deadlines'字段。
            updated_conferences = parse_and_store_deadlines(all_new_conferences) # from logic.py
            
            update_conference_data(updated_conferences) # from logic.py, updates data.conference_data_list
            save_conference_data(conference_data_list) # from data.py, placeholder for saving
            print(f"会议数据已成功更新并保存。共有 {len(conference_data_list)} 条有效会议记录。")
            last_successful_fetch_time = datetime.datetime.now()
        else:
            print("未能从任何类别爬取到新的会议数据。")

    except Exception as e:
        print(f"错误: 执行会议信息爬取和更新任务失败: {e}")

def job_send_reminders():
    """
    定时任务：检查并发送邮件提醒。
    """
    print(f"[{datetime.datetime.now()}] 开始执行邮件提醒检查任务...")
    if not conference_data_list:
        print("  会议数据为空，跳过提醒。请先运行爬虫任务。")
        return
    if not user_preferences:
        print("  用户偏好为空，没有用户需要提醒。")
        return

    reminders_sent_count = 0
    for email in list(user_preferences.keys()): # Use list to avoid issues if dict changes during iteration (though not expected here)
        user_reminders = get_reminders_for_user(email) # logic.py 函数
        if user_reminders:
            print(f"  为用户 {email} 找到 {len(user_reminders)} 条提醒。")
            for reminder in user_reminders:
                subject, message_html = format_reminder_email(reminder) # tongzhi.py 函数
                if send_email(email, subject, message_html): # tongzhi.py 函数
                    # Corrected call to mark_reminder_sent
                    mark_reminder_sent(email, reminder['conference_acronym'], reminder['deadline_type'], reminder['deadline_date'])
                    reminders_sent_count += 1
                else:
                    print(f"    发送给 {email} 关于 {reminder['conference_acronym']} 的提醒失败。")
    
    if reminders_sent_count > 0:
        print(f"邮件提醒检查任务完成，共发送 {reminders_sent_count} 封提醒邮件。")
        # sent_reminders is a global in data.py; if it needs persistence, 
        # data.py should have save/load for it, and it should be called here.
        # save_user_preferences(user_preferences) # Only save if user_preferences itself changed.
    else:
        print("邮件提醒检查任务完成，没有需要发送的提醒。")

def main_scheduler():
    print("初始化调度器...")
    load_conference_data()
    load_user_preferences()

    run_initial_fetch = True
    if last_successful_fetch_time:
        if datetime.datetime.now() - last_successful_fetch_time < datetime.timedelta(hours=FETCH_INTERVAL_HOURS):
            run_initial_fetch = False
            print("最近已成功爬取过数据，跳过首次立即执行。")
    
    if not conference_data_list or run_initial_fetch:
        print("首次运行或数据陈旧，立即执行一次会议信息爬取...")
        job_fetch_and_update_conferences()
    else:
        print(f"现有 {len(conference_data_list)} 条会议数据。")

    schedule.every(FETCH_INTERVAL_HOURS).hours.do(job_fetch_and_update_conferences)
    print(f"已设置定时任务：每 {FETCH_INTERVAL_HOURS} 小时爬取和更新会议信息。")

    schedule.every().day.at("08:00").do(job_send_reminders)
    schedule.every().day.at("14:00").do(job_send_reminders)
    print("已设置定时任务：每天 08:00 和 14:00 检查并发送邮件提醒。")

    print("\n调度器已启动，等待任务执行...")
    print("按 Ctrl+C 退出程序。")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    if not user_preferences:
        print("scheduler.py: 模拟添加测试用户，实际应由 data.py 加载或 GUI 添加")
        # from logic import add_user, subscribe_conference, set_reminder_days # Avoid re-import if possible
        # test_email = 'your_test_email@example.com' # 替换为你的测试邮箱
        # if add_user(test_email): # add_user is from logic, ensure it's available or handle import
        #     save_user_preferences(user_preferences) # Save after modification
        #     print(f"模拟用户 {test_email} 已添加。请确保 tongzhi.py 配置正确以便接收邮件。")
        #     print("注意：订阅会议和设置提醒天数需要会议数据已加载。首次运行时，爬虫会先执行。")
        pass # Placeholder for test user setup if needed, ensure imports are correct

    main_scheduler()