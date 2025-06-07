# Bug 报告与调试记录

本文档记录了开发和调试邮件提醒功能时遇到的主要问题、排查思路和代码调整。

## 1. 初始化与配置加载问题

### 1.1 `NameError: name 'get_conference_details' is not defined`

- **问题描述：** 程序启动就报错，提示 `NameError: name 'get_conference_details' is not defined`。
- **直接影响：** 程序无法启动。
- **排查过程：**
    1.  **分析错误：** `NameError` 说明 `get_conference_details` 这个函数在用它的时候，要么没定义，要么没导入。
    2.  **检查调用处：** 看了下 `gui.py`，发现是在 `load_conference_data` 方法里调用的 `get_conference_details(conf_path)`。
    3.  **确认函数位置：** `get_conference_details` 函数应该是在 `file_operations.py` 文件里。
    4.  **检查导入语句：** 发现 `gui.py` 确实忘了写 `from file_operations import get_conference_details`。
- **根本原因：** `gui.py` 调用了 `file_operations.py` 中的 `get_conference_details` 函数，但没有导入它。
- **代码调整：**
    - **文件：** `e:\py_kshe\project\gui.py`
    - **改动：** 在文件开头加上 `from file_operations import get_conference_details`。
    - **示例 (调整后)：**
      ```python
      from file_operations import load_conferences_from_file, save_user_preferences, load_user_preferences, get_conference_details
      # ...其他导入
      ```

### 1.2 `FileNotFoundError: [Errno 2] No such file or directory: 'user_preferences.json'`

- **问题描述：** `NameError` 解决后，程序启动又报新错：`FileNotFoundError: [Errno 2] No such file or directory: 'user_preferences.json'`。
- **直接影响：** 用户偏好设置加载不了，后续功能可能出问题。
- **排查过程：**
    1.  **分析错误：** `FileNotFoundError` 说明程序想读 `user_preferences.json`，但这个文件不存在。
    2.  **检查加载逻辑：** 看了 `file_operations.py` 里的 `load_user_preferences` 函数，它确实是去打开 `user_preferences.json`。
    3.  **检查创建逻辑：** `save_user_preferences` 函数会创建这个文件。`gui.py` 的 `load_user_preferences` 方法调用了 `file_operations.load_user_preferences`，如果文件不存在，它会创建个空的偏好设置再保存。
    4.  **定位问题：** 问题出在 `gui.py` 的 `__init__` 方法调用 `self.load_user_preferences()` 时。如果文件不存在，`file_operations.load_user_preferences()` 会返回一个空字典。但 `gui.py` 的 `load_user_preferences` 方法在捕获 `FileNotFoundError` 后，虽然创建了 `default_prefs`，却没有把它赋给 `self.user_preferences` *并且立即保存*。它得等其他地方调用 `save_user_preferences` 方法时才保存。
- **根本原因：** `gui.py` 的 `load_user_preferences` 方法在 `user_preferences.json` 首次不存在时，没能正确处理并立刻创建一个空的配置文件，导致后面依赖这个文件的操作都失败了。说得更准一点，`file_operations.load_user_preferences` 应该在文件不存在时返回一个默认的配置结构，`gui.py` 要确保用上这个默认结构，并且在合适的时候（比如第一次加载失败后）保存它。
- **代码调整：**
    - **文件：** `e:\py_kshe\project\file_operations.py`
    - **改动：** 修改 `load_user_preferences` 函数，让它在文件不存在时，返回一个带默认键（比如 `selected_conference_for_testing`）的字典，而不是只返回空字典。
    - **示例 (调整后 - file_operations.py)：**
      ```python
      def load_user_preferences(filename="user_preferences.json"):
          try:
              with open(filename, 'r', encoding='utf-8') as f:
                  return json.load(f)
          except FileNotFoundError:
              # 返回带默认键的结构，免得后面取不到值报错
              return {"selected_conference_for_testing": "", "window_size": "800x600", "theme": "default"} # 加了默认键
          except json.JSONDecodeError:
              return {"selected_conference_for_testing": "", "window_size": "800x600", "theme": "default"} # 处理空文件或无效JSON的情况
      ```
    - **文件：** `e:\py_kshe\project\gui.py`
    - **改动：** 确保 `load_user_preferences` 方法里，如果加载失败（比如文件不存在或内容坏了），会调用 `save_user_preferences` 来创建一个新的、有效的配置文件。
    - **示例 (调整后 - gui.py `load_user_preferences` 方法)：**
      ```python
      def load_user_preferences(self):
          self.user_preferences = load_user_preferences()
          # 如果加载的偏好不完整或为空，确保保存一次默认设置
          if not self.user_preferences or 'selected_conference_for_testing' not in self.user_preferences:
              self.user_preferences = {"selected_conference_for_testing": "", "window_size": "800x600", "theme": "default"}
              self.save_user_preferences() # 确保文件被创建
          # ... (后面更新GUI元素的代码)
      ```

