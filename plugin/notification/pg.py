
import email
import json
import os
import random
import signal
import smtplib
import sys
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiofiles
from HTMLTable import HTMLTable
from attr import dataclass
from fastapi import FastAPI, Request, Form, Header
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, model_serializer
from enum import Enum, unique

from tabulate import tabulate

import shared_vars as shv



#设计给NatterWeb用于即时使用邮件通知公网映射变化
@dataclass
class BaseConfig:
    nav={"name": "动态IP邮件通知", "url": "/plugin/notice_main", "icon": "bi bi-envelope"}
    now_task_status=dict()
class LogManager:
    runninglogs = []

    @staticmethod
    def write_log(log_message):
        # 获取当前时间戳并格式化
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        log_entry = f"{timestamp}: {log_message}"
        LogManager.runninglogs.append(log_entry)

    @staticmethod
    def clear_logs():
        LogManager.runninglogs = []

@unique
class operation_type(str,Enum):
    testsend="testsend"
    save="save"

class EmailPayload(BaseModel):
    operation_type: operation_type
    email_type: str="qq"
    sender_email:EmailStr = "sender@qq.com"
    authorization_code:str="default_code"
    recipient_email:EmailStr="recipient@example.com"
    smtp_enabled:bool

# 防止因为线程不结束而导致结束时卡住
def signal_handler(sig, frame):
    PollTask.stop_thread()
    PollTask.thread_id = None
    PollTask.is_running = False
    # @model_serializer
    # def serialize_emailpayload(self):
    #     source=self.model_dump()
    #     data=dict()
    #     for (key,value) in source.items():
    #         data[key]=value
    #     return data

# pg =  APIRouter()


# pg.mount("/notice/static", StaticFiles(directory="./plugin/notification/static"), name="notice_static")
# static_dir = os.path.abspath("./static")
# pg.mount("/notice/static", StaticFiles(directory=static_dir), name="notice_static")
def bind_all_router():
    global pg
    @pg.get("/notice",tags=["notice"])
    async def read_notice():
        print("messag1e",shv.task_status)
        print("task_status in pgfile:"+str(id(shv.task_status)))
        return {"message": shv.task_status}

    @pg.get("/notice_main",response_class=HTMLResponse,tags=["notice"])
    async def read_notice_main(request: Request,x_update_content: str = Header(None)):
        # dic={ "request": request,"1":"2"}
        # print("pgfile",id(shv.task_status))
        # return {"message":  "test"}
        mailsetting = load_from_json("mail_setting.json")
        shv.main_dict['mailsetting']=mailsetting
        # print(shv.main_dict)
        shv.main_dict['mailserver']=mailserver
        #为ajax更新作出区别处理
        if x_update_content:
            print("receive x-update-content")
            return shv.templates.TemplateResponse("notice_content.html", {"request": request, "main_dict": shv.main_dict})
        else:
            return shv.templates.TemplateResponse("notice.html", {"request": request, "main_dict": shv.main_dict})

    @pg.post("/notice/email_settings",tags=["notice"])
    async def email_set(payload:EmailPayload=Form()):
        if payload.operation_type==operation_type.testsend:
            if sendmail(payload, "测试邮件", "这是Nw发送的测试邮件。"):
                return {"message": "测试邮件发送成功！"}
            else:
                return {"message": "测试邮件发送失败！请检查设置。"}
        if  payload.operation_type==operation_type.save:
            source = payload.model_dump()
            jsonstr=json.dumps(source,indent=4)
            await save_to_json_async(jsonstr,"mail_setting.json")
            if payload.smtp_enabled:
                thread_id = PollTask.poll_function(my_function, 5)
                if thread_id is not None:
                    LogManager.write_log(f"IP变更邮件通知的线程ID为: {thread_id}")
                    return{"message":"已经启用IP变更邮件通知!"}
                else:
                    LogManager.write_log("相同任务的线程已经在运行，不能再次启动。")
                    return{"message":"相同任务的线程已经在运行，不能再次启动。"}
            else:
                if  PollTask.thread_id is not None:
                    PollTask.stop_thread()
                    LogManager.write_log("已经保存设置！并且停用邮件通知任务。")
                    return {"message": "已经保存设置！并且停用邮件通知任务。"}
                else:
                    LogManager.write_log("已经保存设置!")
                    return {"message": "已经保存设置！"}
        return {"message": "无效请求！"}
    @pg.get("/notice/logs",tags=["notice"])
    async def get_logs():
        return{"message": LogManager.runninglogs}

    @pg.post("/notice/empty_logs",tags=["notice"])
    async def empty_logs():
        LogManager.clear_logs()
        return{"message": "清空日志成功!"}


    @pg.get("/notice/testpoint",tags=["notice"])
    async def test_point():
        keys=list(shv.task_status.keys())
        if keys:
            select=random.choice(keys)
            shv.task_status[select]['natmap'] = f"testpoint change test{random.uniform(0, 10)}"
        # print(f"old"+BaseConfig.now_task_status[select].get('natmap') )
        # print(f"new" + shv.task_status[select].get('natmap'))
        # print(f"old{id(BaseConfig.now_task_status[select].get('natmap'))}")
        # print(f"new{id(shv.task_status[select].get('natmap'))}")
        # print(f"old{id(BaseConfig.now_task_status)}")
        # print(f"new{id(shv.task_status)}")

        # print(f"old" + BaseConfig.now_task_status[select].get('natmap'))
        # print(f"new" + shv.task_status[select].get('natmap'))
        # print(str(shv.task_status))
        return {"message": f"任务id{select}被改变了"}

