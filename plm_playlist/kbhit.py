# import os
# import re
import sys
import time

import termios
import atexit
from select import select

from queue import Queue
from threading import Thread


key_queue = Queue()
exit_keys = ("q", "й", "Й")


class KBHit:
    def __init__(self):
        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)

        # New terminal setting unbuffered
        self.new_term[3] = (
            self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(
            self.fd, termios.TCSAFLUSH, self.new_term)

        # Support normal-terminal reset at exit
        atexit.register(self.set_normal_term)

    def set_normal_term(self):
        termios.tcsetattr(
            self.fd, termios.TCSAFLUSH, self.old_term)

    def getch(self):
        return sys.stdin.read(1)

    def kbhit(self):
        dr, dw, de = select([sys.stdin], [], [], 0)
        return dr != []


def getkeys(key_queue: Queue):
    kb = KBHit()
    kbrun = 1
    while kbrun:
        if (kb.kbhit()):
            c_id = 0
            while ((c := kb.getch()) is not None):
                c_id += 1
                key_queue.put(c)
                if (c in exit_keys):
                    key_queue.put('Exit')
                    kbrun = 0
                    break
        time.sleep(0.1)
    print("Exiting getkeys thread        ")
    kb.set_normal_term()


def start():
    global key_thread
    try:
        if (key_thread.is_alive()):
            return
    except NameError:
        ...

    try:
        key_thread = Thread(target=getkeys, args=(key_queue,))
        key_thread.start()
    except RuntimeError:
        print(f"Kbhit error: {sys.exc_info()}")
        print("Possible cause: key_thread already started")
