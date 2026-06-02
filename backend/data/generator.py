"""
Synthetic 5G Network Performance Dataset Generator
Generates 500 realistic telecom incident records for RAG ingestion.
"""
import csv
import random
import os
from datetime import datetime, timedelta

REGIONS = ["North", "South", "East", "West", "Central"]
TECHNOLOGIES = ["5G-NR", "4G-LTE", "3G-UMTS", "Fiber", "MPLS", "SD-WAN"]
SEVERITIES = ["P1-Critical", "P2-High", "P3-Medium", "P4-Low"]
VENDORS = ["Ericsson", "Nokia", "Huawei", "Cisco", "Juniper"]
ALARM_TYPES = [
    "Hardware Failure", "Config Error", "Capacity Overload",
    "Sync Loss", "Link Down", "Software Bug", "Power Failure",
    "Interference", "Transport Failure", "Authentication Failure"
]
SERVICES = [
    "Voice Calls", "Data Sessions", "SMS", "VoLTE", "IoT Connectivity",
    "Enterprise VPN", "Roaming Services", "Emergency Services", "Video Streaming"
]

INCIDENT_TEMPLATES = [
    # 5G-NR templates
    "{count} gNB nodes in {region} region reporting X2 interface failures after firmware upgrade to {version}. "
    "UE attach success rate dropped from 98% to {rate}%. Engineers observed increased RRC connection rejections. "
    "Root cause identified as misconfigured AMF pool configuration post-upgrade.",

    "Massive MIMO antenna tilt misconfiguration on {count} sector sites in {region}. "
    "SINR degraded by {delta} dB causing uplink interference. Capacity reduced by {pct}% during peak hours. "
    "Service degradation reported by enterprise customers using mmWave bands.",

    "5G NR SA core network experiencing PDU session establishment failures in {region}. "
    "UPF processing latency spiked to {latency}ms. Affected {subscribers} IoT devices unable to connect. "
    "SMF logs show session binding errors correlated with UPF software defect #{defect}.",

    "N2/N3 interface congestion between {region} gNBs and AMF cluster. "
    "{count} sites showing SCTP association failures. Emergency handover to 4G-LTE fallback activated. "
    "Traffic load balancing misconfiguration identified as probable cause.",

    "CU-DU functional split failure on {count} distributed 5G nodes in {region}. "
    "F1 interface went down due to transport network IP route withdrawal. "
    "Mid-haul link between CU and DU lost for {duration} minutes causing complete service disruption.",

    # 4G-LTE templates
    "Multiple eNodeBs in {region} showing S1 interface failure after planned maintenance window. "
    "MME connection dropped across {count} sites. Cause: BGP route advertisement error on backhaul routers. "
    "Subscribers experiencing call drops and data session timeouts in the affected area.",

    "LTE carrier aggregation malfunction on Band 3 + Band 7 in {region}. "
    "PDCP layer buffer overflow caused by DRB misconfiguration after software patch {patch}. "
    "{subscribers} high-value subscribers affected. ARPU impact estimated at ${revenue}K.",

    "X2 handover failures between {region} eNodeBs and neighboring cluster. "
    "Inter-eNB handover success rate dropped to {rate}%. Ping-pong handover storms observed. "
    "SON algorithm override required to stabilize mobility parameters.",

    "CSFB (Circuit Switched Fallback) failure rate spike in {region} — {rate}% failure observed. "
    "MSC-S unreachable from {count} eNodeBs due to SS7 link congestion. "
    "Voice call setup failure affected {subscribers} subscribers during peak hours.",

    "LTE PDCP integrity protection mismatch on {vendor} eNodeBs after security patch. "
    "UE contexts being dropped at RRC reconfiguration phase. {count} cells impacted in {region}. "
    "Hotfix deployment required to restore normal operations.",

    # Fiber / Transport templates
    "Fiber cut on backbone ring between {region} hub and metro aggregation node. "
    "APS (Automatic Protection Switching) triggered but secondary path showing {latency}ms additional latency. "
    "{count} enterprise circuits and {subscribers} mobile subscribers affected on dependent transport.",

    "DWDM wavelength drift detected on {region} fiber span kilometer {km}. "
    "OSNR degraded below threshold causing FEC errors to spike. "
    "Amplifier gain tilt compensation adjusted but optical power margin remains critically low.",

    "Submarine cable EDFA failure causing signal degradation on {region} international link. "
    "Capacity reduced from {capacity}Gbps to {reduced}Gbps. "
    "Traffic rerouted via alternate cable system with {latency}ms additional round-trip delay.",

    # MPLS/Core templates
    "MPLS LDP session flap on core router in {region} causing traffic blackhole for {duration} minutes. "
    "{count} L3VPN tunnels re-converging after IGP topology change. "
    "BGP prefix withdrawal storm affected enterprise customers during reconvergence.",

    "ISIS adjacency loss between {region} P-routers after planned IOS-XR upgrade. "
    "SPF recalculation loop detected causing micro-burst packet loss. "
    "ECMP paths became unequal triggering traffic imbalance across {count} interfaces.",

    "Segment routing MPLS path computation failure in {region} SR-TE domain. "
    "PCE-server connectivity lost due to TLS certificate expiry. "
    "{count} critical traffic classes losing QoS guarantees. Enterprise SLA breached.",

    # Hardware failure templates
    "Line card failure on {vendor} core router in {region} data center. "
    "Module {slot} ejected due to ASIC thermal runaway at {temp}°C. "
    "Traffic failover to redundant linecard triggered {latency}ms packet loss event.",

    "Power supply unit failure in {region} outdoor macro cell cabinet. "
    "Generator backup activated but fuel exhaustion after {duration} hours caused site blackout. "
    "{count} collocated operators affected. TSSR dispatched for emergency repair.",

    "Battery backup degradation on {count} {region} BTS sites. "
    "Float charge voltage below threshold causing premature cutoff during grid outage. "
    "Preventive maintenance schedule requires immediate overhaul of UPS systems.",

    # Synchronization templates
    "PTP/IEEE-1588 grandmaster clock failure in {region} synchronization hierarchy. "
    "Holdover mode activated on {count} slave clocks. Phase error accumulating at {rate} ns/s. "
    "5G NR TDD frame alignment at risk after {duration} minutes without reference.",

    "GNSS antenna failure on {region} primary timing reference. "
    "Backup BITS/SSU clock source activated. Stratum level degraded from 1 to 3. "
    "{count} dependent 5G sites at risk of air interface synchronization failure.",

    # Capacity/Congestion templates
    "Uplink PRB utilization exceeding 90% on {count} cells in {region} during peak traffic. "
    "Scheduler fairness degraded for edge UEs. Average throughput dropped {pct}%. "
    "Emergency capacity expansion through spectrum refarming initiated.",

    "Core network signaling storm from {count} IoT devices in {region} entering simultaneous TAU cycles. "
    "MME/AMF overloaded causing {rate}% attach rejection rate. "
    "Emergency rate limiting applied to prevent total core collapse.",

    # Software/Config templates
    "Incorrect ACL configuration pushed to {count} {vendor} routers in {region} via automated provisioning. "
    "Management plane traffic blocked causing loss of visibility to {count} network elements. "
    "Emergency rollback executed via out-of-band console access.",

    "BGP route policy misconfiguration in {region} caused {count}K prefixes to be inadvertently withdrawn. "
    "Internet traffic blackholed for {duration} minutes. "
    "Customer escalations: {subscribers} broadband users reported total connectivity loss.",
]

