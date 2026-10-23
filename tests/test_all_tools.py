#!/usr/bin/env python3
"""
Verification script for all MCP Server tools.
Verification script for MCP Server tools.
Tests wired, wireless, and mesh topologies.

Run from the project directory:
    sudo python3 tests/test_all_tools.py
"""

import sys
import traceback

sys.path.insert(0, "/home/pradeepp/pradeep/containernet-wifi")
sys.path.insert(0, "/home/pradeepp/pradeep/mcp-network-emulator")

import server

results = []


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def test(name, operation, *args, **kwargs):
    """Run one test and record whether it returned an apparent error."""
    print(f"\n[{name}]")

    try:
        result = operation(*args, **kwargs)
        print(result)

        # These tools normally return text; catch exceptions and obvious
        # error messages without assuming every result must be a dict.
        failed = result is None

        if isinstance(result, str):
            message = result.lower()

            failure_markers = (
                "error:",
                "exception:",
                "traceback",
                "no active topology",
                "no result returned",
                "test ran but could not parse output",
            )

            failed = any(marker in message for marker in failure_markers)

        if name == "ping" or name.startswith("ping "):
            failed = failed or (
                isinstance(result, str)
                and "100% packet loss" in result.lower()
            )


        status = "FAIL" if failed else "PASS"
        print(f"RESULT: {status}")

        results.append((name, status))
        return result

    except Exception as exc:
        print(f"EXCEPTION: {exc}")
        traceback.print_exc()
        results.append((name, "FAIL"))
        return None


def cleanup():
    """Attempt to stop the current topology."""
    test("destroy_topology (cleanup)", server.destroy_topology)


try:
    section("WIRED TOPOLOGY TESTS")
    test(
        "create_topology (wired)",
        server.create_topology,
        "wired",
        hosts=2,
        switches=1,
    )
    test("list_nodes", server.list_nodes)
    test("list_links", server.list_links)
    test("set_delay", server.set_delay, "h1", "s1", 50)
    test("set_bandwidth", server.set_bandwidth, "h1", "s1", 100)
    test("set_loss", server.set_loss, "h1", "s1", 5)
    test("ping", server.ping, "h1", "h2")
    test("run_iperf", server.run_iperf, "h1", "h2")
    test("get_routing_table", server.get_routing_table, "h1")
finally:
    cleanup()

try:
    section("WIRELESS TOPOLOGY TESTS")
    test(
        "create_topology (wireless)",
        server.create_topology,
        "wireless",
        aps=1,
        stations=2,
    )
    test("get_wifi_stats", lambda: server.get_wifi_stats("ap1").split("\n")[0])
    test("set_channel", server.set_channel, "ap1", 6)
    test(
        "get_wifi_stats (post-switch)",
        lambda: server.get_wifi_stats("ap1").split("\n")[0],
    )
finally:
    cleanup()

try:
    section("MESH TOPOLOGY TESTS")
    test(
        "create_topology (mesh)",
        server.create_topology,
        "mesh",
        stations=3,
    )
    test("ping sta1->sta3", server.ping, "sta1", "sta3")
finally:
    cleanup()

section("FINAL TEST SUMMARY")
passed = sum(status == "PASS" for _, status in results)
failed = sum(status == "FAIL" for _, status in results)

for name, status in results:
    print(f"{status:4}  {name}")

print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")

if failed:
    print("TEST RUN FAILED: Review the failed tests above.")
    sys.exit(1)

print("TEST RUN COMPLETED: No obvious errors were detected.")
sys.exit(0)
