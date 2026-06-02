"""
Telstra Network Fault Dataset Transformer
==========================================
Converts the real Telstra Network Disruptions dataset (Kaggle) into the
telecom incident schema required by the RAG pipeline.

Source: https://www.kaggle.com/competitions/telstra-recruiting-network
Real fault data from Australia's largest telecommunications carrier.

Field mapping:
  fault_severity (0/1/2)  → severity (P4-Low / P2-High / P1-Critical)
  event_type codes        → alarm_type (human-readable telecom alarm names)
  resource_type codes     → technology_type + device_vendor
  location codes          → network_region (North/South/East/West/Central)
  log feature volumes     → outage_duration, affected_subscribers (derived)
  All text fields         → deterministic rule-based templates (no LLM)
"""

import os
import re
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ─── Paths ─────────────────────────────────────────────────────────────────────

TELSTRA_PATH = r"C:\Users\praveen.kg\Desktop\Capstone_stuffsa\telstra-recruiting-network"
OUTPUT_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "telecom_incidents.csv"
)

# ─── Lookup Tables ─────────────────────────────────────────────────────────────

EVENT_TO_ALARM_TYPE = {
    "event_type 1":  "Hardware Failure",
    "event_type 2":  "Power Supply Fault",
    "event_type 3":  "Link Down",
    "event_type 4":  "Interface Error",
    "event_type 5":  "Signal Degradation",
    "event_type 6":  "Clock Sync Loss",
    "event_type 7":  "Board Failure",
    "event_type 8":  "Fan Unit Failure",
    "event_type 9":  "Temperature Alarm",
    "event_type 10": "Optical Power Loss",
    "event_type 11": "Link Flap",
    "event_type 12": "BGP Session Drop",
    "event_type 13": "OSPF Adjacency Loss",
    "event_type 14": "Fiber Cut",
    "event_type 15": "Physical Layer Fault",
    "event_type 17": "Packet Loss High",
    "event_type 18": "High Latency",
    "event_type 19": "Cell Outage",
    "event_type 20": "Handover Failure",
    "event_type 21": "Configuration Error",
    "event_type 22": "Firmware Upgrade Failure",
    "event_type 23": "Software Bug",
    "event_type 24": "Process Crash",
    "event_type 25": "Memory Exhaustion",
    "event_type 26": "CPU Overload",
    "event_type 27": "Disk Full",
    "event_type 28": "Database Corruption",
    "event_type 29": "License Expiry",
    "event_type 30": "Authentication Failure",
    "event_type 31": "Capacity Exceeded",
    "event_type 32": "Network Congestion",
    "event_type 33": "Traffic Overload",
    "event_type 34": "Threshold Breach",
    "event_type 35": "Traffic Spike",
    "event_type 36": "RRU Fault",
    "event_type 37": "Antenna Failure",
    "event_type 38": "VSWR Alarm",
    "event_type 39": "Feeder Cable Fault",
    "event_type 40": "Cell Capacity Degradation",
    "event_type 41": "Node Restart",
    "event_type 42": "Emergency Restart",
    "event_type 43": "Watchdog Timeout",
    "event_type 44": "Core Dump",
    "event_type 45": "NTP Sync Failure",
    "event_type 46": "DNS Resolution Failure",
    "event_type 47": "SNMP Trap Flood",
    "event_type 48": "Alarm Storm",
    "event_type 49": "Cascading Failure",
    "event_type 50": "Hardware Degradation",
    "event_type 51": "Interface CRC Errors",
    "event_type 52": "Routing Loop",
    "event_type 53": "VPN Tunnel Down",
    "event_type 54": "Multicast Failure",
}

RESOURCE_TO_TECH = {
    "resource_type 1":  "5G-NR",
    "resource_type 2":  "4G-LTE",
    "resource_type 3":  "Fiber",
    "resource_type 4":  "MPLS",
    "resource_type 5":  "SD-WAN",
    "resource_type 6":  "3G-UMTS",
    "resource_type 7":  "Microwave",
    "resource_type 8":  "Core Network",
    "resource_type 9":  "Transport",
    "resource_type 10": "OSS/BSS",
}

RESOURCE_TO_VENDOR = {
    "resource_type 1":  "Ericsson",
    "resource_type 2":  "Nokia",
    "resource_type 3":  "Huawei",
    "resource_type 4":  "Cisco",
    "resource_type 5":  "Juniper",
    "resource_type 6":  "Nokia",
    "resource_type 7":  "Ericsson",
    "resource_type 8":  "Huawei",
    "resource_type 9":  "Cisco",
    "resource_type 10": "Juniper",
}

SERVICE_IMPACT_MAP = {
    "5G-NR":        "Mobile Broadband, IoT, Fixed Wireless Access",
    "4G-LTE":       "VoLTE, Mobile Broadband, SMS, Data Sessions",
    "Fiber":        "Home Broadband, Business Ethernet, IPTV, Backhaul",
    "MPLS":         "Enterprise VPN, Voice Trunks, Cloud Connectivity",
    "SD-WAN":       "Enterprise WAN, Cloud Applications, Branch Connectivity",
    "3G-UMTS":      "Voice Calls, Mobile Data, SMS, Roaming",
    "Microwave":    "Backhaul, Cell Site Transmission, Enterprise Links",
    "Core Network": "All Mobile Services, Signaling, Roaming, Interconnect",
    "Transport":    "Transmission Services, Wavelength Services",
    "OSS/BSS":      "Service Provisioning, Network Management, Billing",
}

REGIONS = ["Central", "North", "South", "East", "West"]

# ─── Description Templates (deterministic, no LLM) ─────────────────────────────

