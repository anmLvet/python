#!/usr/bin/python3

import random
import shelve
import os.path


def get_roll(index):
    roll = min(dice)
    if (index < len(dice)):
        roll = dice[index]

    return roll


dice = (20, 12, 10, 8, 7, 6, 5, 4)

binpath = os.path.expanduser("~/bin")
if (not os.path.isdir(binpath)):
    os.mkdir(binpath)

with shelve.open(os.path.expanduser("~/bin/rolldice.db"), flag='c') as rdb:
    if (not ("state" in rdb)):
        rdb["state"] = random.getstate()
    if (not ("cube_index") in rdb):
        rdb["cube_index"] = 0

    random.setstate(rdb["state"])
    index = rdb["cube_index"]

    roll = get_roll(index)

    roll_result = random.randint(1, roll)
    print(f"roll: {roll}, result: {roll_result}")

    if (roll == roll_result):
        index = 0
    else:
        index += 1

    rdb["state"] = random.getstate()
    rdb["cube_index"] = index

    print(f"next roll: {get_roll(index)}")
