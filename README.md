# Bug Description

## Tested Version
- 5.7.25-TiDB-v5.0.0
- 5.7.25-TiDB-v6.1.0

## Schema
```
create table if not exists t (k integer, v integer, primary key(k));

delete from t;

insert into t(k, v) values (1, 1);
```

## Operations (From General Log)
| Session | Operation                                               |
| ------- | ------------------------------------------------------- |
| 1001    | SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ |
| 1002    | SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ |
| 1001    | start transaction                                       |
| 1001    | update t set v = 2 where k = 1                          |
| 1001    | commit                                                  |
| 1002    | start transaction                                       |
| 1002    | select k, v from t where v = 88                         |
| 1002    | update t set v = 2 where k = 1                          |
| 1002    | select k, v from t where k = 1                          |
| 1002    | commit                                                  |

## How to Repeat

- `transformer.py` translates `minimal-general.log` to `minimal-operations.json`
- `player.py` create a mysql client process for each session
- `player.py` iterates over the list of operations from `minimal-operations.json`, and sends each operation to its session **without waiting for `Query OK`**
- `play.sh` is a script that keeps replaying this reproducible case until it succeeds.

## Wrong Query Result

### Description

- In the beginning, `v` of `Key<1>` is `1`.
  ```
  +---+------+
  | k | v    |
  +---+------+
  | 1 |    1 |
  +---+------+
  ```
- Then Session-1001 updates `v` of `Key<1>` to `2`.  
  Note that it successfully changes that value, because the query result is: 
  ```
  Query OK, 1 row affected (0.00 sec)
  Rows matched: 1  Changed: 1  Warnings: 0
  ```
- When Session-1002 trys updating `v` of `Key<1>` to `2`.  
  It fails to change that value because the vlaue is already `2`:
  ```
  Query OK, 0 rows affected (0.00 sec)
  Rows matched: 1  Changed: 0  Warnings: 0
  ```
- Thers is no wrong execution results so far.
- Next, Session-1002 executes
  ```
  select k, v from t where k = 1
  ```
  As we known, latest `v` of `Key<1>` is `2`  
  However, the query result is:
  ```
  +---+------+
  | k | v    |
  +---+------+
  | 1 |    1 |
  +---+------+
  1 row in set (0.01 sec)
  ```
  The database returns a stale version of data for `Key<1>`

### Details

#### Initial Data
```
+---+------+
| k | v    |
+---+------+
| 1 |    1 |
+---+------+
```

#### Execution Result of Session-1001
```
--------------
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
start transaction
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
update t set v = 2 where k = 1
--------------

Query OK, 1 row affected (0.00 sec)
Rows matched: 1  Changed: 1  Warnings: 0

--------------
commit
--------------

Query OK, 0 rows affected (0.00 sec)

Bye

```

#### Execution Result of Session-1002


```
--------------
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
start transaction
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
select k, v from t where v = 88
--------------

Empty set (0.00 sec)

--------------
update t set v = 2 where k = 1
--------------

Query OK, 0 rows affected (0.01 sec)
Rows matched: 1  Changed: 0  Warnings: 0

--------------
select k, v from t where k = 1
--------------

+---+------+
| k | v    |
+---+------+
| 1 |    1 |
+---+------+
1 row in set (0.00 sec)

--------------
commit
--------------

Query OK, 0 rows affected (0.00 sec)

Bye

```
   

## Key Points to repeat this Bug

### Request Rate is Critical  
- Sleep for 0~0.003 seconds between two operations is OK for reproducing this bug
- If the sleep is longer, it tends to produce correct execution results
  
### Update to the same value
- Two sessions update `v` to the same value
- And the update of Session-1002 must match but not change  
  
### Isolation Level  
- Isolation Level of Session-1001 doesn't matter, RC/RR both are OK
- According to our tests, Isolation Level of Session-1002 must be RR

### For Session-1002, the extra select before the update for `Key<1>` seems unnecessary. But it greatly improves the chance of repeat  
```
select k, v from t where v = 88
```