DESCRIPTION_TEMPLATES = {
    "Hardware Failure": [
        "{vendor} {tech} network element at {region} region reporting critical hardware failure. "
        "Multiple line cards showing fault indicators. Primary processing unit unresponsive to "
        "management queries. Service traffic interrupted on {N} downstream circuits.",

        "Hardware failure detected on {vendor} {tech} equipment in {region} region. Faulty board "
        "identified in slot {slot}. Auto-switchover to standby module failed. Field replacement "
        "unit (FRU) dispatch initiated.",

        "{tech} node at {region} site showing hardware fault condition. {vendor} equipment "
        "management system logging multiple hardware alarms. Physical inspection required. "
        "Traffic being rerouted via alternate path.",
    ],
    "Power Supply Fault": [
        "Power supply unit failure on {vendor} {tech} equipment at {region} site. Primary PSU-A "
        "showing input voltage out of range ({voltage}V). Battery backup activated. Estimated "
        "runtime on backup: {bat_time} minutes.",

        "Dual power supply fault detected at {region} region {tech} node. AC input fluctuations "
        "causing intermittent resets on {vendor} chassis. UPS failover triggered. Power utility "
        "outage confirmed as root cause.",

        "{vendor} {tech} chassis at {region} reporting power feed alarms. PSU-B in fault state; "
        "PSU-A operating at reduced capacity. Generator backup not engaging automatically. "
        "{vendor} TAC contacted for emergency support.",
    ],
    "Link Down": [
        "Physical link failure detected on {vendor} {tech} interface in {region} region. "
        "Port {port} showing no carrier signal. Remote end not responding to OAM keepalives. "
        "Failover to backup link triggered automatically.",

        "{tech} uplink down at {region} site. {vendor} equipment reporting loss of signal on "
        "primary port. Traffic rerouted via secondary path with {util}% additional load. "
        "Cause under investigation.",

        "Link failure on {vendor} {tech} node at {region} region. Interface {iface} "
        "administratively up but physically down. No light detected on fiber receiver. "
        "Physical layer fault suspected — cable or transceiver issue.",
    ],
    "Interface Error": [
        "High error rate detected on {vendor} {tech} interface at {region} region. CRC errors "
        "exceeding threshold: {crc_rate} errors/sec on port {port}. Input and output drops "
        "increasing. Possible cable or transceiver degradation.",

        "{tech} interface on {vendor} equipment at {region} reporting excessive frame errors. "
        "Duplex mismatch identified between {vendor} and peer device. Auto-negotiation disabled; "
        "manual speed/duplex configuration required.",

        "Interface fault on {vendor} {tech} node in {region}. Port flapping observed {flap_count} "
        "times in last hour. SFP module suspected faulty. Traffic impact: {util}% of sessions "
        "affected.",
    ],
    "Signal Degradation": [
        "RF signal degradation detected on {vendor} {tech} cell site in {region} region. RSRP "
        "dropped below -110 dBm threshold across {N} sectors. SINR degraded, causing increased "
        "call drops and data session failures.",

        "Signal quality degradation on {tech} network in {region}. {vendor} RRU reporting "
        "receive sensitivity reduction of {db}dB. Possible antenna feeder issue or external "
        "interference source detected.",

        "{vendor} {tech} base station at {region} showing signal degradation. UL noise floor "
        "increased. Interference analysis initiated. Adjacent cell coordination triggered.",
    ],
    "Clock Sync Loss": [
        "Timing synchronization failure on {vendor} {tech} equipment at {region} region. "
        "GPS/GNSS source unreachable; fallback to holdover mode. Synchronization accuracy "
        "degraded. IEEE 1588 PTP chain affected across {N} downstream nodes.",

        "{tech} network element in {region} lost clock reference. {vendor} synchronization "
        "module reporting stratum 1 source unavailable. Cascading timing issues affecting "
        "{N} downstream nodes.",

        "PTP grandmaster unreachable from {vendor} {tech} node at {region}. Holdover timer "
        "running. SYNCE degraded. Risk of timing-critical service impact after "
        "{holdover_min} minutes.",
    ],
    "Board Failure": [
        "Line card failure on {vendor} {tech} chassis at {region} region. Board in slot {slot} "
        "not responding. Traffic rerouted to redundant module. RMA process initiated for "
        "faulty board replacement.",

        "{vendor} {tech} equipment at {region} reporting blade failure. Processor board reset "
        "loop detected. Automatic recovery failed after {N} attempts. Manual intervention "
        "required.",

        "Hardware board fault on {tech} node in {region}. {vendor} chassis slot {slot} showing "
        "critical hardware error. Redundancy switchover completed. Service restored via "
        "standby blade.",
    ],
    "Fan Unit Failure": [
        "Fan tray failure on {vendor} {tech} equipment at {region} site. {N} of {fan_total} fans "
        "non-operational. Chassis temperature rising: current {temp}C, critical threshold "
        "{crit}C. Cooling capacity degraded.",

        "{tech} node at {region} region showing fan unit alarm. {vendor} chassis temperature "
        "management compromised. Equipment at risk of thermal shutdown. Emergency cooling "
        "measures initiated.",

        "Cooling unit failure detected on {vendor} {tech} rack at {region}. Multiple fan units "
        "showing RPM out of range. Ambient temperature rising. Site visit scheduled for "
        "urgent replacement.",
    ],
    "Temperature Alarm": [
        "Critical temperature alarm on {vendor} {tech} equipment at {region} region. Chassis "
        "internal temperature reached {temp}C (critical threshold: {crit}C). HVAC unit failure "
        "suspected. Equipment at risk of automatic thermal shutdown.",

        "{tech} site at {region} reporting high temperature condition. {vendor} equipment "
        "thermal sensors showing inlet temp {temp}C. Air conditioning failure confirmed. "
        "Backup cooling deployed.",

        "Thermal alarm triggered on {vendor} {tech} node in {region}. Temperature sensors "
        "reading {temp}C, exceeding safe operating range. Traffic being offloaded to reduce "
        "heat generation.",
    ],
    "Optical Power Loss": [
        "Optical receive power loss on {vendor} {tech} fiber link at {region}. Rx power level "
        "dropped to {rx_power}dBm (minimum threshold: {min_rx}dBm). Possible fiber degradation "
        "or connector contamination.",

        "{tech} optical link at {region} region showing power degradation. {vendor} DWDM system "
        "reporting channel loss. OTDR test initiated to locate fault point.",

        "Low optical power alarm on {vendor} {tech} transmission link in {region}. Receive level "
        "below expected range. Fiber splice box inspection required.",
    ],
    "Link Flap": [
        "{vendor} {tech} interface at {region} experiencing repeated link up/down events. "
        "Port {port} flapped {flap_count} times in {interval} minutes. Spanning tree "
        "recalculations causing network instability.",

        "Interface instability on {tech} node in {region} region. {vendor} equipment logging "
        "alternating link state changes. Possible cable or SFP issue causing intermittent "
        "connectivity.",

        "Link flapping detected on {vendor} {tech} backbone connection at {region}. Interface "
        "cycling between up/down state. Traffic impact: {util}% packet loss during flap "
        "events.",
    ],
    "BGP Session Drop": [
        "BGP peering session dropped on {vendor} {tech} router at {region} region. Peer "
        "unreachable. Hold-timer expired. Routes withdrawn: {routes} prefixes. "
        "Convergence in progress.",

        "{tech} BGP session failure at {region}. {vendor} router lost peering with upstream "
        "provider. AS{asn} routes being withdrawn. Traffic falling back to secondary "
        "provider link.",

        "BGP neighbor down on {vendor} {tech} core router in {region}. iBGP mesh disrupted. "
        "{N} downstream routers losing route updates. MPLS LSPs affected.",
    ],
    "OSPF Adjacency Loss": [
        "OSPF adjacency lost on {vendor} {tech} router at {region} region. Neighbor down. "
        "Dead-interval exceeded. SPF recalculation triggered. Traffic rerouting via alternate "
        "OSPF paths.",

        "{tech} OSPF failure at {region}. {vendor} equipment reporting dead interval timeout "
        "with area neighbor. LSA flooding storm detected. Network reconvergence taking longer "
        "than SLA.",

        "OSPF neighbor state stuck on {vendor} {tech} node at {region}. MTU mismatch suspected "
        "between {vendor} and peer. Routing table incomplete — services degraded.",
    ],
    "Fiber Cut": [
        "Fiber cable cut detected on {tech} transmission link at {region} region. OTDR trace "
        "confirms break at {dist}km from splice point. Traffic rerouted via protection path. "
        "Field crew dispatched.",

        "Physical fiber break on {vendor} {tech} backbone route in {region}. Both fiber strands "
        "affected. Protection switching activated. Repair crew on-site within {eta} hours.",

        "Fiber cable damage reported in {region} region affecting {tech} network. Cause: "
        "third-party civil works. {vendor} WDM system activated linear protection. "
        "{N} downstream sites affected.",
    ],
    "Physical Layer Fault": [
        "Physical layer fault on {vendor} {tech} interface at {region}. Layer 1 errors detected: "
        "loss of signal on {N} ports. Transceiver diagnostics showing Tx/Rx power out of spec.",

        "{tech} physical connectivity issue in {region} region. {vendor} equipment management "
        "system reporting layer 1 alarms on multiple ports. Site inspection required.",

        "L1 fault detected on {vendor} {tech} node at {region}. Cable integrity test failed. "
        "Patch panel connectivity issue suspected.",
    ],
    "Packet Loss High": [
        "High packet loss detected on {vendor} {tech} link at {region} region. Current loss "
        "rate: {loss}%. QoS queues backing up. Voice and real-time services severely impacted.",

        "{tech} network experiencing significant packet loss in {region}. {vendor} equipment "
        "showing {loss}% packet drop on core uplink. Possible congestion or hardware fault.",

        "Packet loss alarm on {vendor} {tech} transport link at {region}. BFD session flapping. "
        "Traffic rerouting initiated to restore service quality.",
    ],
    "High Latency": [
        "Abnormally high latency detected on {vendor} {tech} network at {region} region. "
        "RTT increased to {rtt}ms (normal: {normal_rtt}ms). Queuing delay suspected due to "
        "congestion on core uplink.",

        "{tech} latency spike in {region}. {vendor} equipment reporting RTT {rtt}ms, "
        "{x}x above baseline. Real-time applications including VoLTE and video conferencing "
        "impacted.",

        "Latency degradation on {vendor} {tech} path at {region}. Jitter also elevated. "
        "Possible routing suboptimality or queue buildup on intermediate node.",
    ],
    "Cell Outage": [
        "Complete cell outage reported at {vendor} {tech} site in {region} region. All sectors "
        "(A/B/C) non-operational. gNodeB/eNodeB lost NG/S1 interface. {N} UEs in coverage "
        "gap with no service.",

        "{tech} base station failure at {region}. {vendor} BTS/eNB unresponsive to O&M system. "
        "Site power confirmed present. Likely software crash or hardware failure on baseband "
        "unit.",

        "Cell site outage in {region} region affecting {tech} coverage. {vendor} RAN element "
        "reporting total radio failure. Traffic offloaded to neighboring cells causing "
        "congestion.",
    ],
    "Handover Failure": [
        "Handover failure spike on {vendor} {tech} network at {region} region. HO success rate "
        "dropped to {util}% (target: 98%). X2/Xn interface issues suspected. Call drops "
        "increasing.",

        "{tech} handover failures in {region}. {vendor} SON algorithm reporting increased "
        "intra-frequency HO failures. Possible pilot pollution or neighbor list configuration "
        "issue.",

        "Mobility management failures on {vendor} {tech} in {region} region. Inter-cell "
        "handover timeout increasing. A3 event threshold misconfiguration detected after "
        "firmware update.",
    ],
    "Configuration Error": [
        "Configuration error detected on {vendor} {tech} node at {region} region. Recent change "
        "window introduced incorrect routing policy. Traffic blackholing {N} prefixes. "
        "Change rollback initiated.",

        "{tech} misconfiguration in {region}. {vendor} element management system flagging "
        "configuration consistency violation. ACL policy conflict causing service disruption.",

        "Config deployment failure on {vendor} {tech} equipment at {region}. Template mismatch "
        "between intended and applied configuration. Service impact: {util}% of VPN "
        "customers affected.",
    ],
    "Firmware Upgrade Failure": [
        "Firmware upgrade failure on {vendor} {tech} equipment at {region} region. Upgrade "
        "failed during flash programming. Automatic rollback to previous version initiated. "
        "Service restored.",

        "{tech} software upgrade aborted at {region}. {vendor} node reported checksum mismatch "
        "during package verification. Previous software version restored. Root cause "
        "analysis pending.",

        "Failed firmware deployment on {vendor} {tech} at {region} region. Node unresponsive "
        "after upgrade initiation. Console access required. Maintenance window extended.",
    ],
    "Software Bug": [
        "Software defect triggered on {vendor} {tech} system at {region} region. Known bug "
        "causing memory leak in routing process. Workaround applied per vendor advisory. "
        "Service degraded but not completely lost.",

        "{tech} software anomaly detected at {region}. {vendor} NE experiencing unexpected "
        "process behavior. Core dump collected for vendor analysis.",

        "Software crash loop on {vendor} {tech} node at {region}. Process restarting "
        "repeatedly. Vendor patch required to resolve. Temporary stability achieved via "
        "config workaround.",
    ],
    "Process Crash": [
        "Critical process failure on {vendor} {tech} equipment at {region} region. Routing "
        "daemon crashed unexpectedly. Automatic restart attempted {N} times. Manual "
        "intervention required to restore stability.",

        "{tech} control plane process crash at {region}. {vendor} NE lost routing protocol "
        "state. BGP/OSPF sessions dropped. Full convergence required after process restart.",

        "Daemon failure on {vendor} {tech} node in {region}. Process core dumped. Service "
        "partially degraded. Vendor support engaged for crash analysis.",
    ],
    "Memory Exhaustion": [
        "Memory exhaustion on {vendor} {tech} node at {region} region. System memory "
        "utilization at {mem}% (critical threshold: 90%). Routing table growth causing memory "
        "pressure. Process killing initiated.",

        "{tech} node in {region} reporting critical memory shortage. {vendor} equipment memory "
        "pool exhausted. Non-critical processes terminated. Planned maintenance for memory "
        "expansion required.",

        "Out-of-memory condition on {vendor} {tech} at {region}. Swap space activated. System "
        "performance severely degraded. Emergency restart considered.",
    ],
    "CPU Overload": [
        "CPU overload on {vendor} {tech} control plane at {region} region. Processor "
        "utilization at {cpu}% for {interval} minutes. Control plane functions slow to "
        "respond. BGP update processing delayed.",

        "{tech} node at {region} showing critical CPU utilization. {vendor} equipment processing "
        "overhead from routing table churn. Management plane unresponsive. Traffic forwarding "
        "via hardware ASICs maintained.",

        "High CPU alarm on {vendor} {tech} at {region}. Control process consuming {cpu}% CPU "
        "cycles. Possible DDoS or routing protocol storm. Rate-limiting applied.",
    ],
    "Disk Full": [
        "Disk space exhaustion on {vendor} {tech} management node at {region} region. System "
        "partition at {disk}% capacity. Log rotation failed. OSS/NMS functionality impaired.",

        "{tech} node log storage full at {region}. {vendor} equipment unable to write new "
        "system logs or CDRs. Historical data archival required urgently.",

        "File system full on {vendor} {tech} at {region} region. Core dump files consuming "
        "excessive space. Automated cleanup script failed. Manual intervention required.",
    ],
    "Database Corruption": [
        "Database corruption detected on {vendor} {tech} management system at {region} region. "
        "Configuration database inconsistency found. Provisioning operations suspended. "
        "Backup restoration in progress.",

        "{tech} network element database error at {region}. {vendor} NMS reporting data "
        "integrity check failures. Service provisioning affected. Emergency DB recovery "
        "procedure initiated.",

        "Data corruption in {vendor} {tech} element at {region}. Transaction log overflow "
        "corrupted network configuration tables. Rollback to last known good backup initiated.",
    ],
    "License Expiry": [
        "Software license expiry on {vendor} {tech} equipment at {region} region. Feature "
        "license expired. Service capacity limited. Renewal order in progress with vendor.",

        "{tech} node at {region} entering license violation state. {vendor} capacity license "
        "expired. New user sessions being rejected. Emergency license extension requested.",

        "License expiration alarm on {vendor} {tech} at {region}. Multiple features disabled "
        "due to expired entitlements. Traffic engineering and QoS functions affected.",
    ],
    "Authentication Failure": [
        "Authentication failures detected on {vendor} {tech} management interface at {region} "
        "region. Multiple failed login attempts from unknown source. Management access "
        "temporarily restricted.",

        "{tech} RADIUS/TACACS authentication failure at {region}. {vendor} AAA server "
        "unreachable causing fallback to local authentication. Security policy compliance "
        "at risk.",

        "Certificate authentication failure on {vendor} {tech} at {region}. TLS certificate "
        "expired on management plane. Secure management sessions failing.",
    ],
    "Capacity Exceeded": [
        "Network capacity threshold exceeded on {vendor} {tech} link at {region} region. "
        "Utilization at {util}% (threshold: 80%). Traffic shaping activated. Upgrade or "
        "load-balancing required.",

        "{tech} capacity alarm at {region}. {vendor} equipment reporting sustained high "
        "utilization across {N} interfaces. QoS policies enforcing traffic prioritization.",

        "Bandwidth capacity exceeded on {vendor} {tech} at {region} region. Peak traffic "
        "exceeding committed capacity. Burst absorption limit reached.",
    ],
    "Network Congestion": [
        "Network congestion detected on {vendor} {tech} backbone at {region} region. Packet "
        "queuing depths critical on core links. Latency for real-time services increased "
        "{x}x. Traffic policing activated.",

        "{tech} congestion event in {region}. {vendor} routers reporting queue drops on "
        "high-priority traffic classes. VoLTE packet loss impacting voice quality.",

        "Core congestion on {vendor} {tech} at {region}. Traffic burst exceeding buffer "
        "capacity. WRED dropping lower-priority packets. Capacity expansion planned.",
    ],
    "Traffic Overload": [
        "Traffic overload condition on {vendor} {tech} node at {region} region. Incoming "
        "traffic rate {util}% above engineered capacity. Emergency traffic shedding activated "
        "on lower-priority services.",

        "{tech} overload alarm at {region}. {vendor} equipment signaling system congested. "
        "New session setup being rejected at elevated rate.",

        "Traffic surge causing overload on {vendor} {tech} at {region} region. Likely caused "
        "by mass media event or emergency broadcast. Load sharing to adjacent nodes activated.",
    ],
    "Threshold Breach": [
        "KPI threshold breach on {vendor} {tech} network at {region} region. Multiple KPIs "
        "exceeded configured limits for {interval} consecutive minutes. Automated alert "
        "raised to NOC.",

        "{tech} performance threshold alarm at {region}. {vendor} element manager reporting "
        "{N} KPIs in alarm state simultaneously. SLA compliance at risk.",

        "Multiple threshold breaches on {vendor} {tech} at {region}. Key metrics — error "
        "rate, latency, and availability — all outside SLA bounds.",
    ],
    "Traffic Spike": [
        "Sudden traffic spike on {vendor} {tech} network at {region} region. Traffic increased "
        "{x}x above normal in {interval} minutes. Possible flash crowd or DDoS event. "
        "Traffic engineering triggered.",

        "{tech} traffic anomaly at {region}. {vendor} equipment showing {x}x traffic surge. "
        "Cause: possible viral content event or coordinated attack. Scrubbing center "
        "activated.",

        "Unexpected traffic spike on {vendor} {tech} at {region} region. Burst traffic "
        "exceeding capacity planning assumptions. Dynamic rerouting activated.",
    ],
    "RRU Fault": [
        "Remote Radio Unit (RRU) failure on {vendor} {tech} base station at {region} region. "
        "RRU reporting CPRI link alarm and RF output failure. Affected sector out of service.",

        "{tech} RRU hardware fault at {region}. {vendor} RRU showing power amplifier failure. "
        "Sector capacity reduced by {util}%. Replacement unit on order.",

        "CPRI/eCPRI link failure between BBU and RRU on {vendor} {tech} at {region}. Fiber "
        "connection between baseband and radio head disrupted. Cell sector offline.",
    ],
    "Antenna Failure": [
        "Antenna system fault on {vendor} {tech} cell site at {region} region. Remote "
        "Electrical Tilt (RET) motor failure. Antenna pattern distorted. Coverage gap in "
        "{direction} direction.",

        "{tech} antenna hardware failure at {region}. {vendor} active antenna unit (AAU) "
        "reporting failure. Massive MIMO beamforming capability lost.",

        "Antenna connection fault on {vendor} {tech} at {region} region. VSWR measurement "
        "indicates antenna mismatch or connector fault. RF performance significantly "
        "degraded.",
    ],
    "VSWR Alarm": [
        "VSWR alarm triggered on {vendor} {tech} antenna system at {region} region. Standing "
        "wave ratio measured at {vswr}:1 (threshold: 2.5:1). Possible antenna connector "
        "corrosion or cable damage.",

        "{tech} VSWR out of range at {region}. {vendor} base station reporting return loss "
        "degradation. Antenna feeder water ingress suspected.",

        "High VSWR detected on {vendor} {tech} sector at {region}. RF power reflected from "
        "antenna exceeding safe limits. Transmit power reduced automatically.",
    ],
    "Feeder Cable Fault": [
        "Antenna feeder cable fault detected on {vendor} {tech} site at {region} region. "
        "Coax cable showing intermittent continuity. Water ingress at connector joint "
        "suspected. RF performance degraded.",

        "{tech} feeder fault at {region}. {vendor} cell site reporting antenna feeder "
        "disconnection alarm. Physical inspection revealed cable damage.",

        "Feeder cable degradation on {vendor} {tech} at {region} region. Increased insertion "
        "loss on antenna port. Replacement scheduled.",
    ],
    "Cell Capacity Degradation": [
        "Cell capacity degradation on {vendor} {tech} site at {region} region. Sector "
        "throughput reduced to {util}% of nominal. Possible RRU partial failure or antenna "
        "tilt misconfiguration.",

        "{tech} capacity degradation at {region}. {vendor} cell site reporting reduced "
        "spectral efficiency. MIMO rank adaptation showing suboptimal performance.",

        "Gradual capacity reduction on {vendor} {tech} cell at {region}. Throughput declining "
        "over several days. Receiver sensitivity degradation suspected.",
    ],
    "Node Restart": [
        "{vendor} {tech} node at {region} region performed unexpected restart. System rebooted "
        "following critical software exception. Services recovering. BGP/routing convergence "
        "in progress.",

        "{tech} equipment restart at {region}. {vendor} NE self-recovered from fault condition "
        "via watchdog-triggered reboot. Configuration reload from persistent storage.",

        "Unplanned node restart on {vendor} {tech} at {region} region. Cause: power transient. "
        "Service restoration via automatic restart completed.",
    ],
    "Emergency Restart": [
        "Emergency restart initiated on {vendor} {tech} node at {region} region due to "
        "critical system error. All active sessions dropped. Traffic rerouted to redundant "
        "equipment during recovery.",

        "{tech} emergency reboot at {region}. {vendor} equipment manual restart required "
        "after software hang. Full service restoration ETA: {interval} minutes.",

        "Forced restart on {vendor} {tech} at {region} region. System became unresponsive "
        "to management commands. Cold reboot performed.",
    ],
    "Watchdog Timeout": [
        "Watchdog timer timeout on {vendor} {tech} equipment at {region} region. System "
        "heartbeat process failed to respond. Automatic hardware reset triggered. Service "
        "restored after reboot.",

        "{tech} watchdog failure at {region}. {vendor} NE watchdog circuit detected software "
        "hang and forced system reset. Root cause: memory corruption in routing process.",

        "Watchdog-triggered reboot on {vendor} {tech} at {region}. System health monitor "
        "detected unresponsive critical process. Automatic recovery successful.",
    ],
    "Core Dump": [
        "Core dump generated on {vendor} {tech} node at {region} region. Critical process "
        "crashed with segmentation fault. Core file collected for vendor analysis. Service "
        "partially impacted.",

        "{tech} process core dump at {region}. {vendor} NE software crash occurred. "
        "Vendor TAC engaged for crash analysis.",

        "Software crash and core dump on {vendor} {tech} at {region} region. Process failure "
        "caused partial service interruption. Restart restored service.",
    ],
    "NTP Sync Failure": [
        "NTP time synchronization failure on {vendor} {tech} node at {region} region. All "
        "configured NTP servers unreachable. System clock drifting. Certificate validation "
        "and CDR timestamping affected.",

        "{tech} timing error at {region}. {vendor} equipment lost NTP reference. Clock drift "
        "exceeding threshold. Timestamp-sensitive applications affected.",

        "NTP server failure on {vendor} {tech} at {region} region. Stratum 1 source "
        "unreachable. Holdover accuracy degrading. Network-wide time sync at risk.",
    ],
    "DNS Resolution Failure": [
        "DNS resolution failure on {vendor} {tech} management system at {region} region. "
        "Primary and secondary DNS servers unreachable. Service provisioning and management "
        "connectivity affected.",

        "{tech} DNS failure at {region}. {vendor} NE unable to resolve management plane "
        "FQDNs. OAM connectivity degraded.",

        "DNS outage affecting {vendor} {tech} at {region} region. Resolver cache exhausted. "
        "Service activation workflows delayed.",
    ],
    "SNMP Trap Flood": [
        "SNMP trap flood detected from {vendor} {tech} equipment at {region} region. "
        "Excessive traps received by NMS. Trap source isolated to {N} network elements "
        "experiencing hardware issues.",

        "{tech} SNMP storm at {region}. {vendor} NMS receiving trap rate exceeding processing "
        "capacity. Trap filtering applied.",

        "SNMP trap flooding from {vendor} {tech} at {region} region. Network management "
        "system overwhelmed. Root alarm: hardware fault generating repeated notifications.",
    ],
    "Alarm Storm": [
        "Alarm storm on {vendor} {tech} network at {region} region. {N} alarms generated "
        "in {interval} minutes following initial root fault. Alarm correlation and "
        "de-duplication activated in NMS.",

        "{tech} alarm flood at {region}. {vendor} element management system receiving "
        "thousands of correlated alarms. Root cause identified as single point of failure.",

        "Cascading alarm storm on {vendor} {tech} at {region} region. Secondary alarms "
        "masked root cause. OSS correlation engine identifying origin fault.",
    ],
    "Cascading Failure": [
        "Cascading failure on {vendor} {tech} network at {region} region. Initial fault "
        "triggered secondary failures across {N} nodes. Traffic load redistribution causing "
        "additional equipment stress.",

        "{tech} cascading fault in {region}. {vendor} network experiencing domino failure "
        "pattern. Protection mechanisms activated but overloaded.",

        "Multi-node cascading failure on {vendor} {tech} at {region} region. Single link "
        "failure overloaded redundant paths triggering further failures.",
    ],
    "Hardware Degradation": [
        "Hardware degradation detected on {vendor} {tech} equipment at {region} region. "
        "Proactive monitoring shows declining health indicators. Predictive maintenance "
        "alert raised before complete failure.",

        "{tech} hardware aging alarm at {region}. {vendor} equipment diagnostics indicate "
        "component wear. Pre-emptive replacement scheduled during next maintenance window.",

        "Gradual hardware degradation on {vendor} {tech} at {region} region. Error counters "
        "trending upward over several days. Preventive action recommended.",
    ],
    "Interface CRC Errors": [
        "CRC error rate exceeded on {vendor} {tech} interface at {region} region. "
        "{crc_rate} errors/sec on port {port}. Physical layer integrity compromised. "
        "Cable or SFP replacement required.",

        "{tech} interface CRC errors at {region}. {vendor} equipment port showing frame check "
        "sequence failures. Noise or signal integrity issue on physical medium.",

        "Excessive CRC errors on {vendor} {tech} at {region} region. Input errors "
        "accumulating on {N} interfaces. Duplex mismatch or degraded cable suspected.",
    ],
    "Routing Loop": [
        "Routing loop detected on {vendor} {tech} network at {region} region. TTL expiry "
        "alarms flooding network. Specific destination prefix causing loop. Emergency route "
        "filter applied.",

        "{tech} routing loop at {region}. {vendor} routing protocol misconfiguration created "
        "loop. Packets circulating without reaching destination. Traffic blackhole cleared.",

        "Routing table loop on {vendor} {tech} at {region} region. Administrative distance "
        "misconfiguration created suboptimal routing. Network convergence impacted.",
    ],
    "VPN Tunnel Down": [
        "VPN tunnel failure on {vendor} {tech} equipment at {region} region. IPSec/MPLS "
        "tunnel to {N} remote sites down. Enterprise customers unable to access "
        "headquarter resources.",

        "{tech} VPN outage at {region}. {vendor} tunnel endpoint unreachable. IKE phase 1 "
        "negotiations failing. Customer traffic redirected via backup tunnels.",

        "L2VPN/L3VPN service failure on {vendor} {tech} at {region} region. PE-CE connection "
        "down. {N} enterprise customers affected.",
    ],
    "Multicast Failure": [
        "Multicast routing failure on {vendor} {tech} network at {region} region. PIM-SM "
        "sparse mode RP unreachable. IPTV and enterprise multicast streams interrupted.",

        "{tech} multicast outage at {region}. {vendor} equipment PIM join/prune processing "
        "failure. Multicast distribution tree reconstruction required.",

        "IGMP/MLD snooping failure on {vendor} {tech} at {region} region. Multicast traffic "
        "flooding to all ports instead of selective forwarding.",
    ],
}

