#Documentation to make EL(K)/Suricata run with a PI (ARM Architecture) as satellite

The main goal is to setup a PI (or many PI's) as (an) satellite(s) with an IDS (suricata, logstash) and a server (e.g. debian linux) as some kind of graphical display (elasticsearch). So you can monitor network activities on your home network.

**Packages**

- suricata 3.0
- logstash 2.2.2
- elasticsearch 2.2.0
- kibana 4.4.1

# SURICATA
#### Install Dependencies

    apt-get install wget build-essential libpcre3-dev libpcre3-dbg automake
    autoconf libtool libpcap-dev libnet1-dev libyaml-dev zlib1g-dev
    libcap-ng-dev libjansson-dev ethtool

*Maybe some packages are not available or be renamed --> take what you get*

#### Download suricata

    wget http://www.openinfosecfoundation.org/download/suricata-3.0.tar.gz
    tar -xvzf suricata-3.0.tar.gz
    cd suricata-3.0
    ./configure --sysconfdir=/etc --localstatedir=/var
    make
    make install
    make install-conf
    make install-rules

#### Config Suricata
    nano /etc/suricata/suricata.yaml

###### suricata.yaml
    default-log-dir: /var/log/suricata
    ...
    vars:
        HOME_NET: "[IP-NETZ/MASKE]"
        EXTERNAL_NET: "!$HOME_NET"
        HTTP_PORTS: "80"
        SHELLCODE_PORTS: "180"
        SSH_PORTS: "22"

    threading:
        set-cpu-affinity: no
        detect-thread-ratio: 1.5


There is a whole bunch more to setup in that config.
But for the start, these settings should be enough.
For further questions, tasks and config possibilities, just check google. It's easy to find.

#### Start it!
For pcap-mode:

Run this command only this time

    ethtool -K eth0 gro off lro off

Start with the config.

    suricata -c /etc/suricata/suricata.yaml -i eth0
    ...

Stop it with Ctrl+c and see what the IDS detected.


    less /var/log/suricata/fast.log

or

    less /var/log/suricata/eve.json

# Elasticsearch
### Let's get the server to work
#### Install JDK8
Download the JDK8 32 Bit Version (if you have a 64-bit architecure, so
download the 64-bit version) to your computer. Now copy it to your server (e.g. a debian linux server).

    scp jdk-8-xxxxxxxxxxxxxxxxxxxxxx.gz root@IP:/jdk-8.gz

Now there is a gz-file in your / directory.
Follow these steps to install it correctly.

    mkdir -p /opt/java
    chown root:root /opt/java
    cd /opt/java
    mv /jdk-8.0.gz /opt/java
    tar -xvzf jdk-8.0.gz

if it was successful to untar it, clean up your space

    rm jdk-8.0.gz

Let your system know there to find the java-files

    update-alternatives --install "/usr/bin/java" "java" "/opt/java/jdk1.8.0/bin/java" 1
    update-alternatives --set java /opt/java/jdk1.8.0/bin/java

Let's see if it worked...

    java -version

Maybe you have to reboot your system.
If everything went fine, there is an output with your java
version.

Set the HOME_DIR for Java:

    nano /etc/environment

add the following line:

    JAVA_HOME="/opt/java/jdk1.8.0"

edit your ~/.bashrc with appending these lines at the end:

    export JAVA_HOME="/opt/java/jdk1.8.0"
    export PATH=$PATH:$JAVA_HOME/bin

reboot your PI and then see if your changes work:

    echo $JAVA_HOME

#### Install Elasticsearch

Create a directory to there it should be installed (e.g. /usr/src/)

    mkdir /usr/src/elasticsearch
    cd /usr/src/elasticsearch

Create a user for executing elasticsearch

    adduser USER
    su USER

*!!Mind to never start elasticsearch as root!!*

Download and untar it

    wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.2.0/elasticsearch-2.2.0.tar.gz
    tar -zxvf elasticsearch-2.2.0.tar.gz

Clean up the chaos and start it

    rm elasticsearch-2.2.0.tar.gz
    bin/elasticsearch

It could take some seconds to start.
If theres no error while starting, open up a browser on your PC/Laptop and type:

    http://localhost:9200/

or

    http://IP-OF-YOUR-PI:9200/

There should be the following output:

    {
      "ok" : true,
      "status" : 200,
      "name" : "XXX, XXX",
      "version" : {
        "number" : "0.90.0",
        "snapshot_build" : false
        },
      "tagline" : "You Know, for Search"
    }

To test it on the PI, just type:

    curl -XGET http://localhost:9200/

or

    curl -XGET http://IP-OF-YOUR-PI:9200/

You should see the same output right on your commandline.

To make it more graphic, do this:

    cd /usr/src/elasticsearch/elasticsearch-2.2.0/bin
    ./plugin install mobz/elasticsearch-head

So you know have the graphics but elasticsearch is not so elastic yet.
Look into the elasticsearch.yaml config and change like you want to.

    nano /config/elasticsearch.yaml

after that you can open up a browser on your PC/Laptop and type:

    http://localhost:9200/_plugin/head/

or

    http://IP-OF-YOUR-PI:9200/_plugin/head/

You should a graphical frontend for the data suricata sends.
But until now, suricata sends no data so elasticsearch. It doesn't know how. For this, we need another tool on the PI('s) Logstash.

