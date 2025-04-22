# 在文件顶部添加（实际不会运行，仅供Nuitka分析）
if False:
    from HTMLTable import HTMLTable
    from attr import dataclass
    from fastapi import Form
    from pydantic import BaseModel, EmailStr, model_serializer
    from enum import Enum, unique
    from tabulate import tabulate
    from plugin.notification import pg

import sys
import ast
import importlib
import ipaddress
import shutil
import time
import uuid
import zipfile
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, Header, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from poetry.core.masonry.utils import module
from poetry.plugins import Plugin
from starlette.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, constr, conint, field_validator
import subprocess
import os
import re
import asyncio
import json
import aiofiles
import socket
import requests
import functools
import argparse


import shared_vars as shv



class BaseConfig:
    # 一个接口，用来获取公网IPv4地址
    public_ip_interface = ['https://checkip.amazonaws.com/', 'https://ipinfo.io/ip', 'http://ip.jsontest.com/']
    #导航栏目
    nav_items = [
        {"name": "状态", "url": "/", "icon": "bi bi-card-list"},
        {"name": "映射管理", "url": "/manager", "icon": "bi bi-command"},
        {"name": "关于", "url": "/about", "icon": "fa fa-heart"},
    ]
    #从natter日志获取信息的正则表达式
    reg_dic = {
        "sourceip": r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)(?=\s<)",
        "destinationip": r"(?<=-->\s(tcp|udp)://)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)(\r|\n|$|\r\n)",
        "success": r"WAN (.*) OPEN",
        "natmap": r"(?:tcp|udp)(.*) <--Natter-->(.*)",
        "protocol":r"tcp|udp"
    }
    # 检测nat type的脚本路径
    checknatpy =['venv', 'Thirdparty', 'natter-check.py']
    ntpy=['venv','Thirdparty','natter.py']
    checknatpy_path=functools.reduce(lambda x, y: os.path.join(x, y), checknatpy)
    ntpy_path = functools.reduce(lambda x, y: os.path.join(x, y), ntpy)

    __version__ = '1.0.0_bate4'

    @staticmethod
    def is_nuitka():
        # 检查标志、模块、文件路径
        return (
                "__compiled__" in globals()
                or getattr(sys, "frozen", False)
                or any("nuitka" in name.lower() for name in sys.modules)
        )
    @classmethod
    #exe_path无论怎么获取都在程序运行目录，无论是打包前还是打包之后
    def get_exe(cls):
        def get_exe_name_by_platform():
            if sys.platform.startswith("win"):
                exe_name = '.\\ntsub'
            else:
                exe_name = './ntsub'
            return exe_name
        if getattr(sys, 'frozen', False):
            # pyinstaller环境路径处理
            exe_path = os.getcwd()
            exe_name=get_exe_name_by_platform()
        elif cls.is_nuitka:
            #nuitka环境路径，还是单独开一个分支省得干扰原先配置
            exe_path = os.getcwd()
            exe_name = 'python'
        else:
            exe_path = os.path.dirname(os.path.abspath(__file__))
            exe_name = 'python'
        return exe_name,exe_path

    exe_name, exe_path = get_exe()

    # exe=os.path.normpath(os.path.join(exe_path,exe_name))
    file_path = os.path.normpath(os.path.join(exe_path, ntpy_path))
    file_path2 = os.path.normpath(os.path.join(exe_path, checknatpy_path))

# 处理打包后的资源路径
def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS  # PyInstaller 临时解压目录
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, relative_path))

