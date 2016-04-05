#Documentation to make ELK/Suricata/Asterisk/freepbx run on PI (ARM Architecture)

The major goal is to setup a PI with an IDS (suricata, logstash) and graphical display (elasticsearch, kibana).
Furthermore to make use of it, I set up an asterisk/freepbx telephony system on the PI.
If everything works fine, this should be my target, when I'm lay hands on Kali Linux.
The main task is it to hack the PI, see what the IDS is gonna do and find, maybe, some vulnerabilites and
security arrangements.

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

Run this only this time

    ethtool -K eth0 gro off lro off

Start with the config.

    suricata -c /etc/suricata/suricata.yaml -i eth0
    ...

Stop it with Ctrl+c and see what the IDS detected.


    less /var/log/suricata/fast.log

or

    less /var/log/suricata/eve.json


# Elasticsearch
#### Install JDK8
Download the JDK8-ARM 32 Bit Version (if you have a 64-bit architecure, so
download the 64-bit version).
You have to download it to your Computer and then copy it to your PI.

    scp jdk-8-ea-b36e-linux-arm-hflt-29_nov_2012.gz root@IP:/jdk-8.gz

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

If everything went fine, there is an output with your java version.
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

After that you have to change the elasticsearch.yaml config

    nano /config/elasticsearch.yaml



after that you can open up a browser on your PC/Laptop and type:

    http://localhost:9200/_plugin/head/

or

    http://IP-OF-YOUR-PI:9200/_plugin/head/

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


    output {
      elasticsearch {
      hosts => localhost
      #protocol => http
      }
    }

HINT: If you want to forward the data, logstash collected, to elasticsearch on another maschine,
you have to change the host to

      [...]
      hosts => 'IP-Adress'
      protocol => http
      [...]

# Start the whole package!
You will need **three** separate terminal windows!

First window

    suricata -c /etc/suricata/suricata.yaml -i eth0

Second window

    su NUTZER
    cd /usr/src/elasticsearch/elasticsearch-2.2.0/
    bin/elasticsearch

Third window

    cd /usr/src/logstash-2.2.2
    bin/logstash -f logstash.conf

Now visit in your favorite browser

    http://IP-OF-YOUR-PI:9200/_plugin/head

You should see that there are indicies from logstash!

Under "browse" you can see everything whats detected by suricata and read by logstash from eve.json.
You're able to filter on the left side.

# Kibana
#### Download it and make it work

Make sure you have the /var/www/ directory on your PI.
If not, install apache2

    apt-get install apache2

Now download Kibana for 32-Bit architecure

    cd /var/www/
    wget https://download.elastic.co/kibana/kibana/kibana-4.4.1-linux-x86.tar.gz
    tar -xzvf kibana-4.4.1-linux-x86.tar.gz

If you don't have node.js and npm on your PI, you have to install them both too.

    wget http://node-arm.herokuapp.com/node_latest_armhf.deb
    dpkg -i node_latest_armhf.deb
    apt-get install npm

Now you have to create some symlinks for the current node version

    mv /var/www/kibana-4.1.1-linux-x86/node/bin/node
    /var/www/kibana-4.1.1-linux-x86/node/bin/node.orig

    mv /var/www/kibana-4.1.1-linux-x86/node/bin/npm
    /var/www/kibana-4.1.1-linux-x86/node/bin/npm.orig

    ln -s /usr/local/bin/node /var/www/kibana-4.1.1-linux-x86/node/bin/node

    ln -s /usr/local/bin/npm /var/www/kibana-4.1.1-linux-x86/node/bin/npm

Configure Kibana

In your kibana directory under /config is a file named kibana.yml
Open it and edit the following lines:

    server.port: 5601
    server.host: "IP-OF-YOUR-PI"
    elasticsearch.url: "http://IP-OF-YOUR-PI:9200"
    kibana.index: ".kibana"

Start it!

Important:
You have to start elasticsearch **first** (remember not as root)!

First terminal

    su NUTZER
    cd /usr/src/elasticsearch/elasticsearch-2.2.0
    bin/elasticsearch

Second terminal

    cd /var/www/kibana-4.1.1-linux-x86/
    bin/kibana


You should see that node is starting and initializing kibana.
In both terminal windows you should see that both applications connecting to each other.

Open a browser of your choice

    http://IP-OF-YOUR-PI:5601

See the magic.
Don't worry, if you don't started logstash and suricata, there's nothing to show in kibana.
It's just a simple test to see if it runs correctly.
