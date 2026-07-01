# Mininet-WiFi API — Week 4 Notes

Mininet-WiFi is a fork of Mininet adding WiFi stations and APs. It inherits everything from Mininet (node.cmd(), CLI py trick, net.stop()) and adds wireless primitives on top. Uses `net.build()` instead of `net.start()` — same blueprint-vs-real boundary applies.

**Core primitives:**
- `net.addAccessPoint('ap1', ssid='name', mode='g', channel='5', position='x,y,0')` — creates WiFi AP
- `net.addStation('sta1', ip='10.0.0.1/8', position='x,y,0')` — creates WiFi station
- `net.configureNodes()` — generates hostapd/wpa_supplicant configs before build, no Containernet equivalent

**params dictionary — don't trust for live state:**
Verified by hand: `sta1.params['rssi']` returned string 'rssi' (key missing), `ap1.params['channel']` showed '5' after successful switch to channel 11. params is a build-time snapshot only — always read live state from iw or hostapd_cli instead. One reliable use: `ap.params['wlan'][0]` gives the interface name needed for all iw commands.

**get_wifi_stats(ap) — confirmed mechanism:**
`ap.cmd('iw dev ' + ap.params['wlan'][0] + ' station dump')` returns all associated stations with RSSI, TX/RX rates, connection time. Verified — returned two stations at -36 dBm each. No associatedStations key exists in ap.params — iw station dump is the only reliable source.

**set_channel(ap, channel) — confirmed mechanism:**
Raw `iw set channel` fails ("Device or resource busy") while hostapd runs. Correct approach:
`ap.cmd('hostapd_cli -i ' + ap.params['wlan'][0] + ' chan_switch 1 ' + str(freq))`
where `freq = 2407 + (channel * 5)`. Verified — successfully changed ap1 from channel 5 to 11. Must manually update `ap.params['channel'] = str(channel)` after switch since params stays stale.

**wmediumd required for realistic RSSI:**
Plain Mininet_wifi() gives fixed -36 dBm regardless of position. For RSSI to vary with distance (needed for Use Case 2 threshold check), topology must use `Mininet_wifi(link=wmediumd, wmediumd_mode=interference)` with explicit positions and `net.setPropagationModel(model="logDistance", exp=4)`.

**Five wired vs wireless architectural differences:**
1. Links: wired = explicit Python objects; wireless = implicit kernel state from position/signal
2. State: wired = TCIntf objects; wireless = kernel only, params unreliable for runtime changes
3. Modification: wired = one intf.config() call; wireless = separate tools per parameter
4. Measurement: wired = RTT/throughput from traffic; wireless = RSSI/channel from kernel queries
5. Concurrent operation: both backends conflict if run simultaneously — Use Case 3 needs Prof. Lehmann clarification on whether Docker containers are required or plain Mininet hosts suffice

**Session prerequisite:** `sudo modprobe mac80211_hwsim radios=4` before every Mininet-WiFi session — cleanup unloads it on exit.
