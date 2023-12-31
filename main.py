
#!/usr/bin/python3
import json
import os
import threading
import xml.dom.minidom
from io import BytesIO
from tkinter import *
from tkinter import filedialog, messagebox, ttk

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk

BASE_DIR = os.path.join(os.path.expanduser("~"), "httpClient")


class CollectionWindow(object):
    
    def __init__(self, window, callback=None):
        self.window = window
        self.callback = callback

        frame = Frame(window)
        new_collection = Button(frame, text="New Collection")
        new_collection.pack(side=LEFT, padx=10, pady=10)
        new_request = Button(frame, command=self.on_new, text="New request")
        new_request.pack(side=LEFT, padx=10, pady=10)
        frame.pack()

    def on_select(self):
        
        return None

    def on_new(self):
        
        self.callback("new")

    def on_delete(self):
        
        return None


class EnvironmentWindow(object):
    
    def __init__(self):
        return None


class Console(object):
    
    def __init__(self, callback):
        self.callback = callback

    def to_string(self, *args) -> str:
        
        temp = ""
        for item in args:
            if isinstance(item, (str, int, float)):
                temp += f"{item} "
            elif isinstance(item, (dict, list)):
                temp += f"{json.dumps(item)} "
            else:
                temp += str(temp)
        return temp

    def log(self, *args):
        
        self.callback({"level": "log", "content": self.to_string(*args)})

    def info(self, *args):
        
        self.callback({"level": "info", "content": self.to_string(*args)})

    def error(self, *args):
        
        self.callback({"level": "error", "content": self.to_string(*args)})

    def warning(self, *args):
        
        self.callback({"level": "warning", "content": self.to_string(*args)})


