import re
from collections import defaultdict


with open("minimal-general.log", "r") as fin:
    lines = fin.readlines()

pat = re.compile(r"(.*?)\s(\d+)\s(.*)")

transIdDict = defaultdict(lambda: 0)
connInTrans = set()
operationList = []

for number, line in enumerate(lines):
    matcher = pat.match(line)
    connId = matcher.group(2)
    statment = matcher.group(3)
    statmentUpper = matcher.group(3).upper()
    operation = {}
    if statmentUpper.startswith("QUERY	SET SESSION"):
        operation['connId'] = connId
        operation['sql'] = statment[statmentUpper.find('SET'):]
    elif statmentUpper.startswith("QUERY	START"):
        connInTrans.add(connId)
        operation['connId'] = connId
        transIdDict[connId] += 1
        operation['transId'] = transIdDict[connId]
        operation['sql'] = statment[statmentUpper.find('START'):]
    elif statmentUpper.startswith("QUERY	SELECT"):
        operation['connId'] = connId
        if connId in connInTrans:
            operation['transId'] = transIdDict[connId]
        operation['sql'] = statment[statmentUpper.find('SELECT'):]
    elif statmentUpper.startswith("EXECUTE"):
        operation['connId'] = connId
        if connId in connInTrans:
            operation['transId'] = transIdDict[connId]
        operation['sql'] = statment[len('EXECUTE	'):]
    elif statmentUpper.startswith("QUERY	COMMIT"):
        operation['connId'] = connId
        if connId in connInTrans:
            operation['transId'] = transIdDict[connId]
        operation['sql'] = statment[statmentUpper.find('COMMIT'):]
        connInTrans.remove(connId)
    elif statmentUpper.startswith("QUERY	ROLLBACK"):
        operation['connId'] = connId
        if connId in connInTrans:
            operation['transId'] = transIdDict[connId]
            connInTrans.remove(connId)
        operation['sql'] = statment[statmentUpper.find('ROLLBACK'):]
    elif statmentUpper.startswith("PREPARE") or statmentUpper.startswith("RESET STMT") or \
            statmentUpper.startswith("QUIT") or statmentUpper.startswith("CLOSE STMT"):
        continue
    else:
        raise RuntimeError(f'[line {number}] {statment}')
    
    operationList.append(operation)


import json
with open("minimal-operations.json", "w") as fout:
    json.dump(operationList, fout)
