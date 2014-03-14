#!/bin/bash

t=`date +%Y%m%d-%H%M`

echo "
create 'hbase_live', 'cf'
put 'hbase_live', 'row', 'cf:a', 'value1'
put 'hbase_live', 'row${t}', 'cf:a', 'value2'
scan 'hbase_live'
" | hbase shell  &


re=`echo "get 'hbase_live', 'row','cf:a' "| hbase shell`

if [[ "$re" =~ "value1" ]]
then
    exit 0
else
    exit 1
fi

#create 'hbase_check', 'cf' 
#list 'hbase_check'
#put 'hbase_check', 'row1', 'cf:a', 'value1'
#put 'hbase_check', 'row2', 'cf:a', 'value2'
#put 'hbase_check', 'row3', 'cf:a', 'value3'
#scan 'hbase_check'
#get 'hbase_check', 'row1'
#disable 'hbase_check'
#drop 'hbase_check'


