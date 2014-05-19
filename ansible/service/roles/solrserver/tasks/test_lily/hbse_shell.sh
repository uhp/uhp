
hbase shell> create 'record', {NAME => 'data', REPLICATION_SCOPE => 1}

put 'record', 'row7', 'data', 'v7'
 put 'record', 'row8', 'data', 'v8'
 put 'record', 'row9', 'data', 'v9'
 
 put 'record', 'row10', 'data', 'v10'
 put 'record', 'row11', 'data', 'v11'
 put 'record', 'row12', 'data', 'v12'