# def sendmail(sender_email,authorization_code,recipient_email,title,body,email_type):
def sendmail(payload:EmailPayload,title,body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = payload.sender_email
    msg['To'] = payload.recipient_email
    msg['Subject'] = title
    # 连接SMTP服务器
    # server=None
    # if payload.email_type=="qq":
    #     server = smtplib.SMTP('smtp.qq.com', 587)
    # if payload.email_type == "163":
    #     server = smtplib.SMTP('smtp.163.com', 465)
    # if payload.email_type == "outlook":
    #     server = smtplib.SMTP('outlook.office365.com', 993)
    # if payload.email_type == "gmail":
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    email_type_server_mapping = {
        "qq": ('smtp.qq.com', 587),
        "163": ('smtp.163.com', 465),
        "outlook": ('outlook.office365.com', 993),
        "gmail": ('smtp.gmail.com', 587)
    }
    server = None
    try:
        if payload.email_type in email_type_server_mapping:
            server_info = email_type_server_mapping[payload.email_type]
            server = smtplib.SMTP(*server_info)
        # print(server_info)
        server.starttls()
        server.login(payload.sender_email, payload.authorization_code)
        # 发送邮件
        server.sendmail(payload.sender_email, payload.recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"发送邮件时出现错误: {e}")
        return False
def sendmail_html(payload:EmailPayload,title,body):
    msg = email.mime.multipart.MIMEMultipart()
    msg['From'] = payload.sender_email
    msg['To'] = payload.recipient_email
    msg['Subject'] = title
    email_type_server_mapping = {
        "qq": ('smtp.qq.com', 587),
        "163": ('smtp.163.com', 465),
        "outlook": ('outlook.office365.com', 993),
        "gmail": ('smtp.gmail.com', 587)
    }
    msg.attach(MIMEText(body, "html", "utf-8"))
    server = None
    try:
        if payload.email_type in email_type_server_mapping:
            server_info = email_type_server_mapping[payload.email_type]
            server = smtplib.SMTP(*server_info)
        # print(server_info)
        server.starttls()
        server.login(payload.sender_email, payload.authorization_code)
        # 发送邮件
        server.sendmail(payload.sender_email, payload.recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"发送邮件时出现错误: {e}")
        return False

def load_from_json(filename):
    # 检查文件是否存在
    if not os.path.exists(filename):
        # raise FileNotFoundError(f"The file {filename} does not exist.")
        payload=EmailPayload(operation_type=operation_type.save,smtp_enabled=False)
        ret=payload.model_dump()
        return ret
    # 文件存在，继续读取和加载
    with open(filename, 'r') as file:
        a=json.load(file)
        print("a的类型"+str(type(a)))
        return a
async def save_to_json_async(data, filename):
    async with aiofiles.open(filename, 'w') as file:
        await file.write(data)

class PollTask:
    is_running = False
    thread_id = None
    lock = threading.Lock()

    @classmethod
    def poll_function(cls, func, interval):
        def wrapper():
            current_thread = threading.current_thread()
            with cls.lock:
                cls.thread_id = current_thread.ident
            cls.is_running = True
            while cls.is_running:
                func()
                time.sleep(interval)
            cls.is_running = False

        if not cls.is_running:
            thread = threading.Thread(target=wrapper)
            thread.start()
            # 等待线程设置thread_id
            while cls.thread_id is None:
                time.sleep(0.001)
            return cls.thread_id
        return None

    @classmethod
    def stop_thread(cls):
        if cls.is_running:
            cls.is_running = False

def my_function():
    # task_status=shv.main_dict["task_status"]
    #使用dataclass初始化有点慢，所以导致第一次运行时没有这个变量，要先检查是否存在才使用，不想直接实例化这个数据类,
    #这个原因后面也找到了，@dataclass官方不让使用空的可变对象当初始值，原因主要是实例化后对象会共享共一类对象成员，修改其中一个实例中的成员变量会影响到另一个，等于没实例化,报错了但是uvicorn的控制台没有错误输出。
    #可能官方检查不到位，如果不指明变量为dict类型，编译又能过，正常用，反正这个类本来就是静态的，就不会实例化使用。
    #https://blog.csdn.net/Johnzy123123/article/details/129803298
    #没有使用dataclass时，发现主进程的的BaseConfig.now_task_status的值都是好好的(不实例化值也全部都初始化好了)，但是子线程会出现None类型，而且使用线程锁访问也没什么用，
    #最后发现线程中的BaseConfig.now_task_status和主进程上的存储地址不同，不是同一个id,但是类BaseConfig是同一ID,这都什么特性，真是太奇怪了,类是同一个类，成员变量不是同一成员变量
    #反正就是不想实例化类，None做个检测直接赋值，本来就是当做全局变量用的。
    #后期调试发现None是因为copytask没有返回值导致的
    # lock=threading.Lock()
    # print(dir(BaseConfig))
    # with lock:
    if hasattr(BaseConfig, 'now_task_status'):
        # print("BaseConfig:"+str(BaseConfig.now_task_status))
        # print("shv.task_status:" + str(shv.task_status))
        # if BaseConfig.now_task_status is None:
        #     BaseConfig.now_task_status = {}
        # print(f"sub{id(BaseConfig.now_task_status)}")
        if len(BaseConfig.now_task_status)<1:
            BaseConfig.now_task_status = copytask(shv.task_status)
            # print(BaseConfig.now_task_status)
        diff = compare_dicts(BaseConfig.now_task_status, shv.task_status)
        new=get_new_change_diff(diff)
        if check_if_natmapchanged(BaseConfig.now_task_status,shv.task_status) :
            content=make_mail_html(new)
            mailsetting=load_from_json("mail_setting.json")
            email_payload = EmailPayload(**mailsetting)
            if content and email_payload:
                sendmail_html(email_payload, "映射变更通知", content)
        if len(diff)>0 and BaseConfig.now_task_status:
            LogManager.write_log("检测到规则变化，变化规则为"+str(new))
            BaseConfig.now_task_status = copytask(shv.task_status)
    else:
        LogManager.write_log("初始化中。。。")
def compare_dicts(dict1, dict2):
    if dict1:
        diff = {}
        for key in dict1:
            if key not in dict2 or dict1[key]!= dict2[key]:
                diff[key] = [dict1[key], dict2[key] if key in dict2 else None]
        for key in dict2:
            if key not in dict1:
                diff[key] = [None, dict2[key]]
        return diff
    else:
        return ""
def get_new_change_diff(diff:dict):
    new_change=dict()
    for key in diff:
        if isinstance(diff[key],list):
            new_change[key]=diff[key][1]
        else:
            break
            #当没有发现对比项为list时，说明没有对比出差异项，compare_dicts会自行增加list来突出差异项。
    return new_change
#公网IP映射变动，和规则变动有所不同，规则变动只会日志记录，公网IP映射变动则发送邮件，这样做的目的是减少无意义邮件发送。
#检测条件是当旧的task_status和新的task_status的key项完全相同时，其natmap条目发生变动就视为映射变动
#测试变动接口/plugin/notice/testpoint
def check_if_natmapchanged(old_task_status,new_task_status):
    #字典空就直接返回
    if not (old_task_status and new_task_status): return False
    #规则首次生效前，旧的字典的映射是空的，不算是映射变更，减少无用的邮件。
    for value in old_task_status.values():
        if not value.get('natmap'):  # 检查natmap是否为空
            return False
    #key值是一一对应的，那么就有下一步检查的必要
    if set(old_task_status.keys()) == set(new_task_status.keys()):
        keys = old_task_status.keys()
        diff=[]
        for key in keys:
            if old_task_status[key].get('natmap') != new_task_status[key].get('natmap') :
                print(f"检测到任务id{key}映射发生变动")
                diff.append(key)
            # print(f"old"+old_task_status[key].get('natmap') )
            # print(f"new" + new_task_status[key].get('natmap'))
        if diff:
            LogManager.write_log(f"检测到任务id{diff}映射发生变动")
            return True
        return False
    else:
        return False
#新旧字典的浅拷贝会导致子任务字典关联，深拷贝会报错，所以创建专门的函数来处理这个问题
def copytask(source:dict):
    lock=threading.Lock()
    with lock:
        if source is not None:
            dest=dict()
            keys=source.keys()
            for key in keys:
                dest[key]=source[key].copy()
            return dest
        return {}
#检测到变动时整理相关信息
def make_mail_content(new:dict):
    headers = ["规则名", "映射状态"]
    data=[]
    for line in new.values():
        data.append([line['rulename'],line['natmap']])
    # print(data)
    table = tabulate(data, headers=headers, tablefmt="html")
    return table
def make_mail_html(new:dict):
    headers = ["规则名", "映射状态"]
    data=[]
    for line in new.values():
        data.append([line['rulename'],line['natmap']])
    tup=tuple(data)
    return creat_email_html("IP变动通知", tup)

def creat_email_html(table_name, rows_text):
    table = HTMLTable(caption=table_name)

    # 没有实现空行
    table.append_data_rows('')

    # 表头
    table.append_header_rows((
        ('规则名', '映射IP'),
    )
    )
    table.append_data_rows(rows_text)

    # 标题样式
    caption_style = {
        'text-align': 'center',
        'color': '#0002e3;',
        'font-family': '黑体;',
        'font-size': '2rem;'
    }
    table.caption.set_style(caption_style)

    # 设置边框
    border_style = {
        'border-color': '#008eb7',
        'border-width': '1px',
        'border-style': 'solid',
        'border-collapse': 'collapse',
        # 实现表格居中
        'margin': 'auto',
    }
    # 外边框
    table.set_style(border_style)
    # 单元格边框
    table.set_cell_style(border_style)

    # 单元格样式
    # 先得设置cell_style，cell_style包括header_cell_style，会把header_cell_style配置覆盖
    cell_style = {
        'text-align': 'center',
        'padding': '4px',
        'background-color': '#ffffff',
        'font-size': '0.95em',
    }
    table.set_cell_style(cell_style)

    # 表头样式
    header_cell_style = {
        'text-align': 'center',
        'padding': '4px',
        'background-color': '#F8F8FF',
        'color': '#105de3',
        'font-size': '0.95em',
    }
    table.set_header_cell_style(header_cell_style)
    # 生产HTML
    html = table.to_html()
    # print(html)
    return html

def running_smtp_service():
    mailsetting = load_from_json("mail_setting.json")
    email_payload = EmailPayload(**mailsetting)
    if email_payload.smtp_enabled:
        thread_id = PollTask.poll_function(my_function, 5)
        if thread_id is not None:
            LogManager.write_log(f"IP变更邮件通知的线程ID为: {thread_id}")
        else:
            LogManager.write_log("相同任务的线程已经在运行，不能再次启动。")

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS  # PyInstaller 临时解压目录
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, relative_path))

if __name__ != "__main__":
    global pg
    pg= FastAPI()
    static_dir = get_resource_path("./plugin/notification/static")
    print("plugin_static_dir"+static_dir)
    pg.mount("/notice/static", StaticFiles(directory=static_dir), name="notice_static")
    mailserver={"qq":"qq邮箱","163":"163邮箱","Gmail":"Gmail邮箱","outlook":"Outlook邮箱"}
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    bind_all_router()
    # 如果已经启用了通知，就自动开启服务
    running_smtp_service()
# def handle_exit():
#     PollTask.stop_thread()


# atexit.register(handle_exit)



# @pg.get("/notice/static", tags=["notice"])
# async def read_static_static():
#     html_file_path = "./plugin/notification/static/pg.html"
#     return FileResponse(html_file_path)
# if __name__ == '__main__':
#     # 运行fastapi程序
#     uvicorn.run(app="pg:pg", host="192.168.31.15", port=18650, reload=True)