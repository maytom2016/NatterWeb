#任务字典，记录获取NAT类型的协程和natter.py子进程相关信息。
global task_status
global rules
global main_dict
global templates
def init():
    global task_status
    global rules
    global main_dict
    global templates
    templates=None
    rules = {}
    main_dict = {}
    task_status= dict()
    # print("empty task status")