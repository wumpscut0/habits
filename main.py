import subprocess

if __name__ == '__main__':
    subprocess.Popen("python ./backend/main.py", shell=True)
    subprocess.run("python ./frontend/main.py", shell=True)