# ─── Resolution Notes Templates ────────────────────────────────────────────────

RESOLUTION_NOTES = {
    "Hardware Failure":        "Faulty hardware unit replaced with spare. Post-replacement diagnostics confirmed normal operation. Redundancy restored. Service fully recovered.",
    "Power Supply Fault":      "Power supply unit replaced. Input voltage stabilized. Battery backup deactivated. Normal dual-feed operation restored.",
    "Link Down":               "Physical layer fault resolved. Fiber connector re-seated and cable replaced. Link re-established. Traffic restored.",
    "Interface Error":         "Interface errors resolved by replacing SFP transceiver. Duplex/speed settings verified. Error counters reset.",
    "Signal Degradation":      "RF signal restored after antenna feeder inspection and re-termination. Background interference source removed. Coverage metrics returned to baseline.",
    "Clock Sync Loss":         "Timing reference restored. GPS antenna cable repaired. PTP synchronization chain re-established. Stratum 1 accuracy confirmed.",
    "Board Failure":           "Faulty board replaced with spare from warehouse stock. Redundancy restored. Traffic restored after slot reinitialization.",
    "Fan Unit Failure":        "Fan tray replaced. Chassis temperature normalized. Thermal management fully restored.",
    "Temperature Alarm":       "HVAC unit repaired. Ambient temperature reduced to normal range. Chassis temperature within specifications.",
    "Optical Power Loss":      "Optical connector cleaned and re-terminated. Fiber span tested with OTDR. Rx power restored to nominal level.",
    "Link Flap":               "SFP transceiver replaced. Cable integrity verified. Interface stable for 30+ minutes post-repair.",
    "BGP Session Drop":        "BGP session re-established after route reflector connectivity restored. All prefixes re-learned. Traffic forwarding normalized.",
    "OSPF Adjacency Loss":     "OSPF adjacency restored after MTU mismatch corrected on both ends. SPF stabilized. Full routing table restored.",
    "Fiber Cut":               "Fiber cable spliced and re-terminated by field crew. OTDR test confirmed no residual loss. Protection path deactivated.",
    "Physical Layer Fault":    "Physical fault resolved after cable replacement. Layer 1 health indicators green. Traffic restored.",
    "Packet Loss High":        "Congestion resolved by traffic rerouting and QoS queue adjustment. Packet loss returned to 0%.",
    "High Latency":            "Latency normalized after traffic load balanced across alternate paths. RTT returned to baseline.",
    "Cell Outage":             "Cell site restored after baseband unit replacement. All sectors operational. UE reattachment completed.",
    "Handover Failure":        "Handover parameters reconfigured. A3 offset adjusted. HO success rate restored to 98.5%.",
    "Configuration Error":     "Configuration rollback applied from backup snapshot. Correct template re-deployed and verified. Traffic routing confirmed.",
    "Firmware Upgrade Failure":"Upgrade rolled back to previous stable version. Root cause documented. Vendor patch scheduled for next maintenance window.",
    "Software Bug":            "Vendor-supplied patch applied. Affected process restarted cleanly. System stability confirmed over 24 hours.",
    "Process Crash":           "Failed process restarted. Core dump sent to vendor TAC for analysis. Stability patch applied.",
    "Memory Exhaustion":       "Memory recovered after process restart and cache flush. Routing table optimized. Long-term fix: memory expansion scheduled.",
    "CPU Overload":            "CPU overload resolved by rate-limiting routing protocol updates. Processor utilization normalized to 35%.",
    "Disk Full":               "Disk space freed by log archival and automated cleanup. Log rotation re-enabled. 40% free space available.",
    "Database Corruption":     "Database restored from last-known-good backup. Configuration re-synchronized across cluster. Provisioning operations resumed.",
    "License Expiry":          "Emergency license applied via vendor portal. Full capacity restored. Permanent license renewal order raised.",
    "Authentication Failure":  "Authentication issue resolved. RADIUS server connectivity restored. Management access normalized and audited.",
    "Capacity Exceeded":       "Traffic load balanced across additional links. Capacity upgrade order placed for permanent resolution.",
    "Network Congestion":      "Congestion resolved via traffic engineering re-optimization and QoS policy update. Queue depths normalized.",
    "Traffic Overload":        "Traffic overload mitigated via rate-limiting and CDN offload. Normal load levels restored.",
    "Threshold Breach":        "KPI threshold breach resolved. Root cause corrected. Monitoring thresholds recalibrated to reflect network changes.",
    "Traffic Spike":           "Traffic spike absorbed via dynamic traffic engineering. DDoS scrubbing center cleared attack traffic.",
    "RRU Fault":               "Faulty RRU replaced. CPRI link re-established. Sector RF performance verified against baseline.",
    "Antenna Failure":         "Antenna unit replaced. RET motor recalibrated. Coverage pattern restored and verified by drive test.",
    "VSWR Alarm":              "VSWR issue resolved after connector re-termination and weatherproofing. Standing wave ratio normalized to 1.3:1.",
    "Feeder Cable Fault":      "Feeder cable replaced. Weatherproofing tape applied at connectors. RF performance verified.",
    "Cell Capacity Degradation":"Cell capacity restored after RRU replacement. Spectral efficiency metrics normalized.",
    "Node Restart":            "Node recovered after restart. All services and routing protocols re-established. Monitoring confirmed stable.",
    "Emergency Restart":       "Emergency restart completed. Configuration reloaded from persistent storage. Service restored.",
    "Watchdog Timeout":        "Watchdog-triggered reboot resolved hung process. System health monitoring confirmed stable for 2 hours.",
    "Core Dump":               "Core dump analyzed by vendor TAC. Memory corruption found. Patch applied and deployed.",
    "NTP Sync Failure":        "NTP servers restored. Clock synchronized to stratum 1 reference. Timestamp accuracy confirmed.",
    "DNS Resolution Failure":  "DNS servers restored. Name resolution working. Management connectivity re-established.",
    "SNMP Trap Flood":         "SNMP trap source isolated. Trap rate limiting applied. NMS processing normalized.",
    "Alarm Storm":             "Root alarm identified and resolved. Correlation suppressed secondary alarms. NMS alarm queue cleared.",
    "Cascading Failure":       "Cascading failure contained by isolating initial fault. Traffic re-routed. All nodes recovered in sequence.",
    "Hardware Degradation":    "Degraded hardware proactively replaced during maintenance window. No service impact recorded.",
    "Interface CRC Errors":    "CRC errors eliminated after cable replacement. Interface error counters reset to zero.",
    "Routing Loop":            "Routing loop cleared by applying emergency route filter. Permanent fix: routing policy corrected and validated.",
    "VPN Tunnel Down":         "VPN tunnels re-established after IKE renegotiation. Customer connectivity confirmed.",
    "Multicast Failure":       "Multicast routing restored after PIM RP re-election. IPTV streams resumed.",
}

