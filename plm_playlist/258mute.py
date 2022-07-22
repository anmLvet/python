#!/usr/bin/python3
import os
import re
import sys
import time

from threading import Thread
from time import strftime

# required from kbhit.py in the same directory
import kbhit

# 0.find working directory
pll_dir = '~/.plm'

# bell settings
bells = {'bell_work': '258_work.mp3',
         'bell_rest': '258_rest.mp3',
         'bell_add': '258_add.mp3',
         'bell_chime': '258_chime.mp3'}

bin_dir = os.path.dirname(__file__)
config_file = os.path.join(bin_dir, 'plm_playlists.config')
if (os.path.isfile(config_file)):
    with open(config_file) as config:
        for cfg_line in config:
            if (cfg_line.startswith('pll_dir')):
                pll_dir = cfg_line[7:].strip() + "/"
            elif (cfg_line.startswith('bell')):
                for bell_name in bells.keys():
                    if (cfg_line.startswith(bell_name)):
                        bells[bell_name] = cfg_line.replace(bell_name, "")\
                            .strip()

pll_dir = os.path.expanduser(pll_dir)

try:
    os.makedirs(pll_dir)
except FileExistsError:
    ...

# 220709 - removing references to 258.pid file
# pid_258_file = pll_dir + '258.pid'
# 220509 - new file with pids
pid_mode_file = pll_dir + 'period_play.pid'


MPL_RE = re.compile(r"mplayer\d*,(?P<cpid>\d+)\D.*scaletempo")
SID_RE = re.compile(r"\s*index:\s*(?P<sink_id>\d+)(\D.*|)$")
SPID_RE = re.compile(r"\s*application.process.id\s*=\s*\"(?P<spid>\d+)\"")
APPNAME_RE = re.compile(r"\s*application.name\s*=\s*\"(?P<appname>.+)\"")

# domute = sys.argv[1] if len(sys.argv) > 1 else ''

sids = []
stored_unmutes = []


# stage length settings
def get_number_arg(index, def_value):
    if len(sys.argv) <= index:
        return def_value
    try:
        return int(sys.argv[index])
    except Exception:
        return def_value


work_period = get_number_arg(1, 1500)
rest_period = get_number_arg(2, 480)
add_period = get_number_arg(3, 0)

# kbhit settings
# 220421 - упаковали kbhit
kbhit.exit_keys = ("q", "Q", "й", "Й")

ADDTIME_KEYS = ("s", "S", "ы", "Ы", "і", "І")
SUBTIME_KEYS = ("d", "D", "в", "В")

start = 0
current = 0
is_stopped = 0

debug = 0


def debug_msg(msg, level):
    if (debug > level):
        print(f"Debug: {msg}")


# 220520 Started adding logging'''
class Log258:
    def __init__(self):
        self.log_file = pll_dir + '258.log'
        self.log_json = pll_dir + '258.json'
        self.date_fmt = '%d.%m.%Y %H:%M:%S'

    def log_init(self):
        with open(self.log_json, 'a') as log:
            log.write("[\n")

    def log_end(self):
        with open(self.log_json, 'a') as log:
            log.write("],\n")

    def log_msg(self, log_text):
        timestamp = strftime(self.date_fmt)
        with open(self.log_file, 'a') as log:
            log.write(f"{timestamp}: {log_text}\n")

        with open(self.log_json, 'a') as log:
            log.write("\t{\n")
            log.write(f"\t\t\"time\":\"{timestamp}\"\n")
            log.write(f"\t\t\"msg\":\"{log_text}\"\n")
            log.write("\t},\n")


def format_seconds(seconds):
    sign = "-" if (seconds < 0) else ""
    return f"{sign}{abs(int(seconds/60)):02d}:{abs(seconds)%60:02.0f}"


def get_mpids_now_to_mute(mode):
    '''220509 Returns mplayer pids to mute, depending on mode
    All pids that doesn't set with specified mode, should be muted
    '''

    result_pids = []

    try:
        with open(pid_mode_file) as f:
            for pid in f:
                pid_details = pid.split()
                debug_msg(f"{mode}: **{pid_details[1]}**", 3)
                # mute all except for specified mode
                if (pid_details[1] == str(mode)):
                    continue
                with os.popen(f'pstree -ap {pid_details[0]}') as pid_tree:
                    for pid_info in pid_tree:
                        m_cpid = MPL_RE.search(pid_info)
                        if (m_cpid is not None):
                            to_mute = m_cpid.group('cpid')
                            result_pids.append(to_mute)
    except OSError:
        ...

    return result_pids


