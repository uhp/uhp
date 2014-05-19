#
#/**
# * Copyright 2013 NGDATA nv
# *
# * Based on HBase's hbase-env.sh
# * Copyright 2007 The Apache Software Foundation
# *
# * Licensed to the Apache Software Foundation (ASF) under one
# * or more contributor license agreements.  See the NOTICE file
# * distributed with this work for additional information
# * regarding copyright ownership.  The ASF licenses this file
# * to you under the Apache License, Version 2.0 (the
# * "License"); you may not use this file except in compliance
# * with the License.  You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# */

# Set environment variables here.

# This script sets variables multiple times over the course of starting an hbase-indexer process,
# so try to keep things idempotent unless you want to take an even deeper look
# into the startup scripts (bin/hbase-indexer, etc.)

# The java implementation to use.  Java 1.6 required.
# export JAVA_HOME=/usr/java/jdk1.6.0/

# Extra Java CLASSPATH elements.  Optional.
# export HBASE_INDEXER_CLASSPATH=

# The maximum amount of heap to use, in MB. Default is 1000.
# export HBASE_INDEXER_HEAPSIZE=1000

# Extra Java runtime options.
# Below are what we set by default.  May only work with SUN JVM.
# For more on why as well as other possible settings,
# see http://wiki.apache.org/hadoop/PerformanceTuning
export HBASE_INDEXER_OPTS="-XX:+UseConcMarkSweepGC"

# Uncomment below to enable java garbage collection logging for the server-side processes
# this enables basic gc logging for the server processes to the .out file
# export SERVER_GC_OPTS="-verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps $HBASE_INDEXER_GC_OPTS"

# this enables gc logging using automatic GC log rolling. Only applies to jdk 1.6.0_34+ and 1.7.0_2+. Either use this set of options or the one above
# export SERVER_GC_OPTS="-verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=1 -XX:GCLogFileSize=512M $HBASE_INDEXER_GC_OPTS"

# Uncomment below to enable java garbage collection logging for the client processes in the .out file.
# export CLIENT_GC_OPTS="-verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps $HBASE_INDEXER_GC_OPTS"

# Uncomment below (along with above GC logging) to put GC information in its own logfile (will set HBASE_INDEXER_GC_OPTS).
# This applies to both the server and client GC options above
# export HBASE_INDEXER_USE_GC_LOGFILE=true


# Uncomment and adjust to enable JMX exporting
# See jmxremote.password and jmxremote.access in $JRE_HOME/lib/management to configure remote password access.
# More details at: http://java.sun.com/javase/6/docs/technotes/guides/management/agent.html
#
# export HBASE_INDEXER_JMX_BASE="-Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false"
# export HBASE_INDEXER_OPTS="$HBASE_INDEXER_OPTS $HBASE_INDEXER_JMX_BASE -Dcom.sun.management.jmxremote.port=10105"

# Where log files are stored.  $HBASE_INDEXER_HOME/logs by default.
# export HBASE_INDEXER_LOG_DIR=${HBASE_INDEXER_HOME}/logs

# Enable remote JDWP debugging of the hbase-indexer process. Meant for Core Developers
# export HBASE_INDEXER_OPTS="$HBASE_INDEXER_OPTS -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=n,address=8075"

# A string representing this instance of hbase. $USER by default.
# export HBASE_INDEXER_IDENT_STRING=$USER

# The scheduling priority for daemon processes.  See 'man nice'.
# export HBASE_INDEXER_NICENESS=10

# The directory where pid files are stored. /tmp by default.
# export HBASE_INDEXER_PID_DIR=/var/hbase-indexer/pids

# The default log rolling policy is RFA, where the log file is rolled as per the size defined for the
# RFA appender. Please refer to the log4j.properties file to see more details on this appender.
# In case one needs to do log rolling on a date change, one should set the environment property
# HBASE_INDEXER_ROOT_LOGGER to "<DESIRED_LOG LEVEL>,DRFA".
# For example:
# HBASE_INDEXER_ROOT_LOGGER=INFO,DRFA
# The reason for changing default to RFA is to avoid the boundary case of filling out disk space as 
# DRFA doesn't put any cap on the log size. Please refer to HBase-5655 for more context.