### 1.3 `KeyError: 'selected_conference_for_testing'` 和 `AttributeError: 'NoneType' object has no attribute 'get'`

- **问题描述：** `FileNotFoundError` 处理后（创建了文件或用了默认配置），程序启动时可能出现 `KeyError: 'selected_conference_for_testing'`，或者后面操作时出现 `AttributeError: 'NoneType' object has no attribute 'get'`（如果 `conf_detail` 变成了 `None`）。
- **直接影响：** 测试邮件功能没法正常初始化或执行。
- **排查过程：**
    1.  **分析错误：** `KeyError` 说明想访问字典里一个不存在的键。`AttributeError` 通常是期望一个对象结果却拿到了 `None`。
    2.  **检查 `user_preferences` 加载：** 就像 1.2 里说的，如果 `user_preferences.json` 文件一开始是空的或者少了 `selected_conference_for_testing` 这个键，`self.user_preferences.get('selected_conference_for_testing')` 就会返回 `None` (如果用 `.get()`) 或者报 `KeyError` (如果用 `[]`)。
    3.  **追踪 `conf_detail`：** 在 `gui.py` 的 `send_test_submission` (以及类似的函数) 里，`test_conf_title = self.user_preferences.get('selected_conference_for_testing')`。如果 `test_conf_title` 是 `None` 或者空字符串，`conf_detail = next((conf for conf in self.conference_data_list if conf.get('title') == test_conf_title), None)` 就可能让 `conf_detail` 变成 `None`。
    4.  **后续影响：** 如果 `conf_detail` 是 `None`，后面再想用 `conf_detail.get(...)` 就会报 `AttributeError`。
- **根本原因：** `user_preferences.json` 文件在第一次创建或加载时，没保证 `selected_conference_for_testing` 这个键存在并且有效，导致后面依赖这个键的操作都失败了。
- **代码调整：** (已在 1.2 中覆盖)
    - 确保 `file_operations.py` 和 `gui.py` 里的 `load_user_preferences` 都能处理文件不存在或内容不完整的情况，并提供一个包含 `selected_conference_for_testing` 键的默认值。
    - 在 `gui.py` 中，用 `self.user_preferences.get('selected_conference_for_testing', "")` 来安全地获取值，并处理它为空字符串的情况，比如禁用测试按钮或提示用户选个会议。


## 2. 函数调用参数数量不对

### 2.1 “通知提醒”时参数数量不对 (初步发现与修复)

- **问题描述：** 程序在发“通知提醒”测试邮件时崩了，GUI弹窗报错，终端显示 `TypeError: send_notification_reminder() takes 3 positional arguments but 4 were given`。
- **影响范围：** `gui.py` 里的 `send_test_notification` 函数调用 `tongzhi.py` 里的 `send_notification_reminder` 函数时出问题。

- **排查过程：**
    1.  **定位函数定义：** 搜了一下 `send_notification_reminder` 函数的定义，确认它在 `tongzhi.py` 里。
    2.  **检查函数签名：** 看了 `tongzhi.py` 里 `send_notification_reminder` 的函数长什么样，确认它收三个参数：`receiver_email`, `conference_info`, `days_left`。
    3.  **检查函数调用：** 看了 `gui.py` 里 `send_test_notification` 函数是怎么调用 `send_notification_reminder` 的，发现它错误地传了四个参数 (`self.current_user_email`, `test_conf`, `conf_detail`, `3`)。

- **根本原因：** 在 `gui.py` 里调用 `tongzhi.py` 的 `send_notification_reminder` 函数时，不小心多传了一个 `conf_detail` 参数。