def check_mute(mute_mode):
    ''' This subroutine checks and sets mute state for all only mplayer sinks
    In non-muted period all mplayer sinks set non-muted, and subroutine
        is called only once per this period
    In muted period selected mplayer sinks set muted, but all other
        mplayer sinks are checked and set non-muted. In this period
        this subroutine is called every second.'''

    # 220509 mute_mode now essentially mode - какие оставить играть
    # Процессы в pids_to_mute получат mute = 1,
    #     остальные mplayers - mute = 0
    # Не mplayer's скрипт не трогает вообще

    # 220718 special value of -2 means unmute all

    if (mute_mode == -2):
        pids_to_mute = ()
    else:
        pids_to_mute = get_mpids_now_to_mute(mute_mode)

    sink_id = -1
    chk_mute = False

    # Enumerating all sinks to check their mute state
    with os.popen("pacmd list-sink-inputs") as list_sids:
        list_sids_info = list_sids.readlines()

    for list_sids_line in list_sids_info:
        # Step 1. Search for simk_id in "Index: ... " line
        m_sid = SID_RE.match(list_sids_line)
        if (m_sid is not None):
            sink_id = m_sid.group('sink_id')
            # Защита на группы без строчки application.name, если возможны
            chk_mute = False
        # Step 2. Application name in "application.name" line should be MPlayer
        m_appname = APPNAME_RE.match(list_sids_line)
        if (m_appname is not None):
            chk_mute = (m_appname.group('appname') == "MPlayer")

        if (chk_mute):
            # Step 3. if MPlayer, look for pid line.
            # (for application.process.id)
            # In that line do the processing
            m_spid = SPID_RE.match(list_sids_line)
            if (m_spid is not None):
                spid = m_spid.group('spid')
                if (spid in pids_to_mute):
                    os.system(
                        f"pactl set-sink-input-mute {sink_id} 1")
                else:
                    os.system(f"pactl set-sink-input-mute {sink_id} 0")


def play_bell(bell_name):
    log258.log_msg(f"mplayer -volume 50 {bin_dir}/{bells[bell_name]}"
                   + " > /dev/null 2>&1")
    os.system(f"mplayer -volume 50 {bin_dir}/{bells[bell_name]}"
              + " > /dev/null 2>&1")