# ─── Helper Functions ──────────────────────────────────────────────────────────

def get_region(location_str):
    try:
        num = int(str(location_str).split()[-1])
        return REGIONS[num % 5]
    except Exception:
        return "Central"


def fill_template(template: str, row: dict) -> str:
    rng = np.random.RandomState(int(row["id"]))
    vol = float(row.get("total_log_volume", 10))

    values = {
        "vendor":       row["device_vendor"],
        "tech":         row["technology_type"],
        "region":       row["network_region"],
        "N":            str(max(1, int(vol // 15) + rng.randint(1, 4))),
        "slot":         str(rng.randint(1, 9)),
        "port":         f"0/0/{rng.randint(0, 16)}",
        "iface":        f"GigabitEthernet0/{rng.randint(0, 4)}/{rng.randint(0, 8)}",
        "util":         str(min(99, 55 + int(row["fault_severity"]) * 15 + rng.randint(0, 10))),
        "temp":         str(65 + int(row["fault_severity"]) * 8 + rng.randint(0, 8)),
        "crit":         str(80 + rng.randint(0, 5)),
        "cpu":          str(min(99, 60 + int(row["fault_severity"]) * 12 + rng.randint(0, 8))),
        "mem":          str(min(97, 70 + int(row["fault_severity"]) * 8 + rng.randint(0, 8))),
        "disk":         str(min(99, 82 + rng.randint(0, 8))),
        "rtt":          str(20 + int(row["fault_severity"]) * 40 + rng.randint(0, 30)),
        "normal_rtt":   str(rng.randint(5, 15)),
        "x":            str(rng.choice([2, 3, 5, 10])),
        "loss":         f"{0.5 + int(row['fault_severity']) * 2.5 + rng.uniform(0, 1):.1f}",
        "crc_rate":     str(rng.randint(10, 1000)),
        "flap_count":   str(3 + int(row["fault_severity"]) * 5 + rng.randint(0, 10)),
        "interval":     str(rng.randint(5, 30)),
        "routes":       str(rng.randint(100, 5000)),
        "asn":          str(rng.randint(1000, 65000)),
        "db":           str(rng.randint(3, 15)),
        "dist":         f"{rng.uniform(0.5, 50):.1f}",
        "eta":          str(rng.randint(2, 8)),
        "bat_time":     str(rng.choice([30, 60, 120, 240])),
        "voltage":      f"{rng.uniform(195, 215):.0f}",
        "holdover_min": str(rng.randint(15, 60)),
        "rx_power":     f"{-20 - int(row['fault_severity']) * 4 - rng.randint(0, 4):.0f}",
        "min_rx":       f"{-25 - rng.randint(0, 3):.0f}",
        "vswr":         f"{2.5 + rng.uniform(0, 2.0):.1f}",
        "fan_total":    str(rng.choice([4, 6, 8])),
        "direction":    str(rng.choice(["north", "south", "east", "west"])),
    }

    result = template
    for key, val in values.items():
        result = result.replace("{" + key + "}", str(val))
    # Remove any unfilled placeholders
    result = re.sub(r"\{[a-z_]+\}", "", result)
    return result.strip()


# ─── Main Transform ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Telstra -> Telecom Incident Schema Transformer")
    print("=" * 60)

    def read_csv(filename):
        return pd.read_csv(os.path.join(TELSTRA_PATH, filename, filename))

    print("[1/6] Loading Telstra CSVs...")
    train         = read_csv("train.csv")
    event_type    = read_csv("event_type.csv")
    log_feature   = read_csv("log_feature.csv")
    resource_type = read_csv("resource_type.csv")
    severity_type = read_csv("severity_type.csv")
    print(f"      Loaded {len(train)} fault records from Telstra dataset")

    print("[2/6] Aggregating features per incident ID...")
    # Primary event type (most common per id, or first if tie)
    primary_event = (
        event_type.groupby("id")["event_type"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
        .rename(columns={"event_type": "primary_event_type"})
    )

    # Primary resource type
    primary_resource = (
        resource_type.groupby("id")["resource_type"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
        .rename(columns={"resource_type": "primary_resource_type"})
    )

    # Primary severity type
    primary_sev_type = (
        severity_type.groupby("id")["severity_type"]
        .first()
        .reset_index()
    )

    # Log volume stats
    log_stats = (
        log_feature.groupby("id")
        .agg(
            total_log_volume=("volume", "sum"),
            max_log_volume=("volume", "max"),
            log_feature_count=("log_feature", "count"),
        )
        .reset_index()
    )

    # Merge all onto train (left join — keep only labeled records)
    df = train.copy()
    df = df.merge(primary_event,    on="id", how="left")
    df = df.merge(primary_resource, on="id", how="left")
    df = df.merge(primary_sev_type, on="id", how="left")
    df = df.merge(log_stats,        on="id", how="left")

    df["primary_event_type"]    = df["primary_event_type"].fillna("event_type 1")
    df["primary_resource_type"] = df["primary_resource_type"].fillna("resource_type 2")
    df["severity_type"]         = df["severity_type"].fillna("severity_type 2")
    df["total_log_volume"]      = df["total_log_volume"].fillna(5.0)
    df["log_feature_count"]     = df["log_feature_count"].fillna(1.0)

    print("[3/6] Applying domain mappings...")

    df["alarm_id"]       = df["id"].apply(lambda x: f"TLS-{x:05d}")
    df["alarm_type"]     = df["primary_event_type"].map(EVENT_TO_ALARM_TYPE).fillna("Hardware Failure")
    df["technology_type"] = df["primary_resource_type"].map(RESOURCE_TO_TECH).fillna("4G-LTE")
    df["device_vendor"]  = df["primary_resource_type"].map(RESOURCE_TO_VENDOR).fillna("Nokia")
    df["network_region"] = df["location"].apply(get_region)
    df["service_impact"] = df["technology_type"].map(SERVICE_IMPACT_MAP).fillna("Data Services")

    # Severity: Telstra's fault_severity 2 → P1-Critical, 1 → P2-High
    # fault_severity 0 split by log volume: high → P3-Medium, low → P4-Low
    def map_severity(row):
        fs  = int(row["fault_severity"])
        vol = float(row["total_log_volume"])
        if fs == 2:
            return "P1-Critical"
        elif fs == 1:
            return "P2-High"
        elif fs == 0 and vol > 10:
            return "P3-Medium"
        else:
            return "P4-Low"

    df["severity"] = df.apply(map_severity, axis=1)

    print("[4/6] Deriving numeric fields from log volumes...")

    def get_outage_duration(row):
        sev = row["severity"]
        vol = float(row["total_log_volume"])
        rng = np.random.RandomState(int(row["id"]) + 100)
        if sev == "P1-Critical":
            return int(min(vol * 0.6, 300) + 60 + rng.randint(0, 60))
        elif sev == "P2-High":
            return int(min(vol * 0.3, 90) + 20 + rng.randint(0, 30))
        elif sev == "P3-Medium":
            return int(min(vol * 0.15, 30) + 5 + rng.randint(0, 20))
        else:
            return int(rng.randint(1, 10))

    def get_affected_subscribers(row):
        sev  = row["severity"]
        tech = row["technology_type"]
        rng  = np.random.RandomState(int(row["id"]) + 200)
        scale = {
            "Core Network": 8, "5G-NR": 5, "4G-LTE": 4,
            "Fiber": 3, "Transport": 4, "MPLS": 2,
            "3G-UMTS": 3, "Microwave": 2, "SD-WAN": 1, "OSS/BSS": 1,
        }
        m = scale.get(tech, 2)
        if sev == "P1-Critical":
            return int(rng.randint(15000, 80000) * m / 4)
        elif sev == "P2-High":
            return int(rng.randint(3000, 25000) * m / 4)
        elif sev == "P3-Medium":
            return int(rng.randint(300, 5000) * m / 4)
        else:
            return int(rng.randint(10, 500))

    df["outage_duration"]        = df.apply(get_outage_duration, axis=1)
    df["affected_subscribers"]   = df.apply(get_affected_subscribers, axis=1)
    df["resolution_time_minutes"] = (
        df["outage_duration"] * 1.25
        + df.apply(lambda r: np.random.RandomState(int(r["id"]) + 300).randint(5, 25), axis=1)
    ).astype(int)
    df["recurrence_count"] = (
        df["log_feature_count"].clip(upper=40) * 0.4
        + df.apply(lambda r: np.random.RandomState(int(r["id"]) + 400).randint(0, 3), axis=1)
    ).astype(int).clip(upper=20)

    # Timestamps: distributed over 2 years (2023-01-01 to 2024-12-31)
    base_date = datetime(2023, 1, 1)
    df["timestamp"] = df.apply(
        lambda r: (
            base_date
            + timedelta(
                days=int(r["id"]) % 730,
                hours=int(np.random.RandomState(int(r["id"]) + 500).randint(0, 24)),
                minutes=int(np.random.RandomState(int(r["id"]) + 600).randint(0, 60)),
            )
        ).strftime("%Y-%m-%d %H:%M:%S"),
        axis=1,
    )

    print("[5/6] Generating incident descriptions and resolution notes...")

    def gen_description(row):
        alarm  = row["alarm_type"]
        tmpls  = DESCRIPTION_TEMPLATES.get(
            alarm,
            ["{vendor} {tech} network element at {region} region reporting fault condition. "
             "Service impact under investigation. NOC team engaged."]
        )
        tmpl = tmpls[int(row["id"]) % len(tmpls)]
        return fill_template(tmpl, row)

    def gen_resolution(row):
        note = RESOLUTION_NOTES.get(
            row["alarm_type"],
            "Issue identified and resolved by NOC team. Service restored within SLA timeframe.",
        )
        return note

    df["incident_description"] = df.apply(gen_description, axis=1)
    df["resolution_notes"]     = df.apply(gen_resolution, axis=1)

    print("[6/6] Writing output CSV...")
    output_cols = [
        "alarm_id", "incident_description", "network_region", "technology_type",
        "severity", "outage_duration", "device_vendor", "resolution_notes",
        "timestamp", "service_impact", "alarm_type", "affected_subscribers",
        "resolution_time_minutes", "recurrence_count",
    ]
    result = df[output_cols]

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_CSV)), exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)

    print()
    print("=" * 60)
    print(f"SUCCESS: {len(result)} records written to:")
    print(f"  {os.path.abspath(OUTPUT_CSV)}")
    print()
    print("Severity distribution:")
    print(result["severity"].value_counts().to_string())
    print()
    print("Technology distribution:")
    print(result["technology_type"].value_counts().to_string())
    print()
    print("Vendor distribution:")
    print(result["device_vendor"].value_counts().to_string())
    print()
    print("Region distribution:")
    print(result["network_region"].value_counts().to_string())
    print()
    print("Sample record:")
    sample = result.iloc[0]
    print(f"  alarm_id:            {sample['alarm_id']}")
    print(f"  alarm_type:          {sample['alarm_type']}")
    print(f"  severity:            {sample['severity']}")
    print(f"  technology_type:     {sample['technology_type']}")
    print(f"  device_vendor:       {sample['device_vendor']}")
    print(f"  network_region:      {sample['network_region']}")
    print(f"  outage_duration:     {sample['outage_duration']} min")
    print(f"  affected_subscribers:{sample['affected_subscribers']}")
    print(f"  incident_description:{sample['incident_description'][:120]}...")
    print(f"  resolution_notes:    {sample['resolution_notes'][:100]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
