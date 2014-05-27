set -e

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR

f=words.txt
in=/user/$user/test/wordcount/input
out=/user/$user/test/wordcount/output

[ -e $f ] || echo -e "abc\ndef\njbc\ncdh\nok" > $f

hdfs dfs -mkdir -p $in

hdfs dfs -test -e $in/$f || hdfs dfs -put $f $in/

hdfs dfs -test -e $out && hdfs dfs -rm -R -skipTrash $out

MAPREDUCE_PREFIX=/usr/lib/hadoop-mapreduce
yarn jar $MAPREDUCE_PREFIX/hadoop-mapreduce-examples.jar wordcount $in $out
