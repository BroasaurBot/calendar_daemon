#!/bin/python

import signal
import os
import sys

# ---------------Global variables ---------------

PIPE_FILE = "/tmp/cald_pipe"
DATABASE_NAME = "cald_db.csv"
ERROR_LOG_FILE = "/tmp/cald_err.log"
LINK_FILE = "/tmp/calendar_link"
daemon_quit = False

# Help functions

def write_error_log(path, msg):
    error_log = open(ERROR_LOG_FILE, "a+")
    print(msg, file=sys.stderr)
    error_log.write(msg)
    error_log.close()

def get_tokens(line):
    arr = list(line.strip("\n"))
    out = []

    start = 0
    first = -1

    for i in range(len(arr)):
        if arr[i] == "\"":
            if first == -1:
                first = i
            else:
                out.append("".join(arr[first+1:i]))
                first = -1
                start = i + 1
                continue

        if arr[i] == " " and first == -1:
            if i != start:
                out.append("".join(arr[start:i]))
                start = i + 1

    if start != len(arr):
        out.append("".join(arr[start:i+1]))

    return out

def make_directory(path=""):

    if path == ""  or path == " ":
        script_path = os.path.dirname(os.path.realpath(__file__))
        path = script_path + "/" + DATABASE_NAME
    else:
        os.chdir(os.getcwd())
        path = os.path.abspath(path)

    return path

def check_data_base(path=""):

    directory = make_directory(path)
    open(directory, "a+")
    with open(LINK_FILE, "w") as link:
        link.write(directory)
        link.close()
    return directory


def is_valid_date(string):
    if len(string) != 10:
        return False
    if string[2] != "-" or string[5] != "-":
        return False

    parts = string.split("-")
    if not parts[0].isdigit() or not parts[1].isdigit() or not parts[2].isdigit():
        return False

    return True

def get_matching_line(path, cmds):
    data_base = open(path, "r")

    line_pos = 1
    line = data_base.readline().strip("\n")
    while line:

        fields = line.split(",")
        if fields[0] == cmds[0] and fields[1] == cmds[1]:
            return line_pos

        line_pos += 1
        line = data_base.readline().strip("\n")

    data_base.close()
    return -1

#-------------------Data Base Methods ---------------------------

def add_event(path, cmds):

    if len(cmds) != 2 and len(cmds) != 3:
        return

    if not is_valid_date(cmds[0]):
        raise Exception("Incorrect data format: " + cmds[0])

    if get_matching_line(path, cmds) != -1:
        raise Exception("Event (" + cmds[1] + ")  already exists, Call update to change it")

    data_base = open(path, "a+")
    data_base.write(cmds[0] + "," + cmds[1] + ( "," + cmds[2]if len(cmds) == 3 else '') + "\n")
    data_base.close()

def delete_event(path, cmds):
    if len(cmds) != 2:
        return

    line_pos = get_matching_line(path, cmds)

    with open(path, "r") as data_base:
        lines = data_base.readlines()
    with open(path, "w") as data_base:

        for i in range(1, len(lines) + 1):
            if i == line_pos:
                pass
            else:
                data_base.write(lines[i-1])

def update_event(path, cmds):
    if len(cmds) != 3 and len(cmds) != 4:
        return

    line_pos = get_matching_line(path, cmds[:2])

    with open(path, "r") as data_base:
        lines = data_base.readlines()
    with open(path, "w") as data_base:

        for i in range(1, len(lines) + 1):
            if i == line_pos:
                data_base.write(cmds[0] + "," + cmds[2] + ("," + cmds[3] if len(cmds) == 4 else '') + "\n")
            else:
                data_base.write(lines[i-1])




#------------------------- Main Body -----------------------------------------


# Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True

def run():
    # Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    # Create necessary files for the daemon
    # Create necessary pipe
    setup = True
    if not os.path.exists(PIPE_FILE):
        os.mkfifo(PIPE_FILE)


    abs_path = ""
    try:
        if len(sys.argv) >= 2 and sys.argv[1] != "":
            abs_path = check_data_base(path=sys.argv[1])
        else:
            abs_path = check_data_base()

    except FileNotFoundError as e:
        msg = str(e) + "\nDirectory for database not found\n"
        write_error_log(ERROR_LOG_FILE, msg)
        setup = False


    #Begin the pipe to listen to the calendar process
    pipe = None
    while not daemon_quit and setup:
        pipe = os.open(PIPE_FILE, os.O_RDONLY)
        rec_cmd = os.read(pipe, 100).decode()

        #recieved a pipe line
        if len(rec_cmd) != 0 and not daemon_quit:
            tokens = get_tokens(rec_cmd)
            cmd = tokens[0].upper()

            try:
                if len(tokens) > 1:
                    if cmd == "ADD":
                        add_event(abs_path, tokens[1:])
                    elif cmd == "DEL":
                        delete_event(abs_path, tokens[1:])
                    elif cmd == "UPD":
                        update_event(abs_path, tokens[1:])
                    else:
                        pass
            except Exception as e:
                msg = str(e) + "\n"
                write_error_log(ERROR_LOG_FILE, msg)

    #Close all the files
    if pipe:
        os.close(pipe)

if __name__ == '__main__':
    run()
