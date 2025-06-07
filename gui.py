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
        
        # Refresh list button (reload from file)
        refresh_list_button = ttk.Button(main_frame, text="刷新列表 (重新加载)", command=self.refresh_list)
        refresh_list_button.pack(pady=5, anchor='nw')
        
        # Email configuration status
        from email_config import get_config_status
        email_status_frame = ttk.Frame(main_frame)
        email_status_frame.pack(pady=5, anchor='nw')
        
        self.email_status_label = ttk.Label(email_status_frame, text=get_config_status())
        self.email_status_label.pack(side=tk.LEFT)
        
        config_button = ttk.Button(email_status_frame, text="配置邮件", command=self.show_email_config_info)
        config_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Time filter section
        filter_frame = ttk.LabelFrame(main_frame, text="时间筛选", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Date range selection
        date_range_frame = ttk.Frame(filter_frame)
        date_range_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_range_frame, text="会议时间范围:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_date_var = tk.StringVar(value="2024-01-01")
        self.end_date_var = tk.StringVar(value="2025-12-31")
        
        ttk.Label(date_range_frame, text="从:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_date_button = ttk.Button(date_range_frame, textvariable=self.start_date_var, 
                                          command=lambda: self.select_date('start'))
        self.start_date_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(date_range_frame, text="到:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_date_button = ttk.Button(date_range_frame, textvariable=self.end_date_var,
                                        command=lambda: self.select_date('end'))
        self.end_date_button.pack(side=tk.LEFT, padx=(0, 10))
        
        filter_button = ttk.Button(date_range_frame, text="应用筛选", command=self.apply_time_filter)
        filter_button.pack(side=tk.LEFT, padx=(10, 0))
        
        clear_filter_button = ttk.Button(date_range_frame, text="清除筛选", command=self.clear_time_filter)
        clear_filter_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Filter status
        self.filter_status_var = tk.StringVar(value="当前显示: 全部会议")
        self.filter_status_label = ttk.Label(filter_frame, textvariable=self.filter_status_var)
        self.filter_status_label.pack(pady=(5, 0))

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
        subscribed_frame = ttk.LabelFrame(main_frame, text="我订阅的会议 (双击查看详情)", padding="10")
        subscribed_frame.pack(fill=tk.X, pady=10)
        self.subscribed_listbox = tk.Listbox(subscribed_frame, height=5)
        self.subscribed_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.subscribed_listbox.bind("<Double-Button-1>", self.show_conference_details)
        unsubscribe_button = ttk.Button(subscribed_frame, text="取消订阅选中", command=self.unsubscribe_selected_conf)
        unsubscribe_button.pack(side=tk.LEFT, padx=5)
        
        # Test email button
        test_email_button = ttk.Button(subscribed_frame, text="测试邮件发送", command=self.test_email_sending)
        test_email_button.pack(side=tk.LEFT, padx=5)

    def refresh_data_manual(self):
        # Create a new top-level window for date range selection
        date_dialog = tk.Toplevel(self.root)
        date_dialog.title("选择通知日期筛选范围")
        date_dialog.geometry("350x250")

        tk.Label(date_dialog, text="按会议通知日期筛选", font=("Arial", 10, "bold")).pack(pady=5)
        tk.Label(date_dialog, text="开始日期 (YYYY-MM-DD):").pack(pady=5)
        start_date_entry = ttk.Entry(date_dialog)
        start_date_entry.pack(pady=5)
        start_date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d")) # Default to today

        tk.Label(date_dialog, text="结束日期 (YYYY-MM-DD):").pack(pady=5)
        end_date_entry = ttk.Entry(date_dialog)
        end_date_entry.pack(pady=5)
        # Default to one year from today
        end_date_entry.insert(0, (datetime.date.today() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"))

        def validate_dates():
            start_date_str = start_date_entry.get()
            end_date_str = end_date_entry.get()

            if not (start_date_str and end_date_str):
                messagebox.showwarning("输入错误", "开始日期和结束日期均不能为空。", parent=date_dialog)
                return None, None

            try:
                datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
                datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
                return start_date_str, end_date_str
            except ValueError:
                messagebox.showerror("日期格式错误", "日期格式应为 YYYY-MM-DD。", parent=date_dialog)
                return None, None

        def on_confirm_dates():
            start_date_str, end_date_str = validate_dates()
            if start_date_str and end_date_str:
                # 直接执行爬取，不再需要额外的确认步骤和重置对话框的逻辑
                execute_fetch(start_date_str, end_date_str)

        # reset_dialog 函数不再需要，因为确认步骤被移除了
        # def reset_dialog(confirm_frame):
        #     # 重新启用日期输入和确认按钮
        #     start_date_entry.configure(state='normal')
        #     end_date_entry.configure(state='normal')
        #     confirm_dates_button.configure(state='normal')
        #     # 销毁确认框架
        #     confirm_frame.destroy()

        def execute_fetch(start_date_str, end_date_str):
            date_dialog.destroy()
            if messagebox.askyesno("确认", f"将爬取会议数据并按通知日期筛选（{start_date_str} 到 {end_date_str}），可能需要一些时间。是否继续？", parent=self.root):
                try:
                    # Pass date range to the job function
                    job_fetch_and_update_conferences(start_date=start_date_str, end_date=end_date_str)
                    load_conference_data() # Reload data
                    self.populate_conference_list()
                    messagebox.showinfo("成功", "会议数据已刷新。", parent=self.root)
                except Exception as e:
                    messagebox.showerror("错误", f"刷新会议数据失败: {e}", parent=self.root)

        confirm_dates_button = ttk.Button(date_dialog, text="确认日期范围", command=on_confirm_dates)
        confirm_dates_button.pack(pady=10)

        date_dialog.transient(self.root) # Make it a transient window
        date_dialog.grab_set() # Modal
        self.root.wait_window(date_dialog) # Wait for it to close
    
    def select_date(self, date_type):
        """打开日期选择对话框"""
        import tkinter.simpledialog as simpledialog
        from datetime import datetime
        
        current_date = self.start_date_var.get() if date_type == 'start' else self.end_date_var.get()
        
        # 创建日期选择对话框
        date_dialog = tk.Toplevel(self.root)
        date_dialog.title(f"选择{'开始' if date_type == 'start' else '结束'}日期")
        date_dialog.geometry("300x200")
        date_dialog.transient(self.root)
        date_dialog.grab_set()
        
        # 居中显示
        date_dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        frame = ttk.Frame(date_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"请选择{'开始' if date_type == 'start' else '结束'}日期:").pack(pady=(0, 10))
        
        # 年份选择
        year_frame = ttk.Frame(frame)
        year_frame.pack(fill=tk.X, pady=5)
        ttk.Label(year_frame, text="年份:").pack(side=tk.LEFT)
        year_var = tk.StringVar(value=current_date.split('-')[0])
        year_combo = ttk.Combobox(year_frame, textvariable=year_var, values=[str(y) for y in range(2020, 2030)], width=8)
        year_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 月份选择
        month_frame = ttk.Frame(frame)
        month_frame.pack(fill=tk.X, pady=5)
        ttk.Label(month_frame, text="月份:").pack(side=tk.LEFT)
        month_var = tk.StringVar(value=current_date.split('-')[1])
        month_combo = ttk.Combobox(month_frame, textvariable=month_var, values=[f"{m:02d}" for m in range(1, 13)], width=8)
        month_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 日期选择
        day_frame = ttk.Frame(frame)
        day_frame.pack(fill=tk.X, pady=5)
        ttk.Label(day_frame, text="日期:").pack(side=tk.LEFT)
        day_var = tk.StringVar(value=current_date.split('-')[2])
        day_combo = ttk.Combobox(day_frame, textvariable=day_var, values=[f"{d:02d}" for d in range(1, 32)], width=8)
        day_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def confirm_date():
            selected_date = f"{year_var.get()}-{month_var.get()}-{day_var.get()}"
            if date_type == 'start':
                self.start_date_var.set(selected_date)
            else:
                self.end_date_var.set(selected_date)
            date_dialog.destroy()
        
        def cancel_date():
            date_dialog.destroy()
        
        ttk.Button(button_frame, text="确定", command=confirm_date).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=cancel_date).pack(side=tk.LEFT)
        
        self.root.wait_window(date_dialog)
    
    def apply_time_filter(self):
        """应用时间筛选"""
        self.populate_conference_list()
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        self.filter_status_var.set(f"当前显示: {start_date} 至 {end_date}")
    
    def clear_time_filter(self):
        """清除时间筛选"""
        self.start_date_var.set("2024-01-01")
        self.end_date_var.set("2025-12-31")
        self.populate_conference_list()
        self.filter_status_var.set("当前显示: 全部会议")

    def refresh_list(self):
        """重新加载会议数据并刷新列表显示"""
        try:
            load_conference_data()  # 重新从文件加载会议数据
            self.populate_conference_list()  # 刷新GUI中的会议列表
            messagebox.showinfo("成功", f"会议列表已刷新。当前共有 {len(conference_data_list)} 条会议记录。", parent=self.root)
        except Exception as e:
            messagebox.showerror("错误", f"刷新会议列表失败: {e}", parent=self.root)

    def populate_conference_list(self):
        self.conf_listbox.delete(0, tk.END)
        if not conference_data_list:
            self.conf_listbox.insert(tk.END, "暂无会议数据，请尝试刷新。")
            return
        
        # 获取筛选日期范围
        start_date_str = getattr(self, 'start_date_var', tk.StringVar(value="2024-01-01")).get()
        end_date_str = getattr(self, 'end_date_var', tk.StringVar(value="2025-12-31")).get()
        
        from datetime import datetime
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except:
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2025, 12, 31)
        
        # 筛选会议数据
        filtered_conferences = []
        for conf in conference_data_list:
            conf_date = self.parse_conference_date(conf.get('when', ''))
            if conf_date and start_date <= conf_date <= end_date:
                filtered_conferences.append(conf)
            elif not conf_date:  # 如果无法解析日期，也包含在内
                filtered_conferences.append(conf)
        
        # 按等级分组会议
        conferences_by_rank = {'A': [], 'B': [], 'C': [], '其他': []}
        
        for conf in filtered_conferences:
            rank = conf.get('rank', '(absent)')
            if rank == 'A':
                conferences_by_rank['A'].append(conf)
            elif rank == 'B':
                conferences_by_rank['B'].append(conf)
            elif rank == 'C':
                conferences_by_rank['C'].append(conf)
            else:
                conferences_by_rank['其他'].append(conf)
        
        # 按等级顺序显示
        for rank_category in ['A', 'B', 'C', '其他']:
            conferences = conferences_by_rank[rank_category]
            if conferences:
                # 添加分组标题
                self.conf_listbox.insert(tk.END, f"═══════ {rank_category}类会议 ({len(conferences)}个) ═══════")
                
                for conf in conferences:
                    # 基本信息行
                    acronym = conf.get('acronym', 'N/A')
                    full_name = conf.get('full_name', 'Unknown Conference')
                    location = conf.get('location', 'Unknown')
                    when = conf.get('when', 'Unknown')
                    
                    basic_info = f"📋 {acronym} - {full_name}"
                    self.conf_listbox.insert(tk.END, basic_info)
                    
                    # 会议时间和地点
                    time_location = f"   📅 时间: {when} | 📍 地点: {location}"
                    self.conf_listbox.insert(tk.END, time_location)
                    
                    # 关键时间节点 - 改进显示格式
                    deadlines = conf.get('extracted_deadlines', {})
                    if deadlines:
                        deadline_parts = []
                        
                        # 摘要截止时间
                        if deadlines.get('abstract_deadline', {}).get('date_str'):
                            abstract_date = self.format_deadline_date(deadlines['abstract_deadline']['date_str'])
                            deadline_parts.append(f"📝摘要截止: {abstract_date}")
                        
                        # 投稿截止时间
                        if deadlines.get('submission_deadline', {}).get('date_str'):
                            submission_date = self.format_deadline_date(deadlines['submission_deadline']['date_str'])
                            deadline_parts.append(f"📄论文截止: {submission_date}")
                        
                        # 通知时间
                        if deadlines.get('notification_date', {}).get('date_str'):
                            notification_date = self.format_deadline_date(deadlines['notification_date']['date_str'])
                            deadline_parts.append(f"📢录用通知: {notification_date}")
                        
                        # 相机就绪时间
                        if deadlines.get('camera_ready', {}).get('date_str'):
                            camera_ready_date = self.format_deadline_date(deadlines['camera_ready']['date_str'])
                            deadline_parts.append(f"📋终稿截止: {camera_ready_date}")
                        
                        if deadline_parts:
                            self.conf_listbox.insert(tk.END, "   ⏰ 重要时间节点:")
                            for part in deadline_parts:
                                self.conf_listbox.insert(tk.END, f"      {part}")
                        else:
                            self.conf_listbox.insert(tk.END, "   ⏰ 重要时间节点: 暂无详细信息")
                    else:
                        self.conf_listbox.insert(tk.END, "   ⏰ 重要时间节点: 暂无详细信息")
                    
                    # 添加空行分隔
                    self.conf_listbox.insert(tk.END, "")

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
        
        # 从选中的行中提取会议简称
        selected_conferences = []
        for index in selected_indices:
            line_text = self.conf_listbox.get(index)
            # 只处理会议基本信息行（以📋开头）
            if line_text.startswith("📋 "):
                # 提取会议简称："📋 acronym - full_name" -> "acronym"
                try:
                    acronym = line_text.split("📋 ")[1].split(" - ")[0]
                    if acronym not in selected_conferences:
                        selected_conferences.append(acronym)
                except:
                    continue
        
        if not selected_conferences:
            messagebox.showwarning("选择无效", "请选择会议名称行（以📋开头的行）进行订阅。", parent=self.root)
            return

        subscribed_count = 0
        for conf_acronym in selected_conferences:
            if conf_acronym and conf_acronym != 'N/A':
                subscribe_conference(self.current_user_email, conf_acronym)
                subscribed_count += 1
        
        if subscribed_count > 0:
            save_user_preferences(user_preferences)
            messagebox.showinfo("订阅成功", f"成功订阅 {subscribed_count} 个会议。", parent=self.root)
            self.update_subscribed_listbox()
        else:
            messagebox.showwarning("订阅失败", "未能订阅任何会议，请检查会议数据。", parent=self.root)
    
    def show_email_config_info(self):
        """显示邮件配置信息"""
        from email_config import is_email_configured, SMTP_CONFIG
        
        if is_email_configured():
            config_info = f"""当前邮件配置:
            
服务器: {SMTP_CONFIG['server']}
端口: {SMTP_CONFIG['port']}
用户名: {SMTP_CONFIG['username']}
发件人: {SMTP_CONFIG['sender_email']}
连接方式: {'TLS' if SMTP_CONFIG['use_tls'] else 'SSL'}
            
✅ 配置完整，可以发送邮件提醒"""
        else:
            config_info = """❌ 邮件配置未完成
            
请按以下步骤配置邮件功能：
            
1. 打开项目目录下的 email_config.py 文件
2. 在 SMTP_CONFIG 中填入您的邮箱信息：
   - server: SMTP服务器地址（如 smtp.qq.com）
   - port: 端口号（TLS用587，SSL用465）
   - username: 您的邮箱地址
   - password: 邮箱密码或授权码
   - sender_email: 发件人邮箱（通常与username相同）
3. 保存文件并重启程序
            
常见邮箱配置：
• QQ邮箱: smtp.qq.com, 端口587
• 163邮箱: smtp.163.com, 端口587
• Gmail: smtp.gmail.com, 端口587
• Outlook: smtp-mail.outlook.com, 端口587
            
注意：多数邮箱需要开启SMTP服务并使用授权码而非登录密码。"""
        
        messagebox.showinfo("邮件配置信息", config_info, parent=self.root)
        
        # 刷新状态显示
        from email_config import get_config_status
        self.email_status_label.config(text=get_config_status())
    
    def parse_conference_date(self, when_str):
        """解析会议时间字符串，返回datetime对象"""
        if not when_str or when_str == 'Unknown':
            return None
        
        from datetime import datetime
        import re
        
        # 尝试匹配各种日期格式
        patterns = [
            r'(\d{1,2})-(\d{1,2})\s+(\w+),?\s+(\d{4})',  # 22-27 May, 2020
            r'(\w+)\s+(\d{1,2})-(\d{1,2}),?\s+(\d{4})',  # May 22-27, 2020
            r'(\d{1,2})\s+(\w+),?\s+(\d{4})',  # 22 May, 2020
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # May 22, 2020
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2020-05-22
        ]
        
        month_map = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        try:
            # 模式1: 22-27 May, 2020
            match = re.search(patterns[0], when_str, re.IGNORECASE)
            if match:
                start_day, end_day, month_str, year = match.groups()
                month = month_map.get(month_str.lower())
                if month:
                    return datetime(int(year), month, int(start_day))
            
            # 模式2: May 22-27, 2020
            match = re.search(patterns[1], when_str, re.IGNORECASE)
            if match:
                month_str, start_day, end_day, year = match.groups()
                month = month_map.get(month_str.lower())
                if month:
                    return datetime(int(year), month, int(start_day))
            
            # 模式3: 22 May, 2020
            match = re.search(patterns[2], when_str, re.IGNORECASE)
            if match:
                day, month_str, year = match.groups()
                month = month_map.get(month_str.lower())
                if month:
                    return datetime(int(year), month, int(day))
            
            # 模式4: May 22, 2020
            match = re.search(patterns[3], when_str, re.IGNORECASE)
            if match:
                month_str, day, year = match.groups()
                month = month_map.get(month_str.lower())
                if month:
                    return datetime(int(year), month, int(day))
            
            # 模式5: 2020-05-22
            match = re.search(patterns[4], when_str)
            if match:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
        
        except (ValueError, TypeError):
            pass
        
        return None
    
    def format_deadline_date(self, date_str):
        """格式化截止日期显示"""
        if not date_str:
            return "未知"
        
        from datetime import datetime
        
        try:
            # 尝试解析日期
            if ' ' in date_str and ':' in date_str:
                # 格式: 2020-02-18 00:00:00
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                return date_obj.strftime("%Y年%m月%d日")
            elif '-' in date_str:
                # 格式: 2020-02-18
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%Y年%m月%d日")
            else:
                return date_str
        except (ValueError, TypeError):
             return date_str
    
    def show_conference_details(self, event):
        """显示选中会议的详细信息"""
        selection = self.subscribed_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.subscribed_listbox.get(selection[0])
        # 提取会议简称
        conf_acronym = selected_text.split(" - ")[0] if " - " in selected_text else selected_text
        
        # 查找会议详细信息
        conf_detail = None
        for conf in conference_data_list:
            if conf.get('acronym') == conf_acronym:
                conf_detail = conf
                break
        
        if not conf_detail:
            messagebox.showwarning("未找到", f"未找到会议 {conf_acronym} 的详细信息。", parent=self.root)
            return
        
        # 创建详情窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"会议详情 - {conf_acronym}")
        detail_window.geometry("600x500")
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        # 居中显示
        detail_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        # 创建滚动文本框
        frame = ttk.Frame(detail_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Arial', 10))
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充会议信息
        info_text = f"""📋 会议简称: {conf_detail.get('acronym', 'N/A')}
📝 会议全称: {conf_detail.get('full_name', 'N/A')}
🏆 会议等级: {conf_detail.get('rank', 'N/A')}
📅 会议时间: {conf_detail.get('when', 'N/A')}
📍 会议地点: {conf_detail.get('location', 'N/A')}
🌐 会议网站: {conf_detail.get('link', 'N/A')}

📋 重要时间节点:
"""
        
        deadlines = conf_detail.get('extracted_deadlines', {})
        if deadlines:
            if deadlines.get('abstract_deadline', {}).get('date_str'):
                abstract_date = self.format_deadline_date(deadlines['abstract_deadline']['date_str'])
                info_text += f"📝 摘要截止: {abstract_date}\n"
            
            if deadlines.get('submission_deadline', {}).get('date_str'):
                submission_date = self.format_deadline_date(deadlines['submission_deadline']['date_str'])
                info_text += f"📄 论文截止: {submission_date}\n"
            
            if deadlines.get('notification_date', {}).get('date_str'):
                notification_date = self.format_deadline_date(deadlines['notification_date']['date_str'])
                info_text += f"📢 录用通知: {notification_date}\n"
            
            if deadlines.get('camera_ready', {}).get('date_str'):
                camera_ready_date = self.format_deadline_date(deadlines['camera_ready']['date_str'])
                info_text += f"📋 终稿截止: {camera_ready_date}\n"
        else:
            info_text += "暂无详细时间信息\n"
        
        # 添加描述信息
        if conf_detail.get('description'):
            info_text += f"\n📖 会议描述:\n{conf_detail.get('description')}\n"
        
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)  # 只读
        
        # 关闭按钮
        close_button = ttk.Button(detail_window, text="关闭", command=detail_window.destroy)
        close_button.pack(pady=10)
    
    def test_email_sending(self):
        """测试邮件发送功能"""
        if not self.current_user_email:
            messagebox.showwarning("未登录", "请先登录用户。", parent=self.root)
            return
        
        from email_config import is_email_configured
        if not is_email_configured():
            messagebox.showwarning("邮件未配置", "请先配置邮件设置。点击'配置邮件'按钮查看配置说明。", parent=self.root)
            return
        
        # 检查是否有订阅的会议
        if self.current_user_email not in user_preferences or not user_preferences[self.current_user_email].get('subscribed_conferences'):
            messagebox.showwarning("无订阅会议", "请先订阅一些会议再测试邮件发送。", parent=self.root)
            return
        
        # 创建测试邮件发送窗口
        test_window = tk.Toplevel(self.root)
        test_window.title("测试邮件发送")
        test_window.geometry("400x300")
        test_window.transient(self.root)
        test_window.grab_set()
        
        # 居中显示
        test_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 150, self.root.winfo_rooty() + 150))
        
        frame = ttk.Frame(test_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="选择测试邮件类型:", font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # 获取第一个订阅的会议作为测试
        subscribed_confs = user_preferences[self.current_user_email].get('subscribed_conferences', [])
        if subscribed_confs:
            test_conf = subscribed_confs[0]
            conf_detail = next((c for c in conference_data_list if c.get('acronym') == test_conf), None)
            
            if conf_detail:
                ttk.Label(frame, text=f"测试会议: {test_conf} - {conf_detail.get('full_name', '')}").pack(pady=(0, 10))
                
                def send_test_submission():
                    try:
                        from tongzhi import send_submission_reminder
                        send_submission_reminder(self.current_user_email, conf_detail, 7)
                        messagebox.showinfo("发送成功", "投稿截止提醒邮件发送成功！", parent=test_window)
                    except Exception as e:
                        messagebox.showerror("发送失败", f"邮件发送失败: {str(e)}", parent=test_window)
                
                def send_test_notification():
                    try:
                        from tongzhi import send_notification_reminder
                        send_notification_reminder(self.current_user_email, conf_detail, 3)
                        messagebox.showinfo("发送成功", "录用通知提醒邮件发送成功！", parent=test_window)
                    except Exception as e:
                        messagebox.showerror("发送失败", f"邮件发送失败: {str(e)}", parent=test_window)
                
                def send_test_camera_ready():
                    try:
                        from tongzhi import send_camera_ready_reminder
                        send_camera_ready_reminder(self.current_user_email, conf_detail, 5)
                        messagebox.showinfo("发送成功", "终稿截止提醒邮件发送成功！", parent=test_window)
                    except Exception as e:
                        messagebox.showerror("发送失败", f"邮件发送失败: {str(e)}", parent=test_window)
                
                ttk.Button(frame, text="📄 测试投稿截止提醒", command=send_test_submission).pack(pady=5, fill=tk.X)
                ttk.Button(frame, text="📢 测试录用通知提醒", command=send_test_notification).pack(pady=5, fill=tk.X)
                ttk.Button(frame, text="📋 测试终稿截止提醒", command=send_test_camera_ready).pack(pady=5, fill=tk.X)
        
        ttk.Button(frame, text="关闭", command=test_window.destroy).pack(pady=(20, 0))

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