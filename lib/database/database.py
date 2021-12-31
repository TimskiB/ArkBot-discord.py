from os.path import isfile
from sqlite3 import connect
from apscheduler.triggers.cron import CronTrigger

DATA_PATH = "./data/database/database.db"
BUILD_PATH = "./data/database/build.sql"
connection = connect(DATA_PATH, check_same_thread=False)
cursor = connection.cursor()


def with_commit(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit()

    return inner


@with_commit
def build():
    if isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)


def commit():
    connection.commit()


def autosave(s):
    s.add_job(commit, CronTrigger(second=0))


def close():
    connection.close()


def field(command, *values):
    connection.execute(command, tuple(values))
    if (fetch := cursor.fetchone()) is not None:
        return fetch[0]


def record(command, *values):
    connection.execute(command, tuple(values))
    return cursor.fetchone()


def records(command, *values):
    connection.execute(command, tuple(values))
    return cursor.fetchall()


def columns(command, *values):
    connection.execute(command, tuple(values))
    return [item[0] for item in cursor.fetchall()]


def execute(command, *values):
    cursor.execute(command, tuple(values))


def multiexec(command, valueset):
    cursor.executemany(command, valueset)


def scriptexec(path):
    with open(path, "r", encoding="utf-8") as script:
        cursor.executescript(script.read())
