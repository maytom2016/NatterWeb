import sys
sys.path.append('./venv/Thirdparty')
module = __import__("natter-check")
natter = __import__("natter")
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