class RequestWindow(object):
    
    method_list = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    def __init__(self, window, callback=None):
        self.callback = callback

        north = ttk.Frame(window)
        close_btn = ttk.Button(north, text="Close", command=self.on_close)
        close_btn.grid(row=0, column=12)
        save_btn = ttk.Button(north, text="Export", command=self.save_handler)
        save_btn.grid(row=0, column=11)
        # 创建请求方式下拉框和URL输入框
        self.method_box = ttk.Combobox(north, width=10, values=self.method_list)
        self.method_box.current(0)
        self.method_box.grid(row=0, column=0)
        self.url_box = ttk.Entry(north, width=50)
        self.url_box.grid(row=0, column=1, columnspan=8)
        sub_btn = ttk.Button(north, text="Send")  # 发送请求按钮
        # 绑定发送请求按钮的事件处理函数
        sub_btn.config(command=self.send_request)
        sub_btn.grid(row=0, column=10)
        north.pack()

        # 创建一个PanedWindow
        paned_window = ttk.PanedWindow(window, orient=VERTICAL)
        paned_window.pack(fill=BOTH, expand=True)

        # 创建选项卡
        notebook = ttk.Notebook(paned_window)
        paned_window.add(notebook)
        
        # 创建查询参数页面
        params_frame = ttk.Frame(notebook)
        self.params_box = Text(params_frame, height=12)
        self.params_box.insert(END, "{}")
        self.params_box.pack(side=LEFT, fill=BOTH, expand=YES)
        params_scrollbar = ttk.Scrollbar(params_frame, command=self.params_box.yview)
        params_scrollbar.pack(side=LEFT, fill=Y)
        self.params_box.config(yscrollcommand=params_scrollbar.set)
        notebook.add(params_frame, text="Params")

        # 创建请求头页面
        headers_frame = ttk.Frame(notebook)
        self.headers_box = Text(headers_frame, height=12)
        self.headers_box.insert(END, "{}")
        self.headers_box.pack(side=LEFT, fill=BOTH, expand=YES)
        headers_scrollbar = ttk.Scrollbar(headers_frame, command=self.headers_box.yview)
        headers_scrollbar.pack(side=LEFT, fill=Y)
        self.headers_box.config(yscrollcommand=headers_scrollbar.set)
        notebook.add(headers_frame, text="Headers")

        # 创建请求体页面
        body_frame = ttk.Frame(notebook)
        self.body_box = Text(body_frame, height=12)
        self.body_box.insert(END, "{}")
        self.body_box.pack(side=LEFT, fill=BOTH, expand=YES)
        body_scrollbar = ttk.Scrollbar(body_frame, command=self.body_box.yview)
        body_scrollbar.pack(side=LEFT, fill=Y)
        self.body_box.config(yscrollcommand=body_scrollbar.set)
        notebook.add(body_frame, text='Body')

        # pre-request script
        script_frame = ttk.Frame(notebook)
        self.script_box = Text(script_frame, height=12)
        self.script_box.insert(END, "")
        self.script_box.pack(side=LEFT, fill=BOTH, expand=YES)
        script_scrollbar = ttk.Scrollbar(script_frame, command=self.script_box.yview)
        script_scrollbar.pack(side=LEFT, fill=Y)
        self.script_box.config(yscrollcommand=script_scrollbar.set)
        notebook.add(script_frame, text="Pre-request Script")

        # tests
        tests_frame = ttk.Frame(notebook)
        self.tests_box = Text(tests_frame, height=12)
        self.tests_box.insert(END, "")
        self.tests_box.pack(side=LEFT, fill=BOTH, expand=YES)
        tests_scrollbar = ttk.Scrollbar(tests_frame, command=self.tests_box.yview)
        tests_scrollbar.pack(side=LEFT, fill=Y)
        self.tests_box.config(yscrollcommand=tests_scrollbar.set)
        notebook.add(tests_frame, text="Tests")

        # 创建响应区域
        res_note = ttk.Notebook(paned_window)
        paned_window.add(res_note)

        res_body_frame = ttk.Frame(res_note)
        self.res_body_box = Text(res_body_frame, height=12)
        self.res_body_box.pack(side=LEFT, fill=BOTH, expand=YES)
        res_body_scrollbar = ttk.Scrollbar(res_body_frame, command=self.res_body_box.yview)
        res_body_scrollbar.pack(side=LEFT, fill=Y)
        self.res_body_box.config(yscrollcommand=res_body_scrollbar.set)
        res_note.add(res_body_frame, text="Body")

        res_cookie_frame = ttk.Frame(res_note)
        self.res_cookie_table = ttk.Treeview(res_cookie_frame, columns=("key", "value"), show="headings", height=6)
        res_cookie_scrollbar_x = ttk.Scrollbar(res_cookie_frame, orient=HORIZONTAL, command=self.res_cookie_table.xview)
        res_cookie_scrollbar_y = ttk.Scrollbar(res_cookie_frame, command=self.res_cookie_table.yview)
        self.res_cookie_table.column("key", width=1)
        self.res_cookie_table.heading("key", text="key")
        self.res_cookie_table.heading("value", text="value")
        res_cookie_scrollbar_y.pack(side="right", fill=Y, pady=(0, res_cookie_scrollbar_x.winfo_reqheight()))
        res_cookie_scrollbar_x.pack(side="bottom", fill=X)
        self.res_cookie_table.pack(side="left", fill=BOTH, expand=YES)
        self.res_cookie_table.config(xscrollcommand=res_cookie_scrollbar_x.set,
                                     yscrollcommand=res_cookie_scrollbar_y.set)
        res_note.add(res_cookie_frame, text="Cookies")

        res_header_frame = ttk.Frame(res_note)
        self.res_header_table = ttk.Treeview(res_header_frame, columns=("key", "value"), show="headings", height=6)
        self.res_header_table.column("key", width=1)
        self.res_header_table.heading("key", text="key")
        self.res_header_table.heading("value", text="value")
        res_header_scrollbar_x = ttk.Scrollbar(res_header_frame, orient=HORIZONTAL, command=self.res_header_table.xview)
        res_header_scrollbar_y = ttk.Scrollbar(res_header_frame, command=self.res_header_table.yview)
        res_header_scrollbar_y.pack(side="right", fill=Y, pady=(0, res_header_scrollbar_x.winfo_reqheight()))
        res_header_scrollbar_x.pack(side="bottom", fill=X)
        self.res_header_table.pack(side="left", fill=BOTH, expand=YES)
        self.res_header_table.config(xscrollcommand=res_header_scrollbar_x.set,
                                     yscrollcommand=res_header_scrollbar_y.set)
        res_note.add(res_header_frame, text="Headers")

        res_tests_frame = ttk.Frame(res_note)
        self.res_tests_box = Text(res_tests_frame, height=12)
        self.res_tests_box.pack(side=LEFT, fill=BOTH, expand=YES)
        res_tests_scrollbar = ttk.Scrollbar(res_tests_frame, command=self.res_tests_box.yview)
        res_tests_scrollbar.pack(side=LEFT, fill=Y)
        self.res_tests_box.config(yscrollcommand=res_tests_scrollbar.set)
        res_note.add(res_tests_frame, text="Test Results")

    def on_close(self):
        
        self.callback("close")

    def save_handler(self):
        """
        保存测试脚本
        """
        method = self.method_box.get()
        url = self.url_box.get()
        params = self.params_box.get("1.0", END)
        headers = self.headers_box.get("1.0", END)
        body = self.body_box.get("1.0", END)
        pre_request_script = self.script_box.get("1.0", END)
        tests = self.tests_box.get("1.0", END)

        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {}
        try:
            headers = json.loads(headers)
        except json.JSONDecodeError:
            headers = {}
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}
        if pre_request_script == "\n":
            pre_request_script = ""
        if tests == "\n":
            tests = ""

        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("json files", "*.json")])
        if filepath:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(json.dumps({
                    "method": method,
                    "url": url,
                    "params": params,
                    "headers": headers,
                    "body": body,
                    "pre_request_script": pre_request_script,
                    "tests": tests
                }))

    def fill_blank(self, data):
        method = data.get("method", "GET")
        self.method_box.current(self.method_list.index(method))
        self.url_box.delete(0, END)
        self.url_box.insert(END, data.get("url", ""))
        self.params_box.delete("1.0", END)
        self.params_box.insert(END, json.dumps(data.get("params", {}), ensure_ascii=False, indent=4))
        self.headers_box.delete("1.0", END)
        self.headers_box.insert(END, json.dumps(data.get("headers", {}), ensure_ascii=False, indent=4))
        self.body_box.delete("1.0", END)
        self.body_box.insert(END, json.dumps(data.get("body", {}), ensure_ascii=False, indent=4))
        self.script_box.delete("1.0", END)
        self.script_box.insert(END, data.get("pre_request_script", ""))
        self.tests_box.delete("1.0", END)
        self.tests_box.insert(END, data.get("tests", ""))

    def send_request(self):
        """ 定义发送请求的函数 """
        console = Console(self.console)

        # 获取请求方式和URL
        method = self.method_box.get()
        url = self.url_box.get()
        if url is None or url == "":
            messagebox.showerror("错误", "请输出请求地址")
            return
        # 获取查询参数、请求头和请求体
        params = self.params_box.get("1.0", END)
        headers = self.headers_box.get("1.0", END)
        body = self.body_box.get("1.0", END)

        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {}
        try:
            headers = json.loads(headers)
        except json.JSONDecodeError:
            headers = {}
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}

        pre_request_script = self.script_box.get("1.0", END)
        tests = self.tests_box.get("1.0", END)

        try:
            exec(pre_request_script)
        except Exception as error:
            console.error(str(error))

        # 发送网络请求
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            elif method == "POST":
                response = requests.post(url, params=params, data=body, headers=headers)
            elif method == "PUT":
                response = requests.put(url, params=params, data=body, headers=headers)
            elif method == "PATCH":
                response = requests.patch(url, params=params, data=body, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, params=params, headers=headers)
            elif method == "HEAD":
                response = requests.head(url, params=params, headers=headers)
            elif method == "OPTIONS":
                response = requests.head(url, params=params, headers=headers)
            else:
                messagebox.showerror("错误", "不支持的请求类型")
                return
        except requests.exceptions.MissingSchema:
            messagebox.showerror("错误", "请求错误")
            return

        # 将响应显示在响应区域
        self.res_cookie_table.delete(*self.res_cookie_table.get_children())
        for item in response.cookies.keys():
            self.res_cookie_table.insert("", "end", values=(item, response.cookies.get(item)))

        self.res_header_table.delete(*self.res_header_table.get_children())
        content_type = ""
        for item in response.headers.keys():
            if item == "Content-Type":
                content_type = response.headers.get(item)
            self.res_header_table.insert("", "end", values=(item, response.headers.get(item)))

        self.res_body_box.delete("1.0", END)
        if "application/json" in content_type:
            self.res_body_box.insert(END, json.dumps(response.json(), indent=4, ensure_ascii=False))
        elif "text/html" in content_type:
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, "html.parser")
            self.res_body_box.insert(END, soup.prettify())
        elif "text/xml" in content_type or "application/xml" in content_type:
            response.encoding = 'utf-8'
            dom = xml.dom.minidom.parseString(response.text)
            self.res_body_box.insert(END, dom.toprettyxml(indent="    "))
        elif "image" in content_type:
            data_stream = BytesIO(response.content)
            pil_image = Image.open(data_stream)
            tk_image = ImageTk.PhotoImage(pil_image)
            self.res_body_box.image_create(END, image=tk_image)
        else:
            self.res_body_box.insert(END, response.text)

        self.res_tests_box.delete("1.0", END)
        try:
            exec(tests)
        except Exception as error:
            console.error(str(error))

        self.callback("history", **{"data": f"{method} {url}"})
        self.callback("cache", **{"data": {
            "method": method,
            "url": url,
            "params": params,
            "headers": headers,
            "body": body,
            "pre_request_script": pre_request_script,
            "tests": tests
        }})

    def console(self, data):
        
        self.callback("console", **data)


