'''
   PythonPortScanner.py
   
   Usage: pps [c|v] <address> [-p 0-65535]
'''

import sys
# import re
import socket
import asyncio


# USAGE = "Usage: pps [c|v] <address> [p 0-65535]"
MAX_PORT_NUMBER = 65536
MAX_NUM_OPEN_SOCK = 100


def check_ip(ip: str) -> bool:
    '''Checks if passed string is a valid IP Address'''
    try:
        socket.inet_aton(ip)
        return True
    except OSError:
        return False


async def test_port(host: str, port: int) -> tuple[int, str]:
    '''Creates a worker socket for async'''
    loop = asyncio.get_event_loop()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)
    try:
        await loop.sock_connect(s, (host, port))
        res = (port, "Open")
    except ConnectionRefusedError:
        res = (port, "Refused")
    except TimeoutError:
        res = (port, "Timeout")
    finally:
        # closes te object
        s.close()
    return res

# def handle_args() -> tuple[str, str | None, int | None]:
#     '''This function is used to handle passed in or incorrect arguments'''
#     mode = "c"
#     ip = None
#     port = None
#     for arg in sys.argv:
#         arg.replace("-", "")

#         # arg 0 is always the name of the program
#         if arg.find("pps") > -1:
#             continue

#         # Set Mode
#         if re.match(r"[c|v]{1}", arg.lower()):
#             mode = arg
#             continue

#         # Set IP
#         ip = check_ip(arg)
#         if not ip:
#             raise OSError(f"{arg} is not a valid IP")

#         # Set port number if supplied
#         port_args = arg.split()
#         opt = port_args[0].lower()
#         port_num = 0
#         if opt == "p":
#             try:
#                 port_num = int(port_args[2])
#             except ValueError as e:
#                 raise ValueError(f"Invaled Argument {arg}\n{USAGE}") from e

#         if 0 <= port_num < MAX_PORT_NUMBER:
#             port = port_num
#             continue

#         # If we get here we did not get a proper argument
#         raise ValueError(f"Invaled Argument {arg}\n{USAGE}")

#     return mode, ip, port


async def main() -> None:
    '''This is the main function'''

    host = sys.argv[1]
    if not check_ip(host):
        raise OSError(f"{host} is not a valid IPv4 Addr")

    mode = "c"
    # returns 0 if connection succeeds else raises error
    # address and port in the tuple format
    socket.setdefaulttimeout(1)
    iters: int = (MAX_PORT_NUMBER // MAX_NUM_OPEN_SOCK) + 1
    opened = []
    timed_out = []
    refused = []
    for i in range(iters):
        low_bound = i * MAX_NUM_OPEN_SOCK
        high_bound = min(low_bound + MAX_NUM_OPEN_SOCK, MAX_PORT_NUMBER)
        print(f"Checking Ports {low_bound}:{high_bound}", end="\r")
        tasks = [test_port(host, p) for p in range(low_bound, high_bound)]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r[1] == "Open":
                opened.append(r[0])
            if r[1] == "Refused":
                refused.append(r[0])
            if r[1] == "Timeout":
                timed_out.append(r[0])
        if high_bound == MAX_PORT_NUMBER:
            print(f"Checking Ports {low_bound}:{high_bound}")

    print("="*50)
    print("Done!")
    print("="*50)
    if mode == "c":
        searchspace = len(opened) + len(timed_out) + len(refused)
        print(f"Open Ports: {len(opened)}/{searchspace}")
        print(f"Timsed Out Ports: {len(timed_out)}/{searchspace}")
        print(f"Closed Ports: {len(refused)}/{searchspace}")
    else:
        print(f"Open Ports: {opened}")
        print(f"Timed Out Ports: {timed_out}")
        print(f"Closed Ports: {refused}")


if __name__ == "__main__":
    asyncio.run(main())
