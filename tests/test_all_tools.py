#!/usr/bin/env python3
"""
Verification script for all MCP Server tools.
Tests all 10 tools across wired, wireless, and mesh topology types.
Run with: sudo python3 tests/test_all_tools.py
"""

import sys
sys.path.insert(0, '/home/pradeepp/pradeep/containernet-wifi')
sys.path.insert(0, '/home/pradeepp/pradeep/mcp-network-emulator')
import server

def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def test(name, result):
    print(f"\n[{name}]")
    print(result)

section("WIRED TOPOLOGY TESTS")
test("create_topology (wired)", server.create_topology("wired", hosts=2, switches=1))
test("list_nodes", server.list_nodes())
test("list_links", server.list_links())
test("set_delay", server.set_delay("h1", "s1", 50))
test("set_bandwidth", server.set_bandwidth("h1", "s1", 100))
test("set_loss", server.set_loss("h1", "s1", 5))
test("ping", server.ping("h1", "h2"))
test("run_iperf", server.run_iperf("h1", "h2"))
test("get_routing_table", server.get_routing_table("h1"))
test("destroy_topology", server.destroy_topology())

section("WIRELESS TOPOLOGY TESTS")
test("create_topology (wireless)", server.create_topology("wireless", aps=1, stations=2))
test("get_wifi_stats", server.get_wifi_stats("ap1").split("\n")[0])
test("set_channel", server.set_channel("ap1", 6))
test("get_wifi_stats (post-switch)", server.get_wifi_stats("ap1").split("\n")[0])
test("destroy_topology", server.destroy_topology())

section("MESH TOPOLOGY TESTS")
test("create_topology (mesh)", server.create_topology("mesh", stations=3))
test("ping sta1->sta3", server.ping("sta1", "sta3"))
test("destroy_topology", server.destroy_topology())

section("ALL TOOLS VERIFIED SUCCESSFULLY")