# Logstash
#### Download Logstash

    cd /usr/src
    wget https://download.elastic.co/logstash/logstash/logstash-2.2.2.tar.gz
    tar -xvzf logstash-2.2.2.tar.gz

Clean up

    rm logstash-2.2.2.tar.gz

#### Make Logstash work
You need to do a workaround for jruby to get logstash run on the PI:

    apt-get install ant
    $ git clone https://github.com/jnr/jffi.git
    cd jffi/
    ant jar

After you compiled jffi, move to the directory in logstash where jruby is located

    cd logstash-2.2.2/vendor/jruby/lib/
    mkdir -p jni/arm-linux/
    cp /usr/src/jffi/build/jni/libjffi-1.2.so /usr/src/logstash-2.2.2/vendor/jruby/lib/jni/arm-linux

#### Test it!

    USE_JRUBY=1 LS_HEAP_SIZE=64m ./bin/logstash -e 'input { stdin { } } output { stdout { } }'

After this command you can type something (e.g. Test)

    Test

Little bit later there's an output

    TIMESTAMP $HOST_NAME Test

#### Make a config for filtering
##### You have to say logstash what it should forward to elasticsearch

    cd /usr/src/logstash-2.2.2
    nano logstash.conf

E.g. something like this:

    input {
      file {
        path => ["/var/log/suricata/eve.json"]
        codec =>   json
        type => "SuricataIDPS"
      }

    }

    filter {
      if [type] == "SuricataIDPS" {
      date {
        match => [ "timestamp", "ISO8601" ]
      }
      ruby {
        code => "if event['event_type'] == 'fileinfo'; event['fileinfo']['type']=event['fileinfo']['magic'].to_s.split(',')[0]; end;"
      }
    }
    // you can us Google for more filters ;).

    output {
      elasticsearch {
      hosts => localhost
      #protocol => http
      }
    }

HINT: If you want to forward the data, logstash collected, to elasticsearch on another maschine,
you have to change the host to

      [...]
      hosts => 'IP-Address'
      protocol => http //https is always better!
      [...]

# Start the whole package!
On your PI

    suricata -c /etc/suricata/suricata.yaml -i eth0 //there is an option to run it as a daemon --> stoppable via proc-kill

    cd /usr/src/logstash-2.2.2
    bin/logstash -f logstash.conf

On your server

    su USER
    cd /usr/src/elasticsearch/elasticsearch-2.2.0/
    bin/elasticsearch -d //run as daemon

Now visit in your favorite browser

    http://IP-OF-YOUR-PI:9200/_plugin/head

You should see that there are indicies from logstash!

Under "browse" you can see everything whats detected by suricata and read by logstash from eve.json.
You're able to filter on the left side.

#### HINT
It is possible to forward other well-formed data like JSON to elasticsearch. Just tell it logstash like in this example.
(There are more JSON-files from suricata, e.g. dns.log, fast.log,...)

Without any filter, you see every message/packet suricata collected -- be careful with your resources ;).

Have fun!
