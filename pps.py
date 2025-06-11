'''
   PythonPortScanner.py
   
   Usage: pps [c|v] <address> [-p 0-65535]
'''

import time
import math
import socket
import asyncio
import argparse

MAX_NUM_OPEN_SOCK: int = 1000


def check_ip(ip: str) -> bool:
    '''Checks if passed string is a valid IP Address'''
    try:
        socket.inet_aton(ip)
        return True
    except OSError:
        return False


async def test_port(host: str, port: int, semaphore: asyncio.Semaphore) \
        -> tuple[str, str | None, str | None]:
    '''Creates a worker socket for async'''
    async with semaphore:
        loop = asyncio.get_event_loop()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        socket.setdefaulttimeout(1)
        port_str = str(port) + "/tcp"
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


async def main(host: str, start_port: int, end_port: int, verbose: bool) -> None:
    '''This is the main function'''

    if not check_ip(host):
        host = socket.gethostbyname(host)

    opened = []
    timed_out = 0
    refused = 0
    processed_ports = {}
    print("="*50)
    print(f"Using address: {host}")
    start_time = time.time()

    # For each port, check to see if you are able to connect
    tasks: list[asyncio.Task] = []
    semaphore = asyncio.Semaphore(MAX_NUM_OPEN_SOCK)
    async with asyncio.TaskGroup() as group:
        for port in range(start_port, end_port):
            task = group.create_task(test_port(host, port, semaphore))
            tasks.append(task)
    results = [task.result() for task in tasks]

    # Once all ports have been tested, process results
    for r in results:
        processed_ports[r[0]] = (r[1], r[2])
        match r[1]:
            case "Open":
                opened.append(r[0].replace("/tcp", ""))
            case "Refused":
                refused += 1
            case "Timeout":
                timed_out += 1

    finish_time = int(math.trunc(time.time() - start_time))

    print("="*50)
    print(
        f"Done! Time Elapsed: {int(finish_time//60)}:{int(finish_time % 60):0>2}")
    print("="*50)
    searchspace = len(opened) + timed_out + refused

    if not verbose:
        print(f"Closed Ports: {refused}/{searchspace}")
        print(f"Timed Out Ports: {timed_out}/{searchspace}")
        print(f"Open Ports: {len(opened)}/{searchspace}\n{opened}")
    else:
        print(f"Closed Ports: {refused}/{searchspace}")
        print(f"Open Ports:\n{'Port': <8} {'State': <8} Service")
        for port, port_info in processed_ports.items():
            if port_info[0] == "Refused":
                continue
            print(f"{port: <8} {port_info[0]: <8} {port_info[1]}")
    print("="*50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scans open ports on given host")
    parser.add_argument(
        "host",
        help="Select the host that you would like to scan. Can be IPv4 addr or an FQDN.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Shows detailed port information, rather than just lists open ports.",
        action="store_true"
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Specifiy what port(s) to search thourgh. Default = 1-65536",
        dest="port_range",
        default="1-65536"
    )
    args = parser.parse_args()

    if args.port_range.index("-") > -1:
        start, end = args.port_range.split("-")
        sp = int(start)
        ep = int(end)
    elif args.port_range.isnumeric():
        sp = ep = int(args.port_range)
    else:
        raise OSError("Invaid port Selection")

    asyncio.run(main(args.host, sp, ep, args.verbose))
