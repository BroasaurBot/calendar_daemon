import os
import sys
import tokeniser as t

#--------------- Global variable ----------------

PIPE_FILE = "/tmp/cald_pipe"
LINK_FILE = "/tmp/calendar_link"

#----------------- Help Commands ----------------------------

def is_valid_date(string):
    if len(string) != 10:
        return False
    if string[2] != "-" or string[5] != "-":
        return False

    parts = string.split("-")
    if not parts[0].isdigit() or not parts[1].isdigit() or not parts[2].isdigit():
        return False
    return True


def is_date_after(date1, date2):
    time1 = date1.split("-")
    time2 = date2.split("-")

    if time2[2] > time1[2]:
        return 1
    elif time2[2] < time1[2]:
        return -1
    else:

        if time2[1] > time1[1]:
            return 1
        elif time2[1] < time1[1]:
            return -1
        else:

            if time2[0] > time1[0]:
                return 1
            elif time2[0] < time1[0]:
                return -1
            else:
                return 0


def print_event(line):
    line = line.split(",")
    print(line[0] + " : " + line[1] + " : " + (line[2] if len(line) == 3 else ''))

def query_data_date(data_path, date):
    results = []

    with open(data_path, "r") as data_base:
        lines = data_base.readlines()

        for line in lines:
            fields = line.strip("\n").split(",")
            if fields[0] == date:
                results.append(line.strip("\n"))

    return results

def query_data_interval(data_path, start, end):
    results = []

    with open(data_path, "r") as data_base:
        lines = data_base.readlines()

        for line in lines:
            fields = line.strip("\n").split(",")
            if is_date_after(start, fields[0]) == 1 and is_date_after(end, fields[0]) == -1 :
                results.append(line.strip("\n"))

    return results

def query_data_name(data_path, name):
    results = []

    with open(data_path, "r") as data_base:
        lines = data_base.readlines()

        for line in lines:
            fields = line.strip("\n").split(",")
            if fields[1].find(name) == 0:
                results.append(line.strip("\n"))

    return results


def query_data_event(data_path, name, date):
    results = []

    with open(data_path, "r") as data_base:
        lines = data_base.readlines()

        for line in lines:
            fields = line.strip("\n").split(",")
            if fields[1].find(name) == 0 and fields[0] == date:
                results.append(line.strip("\n"))

    return results

#--------------- Commands ------------------------------------

def get_cmd(data_path, args):
    action_option = args[0].upper()
    results = []

    if action_option == "DATE":
        dates = args[1:]

        for date in dates:
            if is_valid_date(date) and len(args) > 1:
                results.extend(query_data_date(data_path, date))
            else:
                print("Unable to parse date", file=sys.stderr)


    elif action_option == "INTERVAL":
        dates = args[1:]
        if len(dates) != 2:
            print("Unable to parse date", file=sys.stderr)
            return

        if is_valid_date(dates[0]) and is_valid_date(dates[1]):
            if is_date_after(dates[0], dates[1]) == 1:
                results.extend(query_data_interval(data_path, dates[0], dates[1]))
            else:
                print("Unable to Process, Start date is after End date", file=sys.stderr)
        else:
            print("Unable to parse date", file=sys.stderr)


    elif action_option == "NAME":
        names = args[1:]

        if len(args) > 1:
            for name in names:
                results.extend(query_data_name(data_path, name))
        else:
            print("Please specify an argument", file=sys.stderr)
    else:
        pass

    if results:
        for result in results:
            print_event(result)


def add_cmd(pipe, args):
    if len(args) < 1:
        print("Multiple errors occur", file=sys.stderr)
        return

    date = None
    name = None
    description = None
    for field in args:
        if is_valid_date(field):
            date = field
            args.remove(date)
            break

    if len(args) == 1:
        name = args[0]
    elif len(args) > 1:
        name = args[0]
        description = args[1]

    if not date and not name:
        print("Multiple errors occur", file=sys.stderr)
    elif not date:
        print("Unable to parse date", file=sys.stderr)
    elif not name:
        print("Missing event name", file=sys.stderr)
    else:
        msg = "ADD " + date + " \"" + name + "\"" + (" \"" +description + "\"" if description else "") + "\n"
        os.write(pipe, bytes(msg, "UTF-8"))


def update_cmd(pipe, data_path ,args):
    if len(args) < 3:
        print("Not enough arguments given", file=sys.stderr)
        return

    date = None
    name = None
    new_name = None
    description = None

    for field in args:
        if is_valid_date(field):
            date = field
            args.remove(date)
            break

    name = args[0]
    new_name = args[1]
    if len(args) > 2:
        description = args[2]

    event_exists = False
    if date:
        event_exists = (True if query_data_event(data_path, name, date) else False)

    if not event_exists and not date:
        print("Unable to parse date", file=sys.stderr)
        print("Multiple errors occur", file=sys.stderr)
    elif not event_exists:
        print("Unable to update, event does not exist", file=sys.stderr)
    else:
        msg = "UPD " + date + " \"" + name + "\" \"" + new_name + "\"" + (" \"" +description + "\"" if description else "") + "\n"
        os.write(pipe, bytes(msg, "UTF-8"))

def delete_cmd(pipe, args):
    if len(args) < 1:
        print("Multiple errors occur", file=sys.stderr)
        return

    date = None
    name = None
    for field in args:
        if is_valid_date(field):
            date = field
            args.remove(date)
            break

    if len(args) == 1:
        name = args[0]

    if not date and not name:
        print("Multiple errors occur", file=sys.stderr)
    elif not date:
        print("Unable to parse date", file=sys.stderr)
    elif not name:
        print("Missing event name", file=sys.stderr)
    else:
        msg = "DEL " + date + " \"" + name + "\"\n"
        os.write(pipe, bytes(msg, "UTF-8"))


# ------------------- Main execution --------------------------------
def run():

    #Find the data base
    data_path = None
    try:
        with open(LINK_FILE, "r") as link_file:
            data_path = link_file.readline()
        open(data_path, "r").readline()
    except Exception as e:
        print("Unable to process calendar database", file=sys.stderr)
        exit()


    if os.path.exists(PIPE_FILE):
        pipe = os.open(PIPE_FILE, os.O_WRONLY)

        try:
            #Here goes the code to interact with the daemon
            command_line = sys.argv[1:]

            action = command_line[0].upper()

            if action == "GET":
                get_cmd(data_path, command_line[1:])
            elif action == "ADD":
                add_cmd(pipe, command_line[1:])
            elif action == "UPD":
                update_cmd(pipe, data_path ,command_line[1:])
            elif action == "DEL":
                delete_cmd(pipe, command_line[1:])
            else:
                pass

        except OSError:
            print("Pipe has been closed")

        except Exception as e:
            print(e, file=sys.stderr)

        os.close(pipe)
    else:
        print("PIPE DOESN'T EXIST", file=sys.stderr)

if __name__ == '__main__':
    run()



