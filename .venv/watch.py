from watchfiles import run_process

def run_script():
    run_process('.', target='python3 web.py')  # Watch the current directory

if __name__ == '__main__':
    run_script()
