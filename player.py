import subprocess
import json
import os
import time


HOST = "127.0.0.1"
PORT = "4000"
DATABASE = "lpybugtest"
USERNAME = "root"
PASSWORD = "root"
REQUEST_INTERVAL = 0.001


print(">>>>>>>>>>>>>>>     Loading Data     <<<<<<<<<<<<<<<")
sql_load_data = rf"""
mysql -h{HOST} -P{PORT} -u{USERNAME} -p{PASSWORD} --unbuffered --local-infile=1 {DATABASE} -vvv -e "create table if not exists t (k integer, v integer, primary key(k)); delete from t; insert into t(k, v) values(1,1);"
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
