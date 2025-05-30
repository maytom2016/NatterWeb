import sys
sys.path.append('./venv/Thirdparty')
import venv.Thirdparty.natter as natter
module = __import__("natter-check")
# module_name =
# module_name ="natter"
# sys.argv = ["","--v"]
# with open("./venv/Thirdparty/natter.py") as f:
#     exec(f.read())
# original_argv = sys.argv.copy()
check=False
nt=False
for arg in sys.argv[1:]:
    if 'natter-check' in arg:
        sys.argv.remove(arg)
        check=True
    if 'natter.py' in arg:
        sys.argv.remove(arg)
        nt = True
if(check):
    module.main()
if(nt):
    natter.main()



# elif(sys.argv.__contains__('./venv/Thirdparty/natter.py')):
#     sys.argv.remove("./venv/Thirdparty/natter.py")
# print(sys.argv)
#
# 恢复原始命令行参数（可选）
# sys.argv = original_argv






