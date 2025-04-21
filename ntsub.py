import sys
sys.path.append('./venv/Thirdparty')
import venv.Thirdparty.natter as natter
module = __import__("natter-check")
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







