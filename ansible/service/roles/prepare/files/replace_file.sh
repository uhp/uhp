#!/bin/bash

FILE=$1
REPLACE_FILE=$2


START='#UHP_START'
END='#UHP_END'

if [ -f "$REPLACE_FILE" ] 
then
    REPLACE=`cat $REPLACE_FILE`
else
    exit 1
fi

find_tag=`cat $FILE|grep $START|wc -l`
if [ "$find_tag" == "0" ]
then
    echo "not it and add to last"
    echo -e "\n\n$START\n$REPLACE\n$END" >> $FILE
else
    echo "find it delete and add to last"
    #sed -e ":begin; /$START/,/$END/ { /$END/! { $! { N; b begin }; }; s/$START.*$END/$START\n$REPLACE\n$END/; };"  -i $FILE
    sed -e ":begin; /$START/,/$END/ { /$END/! { $! { N; b begin }; }; /$START.*$END/d; };"  -i $FILE
    echo -e "$START\n$REPLACE\n$END" >> $FILE
fi

