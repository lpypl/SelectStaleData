import subprocess
import json
import os
import time


HOST = "127.0.0.1"
PORT = "3306"
DATABASE = "bugtest"
USERNAME = "root"
PASSWORD = "root"
REQUEST_INTERVAL = 0.001


print(">>>>>>>>>>>>>>>     Loading Data     <<<<<<<<<<<<<<<")
sql_load_data = rf"""
mysql -h{HOST} -P{PORT} -u{USERNAME} -p{PASSWORD} --unbuffered --local-infile=1 {DATABASE} -vvv -e "create table if not exists table0 (pkId integer, pkAttr0 integer, pkAttr1 integer, pkAttr2 integer, coAttr0_0 integer, primary key(pkAttr0, pkAttr1, pkAttr2)); delete from table0; load data local infile 'table0.csv' into table table0 fields terminated by ',' enclosed by '\"' ignore 1 lines (pkId,pkAttr0,pkAttr1,pkAttr2,coAttr0_0);"
"""
os.system(sql_load_data)


class SQLSession:
    def __init__(self, id) -> None:
        self.stdout = open(f"session-{id}.stdout", 'w')
        self.proc = subprocess.Popen(f'mysql -h{HOST} -P{PORT} -u{USERNAME} -p{PASSWORD} --unbuffered {DATABASE} -vvv', shell=True,
                                     stdin=subprocess.PIPE, stdout=self.stdout, stderr=self.stdout)

    def execute_command(self, command):
        self.proc.stdin.write(command.encode('utf-8'))
        self.proc.stdin.write(";\n".encode('utf-8'))
        self.proc.stdin.flush()

    def close(self):
        self.stdout.close()


with open('minimal-operations.json', 'r') as fin:
    operations = json.load(fin)
sessions: dict[int, SQLSession] = {}


print(">>>>>>>>>>>>>>>     Loading Tran     <<<<<<<<<<<<<<<")
for op in operations:
    connId = op['connId']
    sql = op['sql']

    if connId not in sessions:
        sessions[connId] = SQLSession(connId)

    sessions[connId].execute_command(sql)
    time.sleep(REQUEST_INTERVAL)


time.sleep(1)
for se in sessions.values():
    se.close()
