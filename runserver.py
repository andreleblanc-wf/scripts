#!/usr/bin/env python
import datetime
import re

import subprocess
import sys
import signal
import os
import settingslocal
import argparse

parser = argparse.ArgumentParser("Run the bigsky dev server")
parser.add_argument('-g', '--grep', metavar='REGEX', type=str, nargs=1, dest='search_re')
parser.add_argument('runserver_args', metavar='RUNSERVER', type=str, nargs='*')
parser.add_argument('-f', '--formatter', metavar='FORMATTER', type=str, nargs=1, dest='formatter', default='format_log_advanced')

log_re = re.compile(r'^(WARNING|DEBUG|INFO|ERROR)\s+(\d\d\d\d)\-(\d\d)\-(\d\d)\s(\d?\d):(\d\d):(\d\d),(\d\d\d)\s([\w\d_\.]+):(\d+)\]\s(.*)$')

manage_py_process = "python manage.py runserver"

if hasattr(settingslocal, 'RUNSERVER_PROCESS'):
    manage_py_process = getattr(settingslocal, 'RUNSERVER_PROCESS')

class color:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

COLORS = dict(
    WARNING=color.YELLOW,
    DEBUG=color.BLUE,
    INFO=color.GREEN,
    ERROR=color.RED
)

def format_log_advanced(log_level, log_datetime, filename, file_line, message):

    return "{level_color}{level}\t{datetime:%H}:{datetime:%M}:{datetime:%S} [{filename}:{file_line}]{endc} {message}".format(
        level=log_level,
        datetime=log_datetime,
        filename=filename,
        file_line=file_line,
        message=message,
        level_color=COLORS[log_level],
        endc=color.ENDC
    )

def main(args):

    if args.search_re is not None:
        matches = []
        search_re = re.compile(re.escape(args.search_re[0]))
    else:
        search_re = None

    if args.formatter is None:
        formatter = format_log_advanced
    else:
        formatter = globals()[args.formatter]

    process = subprocess.Popen("%s %s" % (manage_py_process, (' '.join(args.runserver_args))), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = process.stderr

    def signal_handler(input_signal, frame):
        os.kill(process.pid, signal.SIGTERM)
        if matches:
            print "\nCAPTURED OUTPUT"
            print "---------------"
            for m in matches:
                print m
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    blank_lines = 0
    while output:
        line = output.readline().strip('\n')
        if line:
            blank_lines = 0
            m = log_re.match(line)
            if m:
                level, year, month, day, hour, minute, sec, msec, filename, file_line, msg = m.groups()

                if search_re and search_re.search(msg):
                    msg = color.PINK + msg + color.ENDC
                    matches.append(formatter(level, log_timestamp, filename, file_line, msg))

                log_timestamp = datetime.datetime(int(year), int(month), int(day),
                      int(hour), int(minute), int(sec), int(msec) * 1000)
                print formatter(level, log_timestamp, filename, file_line, msg)
                continue

        print '\t' + line
        blank_lines += 1
        if blank_lines > 4:
            try:
                process.kill()
            except Exception:
                pass
            sys.exit(0)

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)