- **代码调整 (第一次修复)：**
    - **文件：** `e:\py_kshe\project\gui.py`
    - **改动：** 在 `send_test_notification` 函数里调用 `send_notification_reminder` 时，把多余的 `conf_detail` 参数删了。
    - **示例 (调整前)：**
      ```python
      # self.send_test_notification 函数内
      send_notification_reminder(self.current_user_email, test_conf, conf_detail, 3)
      ```
    - **示例 (调整后)：**
      ```python
      # self.send_test_notification 函数内
      send_notification_reminder(self.current_user_email, test_conf, 3)
      ```

### 2.2 其他提醒功能也存在参数数量不对的问题 (扩展修复)

- **问题描述：** `send_notification_reminder` 的调用修好后，检查了一下发现其他测试邮件功能（投稿提醒、最终版提醒）也可能有类似问题。
- **影响范围：** `gui.py` 里的 `send_test_submission` 和 `send_test_camera_ready` 函数分别调用 `tongzhi.py` 里的 `send_submission_reminder` 和 `send_camera_ready_reminder` 函数。

- **排查过程：**
    1.  **代码审查：** 主动看了 `gui.py` 里 `send_test_submission` 和 `send_test_camera_ready` 函数是怎么调用相应提醒函数的。
    2.  **确认问题：** 发现这两个函数调用也一样传错了四个参数，多了一个 `conf_detail`。
    3.  **参考函数签名：** 回顾了 `tongzhi.py` 里 `send_submission_reminder` 和 `send_camera_ready_reminder` 的函数签名（跟 `send_notification_reminder` 类似，都收三个参数）。

- **根本原因：** 跟 2.1 类似，在 `gui.py` 里调用 `tongzhi.py` 的 `send_submission_reminder` 和 `send_camera_ready_reminder` 函数时，也多传了一个 `conf_detail` 参数。

- **代码调整 (第二次修复)：**
    - **文件：** `e:\py_kshe\project\gui.py`
    - **改动：** 在 `send_test_submission` 函数里调用 `send_submission_reminder` 时，以及在 `send_test_camera_ready` 函数里调用 `send_camera_ready_reminder` 时，都把多余的 `conf_detail` 参数删了。
    - **示例 (调整前 - send_test_submission)：**
      ```python
      # self.send_test_submission 函数内
      send_submission_reminder(self.current_user_email, test_conf, conf_detail, 7)
      ```
    - **示例 (调整后 - send_test_submission)：**
      ```python
      # self.send_test_submission 函数内
      send_submission_reminder(self.current_user_email, test_conf, 7)
      ```

## 3. 属性错误：对字符串用了字典的 'get' 方法

- **问题描述：** 参数数量问题修好后，再测试发邮件，GUI弹窗报错：`邮件发送失败: 'str' object has no attribute 'get'`。
- **影响范围：** `gui.py` 里的 `send_test_submission`, `send_test_notification`, `send_test_camera_ready` 函数。

- **排查过程：**
    1.  **分析错误：** 这个错误是说代码想在一个字符串上用字典的 `get()` 方法，那肯定不行。
    2.  **检查参数传递：** 看了 `gui.py` 里测试邮件发送函数。发现传给 `tongzhi.py` 里邮件发送函数的第二个参数 `test_conf` 是个字符串（会议名），而不是期望的会议信息字典。
        ```python
        # gui.py 相关代码片段
        test_conf = self.user_preferences.get('selected_conference_for_testing')
        # ...
        conf_detail = next((conf for conf in self.conference_data_list if conf.get('title') == test_conf), None)
        # ...
        send_notification_reminder(self.current_user_email, test_conf, 3) # 这里的 test_conf 是字符串
        ```
    3.  **确认期望类型：** 看了 `tongzhi.py` 里的 `send_conference_reminder` 函数（其他提醒函数内部会调它或用类似逻辑），确认它的 `conference_info` 参数期望是个包含会议详细信息的字典，因为它会用 `conference_info.get('title')` 之类的方法。

- **根本原因：** 在 `gui.py` 的测试邮件发送函数里，错误地把会议名称字符串 (`test_conf`) 而不是包含会议完整信息的字典 (`conf_detail`) 传给了 `tongzhi.py` 里的邮件发送函数。

