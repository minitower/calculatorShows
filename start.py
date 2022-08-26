import os
import subprocess

def start():
    path = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault('PROJECT_PATH', path)
    p = subprocess.Popen(['./init/Scripts/pythonw.exe', '-m', 
                                'waitress-serve', 'server:app'], 
                         shell=True)
    

if __name__ == "__main__":
    start()