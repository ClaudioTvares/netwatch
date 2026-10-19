"""Network check logic for Netwatch."""

import socket
import time
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    """The possible outcomes of a check."""
    ONLINE       = "online"
    HOST_DOWN    = "host_down"
    PORT_BLOCKED = "port_blocked"
    TIMEOUT      = "timeout"


@dataclass
class CheckResult:
    """The result of checking one device once."""
    state: State
    latency_ms: float | None
    error: str | None


# ---------------------------------------------------------------------
# TCP connect test
# ---------------------------------------------------------------------

def tcp_check(ip: str, port: int, timeout: float = 3.0) -> CheckResult:
    """Attempt a TCP connection to ip:port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    start_time = time.perf_counter()
    
    try:
        sock.connect((ip, port))
        latency = (time.perf_counter() - start_time) * 1000
        return CheckResult(State.ONLINE, latency, None)
    except socket.timeout:
        return CheckResult(State.TIMEOUT, None, "TCP timeout")
    except ConnectionRefusedError:
        return CheckResult(State.PORT_BLOCKED, None, "Connection refused")
    except OSError as e:
        return CheckResult(State.HOST_DOWN, None, str(e))
    finally:
        sock.close()


# ---------------------------------------------------------------------
# ICMP (ping) test
# ---------------------------------------------------------------------

def icmp_check(ip: str, timeout: float = 2.0) -> bool:
    """Return True if the host responds to ICMP echo, else False."""
    try:
        from icmplib import ping
        host = ping(ip, count=1, timeout=timeout, privileged=False)
        return host.is_alive
    except Exception:
        return False


# ---------------------------------------------------------------------
# The one function the rest of the app calls
# ---------------------------------------------------------------------

def full_check(
    ip: str,
    port: int | None,
    tcp_timeout: float = 3.0,
    icmp_timeout: float = 2.0,
) -> CheckResult:
    """Run the most informative check possible for this device."""
    if port:
        result = tcp_check(ip, port, timeout=tcp_timeout)
        if result.state == State.ONLINE:
            return result

        # TCP failed. Is the host at least alive?
        if icmp_check(ip, timeout=icmp_timeout):
            return CheckResult(
                State.PORT_BLOCKED, None,
                result.error or "TCP failed but host is reachable",
            )

        return CheckResult(State.HOST_DOWN, None, result.error)

    # No port configured: rely purely on ICMP.
    if icmp_check(ip, timeout=icmp_timeout):
        # For ICMP checks, we don't measure latency in this simple implementation
        return CheckResult(State.ONLINE, None, None)
    return CheckResult(State.HOST_DOWN, None, "ICMP failed")