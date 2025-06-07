# main.py
import tkinter as tk
from gui import ConferenceReminderApp # 修正导入的类名
from data import load_conference_data, load_user_preferences, save_user_preferences
from logic import update_conference_data, get_reminders_for_user, mark_reminder_sent, parse_and_store_deadlines
from pachong import fetch_conferences
from tongzhi import send_email, format_reminder_email
from scheduler import main_scheduler # 导入调度器主函数
import threading # 导入threading模块

if __name__ == "__main__":
    # 加载初始数据
    load_user_preferences()

    # 启动GUI
    root = tk.Tk()
    app = ConferenceReminderApp(root) # 使用正确的类名实例化应用
    
    # GUI初始化完成后，立即更新会议数据
    from scheduler import job_fetch_and_update_conferences
    job_fetch_and_update_conferences()
    
    # 数据更新完成后，刷新GUI显示
    app.refresh_list()
    
    # 在后台线程中启动调度器
    scheduler_thread = threading.Thread(target=main_scheduler, daemon=True)
    scheduler_thread.start()

    root.mainloop()
    print("GUI已关闭。")