RESOLUTION_TEMPLATES = [
    "Rolled back firmware to previous stable version {version}. Reconfigured AMF pool settings per vendor guidelines. "
    "Performed progressive site-by-site upgrade with validation checkpoints. Full service restored.",

    "Executed RF parameter optimization using SON toolset. Adjusted antenna tilt by {delta} degrees. "
    "Activated neighbor cell load balancing. Service KPIs returned to baseline within {duration} minutes.",

    "Applied emergency hotfix patch {patch} from vendor. Restarted UPF/SMF network functions. "
    "Verified PDU session establishment in staging environment before production rollout.",

    "Restored BGP route advertisements on backhaul routers. Reset SCTP associations to AMF. "
    "Implemented route dampening to prevent future flapping. Added monitoring alerts for BGP state changes.",

    "Replaced failed hardware component. Ran comprehensive diagnostic tests post-replacement. "
    "Updated preventive maintenance schedule and raised spare parts inventory threshold.",

    "Restored fiber cut using emergency splice. Reconfigured DWDM parameters. "
    "Implemented enhanced physical layer monitoring with OTDR alerts. SLA credit issued to affected customers.",

    "Re-established PTP synchronization chain using backup grandmaster. "
    "Deployed additional GNSS antennas for redundancy. Updated synchronization monitoring dashboards.",

    "Implemented emergency traffic offload through carrier WiFi and small cell densification. "
    "Activated additional spectrum through dynamic frequency assignment. Permanent capacity upgrade planned.",

    "Executed rollback of misconfigured ACL policies via out-of-band management. "
    "Implemented pre-deployment validation checks in CI/CD pipeline. Change freeze applied.",

    "Restarted affected network function instances. Applied configuration correction. "
    "Root cause analysis completed and design fix scheduled for next maintenance window.",
]


