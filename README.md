# rhscon-bootstrap-agent.py
* Bootstrap a client agent in Red Hat Storage Console 2.0 for the lazy:
~~~
$ bootstrap-client-agent.py --type mon --host ceph2.example.com --server
ceph1.example.com
~~~
* How about multiple clients of the same type:
~~~
$ ./bootstrap-client-agent.py --type osd --host
ceph5.example.com,ceph6.example.redhat.com --server
ceph1.example.com
~~~