class ConsoleWindow(object):
    """ 控制台 """

    def __init__(self, window):
        self.window = window
        ttk.Label(window, text="Console").pack(anchor="nw", side="top")
        self.text_box = Text(window, height=12)
        scrollbar = ttk.Scrollbar(window, command=self.text_box.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.text_box.pack(side=LEFT, fill=BOTH, expand=YES)
        self.text_box.config(yscrollcommand=scrollbar.set)

    def show_window(self):
        self.window.deiconify()  # 显示子窗口

    def hidden_window(self):
        self.window.withdraw()  # 隐藏子窗口

    def log(self, data):
        self.text_box.insert(END, data)
        self.text_box.insert(END, "\n")

    def info(self, data):
        self.text_box.insert(END, data)
        self.text_box.insert(END, "\n")

    def warning(self, data):
        self.text_box.insert(END, data)
        line_start = self.text_box.index("insert linestart")
        line_end = self.text_box.index("insert lineend")
        self.text_box.tag_config('warning', foreground="orange")
        self.text_box.tag_add("warning", line_start, line_end)
        self.text_box.insert(END, "\n")

    def error(self, data):
        self.text_box.insert(END, data)
        line_start = self.text_box.index("insert linestart")
        line_end = self.text_box.index("insert lineend")
        self.text_box.tag_config("error", foreground="red")
        self.text_box.tag_add("error", line_start, line_end)
        self.text_box.insert(END, "\n")

    def clear(self):
        self.text_box.delete("1.0", END)


class HistoryWindow(object):
    """ 历史记录窗口 """

    def __init__(self, window, callback=None):
        self.window = window
        self.callback = callback

        ttk.Label(window, text="History").pack(anchor="nw")
        self.history_box = Listbox(window)
        scrollbar = ttk.Scrollbar(window, command=self.history_box.yview)
        sbx = ttk.Scrollbar(window, command=self.history_box.xview, orient=HORIZONTAL)
        scrollbar.pack(fill=Y, side=RIGHT, pady=(0, sbx.winfo_reqheight()))
        sbx.pack(side=BOTTOM, fill=X)
        self.history_box.pack(side=LEFT, fill=BOTH, expand=YES)

        self.menu = Menu(window, tearoff=0)
        self.menu.add_command(label="Delete", command=self.on_delete)
        self.history_box.bind("<Double-Button-1>", self.on_select)
        self.history_box.bind("<Button-3>", self.popup_menu)
        self.history_box.config(yscrollcommand=scrollbar.set, xscrollcommand=sbx.set)

    def popup_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def show_window(self):
        self.window.deiconify()  # 显示子窗口

    def hidden_window(self):
        self.window.withdraw()  # 隐藏子窗口

    def log(self, data):
        self.history_box.insert(0, data)

    def clear(self):
        self.history_box.delete(0, END)

    def on_delete(self):
        selection = self.history_box.curselection()
        if selection:
            print(selection)
            self.history_box.delete(selection)
            self.callback("destroy", **{"index": selection[0]})

    def on_clear(self):
        self.clear()
        self.callback("clear")

    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.callback("select", **{"index": index})


class AboutWindow(Toplevel):
    """ 关于窗口 """

    def __init__(self):
        super().__init__()

        label = Label(self, text="Http Client\n0.0.1")
        label.pack()


class HelpWindow(Toplevel):
    """ 帮助窗口 """

    def __init__(self):
        super().__init__()

        label = Label(self, text="""
打印日志可以使用
console.log()
console.error()
console.info()
console.warning()
        """)
        label.pack()


class MainWindow(object):
    
    history_list = []  # 历史记录列表

    def __init__(self, root):
        self.root = root
        # 创建主窗口
        root.title("HTTP Client")
        root.after(0, self.on_start)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        pw1 = ttk.PanedWindow(root)
        pw1.pack()
        pw2 = ttk.PanedWindow(pw1, orient=HORIZONTAL)
        pw1.add(pw2)

        self.history_top = ttk.Frame(pw2)
        pw2.add(self.history_top)
        self.history_window = HistoryWindow(self.history_top, self.history)

        self.notebook = ttk.Notebook(pw2)
        pw2.add(self.notebook)

        console_top = ttk.Frame(pw1)
        pw1.add(console_top)
        self.console_window = ConsoleWindow(console_top)
        self.new_request()

        menu_bar = Menu(root)
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(command=self.new_request, label="New Request")
        file_menu.add_command(command=self.open_handler, label="Import")
        view_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(command=self.history_window.on_clear, label="Clear History")
        view_menu.add_command(command=self.console_window.clear, label="Clear Console")
        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(command=HelpWindow, label="Help")
        help_menu.add_command(command=AboutWindow, label="About")
        root.config(menu=menu_bar)

    def open_handler(self):
        """ 打开文件 """
        filepath = filedialog.askopenfilename()
        if filepath:
            with open(filepath, "r", encoding="utf-8") as file:
                data = file.read()

                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    messagebox.showerror("错误", "文本内容必须是一个json")
                    return

                self.new_request(data)

    def new_request(self, data=None):
        
        tl = Frame(self.notebook)
        req_win = RequestWindow(tl, self.request)
        if data is not None:
            req_win.fill_blank(data)
        self.notebook.add(tl, text="New request")
        self.notebook.select(self.notebook.index("end") - 1)

    def show_history(self, data):
        
        self.history_window.clear()
        for item in data:
            self.history_list.append(item)
            try:
                self.history_window.log(f"{item.get('method' '')} {item.get('url', '')}")
            except AttributeError:
                pass

    def on_start(self):
        
        filepath = os.path.join(BASE_DIR, "history.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                try:
                    data = file.read()
                    data = json.loads(data)
                    thread = threading.Thread(target=self.show_history, args=(data,))
                    thread.start()
                except json.JSONDecodeError:
                    pass

    def on_closing(self):
        
        with open(os.path.join(BASE_DIR, "history.json"), "w", encoding="utf-8") as file:
            file.write(json.dumps(self.history_list))
        self.root.destroy()

    def collection(self, action):
        
        if action == "new":
            self.new_request()

    def request(self, action, **kwargs):
        """ 请求窗口回调 """
        if action == 'cache':
            # 缓存历史记录
            self.history_list.append(kwargs.get("data"))
        elif action == "history":
            # 写入历史记录列表
            self.history_window.log(kwargs.get("data"))
        elif action == "console":
            # 写入控制台
            level = kwargs.get("level")
            if level == "log":
                self.console_window.log(kwargs.get("content"))
            elif level == "info":
                self.console_window.info(kwargs.get("content"))
            elif level == "error":
                self.console_window.error(kwargs.get("content"))
            elif level == "warning":
                self.console_window.warning(kwargs.get("content"))
        elif action == "close":
            self.close_request()

    def history(self, action, **kwargs):
        """ 历史记录回调 """
        if action == "select":
            index = kwargs.get("index")
            if index is not None:
                i = len(self.history_list) - index - 1
                data = self.history_list[i]
                self.new_request(data)

        elif action == "destroy":
            index = kwargs.get("index")
            if index is not None:
                i = len(self.history_list) - index - 1
                self.history_list.pop(i)

        elif action == 'clear':
            self.history_list = []

    def close_request(self):
        
        self.notebook.forget(self.notebook.select())
        if self.notebook.select() == "":
            self.new_request()


if __name__ == '__main__':
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    tk = Tk()
    MainWindow(tk)
    # 进入消息循环
    tk.mainloop()