def tune_period(period_length, mute_mode, label):
    '''Temporary solution - before there will be better idea -
    second rest block acts the same mute_mode way as first rest block,
    the only difference is the signal between first and second rest block.

    What signal to give is determined at end of first end block,
    depending on existence of second rest block
    (which does not exist by default)
    '''

    global is_stopped

    period_info = format_seconds(period_length)
    log258.log_msg(f"Starting {label[0].upper()}:{period_info}")
    preemptive_info = ''

    start = time.time()
    current = start
    mute_iter = 0

    signal_given = 0
    bell_given = 0

    base_signal = 1 if (mute_mode == 0) else 4.1

    break_time = 1.2
    last_key = None
    before_change_info = None
    before_change_tag = None

    # if (mute_mode == 0):
    # 220509 Now symmetric on mute_mode - do this every time
    # test: mute all for the first 3.5 seconds
    mute_iter = -25
    check_mute(-1)

    # cycle while current = time.time() is between
    #     start (=time.time() as sub start) and
    #     start+period_length
    while (current < start + period_length):
        time.sleep(0.1)

        # Process pause state if needed
        old_current = 0
        if (is_stopped == 1):
            old_current = current

        current = time.time()

        if (is_stopped == 1):
            start += current - old_current

        if (before_change_info is not None):
            if (current > last_key + break_time):
                after_change_info = format_seconds(period_length)
                log258.log_msg(f"At {before_change_tag}. Changed period from "
                               + f"{before_change_info} "
                               + f"to {after_change_info}")
                before_change_info = None

        # Process user interaction - impacts either start value or exits
        while (not kbhit.key_queue.empty()):
            key = kbhit.key_queue.get()
            last_key = current
            if (key in ADDTIME_KEYS):
                # start = start + 60
                if (before_change_info is None):
                    before_change_info = format_seconds(period_length)
                    before_change_tag = format_seconds(current - start)
                period_length = period_length + 60
            elif (key in SUBTIME_KEYS):
                if (start > current - period_length + 60):
                    # start -= 60
                    if (before_change_info is None):
                        before_change_info = format_seconds(period_length)
                        before_change_tag = format_seconds(current - start)
                    period_length -= 60
            elif (key == " "):
                # Pause - unpause actions and inform about is
                is_stopped = 1 - is_stopped
                remained = format_seconds(period_length - current + start)
                if (is_stopped == 1):
                    print(f"Paused: {remained}                           ")
                    pause_start = current
                else:
                    pause_period = format_seconds(current - pause_start)
                    print(f"Unpaused after {pause_period}                ")

            elif (key in kbhit.exit_keys):
                sys.exit()
            elif (key == "\x0A"):
                # start = current - period_length + base_signal + 1
                old_info = format_seconds(period_length)
                period_length = current - start + base_signal + 1
                preemptive_info = f"Preemptive end. Length was {old_info}"

        # Giving signal at end of period (change signal for add perion - TODO)
        if (signal_given == 0
                and (current > start + period_length - base_signal)):
            if ((mute_mode == 1) and (add_period > 0)):
                signal_thread = Thread(target=play_bell, args=('bell_add',))
            elif (mute_mode == 0):
                signal_thread = Thread(target=play_bell, args=('bell_rest',))
            else:
                signal_thread = Thread(target=play_bell, args=('bell_work',))

            signal_thread.start()
            signal_given = 1

        # If user adds time, reset the need to give signal
        if (current < start + period_length - base_signal - 2):
            signal_given = 0

        # (220509 edit) For alternate blocks (not main study)
        # give presignal(bell) 30 seconds before end of block
        # Works for all mute_mode > 0
        if (mute_mode >= 1):
            # 15 seconds before end_period - suppress bell anyway
            if (current > start + period_length - 15):
                bell_given = 1

            # time for the bell
            if (bell_given == 0 and (current > start + period_length - 30)):
                bell_thread = Thread(target=play_bell, args=('bell_chime',))
                bell_thread.start()
                check_mute(mute_mode)
                bell_given = 1

            # return before 31 seconds before end_period
            # - add necessity for the bell
            if (current < start + period_length - 31):
                bell_given = 0

        # Reinforce mute-unmute status every second,
        #    because pactl doesn't do it correctly
        # 220509 Symmetrically this time
        mute_iter += 1
        if (mute_iter >= 10):
            check_mute(mute_mode)
            mute_iter = 0

        # Display (220509 - added pause)
        # In window title:
        # W|R|A:mm:ss - running word/rest/add
        # (W|R|A)P:mm:ss - same paused
        # 220518 - Added display of current period_length
        remained = format_seconds(period_length - current + start)
        print(
            f"Remained {label} period: {remained} "
            + f"/ {format_seconds(period_length)}   ",
            end="\r")
        sys.stdout.write(f"\x1b]2;{label[0].upper()}"
                         + f"{'P' if (is_stopped == 1) else ''}"
                         + f":{remained}\x07")

    result_info = format_seconds(period_length)
    log258.log_msg(f"Ended {result_info}. {preemptive_info}")
    print()


def main():
    global log258
    log258 = Log258()
    log258.log_init()

    print("Starting pomodoro. Parameters:")
    period_info = tuple(map(format_seconds,
                            (work_period, rest_period, add_period)))
    print(f"Work period: {period_info[0]}")
    print(f"Rest period: {period_info[1]}")
    log_start = f"W:{period_info[0]} R:{period_info[1]}"

    if (add_period > 0):
        print(f"Add  period: {period_info[2]}")
        log_start = log_start + f" A:{period_info[2]}"

    log258.log_msg(f"Starting 258 with {log_start}")

    try:
        kbhit.start()

        while 1:
            tune_period(work_period, 0, "work")
            tune_period(rest_period, 1, "rest")
            if (add_period > 0):
                tune_period(add_period, 2, "add ")

    except OSError as X:
        print(f"In main cycle: {X.strerror}. Exiting")
    finally:
        check_mute(-2)
        log258.log_end()


if __name__ == "__main__":
    main()

# pacmd list-sink-inputs
# ...
#     index: 0
#       application.name = "MPlayer"
#       application.process.id = "22981"
#       application.process.binary = "mplayer"

# pacmd set-sink-input-mute <index> 1 to mute
# pacmd set-sink-input-mute <index> 0 to unmute

# pstree -aps <ppid>
# ─mplayer,313635 -af scaletempo -novideo -shuffle -loop 0 -fs -ass
#     -playlist /home/mai/bin/pll/allsongs.txt