- **代码调整：**
    - **文件：** `e:\py_kshe\project\gui.py`
    - **改动：** 在 `send_test_submission`, `send_test_notification`, `send_test_camera_ready` 函数里，把传给 `tongzhi.py` 相应函数的第二个参数从 `test_conf` (字符串) 改成 `conf_detail` (字典)。
    - **示例 (调整前)：**
      ```python
      # self.send_test_notification 函数内
      send_notification_reminder(self.current_user_email, test_conf, 3)
      ```
    - **示例 (调整后)：**
      ```python
      # self.send_test_notification 函数内
      send_notification_reminder(self.current_user_email, conf_detail, 3)
      ```

## 4. SMTP 配置错误导致收不到邮件

- **问题描述：** 程序界面提示邮件发送成功，但邮箱里实际没收到邮件。
- **影响范围：** 所有邮件发送功能。

- **排查过程：**
    1.  **用户反馈：** 用户说没收到邮件。
    2.  **检查配置文件：** 看了 `e:\py_kshe\project\email_config.py` 文件。
    3.  **发现配置问题：**
        *   `SMTP_CONFIG['server']` 错误地设成了 `'smtp@qq.com'`，应该是 `'smtp.qq.com'`。
        *   `SMTP_CONFIG['sender_email']` 设成了发件人昵称 `'偷影子的人'`，它应该是个有效的邮箱地址，通常跟 `'username'` 一样。

- **根本原因：** SMTP服务器地址和发件人邮箱地址在配置文件里设错了。

- **代码调整：**
    - **文件：** `e:\py_kshe\project\email_config.py`
    - **改动：**
        *   把 `SMTP_CONFIG['server']` 的值从 `'smtp@qq.com'` 改成 `'smtp.qq.com'`。
        *   把 `SMTP_CONFIG['sender_email']` 的值从 `'偷影子的人'` 改成实际的邮箱地址 `'your_email@example.com'`。
    - **调整后相关配置：**
      ```python
      SMTP_CONFIG = {
          'server': 'smtp.qq.com',  # 例如: 'smtp.qq.com'
          'port': 587,
          'username': 'your_email@example.com',
          'password': 'YOUR_EMAIL_PASSWORD_OR_APP_SPECIFIC_PASSWORD', # 实际应为授权码
          'sender_email': 'your_email@example.com', 
          'sender_name': '会议提醒助手',
          'use_tls': True
      }
      ```

## 5. SMTP "From" 邮件头格式错误 (QQ邮箱)

- **问题描述：** SMTP配置修好后，程序发邮件时，终端日志显示SMTP错误：`(550, b'The "From" header is missing or invalid. Please follow RFC5322, RFC2047, RFC822 standard protocol. https://service.mail.qq.com/detail/124/995.')`。
- **影响范围：** 所有邮件发送功能，特别是用QQ邮箱作SMTP服务的时候。

- **排查过程：**
    1.  **检查日志：** 程序重新跑起来后，看了终端输出，发现了上面说的SMTP 550错误。
    2.  **定位邮件头设置：** 看了 `e:\py_kshe\project\tongzhi.py` 中 `send_email` 函数里邮件头是怎么构造的。
        ```python
        # tongzhi.py 修改前相关代码
        msg['From'] = Header(f"{config['sender_name']} <{config['sender_email']}>", 'utf-8')
        msg['To'] = Header(receiver_email, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        ```
    3.  **分析原因：** QQ邮箱对`From`和`To`头部的格式要求比较严。用 `email.header.Header` 对象包装包含显示名称（特别是中文名）和邮箱地址的复杂格式，可能导致QQ邮箱服务器验证不过。

- **根本原因：** `From` 和 `To` 邮件头的格式不完全符合QQ邮箱SMTP服务器的严格要求，特别是当包含显示名称和特殊字符时。

- **代码调整：**
    - **文件：** `e:\py_kshe\project\tongzhi.py`
    - **改动：** 简化 `From` 和 `To` 邮件头的设置，直接用邮箱地址字符串，不用 `Header` 对象搞复杂编码了。`Subject` 还是用 `Header` 来支持非ASCII字符。
    - **调整后相关代码：**
      ```python
      # tongzhi.py 修改后相关代码
      msg['From'] = config['sender_email']
      msg['To'] = receiver_email
      msg['Subject'] = Header(subject, 'utf-8')
      ```

通过这些调整，邮件发送功能相关的主要问题都解决了。