#!/usr/bin/env python3
"""
GitHub Actions 路径自适应脚本
功能：
1. 自动识别 PyInstaller 打包环境
2. 修改代码中的资源路径引用
3. 生成备份文件便于调试
"""

import os
import sys
import re
from pathlib import Path
import shutil

# 需要处理的文件列表
TARGET_FILES = ["app.py", "plugin/notification/pg.py"]

def is_frozen():
    """检查是否在打包环境中运行"""
    return getattr(sys, 'frozen', False)

def get_base_path():
    """获取正确的基准路径"""
    return Path(sys._MEIPASS) if is_frozen() else Path(__file__).parent.parent

def adapt_path(code_content):
    """
    替换代码中的路径引用为自适应版本
    处理以下常见模式：
    1. open('static/file') -> 自适应路径
    2. Path(__file__).parent / 'data' -> 自适应路径
    3. os.path.join(os.path.dirname(__file__), ...) -> 自适应路径
    """
    # 模式1：直接路径字符串
    pattern1 = re.compile(r'(open|Path)\(([\'"])(\.?/)?(static|templates|plugin)/')
    replacement1 = rf'\1(\2{get_base_path()}/\4/'
    
    # 模式2：__file__ 相对路径
    pattern2 = re.compile(
        r'(Path\(__file__\)\.parent\s*[/\\]\s*[\'"]|'
        r'os\.path\.join\(os\.path\.dirname\(__file__\),\s*[\'"])'
    )
    replacement2 = f'Path(r"{get_base_path()}").joinpath('

    # 模式3：importlib 动态导入
    pattern3 = re.compile(r'importlib\.(?:util\.)?spec_from_file_location\(.*?__file__.*?,')
    replacement3 = f'importlib.util.spec_from_file_location(name, str(Path(r"{get_base_path()}") /'

    code_content = pattern1.sub(replacement1, code_content)
    code_content = pattern2.sub(replacement2, code_content)
    code_content = pattern3.sub(replacement3, code_content)
    
    return code_content

def process_file(file_path):
    """处理单个文件"""
    orig_path = Path(file_path)
    backup_path = orig_path.with_suffix(f"{orig_path.suffix}.bak")
    
    print(f"🔧 处理文件: {file_path}")
    print(f"  打包环境: {'是' if is_frozen() else '否'}")
    print(f"  基准路径: {get_base_path()}")

    # 创建备份
    shutil.copy(file_path, backup_path)
    print(f"  已创建备份: {backup_path}")

    # 修改文件
    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        adapted = adapt_path(content)
        
        if adapted != content:
            f.seek(0)
            f.write(adapted)
            f.truncate()
            print("  ✅ 已适配路径")
        else:
            print("  ℹ️ 无需修改")

def main():
    print("🛠️ GitHub Actions 路径适配器启动")
    print(f"工作目录: {os.getcwd()}")
    
    for file in TARGET_FILES:
        if Path(file).exists():
            process_file(file)
        else:
            print(f"⚠️ 文件不存在: {file}")

    print("\n✨ 操作完成！")
    if is_frozen():
        print("提示：当前运行在打包环境中，所有路径已指向 sys._MEIPASS")

if __name__ == '__main__':
    main()
