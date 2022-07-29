create table if not exists t (k integer, v integer, primary key(k));

delete from t;

insert into t(k, v) values (1, 1);