def random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def fill_template(template: str) -> str:
    subs = {
        "{count}": str(random.randint(2, 50)),
        "{region}": random.choice(REGIONS),
        "{version}": f"{random.randint(18,23)}.Q{random.randint(1,4)}",
        "{rate}": str(random.randint(40, 85)),
        "{delta}": str(random.randint(2, 15)),
        "{pct}": str(random.randint(15, 60)),
        "{latency}": str(random.randint(50, 500)),
        "{subscribers}": str(random.randint(500, 150000)),
        "{defect}": f"SW-{random.randint(10000, 99999)}",
        "{duration}": str(random.randint(10, 480)),
        "{patch}": f"HF-{random.randint(1000, 9999)}",
        "{revenue}": str(random.randint(50, 2000)),
        "{km}": str(random.randint(10, 500)),
        "{capacity}": str(random.randint(100, 400)),
        "{reduced}": str(random.randint(20, 80)),
        "{slot}": f"{random.randint(1,16)}/{random.randint(0,3)}",
        "{temp}": str(random.randint(85, 120)),
        "{vendor}": random.choice(VENDORS),
        "{temp}": str(random.randint(85, 120)),
    }
    result = template
    for key, val in subs.items():
        result = result.replace(key, val)
    return result


def generate_dataset(n: int = 500) -> list[dict]:
    records = []
    for i in range(n):
        region = random.choice(REGIONS)
        tech = random.choice(TECHNOLOGIES)
        severity = random.choice(SEVERITIES)
        vendor = random.choice(VENDORS)
        alarm_type = random.choice(ALARM_TYPES)

        severity_weight = {"P1-Critical": 4, "P2-High": 3, "P3-Medium": 2, "P4-Low": 1}[severity]
        outage_duration = random.randint(5 * severity_weight, 60 * severity_weight)
        affected_subscribers = random.randint(100 * severity_weight, 50000 * severity_weight)
        resolution_time = random.randint(outage_duration, outage_duration * 3)

        template = random.choice(INCIDENT_TEMPLATES)
        resolution_template = random.choice(RESOLUTION_TEMPLATES)

        description = fill_template(template)
        resolution = fill_template(resolution_template)

        service_impacts = random.sample(SERVICES, k=random.randint(1, 3))

        records.append({
            "alarm_id": f"ALM-{2023 + i // 200}-{str(i + 1).zfill(5)}",
            "incident_description": description,
            "network_region": region,
            "technology_type": tech,
            "severity": severity,
            "outage_duration": outage_duration,
            "device_vendor": vendor,
            "resolution_notes": resolution,
            "timestamp": random_date().isoformat(),
            "service_impact": ", ".join(service_impacts),
            "alarm_type": alarm_type,
            "affected_subscribers": affected_subscribers,
            "resolution_time_minutes": resolution_time,
            "recurrence_count": random.randint(0, 8),
        })

    records.sort(key=lambda x: x["timestamp"])
    return records


def save_dataset(records: list[dict], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "../../data/telecom_incidents.csv")
    records = generate_dataset(500)
    save_dataset(records, output)
    print(f"Sample record:\n  {records[0]['alarm_id']}: {records[0]['incident_description'][:100]}...")
    print(f"Severity distribution: { {s: sum(1 for r in records if r['severity'] == s) for s in ['P1-Critical','P2-High','P3-Medium','P4-Low']} }")
