# main.py
import tkinter as tk
from gui import ConferenceReminderApp
from data import load_conference_data, load_user_preferences, load_sent_reminders

if __name__ == '__main__':
    # 在启动GUI之前，确保所有必要的数据都已从文件加载到内存中
    # data.py 在其模块级别加载这些数据，但为了明确，可以在此调用
    # 不过，由于 data.py 在导入时就会执行加载，这里的显式调用主要是为了可读性
    # 或在需要重新加载的场景下使用。
    # load_conference_data() # data.py 导入时已执行
    # load_user_preferences() # data.py 导入时已执行
    # load_sent_reminders() # data.py 导入时已执行

    print("正在启动论文投稿提醒系统 GUI...")
    root = tk.Tk()
    app = ConferenceReminderApp(root)
    root.mainloop()
    print("GUI已关闭。")