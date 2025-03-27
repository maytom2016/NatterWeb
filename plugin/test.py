import ast

var1=None
dict=None
nav_items=None

def gltest():
    global var1
    var1=121
    global dict
    dict={"1":"2"}
    global nav_items
    nav_items = [
        {"name": "状态", "url": "/", "icon": "bi bi-card-list"},
        {"name": "映射管理", "url": "/manager", "icon": "bi bi-command"},
        {"name": "关于", "url": "/about", "icon": "fa fa-heart"},
    ]

def check_import(module_name, file_path):
    with open(file_path, 'r') as f:
        source = f.read()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                print(alias.name)
                if alias.name == module_name:
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == module_name:
                print(node.module)
                return True
    return False

gltest()
print(var1)
print(dict)
print(nav_items)

# 假设当前模块名为'my_module'，要检查的文件为'target_file.py'
result = check_import('app', './notification/pg.py')
print(result)

