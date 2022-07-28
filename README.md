# Bug Description

## Schema
```
create table table0 (pkId integer, pkAttr0 integer, pkAttr1 integer, pkAttr2 integer, coAttr0_0 integer, primary key(pkAttr0, pkAttr1, pkAttr2));
```

Initial data: `table0.csv`

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

## Wrong Query Result

### Description

- In the beginning, `coAttr0_0` of `Key<412,409,258>` is `17702`.
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
  |    .... |    .... |     ... |     ..... |
  |     412 |     409 |     258 |     17702 |
  |    .... |    .... |     ... |     ..... |
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

Query OK, 0 rows affected (0.01 sec)
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

+---------+---------+---------+-----------+
| pkAttr0 | pkAttr1 | pkAttr2 | coAttr0_0 |
+---------+---------+---------+-----------+
|      35 |      39 |      22 |     89665 |
|     146 |     144 |      93 |     89665 |
|     162 |     160 |     101 |     89665 |
|     170 |     168 |     106 |     89665 |
|     347 |     345 |     217 |     89665 |
|     442 |     440 |     276 |     89665 |
|     587 |     586 |     367 |     89665 |
|     611 |     610 |     383 |     89665 |
|     745 |     751 |     466 |     89665 |
|     791 |     786 |     492 |     89665 |
|     839 |     837 |     523 |     89665 |
|    1120 |    1122 |     704 |     89665 |
|    1144 |    1146 |     719 |     89665 |
|    1184 |    1189 |     743 |     89665 |
|    1200 |    1203 |     751 |     89665 |
|    1266 |    1270 |     794 |     89665 |
|    1383 |    1380 |     864 |     89665 |
|    1553 |    1555 |     973 |     89665 |
+---------+---------+---------+-----------+
18 rows in set (0.00 sec)

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
|      21 |      18 |      12 |     17702 |
|     114 |     119 |      71 |     17702 |
|     284 |     287 |     177 |     17702 |
|     292 |     289 |     184 |     17702 |
|     300 |     297 |     185 |     17702 |
|     308 |     311 |     191 |     17702 |
|     315 |     313 |     199 |     17702 |
|     397 |     399 |     246 |     17702 |
|     412 |     409 |     258 |     17702 |
|     420 |     423 |     262 |     17702 |
|     530 |     528 |     331 |     17702 |
|     573 |     574 |     356 |     17702 |
|     603 |     606 |     377 |     17702 |
|     705 |     711 |     443 |     17702 |
|     951 |     948 |     592 |     17702 |
|    1039 |    1037 |     649 |     17702 |
|    1152 |    1154 |     721 |     17702 |
|    1222 |    1217 |     763 |     17702 |
|    1351 |    1349 |     841 |     17702 |
|    1401 |    1404 |     879 |     17702 |
|    1521 |    1523 |     951 |     17702 |
|    1543 |    1541 |     963 |     17702 |
|    1551 |    1549 |     969 |     17702 |
|    1585 |    1587 |     993 |     17702 |
+---------+---------+---------+-----------+
24 rows in set (0.00 sec)

--------------
commit
--------------

Query OK, 0 rows affected (0.00 sec)
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