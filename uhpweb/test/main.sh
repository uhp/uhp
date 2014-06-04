#!/bin/bash

[ -z "$UHP_HOME" ] && source $HOME/.bash_profile 

[ -z "$UHP_HOME" ] && {
    echo "UHP_HOME not set."
    exit 1
}

sh $UHP_HOME/bin/stop-web.sh

sh $UHP_HOME/bin/start-web.sh

cd $UHP_HOME/uhpweb/test
for py in `ls $UHP_HOME/uhpweb/test`
do
    if [[ "$py" == *py ]]
    then
        python $py
    fi
done


