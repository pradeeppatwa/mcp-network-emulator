#!/usr/bin/env python3
"""
Effect test for the link impairment tools.
Checks that delay, bandwidth and loss on one link are kept together and that
a single setting can be removed again.
Run with: sudo python3 tests/test_impairments.py
"""
import sys
sys.path.insert(0, '/home/pradeepp/pradeep/containernet-wifi')
sys.path.insert(0, '/home/pradeepp/pradeep/mcp-network-emulator')
import re
import server

def rtt(result):
    return float(re.search(r"= ([\d.]+)/", result).group(1))

def rules(node, intf):
    return server.net.get(node).cmd(f"tc qdisc show dev {intf}")

def check(name, ok):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        raise SystemExit(1)

server.create_topology("wired", hosts=2, switches=1)
try:
    base = rtt(server.ping("h1", "h2"))
    check(f"baseline RTT is small ({base:.2f} ms)", base < 10)

    server.set_delay("h1", "s1", 50)
    d = rtt(server.ping("h1", "h2"))
    check(f"delay of 50 ms raises the RTT ({d:.1f} ms)", 45 <= d <= 70)

    server.set_bandwidth("h1", "s1", 100)
    d2 = rtt(server.ping("h1", "h2"))
    check(f"delay is kept after set_bandwidth ({d2:.1f} ms)", 45 <= d2 <= 70)
    check("bandwidth limit (htb) is active on h1-eth0", "htb" in rules("h1", "h1-eth0"))

    server.set_loss("h1", "s1", 5)
    r = rules("h1", "h1-eth0")
    check("delay, bandwidth and loss are all active on h1-eth0",
          "delay 50ms" in r and "loss 5%" in r and "htb" in r)
    r2 = rules("s1", "s1-eth1")
    check("bandwidth and loss are active on s1-eth1", "htb" in r2 and "loss 5%" in r2)

    server.set_delay("h1", "s1", 0)
    r = rules("h1", "h1-eth0")
    check("delay can be removed without touching the others",
          "delay 50ms" not in r and "loss 5%" in r and "htb" in r)
finally:
    server.destroy_topology()
print("ALL IMPAIRMENT CHECKS PASSED")
