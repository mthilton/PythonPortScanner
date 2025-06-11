# Python Port Scanner

usage: pps.py [-h] [-v] [-p PORT_RANGE] host

Scans open ports on given host

positional arguments:
  host                  Select the host that you would like to scan. Can be IPv4 addr or an FQDN.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Shows detailed port information, rather than just lists open ports.
  -p, --port PORT_RANGE
                        Specifiy what port(s) to search thourgh. Default = 1-65536