def init_vars():
    global rules
    global main_dict
    global templates
    global app
    global othertasks
    global log_task
    global task_status
    global netstatus
    global logs_dict

    # 任务字典，记录获取NAT类型的协程和natter.py子进程相关信息。
    shv.init()
    logs_dict={}
    rules = shv.rules
    # 加载映射规则
    if not os.path.exists('rules.json'):
        rules = {}
    else:
        rules = load_from_json('rules.json')
        # print(rules)
    task_status = shv.task_status
    netstatus = {"ver": '', 'tcpnat': '-1', 'udpnat': '-1', 'locahostip': '', 'internetip': ''}
    shv.main_dict = {'nav_items': BaseConfig.nav_items, 'netstatus': netstatus, 'rules': rules,
                 'task_status': task_status,"version":BaseConfig.__version__}  # 初始化主字典
    main_dict = shv.main_dict


    # 不得以创建出来的集合，对全局的task进行强引用，以便回收，具体可以看
    # https://zhuanlan.zhihu.com/p/602955920
    # 有一些任务不关心，只是为了启动进程/线程/协程一次性任务，都在结束后检查是否正常退出。
    # 还有就是set能排除重复数据，task_status存放的主要是进程信息，othertasks基本是createtask创建的协程。
    othertasks = set()
    ##子单位为结构为taskid：一个task集合，包括所有持续捕捉日志的相关任务.
    log_task = dict()
    ##发现asyncio.queue()创建的任务不会随着被捕捉日志的进程结束而结束，所以做一个任务清理，当停止进程时，同时检查任务，若任务存在则取消。
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load
        # print("load")
        pass
        yield
        pass
        # print("clean")
        # Clean up
    #fastapi主实例
    static_path=get_resource_path("static")
    plugin_path = get_resource_path("plugin")
    templates_path=get_resource_path("templates")
    app = FastAPI(lifespan=lifespan)
    # 推荐的挂载静态文件目录的方式
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    # print(plugin_path)
    temp_list = Plugin.find_temp_filefold(plugin_path)
    temp_list.append(templates_path)
    # print(temp_list)
    shv.templates = Jinja2Templates(directory=temp_list)
    # print("appfile1", id(shv.templates))
    templates = shv.templates
    # print("appfile2", id(templates))
    # print (main_dict)
    # print('initdict')

def load_from_json(filename):
    # 检查文件是否存在
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The file {filename} does not exist.")

    # 文件存在，继续读取和加载
    with open(filename, 'r') as file:
        return json.load(file)



class Rule(BaseModel):
    rulename: constr(max_length=12)  # 字符串长度限制
    hostip: str
    protocol:str
    port: conint(gt=0, le=65535)  # 端口数字限制
    upnp:bool
    enabled: bool

    @field_validator('hostip')
    def validate_hostip(cls, v):
        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError:
            raise ValueError('主机IP必须是有效的 IPv4 地址')
        return v
class Ruleid(BaseModel):
    id:str
class Rulemodify(BaseModel):
    id:str
    rulename: constr(max_length=12)  # 字符串长度限制
    hostip: str
    protocol: str
    port: conint(gt=0, le=65535)  # 端口数字限制
    upnp: bool
    enabled: bool


def get_tasks_with_function(tasks, function_name):
    return {key: value for key, value in tasks.items() if value['function'] == function_name}

def processmanager():
    def task_tracker(func):
        lock = asyncio.Lock()
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            #装饰器内部要是异步的，否则包装的异步函数会立刻返回结果，那么对任务的记录会有误。
            # 如果外部没有传入task_id，则生成新的；否则使用传入的task_id
            task_id = kwargs.pop('task_id', str(uuid.uuid4()))
            async with lock:
                task_status[task_id] = {"status": "Running", "function": func.__name__}
                start_time = time.perf_counter()
                print('tasktracker:',task_status)
            try:
                # 将task_id放入kwargs，以供func访问
                if 'task_id' not in kwargs:
                    kwargs['task_id'] = task_id
                result = await func(*args, **kwargs)
                async with lock:
                    task_status[task_id]["status"] = "Executed"

                end_time = time.perf_counter()
                print(f"执行时间: {end_time - start_time:.6f} 秒")
                return result
            except Exception as e:
                async with lock:
                    task_status[task_id]["status"] = "Failed"
                raise e
            # except BaseException as e:
            #     print("task canceled")
            finally:
                pass
                #print("end of wrapper")
        return wrapper
    return task_tracker

def process_natter_task(input_str,task_id=None):
    # 初始化用于存储结果的子字典
    if task_id not in task_status or not bool(task_status[task_id]):
        task_status[task_id] = {}
        print('task_id:',task_id)
    # 遍历正则表达式字典
    for key, pattern in BaseConfig.reg_dic.items():
        # 尝试在输入字符串中匹配正则表达式
        match = re.search(pattern, input_str)
        if match:
            if key == 'success':
                task_status[task_id][key]='成功连接'
            else:
                task_status[task_id][key] = match.group(0)
    return task_status

def init_dic_key(dic,task_id,value):
    if task_id not in dic or not bool(dic[task_id]):
        dic[task_id] = value
def lookup_taskstatus(rule_id):
    ulis=[]
    for uuid,task in task_status.items():
        if task.get('rule_id','')==rule_id:
            ulis.append(uuid)
    return ulis


async def process_output(pipe, queue):
    while True:
        line = await pipe.readline()
        if line:
            queue.put_nowait(line)
        else:
            break

def remove_from_running_tasks(task):
    # print("Removing task from running tasks.")
    #task.cancel()
    othertasks.remove(task)

