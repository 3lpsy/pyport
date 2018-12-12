# Pyport

A simple multi threaded port scanner written in python3 with no dependencies.

## Pro Tip

Sometimes interesting things happen. If you use -vv, pyport will display exception messages when encountering an error that is not related to timeouts. I recommend using -vv when using pyport.

```
usage: pyport.py [-h] -t TARGET [-p PORT [PORT ...]] [-P {tcp,udp,http,https}]
                 [-m MIN_PORT] [-M MAX_PORT] [-T THREADS] [--timeout TIMEOUT]
                 [--verbose] [--no-random]

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        desired target (ip)
  -p PORT [PORT ...], --port PORT [PORT ...]
                        ports (-p 1 2 3, -p 1-5, or -p 1,2,3)
  -P {tcp,udp,http,https}, --proto {tcp,udp,http,https}
                        protocol
  -m MIN_PORT, --min-port MIN_PORT
                        min port (range)
  -M MAX_PORT, --max-port MAX_PORT
                        max port (range)
  -T THREADS, --threads THREADS
                        do you want to go fast?
  --timeout TIMEOUT     set timeout
  --verbose, -v         verbosity (-v, -vv, -vvv, -vvvv)
  --no-random           don't randomize port order
```

TODO:
```
[ ] unique ports if passing in complex port formats
[ ] progress notification
[ ] rewrite in go
```
