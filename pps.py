'''
   PythonPortScanner.py
   
   Usage: pps [c|v] <address> [-p 0-65535]
'''

import sys
import socket
import asyncio

MAX_PORT_NUMBER = 65536
MAX_NUM_OPEN_SOCK = 100


def check_ip(ip: str) -> bool:
    '''Checks if passed string is a valid IP Address'''
    try:
        socket.inet_aton(ip)
        return True
    except OSError:
        return False


async def test_port(host: str, port: int) -> tuple[str, str, str]:
    '''Creates a worker socket for async'''
    loop = asyncio.get_event_loop()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)
    socket.setdefaulttimeout(1)
    port_str = str(port) + "\\tcp"
    port_state = None
    port_service = None

    # Is the Port open?
    try:
        await loop.sock_connect(s, (host, port))
        port_state = "Open"
        port_service = socket.getservbyport(port)
    except ConnectionRefusedError:
        port_state = "Refused"
    except TimeoutError:
        port_state = "Timeout"
    except OSError:
        port_service = "Unknown"
    finally:
        s.close()

    return port_str, port_state, port_service


async def main() -> None:
    '''This is the main function'''

    loc = sys.argv[1]
    if check_ip(loc):
        host = loc
    else:
        host = socket.gethostbyname(loc)

    mode = "v"
    # returns 0 if connection succeeds else raises error
    # address and port in the tuple format
    iters: int = (MAX_PORT_NUMBER // MAX_NUM_OPEN_SOCK) + 1
    opened = 0
    timed_out = 0
    refused = 0
    processed_ports = {}
    print(f"Using address: {host}")
    print("="*50)
    for i in range(iters):
        low_bound = i * MAX_NUM_OPEN_SOCK
        high_bound = min(low_bound + MAX_NUM_OPEN_SOCK, MAX_PORT_NUMBER)
        print(f"Checking Ports {low_bound}:{high_bound}", end="\r")
        tasks = [test_port(host, p) for p in range(low_bound, high_bound)]
        results = await asyncio.gather(*tasks)

        for r in results:
            processed_ports[r[0]] = (r[1], r[2])
            match r[1]:
                case "Open":
                    opened += 1
                case "Refused":
                    refused += 1
                case "Timeout":
                    timed_out += 1

        if high_bound == MAX_PORT_NUMBER:
            print(f"Checking Ports {low_bound}:{high_bound}")

    print("="*50)
    print("Done!")
    print("="*50)
    searchspace = opened + timed_out + refused
    if mode == "c":
        print(f"Open Ports: {opened}/{searchspace}")
        print(f"Timsed Out Ports: {timed_out}/{searchspace}")
        print(f"Closed Ports: {refused}/{searchspace}")
    else:
        print(f"Closed Ports: {refused}/{searchspace}")
        print(f"Open Ports:\n{'Port': <8} {'State': <8} Service")
        for port, port_info in processed_ports.items():
            if port_info[0] == "Refused":
                continue
            print(f"{port: <8} {port_info[0]: <8} {port_info[1]}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