def remove_from_log_tasks(task,taskid):
    if log_task.get(taskid):
        log_task.get(taskid).discard(task)

async def run_command(command, output_file):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    with open(output_file, 'wb') as f:
        while True:
            data = await process.stdout.read(1024)
            if not data:
                break
            f.write(data)
    await process.wait()

@processmanager()
async def checknat(task_id =None):
    if getstatus("tcpnat") !='-1' and getstatus("udpnat")!='-1':
        return
    command = [BaseConfig.exe_name, BaseConfig.checknatpy_path]
    output_file = 'nattype.txt'
    await run_command(command, output_file)
    lines = []
    try:
        with open('nattype.txt', 'r') as f:
            for line in f:
                lines.append(line.strip())
    except FileNotFoundError:
        print("文件不存在")
    print(lines)
    for index, line in enumerate(lines):
        pattern = r'-?\b\d+\b'
        match = re.search(pattern, line)
        if match:
            number = match.group()
            print(index)
            print(line)
            if index == 2:
                main_dict['netstatus']["tcpnat"] = number
                print("TCP NAT:" + number)
            if index == 3:
                main_dict['netstatus']["udpnat"] = number
                print("UDP NAT:" + number)


@processmanager()
async def launch_natter_task(cmdlist, rule_id, task_id=None):
    # signal.signal(signal.SIGINT, signal.SIG_IGN)  # 忽略 SIGINT 以确保不被默认处理
    # signal.signal(signal.SIGINT, signal_handler)
    # script_directory = os.path.dirname(os.path.abspath(__file__))
    # file_path = os.path.join(script_directory, "./venv/Thirdparty", 'natter.py')

    command = [BaseConfig.exe_name, BaseConfig.file_path] + cmdlist
    # print("command:"+str(command))
    process = await asyncio.create_subprocess_exec(*command,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
    stdout_queue, stderr_queue=setup_log_task(process,task_id)
    # 创建锁对象
    lock = asyncio.Lock()
    async with lock:
        # 初始化对应键值
        init_dic_key(logs_dict, task_id, "")
        task_status[task_id]['process'] = process
        task_status[task_id]['rule_id'] = rule_id
        # task_status[task_id]['rulename']=main_dict['rules'][rule_id]['rulename']
        task_status[task_id]['rulename'] = rules[rule_id]['rulename']
        # 设置success默认值
        task_status[task_id]['success'] = '未连接'
    while True:
        task_stdout = asyncio.create_task(stdout_queue.get())
        task_stderr = asyncio.create_task(stderr_queue.get())
        log_task_add(task_id,task_stdout,task_stderr)

        tasks = [task_stdout, task_stderr]
        line = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        done, _ = line
        for item in done:
            line = item.result()
            # encoding = chardet.detect(line)['encoding']
            # print ('edcode',encoding)
            linestr=line.decode('ascii','ignore')
            process_natter_task(linestr, task_id=task_id)
            logs_dict[task_id] += linestr
            v=task_status[task_id]
            sourceip=v.get('sourceip')
            pro=v.get('protocol')
            if pro and sourceip:
                async with aiofiles.open("./logs/"+ pro + sourceip +".txt", 'a') as file:
                    await file.write(linestr)
            # print(logs_dict)


def is_nested(lst):
    return any(isinstance(i, list) for i in lst)


async def run_natter_mutiprogracess():
    cmddic = makecommand(rules)
    for ruleid, cmdlist in cmddic.items():
        if is_nested(cmdlist):
            for cmd in cmdlist:
                task=asyncio.create_task(launch_natter_task(cmd, ruleid))
                othertasks.add(task)
                task.add_done_callback(lambda t: remove_from_running_tasks(t))
        else:
            # await asyncio.create_task(sleep1000s())
            task=asyncio.create_task(launch_natter_task(cmdlist, ruleid))
            othertasks.add(task)
            task.add_done_callback(lambda t: remove_from_running_tasks(t))



async def launch_simple_rule(rule_id):
    if rules[rule_id]['enabled']:
        cmdlist = makecommand(rules[rule_id])
        print(rule_id, cmdlist)
        if is_nested(cmdlist):
            for cmd in cmdlist:
                task=asyncio.create_task(launch_natter_task(cmd, rule_id))
                othertasks.add(task)
                task.add_done_callback(lambda t: remove_from_running_tasks(t))
        else:
            task=asyncio.create_task(launch_natter_task(cmdlist, rule_id))
            othertasks.add(task)
            task.add_done_callback(lambda t: remove_from_running_tasks(t))

def extract_version(s):
    pattern = r'\b(\d+\.\d+\.\d+)\b'  # 正则表达式，匹配形如 x.x.x 的版本号
    match = re.search(pattern, s)  # 在字符串中搜索匹配项
    if match:
        # 如果找到了匹配项，则返回第一个匹配组（即整个匹配部分）
        return match.group(1)
    else:
        # 如果没有找到匹配项，返回None或其他合适的默认值
        return None

async def save_to_json_async(data, filename):
    async with aiofiles.open(filename, 'w') as file:
        await file.write(json.dumps(data, indent=4))


def get_natter_version():
    if main_dict['netstatus']["ver"]!= '':return
    # script_directory = os.path.dirname(os.path.abspath(__file__))
    # file_path = os.path.join(script_directory, "./venv/Thirdparty", 'natter.py')
    result = subprocess.run([BaseConfig.exe_name, BaseConfig.file_path, '--version'], capture_output=True)
    # print("Standard Output:", result.stdout.decode())
    # print("Standard Error:", result.stderr.decode())
    if result.stdout.decode():
        main_dict['netstatus']["ver"]  =extract_version(result.stdout.decode())

def get_host_local_ip():
    try:
        # 创建一个socket，连接到外部服务器（如Google的公共DNS服务器）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        if s.getsockname()[0] is None:
            main_dict['netstatus']["localhostip"]= ''  # 获取本地IP
        else:
            main_dict['netstatus']["localhostip"]=s.getsockname()[0]
        s.close()  # 关闭socket
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def makecommand(rules_list):
    def is_nested_dict(d):
        return any(isinstance(v, dict) for v in d.values())
    def makecommandsimpleline(rule,protocol):
        cmd_list = []
        for k, v in rule.items():
            if k == 'hostip':
                cmd_list += ['-t', v]
            elif k== 'port':
                cmd_list+=['-p', str(v)]
            elif k== 'upnp' and v==True:
                print(v)
                cmd_list.append('-U')
        if protocol == 'udp':
            cmd_list.append('-u')
        return cmd_list

    if not is_nested_dict(rules_list):
        # print(rules)
        if rules_list.get('protocol') == 'both':
            tcp_list = makecommandsimpleline(rules_list, 'tcp')
            udp_list = makecommandsimpleline(rules_list, 'udp')
            return  [tcp_list, udp_list]
        else:
            return  makecommandsimpleline(rules_list, rules_list['protocol'])

    dic = {}
    enabled_rules = {uuid: rule for uuid, rule in rules_list.items() if rule.get("enabled", False)}
    for uuid, rule in enabled_rules.items():
        print(f"Rule {uuid}: {rule}")
        if rule['protocol'] == 'both':
            tcp_list = makecommandsimpleline(rule, 'tcp')
            udp_list = makecommandsimpleline(rule, 'udp')
            # lists+=[tcp_list,udp_list]
            dic[uuid] = [tcp_list, udp_list]
        else:
            dic[uuid] = makecommandsimpleline(rule, rule['protocol'])
    return dic

def get_internet_ip(public_ip_interfaces):
    for url in public_ip_interfaces:
        try:
            # 发送GET请求
            response = requests.get(url)
            # 根据每个接口的特点处理响应数据
            if url.endswith('/'):
                # 对于返回纯文本的接口
                if response.status_code == 200:
                    public_ip = response.text.strip()
                    main_dict['netstatus']["internetip"] =public_ip
                    return public_ip
            elif url == "http://ip.jsontest.com/":
                # 特别处理 JSON 响应
                if response.status_code == 200:
                    data = response.json()
                    public_ip = data.get('ip')
                    main_dict['netstatus']["internetip"] = public_ip
                    return public_ip
        except requests.RequestException as e:
            return None
    return None
def getstatus(which: str):
    try:
        return main_dict['netstatus'][which]
    except KeyError:
        return "Key not found"
    except TypeError:
        return "Invalid data type"
def setstatus():
    get_natter_version()
    if getstatus("localhostip").strip(): get_host_local_ip()
    if getstatus("internetip") == '': get_internet_ip(BaseConfig.public_ip_interface)

def log_task_add(taskid,*args):
    for task in args:
        taskset=log_task.get(taskid)
        if taskset is None:
            log_task[taskid]= {task}
        else:
            taskset.add(task)
        task.add_done_callback(lambda t: remove_from_log_tasks(t,taskid))
def setup_log_task(process,taskid):
    stdout_queue = asyncio.Queue()
    stderr_queue = asyncio.Queue()
    task1 = asyncio.create_task(process_output(process.stdout, stdout_queue))
    task2 = asyncio.create_task(process_output(process.stderr, stderr_queue))
    log_task_add(taskid,task1,task2)
    return stdout_queue,stderr_queue

#当相关进程被关闭时，取消所有任务
def log_task_cancel(taskid):
    taskset = log_task.get(taskid)
    if taskset is None:return
    for task in taskset:
        task.cancel()
    del log_task[taskid]

def print_status_and_logs():
    print("Task Status: ", task_status)
    print("Logs Dictionary: ")
    for key, value in logs_dict.items():
        print(f"  {key}: {value}")

#之所以搞个函数套壳是因为@app.get这个用法在外部运行app是Nonetype会引起错误
def bind_all_router():
    # @app.get("/testpoint")
    # async def test_point():
    #     keys = list(task_status.keys())
    #     select = random.choice(keys)
    #     print(f"new" + task_status[select].get('natmap'))
    #     task_status[select]['natmap'] = f"testpoint change test{random.uniform(0, 10)}"
    #     return {"message": f"任务id{select}被改变了"}
    @app.get("/favicon.ico")
    async def get_favicon():
        return FileResponse(get_resource_path("static/favicon.ico"))

    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request,x_update_content: str = Header(None)):
        setstatus()
        # print(task_status)
        #print(logs_dict)
        if x_update_content:
            print ("receive x-update-content")
            return templates.TemplateResponse("status_content.html", {"request": request, "main_dict": main_dict})
        else:

            return templates.TemplateResponse("status.html", {"request": request, "main_dict": main_dict})

    @app.post("/updatenattype")
    async def updatenattype(request: Request,background_tasks: BackgroundTasks):
        def value_or_loading(val):
            # 如果val等于-1，返回'loading'，否则返回val本身
            return 'loading' if val == '-1' else val

        # lock = asyncio.Lock()
        referer = request.headers.get("referer")
        if not referer:
            return JSONResponse(status_code=400, content={"message": "请求无效"})
        if referer.endswith('/') or referer.endswith('manager'):
            task = get_tasks_with_function(task_status, 'get_tcpudpnat1')
            running_tasks = any(value['status'] == 'Running' for key, value in task.items())
            if task_status.get('checknat'):
                running_tasks = True if task_status.get('checknat').get('status') == 'Running' else False
            else:
                running_tasks = False
            # async with lock:
            #     print(task_status)
            if (getstatus("tcpnat").find('-') == -1 or getstatus("udpnat").find('-') != -1) and not running_tasks:
                # task = asyncio.create_task(get_tcpudpnat1(task_id='checknat'))#这个库调用函数要改函数本身为异步函数，需要增加异步的处理逻辑，能用，但是写相关代码麻烦，毕竟这里只需要把这个func丢给另一个线程处理就不用管了。
                # background_tasks.add_task(get_tcpudpnat,task_id='checknat')
                #background_tasks.add_task(foo,"test",task_id='checknat')
                background_tasks.add_task(checknat,task_id='checknat')
                pass
            else:
                pass
                # print('正在检查nat type，请稍等...')
            return {"tcpnat":value_or_loading(getstatus("tcpnat")),"udpnat":value_or_loading(getstatus("udpnat"))}
        else:
            # 如果referer不存在，你可以选择返回默认模板或处理逻辑
            return JSONResponse(status_code=400, content={"message": "请求无效"})
    @app.post("/run")
    async def run_endpoint(background_tasks: BackgroundTasks):
        rule_keys = list(k for k, v in rules.items() if v.get('enabled'))

        not_found_keys = list(key for key in rule_keys if
                              not any(v.get('rule_id') == key for k, v in task_status.items()))
        if len(rule_keys)==len(not_found_keys):
            background_tasks.add_task(run_natter_mutiprogracess)
            return JSONResponse(status_code=200, content={"message": "未找到任何正在运行规则，直接启动所有启用规则"})
        elif len(not_found_keys)>0 :
            for rule_id in not_found_keys:
                background_tasks.add_task(launch_simple_rule, rule_id)
            return JSONResponse(status_code=200, content={"message": "已经启动部分未正常运行规则"})
        else:
            return JSONResponse(status_code=200, content={"message": "所有规则正常运行，无须操作"})

    #从规则中找到已经启用的规则，并查看是否启动，如果没有，则启动。
        # for key in rule_keys_iter:
        #     for k,v in task_status.items():
        #         if v.get('rule_id')==key:
        #             print(v)

        # print(task_status)
        # try:

            # await asyncio.gather(*tasks)
            # return {"status": "success"}
        # except Exception as e:
        #     # 如果发生任何错误，抛出HTTPException
        #     raise HTTPException(status_code=500, detail=str(e))
    @app.post("/stop_all")
    async def stop_endpoint():
        del_id_list=[]
        for id,v in task_status.items():
            process = v.get('process')
            process.terminate()
            await process.wait()
            log_task_cancel(id)
            # print("after_process_terminate", othertasks)
            del_id_list.append(id)
        for id in del_id_list:
            del task_status[id]
        if len(task_status)==0:
            return JSONResponse(status_code=200, content={"message": "已经结束所有Natter.py进程"})
    @app.get("/manager", response_class=HTMLResponse)
    async def manager(request: Request,x_update_content: str = Header(None)):
        print(request.headers)
        setstatus()
        if x_update_content:
            print(main_dict)
            return templates.TemplateResponse("manager_content.html", {"request": request, "main_dict": main_dict})
        else:
            return templates.TemplateResponse("manager.html", {"request": request, "main_dict": main_dict})


    @app.get("/about", response_class=HTMLResponse)
    async def about(request: Request,x_update_content: str = Header(None)):
        user_agent = request.headers.get("User-Agent")
        print(user_agent)  # 在控制台打印用户代理
        if x_update_content:
            print("receive x-update-content")
            return templates.TemplateResponse("about_content.html", {"request": request, "main_dict": main_dict})
        else:
            return templates.TemplateResponse("about.html", {"request": request, "main_dict": main_dict})


    @app.post("/add_rule/")
    async def add_rule(rule: Rule,background_tasks: BackgroundTasks):
        def check_duplicate(newrule):
            lookup = {(v['hostip'], v['port'], v['protocol']): k for k, v in rules.items()}
            for hostip, port, protocol in lookup:
                if newrule.hostip == hostip and newrule.port == port:
                    if newrule.protocol == protocol:
                        return True
                    if newrule.protocol == 'both' or protocol == 'both':
                        return True
            return False
        if check_duplicate(rule):
            raise ValueError("规则已存在，不能添加重复规则")
        else:
            rule_id = str(uuid.uuid4())
            rules[rule_id] = rule.model_dump()
            #新规则，要看是否规则是否启用，如果启用，那么直接启动natter.py进程
            background_tasks.add_task(launch_simple_rule,rule_id)
            await save_to_json_async(rules, 'rules.json')
        # print(rules)
        return {"rule_id": rule_id, "rule": rule.model_dump()}

    @app.post("/delete_rule/")
    async def delete_rule(rule_id: Ruleid):
        deleteid=rule_id.id
        # 删除规则，但是发现进程正在运行
        taskid = lookup_taskstatus(rule_id.id)
        if taskid :
            for id in taskid:
                print("before_process_terminate", othertasks)
                process = task_status.get(id).get('process')
                process.terminate()
                await process.wait()
                log_task_cancel(id)
                print("after_process_terminate",othertasks)
                del task_status[id]

        value=rules.pop(deleteid, '不成功')
        value_str = json.dumps(value, ensure_ascii=False).replace('"', '')
        print('删除' + value_str)
        if not ('不成功' in value_str):
            await save_to_json_async(rules, 'rules.json')
            return {"message": "删除成功","rule":value_str}
        return {"message": "删除失败"}

    @app.post("/edit_rule/")
    async def edit_rule(rule_data: Rulemodify,background_tasks: BackgroundTasks):
        def check_duplicate(rule_data):
            # filtered_rules = {}
            for rule_id, rule in rules.items():
                # 如果有enabled过滤条件，检查是否满足
                if rule_data.id==rule_id:
                    continue
                else:
                    if rule_data.hostip == rule['hostip'] and rule_data.port == rule['port']:
                        if rule_data.protocol == rule['protocol']:
                            return True
                        if rule_data.protocol == 'both' or rule['protocol'] == 'both':
                            return True
            return False
        print(rule_data)
        if check_duplicate(rule_data):
            raise ValueError("规则已存在，不能修改为重复的规则")
        else:
            editrule={'rulename' : rule_data.rulename,'hostip' : rule_data.hostip,
                  'protocol':rule_data.protocol,'port' : rule_data.port,
                  'upnp':rule_data.upnp,'enabled' : rule_data.enabled}
            rules[rule_data.id]=editrule
            ##判断启用规则还是停用规则
            taskid=lookup_taskstatus(rule_data.id)

            if rules[rule_data.id].get('enabled') and not taskid:
                #启用规则，但是没有找到任务正在运行
                cmdlist = makecommand(rules[rule_data.id])
                print(cmdlist)
                background_tasks.add_task(launch_simple_rule,rule_data.id)
            elif not rules[rule_data.id].get('enabled') and taskid:
                #停用规则，但是发现进程正在运行
                for id in taskid:
                    process = task_status.get(id).get('process')
                    print(process)
                    process.terminate()
                    await process.wait()
                    log_task_cancel(id)
                    print ('taskid',id)
                    del task_status[id]
                    print(task_status)
            await save_to_json_async(rules, 'rules.json')
            return {"message": "规则更新成功", "data": rule_data}

    @app.get("/testrouter")
    async def test_point():
        global num
        task_status['test1']=num
        num+=1
        print("task_status in appfile:"+str(id(task_status)))
        return {"message:taskchanged"}




