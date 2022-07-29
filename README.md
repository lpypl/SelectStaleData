# Bug Description

## Tested Version
- 8.0.29

## Schema
```
create table table0 (pkId integer, pkAttr0 integer, pkAttr1 integer, pkAttr2 integer, coAttr0_0 integer, primary key(pkAttr0, pkAttr1, pkAttr2));
```

Initial data: `table0.csv`  

```
+---------+---------+---------+-----------+
| pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
+---------+---------+---------+-----------+
|     412 |     409 |     258 |     17702 |
+---------+---------+---------+-----------+
```

## Operations (From General Log)
| Session | Operation                                                                                                         |
| ------- | ----------------------------------------------------------------------------------------------------------------- |
| 282     | SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE                                                              |
| 281     | SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ                                                           |
| 282     | start transaction                                                                                                 |
| 282     | update `table0` set `coAttr0_0` = 40569 where ( `pkAttr0` = 412 ) and ( `pkAttr1` = 409 ) and ( `pkAttr2` = 258 ) |
| 282     | commit                                                                                                            |
| 281     | start transaction                                                                                                 |
| 281     | select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 89665 )                   |
| 281     | update `table0` set `coAttr0_0` = 40569 where ( `pkAttr0` = 412 ) and ( `pkAttr1` = 409 ) and ( `pkAttr2` = 258 ) |
| 281     | select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 17702 )                   |
| 281     | commit                                                                                                            |

## How to Reproduce

- `transformer.py` translates `minimal-general.log` to `minimal-operations.json`
- `player.py` create a mysql client process for each session
- `player.py` iterates over the list of operations from `minimal-operations.json`, and sends each operation to its session **without waiting for `Query OK`**
- `play.sh` is a script that keeps replaying this reproducible case until it succeeds.

## Wrong Query Result

### Description

- In the beginning, `coAttr0_0` of `Key<412,409,258>` is `17702`.
  ```
  +---------+---------+---------+-----------+
  | pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
  +---------+---------+---------+-----------+
  |     412 |     409 |     258 |     17702 |
  +---------+---------+---------+-----------+
  ```
- Then Session-282 updates `coAttr0_0` of `Key<412,409,258>` to `40569`.  
  Note that it successfully changes that value, because the query result is: 
  ```
  Query OK, 1 row affected (0.00 sec)
  Rows matched: 1  Changed: 1  Warnings: 0
  ```
- When Session-281 trys updating `coAttr0_0` of `Key<412,409,258>` to `40569`.  
  It fails to change that value because the vlaue is already `40569`:
  ```
  Query OK, 0 rows affected (0.00 sec)
  Rows matched: 1  Changed: 0  Warnings: 0
  ```
- Thers is no wrong execution results so far.
- Next, Session-282 executes
  ```
  select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 17702 )
  ```
  As we known, latest `coAttr0_0` of `Key<412,409,258>` is `40569`  
  However, the query result is:
  ```
  +---------+---------+---------+-----------+
  | pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
  +---------+---------+---------+-----------+
  |     412 |     409 |     258 |     17702 |
  +---------+---------+---------+-----------+
  ```
  The database returns a stale version of data for `Key<412,409,258>`

### Details

#### Initial Data
```
+---------+---------+---------+-----------+
| pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
+---------+---------+---------+-----------+
|     412 |     409 |     258 |     17702 |
+---------+---------+---------+-----------+
```

#### Execution Result of Session-282
```
--------------
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
start transaction
--------------

Query OK, 0 rows affected (0.00 sec)

--------------
update `table0` set `coAttr0_0` = 40569 where ( `pkAttr0` = 412 ) and ( `pkAttr1` = 409 ) and ( `pkAttr2` = 258 )
--------------

Query OK, 1 row affected (0.00 sec)
Rows matched: 1  Changed: 1  Warnings: 0

--------------
commit
--------------

Query OK, 0 rows affected (0.00 sec)

Bye

```

#### Execution Result of Session-281


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
select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 89665 )
--------------

Empty set (0.00 sec)

--------------
update `table0` set `coAttr0_0` = 40569 where ( `pkAttr0` = 412 ) and ( `pkAttr1` = 409 ) and ( `pkAttr2` = 258 )
--------------

Query OK, 0 rows affected (0.00 sec)
Rows matched: 1  Changed: 0  Warnings: 0

--------------
select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 17702 )
--------------

+---------+---------+---------+-----------+
| pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
+---------+---------+---------+-----------+
|     412 |     409 |     258 |     17702 |
+---------+---------+---------+-----------+
1 row in set (0.01 sec)

--------------
commit
--------------

Query OK, 0 rows affected (0.00 sec)

Bye

```
   

## Key Points to Reproduce this Bug

### Request Rate is Critical  
- Sleep for 0~0.003 seconds between two operations is OK for reproducing this bug
- If the sleep is longer, it tends to produce correct execution results
  
### Update to the same value
- Two sessions update `coAttr0_0` to the same value
- And the update of Session-281 must match but not change  
  
### Isolation Level  
- Isolation Level of Session-282 doesn't matter, RU/RC/RR/SR all is OK
- According to our tests, Isolation Level of Session-281 must be RR

### For Session-281, the extra select before the update for `Key<412,409,258>` seems necessary  
```
select `pkAttr0`, `pkAttr1`, `pkAttr2`, `coAttr0_0` from `table0` where ( `coAttr0_0` = 89665 )
```