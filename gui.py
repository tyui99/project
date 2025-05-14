# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime

# 从其他模块导入必要的函数和数据
# 为了GUI的独立性，实际项目中这些交互会更复杂，可能通过一个控制器或API层
# 这里我们先假设可以直接访问或通过占位符函数模拟
try:
    from logic import (
        add_user, subscribe_conference, unsubscribe_conference, 
        set_reminder_days, user_preferences, conference_data_list,
        get_reminders_for_user # Potentially for displaying upcoming reminders
    )
    from data import save_user_preferences, load_user_preferences, load_conference_data
    # 假设有一个函数可以触发一次性的爬虫和数据更新
    from scheduler import job_fetch_and_update_conferences 
except ImportError:
    print("GUI: Failed to import from logic, data, or scheduler. Using placeholders.")
    # Placeholder functions if other modules are not ready
    user_preferences = {}
    conference_data_list = []
    def add_user(email): print(f"[GUI-Placeholder] Add user: {email}")
    def subscribe_conference(email, conf): print(f"[GUI-Placeholder] Subscribe {email} to {conf}")
    def unsubscribe_conference(email, conf): print(f"[GUI-Placeholder] Unsubscribe {email} from {conf}")
    def set_reminder_days(email, dtype, days): print(f"[GUI-Placeholder] Set {dtype} reminder for {email} to {days} days")
    def save_user_preferences(data): print("[GUI-Placeholder] Save user prefs")
    def load_user_preferences(): print("[GUI-Placeholder] Load user prefs")
    def load_conference_data(): print("[GUI-Placeholder] Load conf data")
    def job_fetch_and_update_conferences(): print("[GUI-Placeholder] Fetch conferences")
    def get_reminders_for_user(email): return []

class ConferenceReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("论文投稿提醒系统")
        self.root.geometry("800x600")

        self.current_user_email = None

        # Load initial data
        load_conference_data() # Load available conferences
        load_user_preferences() # Load existing user settings

        self.create_widgets()
        self.populate_conference_list()

        # Prompt for user email on startup if not set
        self.login_user()

    def login_user(self):
        email = simpledialog.askstring("用户登录/注册", "请输入您的邮箱地址:", parent=self.root)
        if email:
            self.current_user_email = email
            if email not in user_preferences:
                add_user(email)
                save_user_preferences(user_preferences)
                messagebox.showinfo("新用户", f"欢迎您，{email}! 已为您创建新账户。", parent=self.root)
            else:
                messagebox.showinfo("欢迎回来", f"欢迎回来，{email}!", parent=self.root)
            self.root.title(f"论文投稿提醒系统 - 用户: {self.current_user_email}")
            self.load_user_settings()
        else:
            messagebox.showwarning("未登录", "未提供邮箱，部分功能将受限。", parent=self.root)
            self.root.title("论文投稿提醒系统 - 未登录")

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # User management button
        user_button = ttk.Button(main_frame, text="切换/注册用户", command=self.login_user)
        user_button.pack(pady=5, anchor='ne')

        # Refresh conference data button
        refresh_button = ttk.Button(main_frame, text="刷新会议数据 (执行爬虫)", command=self.refresh_data_manual)
        refresh_button.pack(pady=5, anchor='nw')

        # Conference List Section
        conf_frame = ttk.LabelFrame(main_frame, text="会议列表 (选择订阅)", padding="10")
        conf_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.conf_listbox = tk.Listbox(conf_frame, selectmode=tk.MULTIPLE, height=15)
        self.conf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conf_scrollbar = ttk.Scrollbar(conf_frame, orient=tk.VERTICAL, command=self.conf_listbox.yview)
        conf_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.conf_listbox.config(yscrollcommand=conf_scrollbar.set)

        subscribe_button = ttk.Button(conf_frame, text="订阅选中会议", command=self.subscribe_selected)
        subscribe_button.pack(pady=5)

        # User Settings Section
        settings_frame = ttk.LabelFrame(main_frame, text="用户提醒设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)

        ttk.Label(settings_frame, text="投稿截止提醒 (天数): ").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.submission_days_var = tk.StringVar(value="7")
        self.submission_days_entry = ttk.Entry(settings_frame, textvariable=self.submission_days_var, width=5)
        self.submission_days_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(settings_frame, text="录用通知提醒 (天数): ").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.notification_days_var = tk.StringVar(value="3")
        self.notification_days_entry = ttk.Entry(settings_frame, textvariable=self.notification_days_var, width=5)
        self.notification_days_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(settings_frame, text="最终版提交提醒 (天数): ").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.camera_ready_days_var = tk.StringVar(value="5")
        self.camera_ready_days_entry = ttk.Entry(settings_frame, textvariable=self.camera_ready_days_var, width=5)
        self.camera_ready_days_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        save_settings_button = ttk.Button(settings_frame, text="保存提醒天数设置", command=self.save_reminder_settings)
        save_settings_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Display subscribed conferences and allow unsubscription
        subscribed_frame = ttk.LabelFrame(main_frame, text="我订阅的会议", padding="10")
        subscribed_frame.pack(fill=tk.X, pady=10)
        self.subscribed_listbox = tk.Listbox(subscribed_frame, height=5)
        self.subscribed_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        unsubscribe_button = ttk.Button(subscribed_frame, text="取消订阅选中", command=self.unsubscribe_selected_conf)
        unsubscribe_button.pack(side=tk.LEFT, padx=5)

    def refresh_data_manual(self):
        if messagebox.askyesno("确认", "这将执行网络爬虫并更新会议数据，可能需要一些时间。是否继续？", parent=self.root):
            try:
                job_fetch_and_update_conferences() # This is from scheduler
                load_conference_data() # Reload data into the global var if needed
                self.populate_conference_list()
                messagebox.showinfo("成功", "会议数据已刷新。", parent=self.root)
            except Exception as e:
                messagebox.showerror("错误", f"刷新会议数据失败: {e}", parent=self.root)

    def populate_conference_list(self):
        self.conf_listbox.delete(0, tk.END)
        if not conference_data_list:
            self.conf_listbox.insert(tk.END, "暂无会议数据，请尝试刷新。")
            return
        
        for conf in conference_data_list:
            # Display format: Acronym - Full Name (Rank)
            display_text = f"{conf.get('acronym', 'N/A')} - {conf.get('full_name', 'Unknown Conference')} (Rank: {conf.get('rank', 'N/A')})"
            self.conf_listbox.insert(tk.END, display_text)

    def load_user_settings(self):
        if self.current_user_email and self.current_user_email in user_preferences:
            prefs = user_preferences[self.current_user_email]
            self.submission_days_var.set(str(prefs['reminder_days_before'].get('submission_deadline', 7)))
            self.notification_days_var.set(str(prefs['reminder_days_before'].get('notification_date', 3)))
            self.camera_ready_days_var.set(str(prefs['reminder_days_before'].get('camera_ready', 5)))
            self.update_subscribed_listbox()
        else:
            # Reset to defaults if no user or no prefs
            self.submission_days_var.set("7")
            self.notification_days_var.set("3")
            self.camera_ready_days_var.set("5")
            self.update_subscribed_listbox() # Clears the list

    def update_subscribed_listbox(self):
        self.subscribed_listbox.delete(0, tk.END)
        if self.current_user_email and self.current_user_email in user_preferences:
            user_subs = user_preferences[self.current_user_email].get('subscribed_conferences', [])
            for conf_acronym in user_subs:
                # Find full name for display
                conf_detail = next((c for c in conference_data_list if c.get('acronym') == conf_acronym), None)
                display_name = conf_acronym
                if conf_detail:
                    display_name = f"{conf_acronym} - {conf_detail.get('full_name', '')}"
                self.subscribed_listbox.insert(tk.END, display_name)

    def subscribe_selected(self):
        if not self.current_user_email:
            messagebox.showwarning("未登录", "请先登录/注册用户。", parent=self.root)
            return
        
        selected_indices = self.conf_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选择", "请先从列表中选择要订阅的会议。", parent=self.root)
            return

        subscribed_count = 0
        for i in selected_indices:
            # We stored "Acronym - Full Name (Rank)", need to extract Acronym
            list_item_text = self.conf_listbox.get(i)
            conf_acronym = list_item_text.split(' - ')[0]
            if conf_acronym and conf_acronym != 'N/A':
                subscribe_conference(self.current_user_email, conf_acronym)
                subscribed_count += 1
        
        if subscribed_count > 0:
            save_user_preferences(user_preferences)
            messagebox.showinfo("订阅成功", f"成功订阅 {subscribed_count} 个会议。", parent=self.root)
            self.update_subscribed_listbox()
        else:
            messagebox.showwarning("订阅失败", "未能订阅任何会议，请检查会议数据。", parent=self.root)

    def unsubscribe_selected_conf(self):
        if not self.current_user_email:
            messagebox.showwarning("未登录", "请先登录/注册用户。", parent=self.root)
            return

        selected_indices = self.subscribed_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("未选择", "请先从'我订阅的会议'列表中选择要取消订阅的会议。", parent=self.root)
            return

        unsubscribed_count = 0
        for i in selected_indices:
            list_item_text = self.subscribed_listbox.get(i)
            conf_acronym = list_item_text.split(' - ')[0]
            if conf_acronym:
                unsubscribe_conference(self.current_user_email, conf_acronym)
                unsubscribed_count +=1
        
        if unsubscribed_count > 0:
            save_user_preferences(user_preferences)
            messagebox.showinfo("取消订阅成功", f"成功取消订阅 {unsubscribed_count} 个会议。", parent=self.root)
            self.update_subscribed_listbox()

    def save_reminder_settings(self):
        if not self.current_user_email:
            messagebox.showwarning("未登录", "请先登录/注册用户。", parent=self.root)
            return
        try:
            sub_days = int(self.submission_days_var.get())
            notif_days = int(self.notification_days_var.get())
            cam_days = int(self.camera_ready_days_var.get())

            set_reminder_days(self.current_user_email, 'submission_deadline', sub_days)
            set_reminder_days(self.current_user_email, 'notification_date', notif_days)
            set_reminder_days(self.current_user_email, 'camera_ready', cam_days)
            
            save_user_preferences(user_preferences)
            messagebox.showinfo("设置已保存", "提醒天数设置已成功保存。", parent=self.root)
        except ValueError:
            messagebox.showerror("输入错误", "提醒天数必须是有效的整数。", parent=self.root)
        except Exception as e:
            messagebox.showerror("保存失败", f"保存设置失败: {e}", parent=self.root)

if __name__ == '__main__':
    # Example data for GUI testing if run standalone
    # In a real scenario, data.py and logic.py would provide this.
    if not conference_data_list: # If imports failed or data is empty
        print("GUI standalone: Populating sample conference data for testing.")
        conference_data_list.extend([
            {'acronym': 'TESTCONF1', 'full_name': 'Test Conference Alpha', 'rank': 'A', 'parsed_deadlines': {}},
            {'acronym': 'TESTCONF2', 'full_name': 'Test Conference Beta', 'rank': 'B', 'parsed_deadlines': {}},
            {'acronym': 'IEEEFAKE', 'full_name': 'IEEE Fake Conference on AI', 'rank': 'A*', 'parsed_deadlines': {}}
        ])
    
    # Ensure there's a dummy user preference for testing if logic.py didn't load
    if 'testgui@example.com' not in user_preferences:
        user_preferences['testgui@example.com'] = {
            'user_email': 'testgui@example.com',
            'subscribed_conferences': ['TESTCONF1'],
            'reminder_days_before': { 
                'submission_deadline': 7, 
                'notification_date': 3,
                'camera_ready': 5
            },
            'custom_reminder_days': False
        }

    root = tk.Tk()
    app = ConferenceReminderApp(root)
    root.mainloop()