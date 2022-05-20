import os
import subprocess
from time import sleep
from server import Server


def handle_os_error():
    result = subprocess.check_output("netstat -ano|findstr 2508", shell=True).decode()
    result = result[71:].strip()

    os.system(f"tskill {result}")


def main():
    try:
        Server()
    except OSError:
        handle_os_error()
        sleep(2)
        Server()


if __name__ == "__main__":
    main()
