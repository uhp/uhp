set -e


# sudo -u hdfs hdfs dfs -mkdir /user/$USER
# sudo -u hdfs hdfs dfs -chown $USER:$USER /user/$USER

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR


f=words.txt
in=/user/$USER/test/wordcount/input
out=/user/$USER/test/wordcount/output

[ $1 == "r" ] && {
    rm -rf $f
    hdfs dfs -rm -R -skipTrash $in
}

#[ -e $f ] || echo -e "abc\ndef\njbc\ncdh\nok" > $f
#[ -e $f ] || seq 1 10000000 > $f #约 88 M
[ -e $f ] || seq 1 1000000 > $f #约 8 M

hdfs dfs -mkdir -p $in

hdfs dfs -test -e $in/$f || hdfs dfs -put $f $in/

hdfs dfs -test -e $out && hdfs dfs -rm -R -skipTrash $out

MAPREDUCE_PREFIX=/usr/lib/hadoop-mapreduce
yarn jar $MAPREDUCE_PREFIX/hadoop-mapreduce-examples.jar wordcount $in $out
