
create table IF NOT EXISTS check (name string , v int, t int) row format delimited fields terminated by ',' ; 

load data inpath 'hive_data' into table check;

select * from check;

select * from check group by name;
