#!/usr/bin/env python3
"""
增强版路径适配脚本
新增功能：
1. 识别并处理 Starlette/FastAPI 的 StaticFiles 挂载
2. 处理自定义的路径查找函数（如 find_temp_filefold）
3. 支持更多动态路径模式
"""

import os
import sys
import re
import ast
from pathlib import Path
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('PathAdapter')

# 需要处理的文件列表
TARGET_FILES = ["app.py", "plugin/notification/pg.py"]

class PathTransformer(ast.NodeTransformer):
    """AST 节点转换器，用于深度分析代码结构"""
    
    def __init__(self):
        self.changed = False
    
    def visit_Call(self, node):
        # 处理 StaticFiles(directory="static") 模式
        if (isinstance(node.func, ast.Name) and node.func.id == 'StaticFiles':
            for kw in node.keywords:
                if kw.arg == 'directory' and isinstance(kw.value, ast.Str):
                    new_value = ast.Call(
                        func=ast.Name(id='str', ctx=ast.Load()),
                        args=[
                            ast.BinOp(
                                left=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id='Path', ctx=ast.Load()),
                                        attr='joinpath',
                                        ctx=ast.Load()
                                    ),
                                    args=[
                                        ast.Call(
                                            func=ast.Name(id='get_resource_base', ctx=ast.Load()),
                                            args=[],
                                            keywords=[]
                                        ),
                                        ast.Str(s=kw.value.s)
                                    ],
                                    keywords=[]
                                ),
                                op=ast.Div(),
                                right=ast.Str(s='')
                            )
                        ],
                        keywords=[]
                    )
                    kw.value = new_value
                    self.changed = True
        
        # 处理 find_temp_filefold("./plugin") 模式
        if (isinstance(node.func, ast.Attribute) and 
            node.func.attr == 'find_temp_filefold' and 
            len(node.args) > 0 and 
            isinstance(node.args[0], ast.Str)):
            node.args[0] = ast.Call(
                func=ast.Name(id='get_resource_path', ctx=ast.Load()),
                args=[ast.Str(s=node.args[0].s)],
                keywords=[]
            )
            self.changed = True
        
        return self.generic_visit(node)

def get_resource_base():
    """获取基础路径（兼容打包环境）"""
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent

def get_resource_path(relative_path):
    """通用路径获取函数"""
    base = get_resource_base()
    return str(base / relative_path)

def add_imports(code):
    """确保必要的导入语句存在"""
    imports = [
        "from pathlib import Path",
        "import sys",
        "import os",
        f"from {__name__} import get_resource_base, get_resource_path"
    ]
    
    # 检查是否已存在这些导入
    for imp in imports[:2]:
        if imp.split(' import ')[0] in code:
            imports.remove(imp)
    
    if imports:
        return "\n".join(imports) + "\n\n" + code
    return code

def process_file(file_path):
    """处理单个文件"""
    orig_path = Path(file_path)
    backup_path = orig_path.with_suffix(f"{orig_path.suffix}.bak")
    
    logger.info(f"🔧 处理文件: {file_path}")
    logger.info(f"  打包环境: {'是' if getattr(sys, 'frozen', False) else '否'}")
    logger.info(f"  基准路径: {get_resource_base()}")

    # 创建备份
    shutil.copy(file_path, backup_path)
    logger.info(f"  已创建备份: {backup_path}")

    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        
        # 使用AST进行精确修改
        try:
            tree = ast.parse(content)
            transformer = PathTransformer()
            new_tree = transformer.visit(tree)
            
            if transformer.changed:
                # 添加必要的导入
                new_content = add_imports(ast.unparse(new_tree))
                
                # 格式化代码（可选）
                try:
                    import autopep8
                    new_content = autopep8.fix_code(new_content)
                except ImportError:
                    pass
                
                # 写回文件
                f.seek(0)
                f.write(new_content)
                f.truncate()
                logger.info("  ✅ 已适配路径（AST模式）")
            else:
                logger.info("  ℹ️ 无需修改（AST模式）")
        except Exception as e:
            logger.error(f"  ❌ AST解析失败，使用正则回退: {str(e)}")
            # AST失败时使用正则回退
            adapted = adapt_path_with_regex(content)
            if adapted != content:
                f.seek(0)
                f.write(add_imports(adapted))
                f.truncate()
                logger.info("  ✅ 已适配路径（正则模式）")
            else:
                logger.info("  ℹ️ 无需修改（正则模式）")

def adapt_path_with_regex(content):
    """正则表达式回退方案"""
    # 处理 StaticFiles(directory="static")
    pattern1 = re.compile(
        r'StaticFiles\(.*?directory\s*=\s*([\'"])(\.?/?[^\'"]+)\1',
        re.DOTALL
    )
    replacement1 = rf'StaticFiles(directory=get_resource_path(\1\2\1)'
    
    # 处理 find_temp_filefold("./plugin")
    pattern2 = re.compile(
        r'(\.find_temp_filefold\s*\(\s*)([\'"])(\.?/?[^\'"]+)\2',
        re.DOTALL
    )
    replacement2 = rf'\1get_resource_path(\2\3\2)'
    
    content = pattern1.sub(replacement1, content)
    content = pattern2.sub(replacement2, content)
    
    return content

def main():
    logger.info("🛠️ 增强版路径适配器启动")
    logger.info(f"工作目录: {os.getcwd()}")
    
    for file in TARGET_FILES:
        if Path(file).exists():
            process_file(file)
        else:
            logger.warning(f"⚠️ 文件不存在: {file}")

    logger.info("\n✨ 操作完成！以下是您需要使用的路径函数模板：")
    print("\n# 请将以下函数复制到您的主模块中：")
    print("""
# ---- 路径处理函数 ----
from pathlib import Path
import sys
import os

def get_resource_base():
    \"\"\"获取基础路径（兼容打包环境）\"\"\"
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent

def get_resource_path(relative_path):
    \"\"\"通用路径获取函数\"\"\"
    return str(get_resource_base() / relative_path)
# ---------------------
""")

if __name__ == '__main__':
    main()