class ExitException(Exception):
    pass

class Plugin:
    #寻找插件子应用的templates路径
    @staticmethod
    def find_temp_filefold(root_path):
        temp_list=[]
        for root, dirs, files in os.walk(root_path):
            split_path = root.split(os.sep)
            if split_path.count("templates")>=1:
                path=os.path.join(root)
                temp_list.append(path)
        return temp_list

    #寻找插件子应用的PY文件。
    @staticmethod
    def find_py_files(root_path):
        py_files = []
        root_path=get_resource_path(root_path)
        # print(root_path)
        for root, dirs, files in os.walk(root_path):
            # print("root:"+root)
            if root.count(os.sep) - root_path.count(os.sep) == 1:
                for file in files:
                    if file.endswith('.py') and file!= '__init__.py':
                        py_files.append(os.path.join(root, file))
        return py_files
    #导入插件时应该检查一下是否存在导入主程序py，如果存在，则不加载插件，否则可能代码重复执行两次可能引起功能异常。
    @staticmethod
    def check_import(module_name, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == module_name:
                    print("存在循环导入，模块名为："+node.module)
                    return True
        return False
    #自动依据目录生成插件配置字符如'plugin.notification.pg'
    @staticmethod
    def detect_plugin():
        py_files = Plugin.find_py_files( "./plugin")
        # print(py_files)
        py_files_no_loop_import=[]
        for py in py_files:
            if not Plugin.check_import('app',py):
                py_files_no_loop_import.append(py)
            else:
                print("发现"+py+"插件存在循环导入主程序，所以不加载此插件")
        nonedot_py_files=[s.replace('.py','').replace('.', '') for s in py_files_no_loop_import]
        plugin_list = []
        for py_file in nonedot_py_files:
            parts = py_file.split(os.sep)
            plugin_name_parts = []
            for part in parts:
                if part.endswith('.py'):
                    part = part[: -3]
                if part:
                    plugin_name_parts.append(part)
            plugin_name = '.'.join(plugin_name_parts[-3::])
            print("plugin_name:"+plugin_name)
            plugin_list.append(plugin_name)
        return plugin_list

    @staticmethod
    def add_plugin_nav_item(plugin_obj:module):
        global main_dict
        list=main_dict['nav_items']
        list.append(plugin_obj.BaseConfig.nav)
        print(main_dict)

    @staticmethod
    def safe_import(module_name):
        try:
            # 先尝试常规导入
            return importlib.import_module(module_name)
        except ImportError:
            if getattr(sys, 'frozen', False):
                # 打包环境下转换模块路径为文件路径
                module_path = os.path.join(
                    sys._MEIPASS,
                    *module_name.split('.')
                ) + '.py'
                # 动态加载模块
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None:
                    raise ImportError(f"无法创建模块规范: {module_path}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
            raise  # 非打包环境直接抛出原异常

    @classmethod
    def load_plugin(cls,plugin_name):
        try:
            module = Plugin.safe_import(plugin_name)
            # print(module)
            pg = getattr(module, 'pg')
            # for a in pg.routes:
            #     print(a.path)
            print(module.BaseConfig.nav)
            Plugin.add_plugin_nav_item(module)
            # print(type(module))
            return pg
        except (ModuleNotFoundError, AttributeError) as e:
            print(f"Error: {e}")
    @classmethod
    def load_all_plugin(cls):
        plugin_list=Plugin.detect_plugin()
        for p in plugin_list:

            plugin = cls.load_plugin(p)
            # print(plugin.router)
            app.mount("/plugin",plugin)
        #包括路由的方式难以以非侵入的方法挂载静态文件，目前没找到方法，只能使用独立fastapi子应用。
        # app.include_router(plugin.router, prefix="/plugin")
    @classmethod
    def testload(cls):
        plugin = cls.load_plugin('plugin.notification.pg')
        # plugin = cls.load_plugin('plugin.test')
def get_task_status():
    return task_status


def main():
    env_path={"程序名":BaseConfig.exe_name,"程序路径":BaseConfig.exe_path,"natter脚本路径":BaseConfig.file_path,"check脚本路径":BaseConfig.file_path2}
    print(env_path)
    parser = argparse.ArgumentParser(
        description='A WEB GUI for Natter(Expose your port behind full-cone NAT to the Internet.)')
    parser.add_argument("--version", "-V", action="version", version="Natter Web %s" % BaseConfig.__version__,
                        help="show the version of Natter web")
    parser.add_argument("-r", action='store_true',
                        help="run enabled natter rules when started")
    parser.add_argument(
        "-t", type=str, metavar="<address>", default="0.0.0.0",
        help="IP address of listen"
    )
    parser.add_argument(
        "-p", type=int, metavar="<port>", default=18650,
        help="port number of listen"
    )
    init_vars()
    args = parser.parse_args()
    start = args.r
    host=args.t
    port=args.p
    bind_all_router()

    def run_server():
        if start:
            task=asyncio.create_task(run_natter_mutiprogracess())
            othertasks.add(task)
            task.add_done_callback(lambda t: remove_from_running_tasks(t))

        # print(Plugin.find_py_files("./plugin"))
        # print(Plugin.detect_plugin())
        Plugin.load_all_plugin()
        # print(Plugin.find_temp_filefold("./plugin"))
        # Plugin.testload()

        # server = erver(config)
        #server.run()
        # server.serve()
        return host,port
        # app.run()
    # try:
    #     #有问题会执行两次app.py脚本
    #     # asyncio.run(run_server())
    return run_server()
    # except (ExitException, KeyboardInterrupt):
    #     sys.exit()
def check_exists_thirdparty_get_natter_from_github():
    zip_path = './venv/Thirdparty/natter.zip'
    save_path = './venv/Thirdparty/'
    need_file = ['natter.py', 'natter-check.py']
    # initfile = '__init__.py'
    def check_and_create_directory():
        if not os.path.exists(save_path):
            os.makedirs(save_path)
    def download_zipfile():
        response = requests.get("https://api.github.com/repos/MikeWang000000/Natter/releases")
        if response.status_code == 200:
            release_info = response.json()
            latest_release_download_url = release_info[0]["zipball_url"]
            if latest_release_download_url:
                my_file=requests.get(latest_release_download_url)
                open("./venv/Thirdparty/natter.zip",'wb').write(my_file.content)
    def extract_need_file():
        # 创建ZipFile对象
        file = zipfile.ZipFile(zip_path, 'r')
        with zipfile.ZipFile(zip_path) as zip_file:
            members_to_extract = []
            for member in zip_file.namelist():
                filename = os.path.basename(member)
                # skip directories
                if not filename:
                    continue
                for filename in need_file:
                    if member.find(filename) >= 0:
                        source = zip_file.open(member)
                        target = open(os.path.join(save_path, filename), "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)

    check_and_create_directory()
    #确保savepath目录存在
    download_zipfile()
    #从github下载natter.zip
    if os.path.exists(zip_path):
        extract_need_file()
    #解压natter.py和natter-check.py
    #open(os.path.join(save_path, initfile), "wb")
    #因为调用方法不是直接引入python文件，所以现在不用__init__.py

def create_directory(directory_path):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"目录 {directory_path} 创建成功")
        except OSError as e:
            print(f"创建目录 {directory_path} 时出错: {e}")
    else:
        print(f"目录 {directory_path} 已经存在")
    

if __name__ == "__main__":
    global rules
    global main_dict
    global templates
    global app
    global othertasks
    global log_task
    global task_status
    global netstatus
    global logs_dict
    num = 1
    create_directory("./logs")
    try:
        if not (os.path.exists('./venv/Thirdparty/natter.py') and os.path.exists('./venv/Thirdparty/natter-check.py')):
            check_exists_thirdparty_get_natter_from_github()
        host,port =main()
        uvicorn.run(app,host=host,port=port)
        # uvicorn.run(app, host="127.0.0.1", port=8001)
        pass
    except Exception as e:
        raise e
    finally:
        pass
        #输出所有任务是否全部取消，若没有取消会有报错信息.
        # print(othertasks)
        # print(log_task)
    #print(args.accumulate(args.integers))

