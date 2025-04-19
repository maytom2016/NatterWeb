#!/usr/bin/env python3
"""
增强版路径适配脚本
修复版本主要修改：
1. 修复 AST 转换器中的条件判断语法错误
2. 增强正则表达式匹配模式
3. 优化导入语句处理逻辑
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
    """AST 节点转换器（修复条件判断语法）"""

    def __init__(self):
        self.changed = False

    def visit_Call(self, node):
        # 修复：添加缺失的冒号和完善条件判断
        if (isinstance(node.func, ast.Name)
                and node.func.id == 'StaticFiles'):
            for kw in node.keywords:
                if (kw.arg == 'directory'
                        and isinstance(kw.value, ast.Constant)):
                    new_value = ast.Call(
                        func=ast.Name(id='str', ctx=ast.Load()),
                        args=[
                            ast.BinOp(
                                left=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Call(
                                            func=ast.Name(id='get_resource_base', ctx=ast.Load()),
                                            args=[],
                                            keywords=[]
                                        ),
                                        attr='joinpath',
                                        ctx=ast.Load()
                                    ),
                                    args=[ast.Constant(value=kw.value.value)],
                                    keywords=[]
                                ),
                                op=ast.Div(),
                                right=ast.Constant(value='')
                            )
                        ],
                        keywords=[]
                    )
                    kw.value = new_value
                    self.changed = True

        # 修复：增加方法调用者的类型检查
        if (isinstance(node.func, ast.Attribute)
                and node.func.attr == 'find_temp_filefold'
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'Plugin'
                and node.args
                and isinstance(node.args, ast.Constant)):
            node.args = ast.Call(
                func=ast.Name(id='get_resource_path', ctx=ast.Load()),
                args=[ast.Constant(value=node.args.value)],
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
    """智能添加导入语句"""
    required_imports = {
        'Path': 'from pathlib import Path',
        'sys': 'import sys',
        'os': 'import os',
        'get_resource': f'from {__name__} import get_resource_base, get_resource_path'
    }

    # 检查现有导入
    existing = set()
    for line in code.split('\n'):
        if 'import' in line:
            for key in required_imports:
                if required_imports[key].split(' import ') in line:
                    existing.add(key)

    # 生成需要添加的导入
    missing = [required_imports[k] for k in required_imports if k not in existing]
    return '\n'.join(missing) + '\n\n' + code if missing else code


def process_file(file_path):
    """修复：使用更安全的文件写入方式"""
    orig_path = Path(file_path)
    backup_path = orig_path.with_suffix(f"{orig_path.suffix}.bak")

    logger.info(f"🔧 处理文件: {file_path}")

    try:
        # 读取原始内容
        content = orig_path.read_text(encoding='utf-8')

        # 创建备份
        shutil.copy(file_path, backup_path)
        logger.info(f"  已创建备份: {backup_path}")

        # AST 转换
        try:
            tree = ast.parse(content)
            transformer = PathTransformer()
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)

            if transformer.changed:
                new_content = ast.unparse(new_tree)
                new_content = add_imports(new_content)

                # 格式化代码
                try:
                    from black import format_str, FileMode
                    new_content = format_str(new_content, mode=FileMode())
                except ImportError:
                    pass

                # 安全写入
                orig_path.write_text(new_content, encoding='utf-8')
                logger.info("  ✅ 已适配路径（AST模式）")
            else:
                logger.info("  ℹ️ 无需修改（AST模式）")

        except Exception as e:
            logger.error(f"  ❌ AST解析失败，使用正则回退: {str(e)}")
            adapted = adapt_path_with_regex(content)
            if adapted != content:
                orig_path.write_text(add_imports(adapted), encoding='utf-8')
                logger.info("  ✅ 已适配路径（正则模式）")
            else:
                logger.info("  ℹ️ 无需修改（正则模式）")

    except Exception as e:
        logger.error(f"  🚨 文件处理失败: {str(e)}")


def adapt_path_with_regex(content):
    """增强版正则表达式处理"""
    # 处理 StaticFiles(directory=...) 模式
    patterns = [
        # 匹配带 directory 参数的 StaticFiles 调用
        (r'(StaticFiles\s*\(\s*.*?directory\s*=\s*)(["\'])(\.?/?[^"\']+)\2',
         r'\1get_resource_path(\2\3\2)'),

        # 处理 Plugin.find_temp_filefold(...)
        (r'(\.find_temp_filefold\s*\(\s*)(["\'])(\.?/?[^"\']+)\2',
         r'\1get_resource_path(\2\3\2)')
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    return content


def main():
    logger.info("🛠️ 增强版路径适配器启动")
    logger.info(f"工作目录: {os.getcwd()}")

    for file in TARGET_FILES:
        if Path(file).exists():
            process_file(file)
        else:
            logger.warning(f"⚠️ 文件不存在: {file}")

    # 显示使用示例
    logger.info("\n✨ 操作完成！示例修改结果：")
    print("原始代码 -> 修改后代码".center(50, '-'))
    print(f"StaticFiles(directory='static') -> StaticFiles(directory=get_resource_path('static'))")
    print(f"Plugin.find_temp_filefold('./plugin') -> Plugin.find_temp_filefold(get_resource_path('./plugin'))")


if __name__ == '__main__':
    main()
