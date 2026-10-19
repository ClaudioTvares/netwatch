"""Network check logic for Netwatch.

This module is purely functional — it doesn't touch the GUI, the
database, or licenses. It just answers one question:

    "Given this IP and port, what is the device's current state?"

The rest of the app (the engine thread, the GUI) calls `full_check()`
and acts on the result.

Why TCP first, ICMP second?
    * A TCP connect to the monitored port tells us exactly what we care
      about: "is the service reachable?"
    * ICMP tells us whether the machine itself is alive. If TCP fails
      but ICMP works, the port is blocked (service down or filtered).
    * If a device has no monitored port, ICMP is all we can do.
"""

import socket
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    """The possible outcomes of a check.

    Inheriting from `str` means these can be compared to plain strings
    (`State.ONLINE == "online"` is True) and serialized to JSON without
    any conversion. Very convenient.
    """
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
    """Attempt a TCP connection to ip:port.

    Returns a CheckResult with:
        * State.ONLINE       if the connection succeeds
        * State.PORT_BLOCKED if the host actively refused (RST)
        * State.TIMEOUT      if the connection just timed out
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        return CheckResult(State.ONLINE, None, None)
    except socket.timeout:
        return CheckResult(State.TIMEOUT, None, "TCP timeout")
    except ConnectionRefusedError:
        # The OS on the target explicitly said "nothing listening here".
        # The device is up, the port is not.
        return CheckResult(State.PORT_BLOCKED, None, "Connection refused")
    except OSError as e:
        # DNS failure, unreachable network, etc.
        return CheckResult(State.HOST_DOWN, None, str(e))
    finally:
        sock.close()


# ---------------------------------------------------------------------
# ICMP (ping) test
# ---------------------------------------------------------------------

def icmp_check(ip: str, timeout: float = 2.0) -> bool:
    """Return True if the host responds to ICMP echo, else False.

    Uses `icmplib`, which doesn't need administrator privileges on
    Windows because it falls back to an unprivileged ping mode.
    """
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
    """Run the most informative check possible for this device.

    * If a port is configured, start with TCP. On failure, ping to
      decide between "port blocked" and "host down".
    * If no port is configured, just ping.
    """
    if port:
        result = tcp_check(ip, port, timeout=tcp_timeout)
        if result.state == State.ONLINE:
            return result

        # TCP failed. Is the host at least alive?
        if icmp_check(ip, timeout=icmp_timeout):
            # Host is alive, but the port refused or timed out.
            return CheckResult(
                State.PORT_BLOCKED, None,
                result.error or "TCP failed but host is reachable",
            )

        # Neither TCP nor ICMP responded: assume host is down.
        return CheckResult(State.HOST_DOWN, None, result.error)

    # No port configured: rely purely on ICMP.
    if icmp_check(ip, timeout=icmp_timeout):
        return CheckResult(State.ONLINE, None, None)
    return CheckResult(State.HOST_DOWN, None, "ICMP failed")