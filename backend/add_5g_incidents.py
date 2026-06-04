"""
Augment dataset with synthetic 5G-NR incidents across all regions.
Appends to CSV, re-embeds via gateway (if available), and rebuilds BM25.
"""
import sys, os, csv, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SYNTHETIC_5G = [
    # SOUTH (10 incidents)
    {"alarm_id":"SYN-5G-S01","network_region":"South","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Radio Link Failure","device_vendor":"Ericsson","outage_duration":45,"affected_subscribers":28000,"recurrence_count":3,"service_impact":"Voice calls, Mobile data","resolution_time_minutes":60,"incident_description":"5G-NR Radio Link Failure (RLF) storm in South region. Ericsson gNB sites reporting T310 timer expiry causing mass UE detachments. RSRP dropped below -115 dBm across South cluster. 3GPP TS 38.331 layer 3 messages showing repeated RRCReconfiguration failures. Connectivity failure affecting 28,000 subscribers.","resolution_notes":"Identified interference from adjacent LTE band. Adjusted 5G NR carrier frequency and PCI conflict resolved. UEs reconnected after gNB parameter update.","timestamp":"2023-11-15 14:30:00"},
    {"alarm_id":"SYN-5G-S02","network_region":"South","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Handover Failure","device_vendor":"Nokia","outage_duration":30,"affected_subscribers":15000,"recurrence_count":5,"service_impact":"Data sessions, VoNR calls","resolution_time_minutes":45,"incident_description":"5G-NR X2/Xn handover failure in South region. Nokia gNB reporting increased handover failure rate (HFR) at 23% against 2% KPI target. UEs experiencing call drops during mobility between South sector cells. A1/A2/A3 event triggers misconfigured after recent parameter push. 15,000 subscribers affected in South coverage zone.","resolution_notes":"Rolled back parameter push. Re-optimized A3 event offset and TTT values. Handover success rate restored to 98.5%.","timestamp":"2023-10-08 09:15:00"},
    {"alarm_id":"SYN-5G-S03","network_region":"South","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Physical Layer Fault","device_vendor":"Huawei","outage_duration":60,"affected_subscribers":35000,"recurrence_count":1,"service_impact":"Complete 5G service loss, fallback to 4G","resolution_time_minutes":75,"incident_description":"5G-NR physical layer (PHY) fault in South region. Huawei AAU (Active Antenna Unit) reporting Layer 1 synchronization loss across South macro layer. PDSCH/PUSCH decode failures at 45%. Beamforming vectors misaligned after firmware upgrade to V300R019C10. South region 5G NR service degraded to near-complete outage.","resolution_notes":"Emergency firmware rollback to V300R018C20. AAU recalibration performed. Beamforming parameters restored from backup. 5G service recovered.","timestamp":"2023-12-01 02:45:00"},
    {"alarm_id":"SYN-5G-S04","network_region":"South","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Clock Sync Loss","device_vendor":"Ericsson","outage_duration":25,"affected_subscribers":12000,"recurrence_count":2,"service_impact":"5G NR timing degradation, URLLC service impact","resolution_time_minutes":35,"incident_description":"5G-NR timing synchronization failure in South region. Ericsson baseband unit (BBU) lost GPS/PTP timing reference. IEEE 1588v2 boundary clock drift of 180ns exceeding 100ns 3GPP requirement. South region gNBs showing PTPD daemon errors and SyncE holdover mode. 12,000 subscribers experiencing intermittent 5G connectivity.","resolution_notes":"GPS antenna cable fault identified and replaced. PTP grandmaster failover to secondary source. Timing lock restored within SLA.","timestamp":"2023-09-20 18:00:00"},
    {"alarm_id":"SYN-5G-S05","network_region":"South","technology_type":"5G-NR","severity":"P3-Medium","alarm_type":"Signal Degradation","device_vendor":"Nokia","outage_duration":18,"affected_subscribers":8500,"recurrence_count":7,"service_impact":"Throughput degradation, higher latency","resolution_time_minutes":30,"incident_description":"5G-NR signal quality degradation in South region. Nokia gNB SINR measurements dropping to -3dB in affected South sectors. DL throughput reduced from 800 Mbps to 120 Mbps. Interference suspected from nearby industrial equipment. CQI feedback from UEs showing MCS index drop from 28 to 8. Affecting South region premium subscribers.","resolution_notes":"Drive test identified source of interference at industrial site. Coordinated with site management. Temporary beam tilt adjustment +2 degrees applied.","timestamp":"2023-08-14 11:30:00"},
    {"alarm_id":"SYN-5G-S06","network_region":"South","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"gNB Connectivity Failure","device_vendor":"Huawei","outage_duration":90,"affected_subscribers":42000,"recurrence_count":1,"service_impact":"Complete 5G outage in South sector","resolution_time_minutes":110,"incident_description":"5G-NR gNB connectivity failure in South region. Huawei gNB NG interface to 5G Core (AMF) disconnected following core upgrade. SCTP association teardown detected. S-NSSAI routing failure for eMBB slice. UE registration procedure failing with cause NAS reject. 42,000 South region subscribers unable to access 5G network services.","resolution_notes":"5G Core AMF routing table corrupted during upgrade. Rollback of NGU interface configuration. SCTP multi-homing paths restored. gNB reconnected to AMF.","timestamp":"2023-07-22 22:00:00"},
    {"alarm_id":"SYN-5G-S07","network_region":"South","technology_type":"5G-NR","severity":"P2-High","alarm_type":"VSWR Alarm","device_vendor":"Ericsson","outage_duration":40,"affected_subscribers":19000,"recurrence_count":4,"service_impact":"5G coverage holes, increased call drops","resolution_time_minutes":55,"incident_description":"5G-NR VSWR (Voltage Standing Wave Ratio) alarm in South region. Ericsson Remote Radio Unit (RRU) reporting VSWR > 3.0 on n78 band antenna port. Antenna feeder cable moisture ingress suspected. South region 5G coverage reduced by 40%. Affected subscribers experiencing dropped connections at cell edge.","resolution_notes":"Antenna feeder inspection confirmed moisture ingress at junction. Cable replaced and weatherproofing applied. VSWR returned to 1.3, within 1.5 threshold.","timestamp":"2023-06-10 07:20:00"},
    {"alarm_id":"SYN-5G-S08","network_region":"South","technology_type":"5G-NR","severity":"P3-Medium","alarm_type":"Link Flap","device_vendor":"Nokia","outage_duration":15,"affected_subscribers":6000,"recurrence_count":12,"service_impact":"Intermittent 5G disconnections","resolution_time_minutes":25,"incident_description":"5G-NR fronthaul link flapping in South region. Nokia CPRI/eCPRI fronthaul link between DU (Distributed Unit) and RU (Radio Unit) experiencing microwave path fluctuations. Link flap rate 8 per hour against 0 per hour SLA. South region subscribers experiencing intermittent 5G service interruptions every 7-8 minutes.","resolution_notes":"Fronthaul transport path QoS mis-configuration identified. Priority queuing for fronthaul traffic restored. Link stability confirmed stable for 2 hours.","timestamp":"2023-05-05 15:45:00"},
    {"alarm_id":"SYN-5G-S09","network_region":"South","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Board Failure","device_vendor":"Huawei","outage_duration":50,"affected_subscribers":22000,"recurrence_count":2,"service_impact":"5G sector outage, 33% capacity loss","resolution_time_minutes":65,"incident_description":"5G-NR baseband board failure in South region. Huawei BBU board LBBP (LTE/NR Baseband Processing) reporting fatal hardware error. Three South region 5G NR cells taken out of service. Board temperature alarm preceded fault by 2 hours. South area subscribers losing 5G connectivity, falling back to 4G-LTE.","resolution_notes":"LBBP board replaced on-site. Spare board provisioned from regional depot. 5G cells restored after board swap and software re-provisioning.","timestamp":"2023-04-18 03:10:00"},
    {"alarm_id":"SYN-5G-S10","network_region":"South","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Handover Failure","device_vendor":"Ericsson","outage_duration":70,"affected_subscribers":31000,"recurrence_count":1,"service_impact":"5G mobility failure, mass call drops","resolution_time_minutes":85,"incident_description":"5G-NR mass handover failure in South region. Ericsson 5G-NR network experiencing Xn-based handover failures due to AMF overload after software upgrade. NGAP procedure timeout causing source gNB to release UE context. 31,000 South region subscribers experiencing sustained call drops during mobility. Connected mode mobility failure rate at 34%.","resolution_notes":"AMF capacity scaling applied. Xn handover timeout parameters tuned. Congestion window reset. Handover success rate recovered to 99.1%.","timestamp":"2023-03-07 16:30:00"},

    # NORTH (6 incidents - already has 5, add 6 more)
    {"alarm_id":"SYN-5G-N01","network_region":"North","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Radio Link Failure","device_vendor":"Ericsson","outage_duration":55,"affected_subscribers":33000,"recurrence_count":2,"service_impact":"5G North sector outage","resolution_time_minutes":70,"incident_description":"5G-NR radio link failure in North region. Mass RLF event across Ericsson gNB cluster following unexpected cell parameter change. North region reporting 28% RLF rate against 0.5% target. RRC connection setup success degraded. 33,000 subscribers in North area losing 5G connectivity.","resolution_notes":"Parameter rollback executed. RLF rate normalized. Investigated root cause: automated SON algorithm triggered incorrect power reduction.","timestamp":"2023-11-20 10:00:00"},
    {"alarm_id":"SYN-5G-N02","network_region":"North","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Signal Degradation","device_vendor":"Nokia","outage_duration":35,"affected_subscribers":18000,"recurrence_count":6,"service_impact":"North 5G throughput degradation","resolution_time_minutes":50,"incident_description":"5G-NR signal degradation in North region. Nokia mmWave (FR2) gNB sites showing PDSCH MCS drop from 27 to 12. North region 5G mmWave cells experiencing rain fade attenuation. SINR degraded to -5dB. 18,000 North subscribers experiencing reduced 5G speeds from 2 Gbps to 300 Mbps.","resolution_notes":"FR2 beam management optimized for weather resilience. Backup FR1 cells capacity boosted. mmWave performance monitoring enhanced.","timestamp":"2023-10-12 14:00:00"},
    {"alarm_id":"SYN-5G-N03","network_region":"North","technology_type":"5G-NR","severity":"P3-Medium","alarm_type":"Clock Sync Loss","device_vendor":"Huawei","outage_duration":22,"affected_subscribers":9000,"recurrence_count":3,"service_impact":"5G timing degradation","resolution_time_minutes":35,"incident_description":"5G-NR timing synchronization issue in North region. Huawei gNB reporting PTP timing offset exceeding 3GPP requirements. North region synchronized network (SyncE) chain broken at aggregation switch. Time error accumulation causing PDSCH scheduling inefficiency. 9,000 North subscribers experiencing intermittent 5G connectivity.","resolution_notes":"SyncE chain rebuilt from grandmaster. PTP BC configuration verified. Timing error below 100ns. Monitors set for early detection.","timestamp":"2023-09-25 08:00:00"},

    # WEST (6 incidents - already has 4, add more)
    {"alarm_id":"SYN-5G-W01","network_region":"West","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Physical Layer Fault","device_vendor":"Nokia","outage_duration":65,"affected_subscribers":37000,"recurrence_count":1,"service_impact":"West 5G complete outage","resolution_time_minutes":80,"incident_description":"5G-NR physical layer fault in West region. Nokia AirScale AAU firmware bug triggered mass physical layer reset across West region gNBs. PUSCH decode success rate dropped to 12%. West area subscribers completely unable to access 5G services. NG interface remained up but no radio connectivity. Emergency field dispatch required.","resolution_notes":"Nokia TAC emergency patch applied. AAU firmware rolled back to stable version. Physical layer re-initialized. West 5G service restored.","timestamp":"2023-12-10 23:00:00"},
    {"alarm_id":"SYN-5G-W02","network_region":"West","technology_type":"5G-NR","severity":"P2-High","alarm_type":"VSWR Alarm","device_vendor":"Ericsson","outage_duration":42,"affected_subscribers":21000,"recurrence_count":3,"service_impact":"West 5G coverage degradation","resolution_time_minutes":58,"incident_description":"5G-NR VSWR alarm in West region. Ericsson 5G antenna systems in West cluster reporting elevated VSWR values (2.8-3.5) on n41 and n78 bands. Lightning strike nearby caused surge protection damage on multiple antenna ports. West region 5G coverage reduced significantly. Subscribers experiencing higher call drop rates.","resolution_notes":"On-site inspection found surge arrestors blown on 3 sites. Components replaced. Antenna system re-tested and calibrated.","timestamp":"2023-08-30 17:45:00"},

    # EAST (6 incidents - already has 3, add more)
    {"alarm_id":"SYN-5G-E01","network_region":"East","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"gNB Connectivity Failure","device_vendor":"Huawei","outage_duration":75,"affected_subscribers":39000,"recurrence_count":1,"service_impact":"East 5G service disruption","resolution_time_minutes":90,"incident_description":"5G-NR gNB connectivity failure in East region. Huawei gNBs in East losing NG interface after datacenter power event affecting 5G Core equipment. AMF-gNB SCTP associations reset. N2 interface procedures failing. East region 39,000 subscribers unable to register on 5G network. VoNR sessions terminated.","resolution_notes":"5G Core AMF restored after power recovery. SCTP associations re-established. gNB N2 procedures normalized. Full 5G service restored in East.","timestamp":"2023-11-28 01:15:00"},
    {"alarm_id":"SYN-5G-E02","network_region":"East","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Board Failure","device_vendor":"Ericsson","outage_duration":48,"affected_subscribers":24000,"recurrence_count":2,"service_impact":"East 5G partial outage","resolution_time_minutes":63,"incident_description":"5G-NR baseband processing failure in East region. Ericsson Baseband 6630 module reporting thermal shutdown in East cluster. Three sectors lost 5G service. CPU utilization was at 95% before shutdown due to software memory leak. East subscribers on affected cells forced to 4G fallback. 24,000 impacted.","resolution_notes":"Baseband module cooled and restarted. Software patch applied to fix memory leak. Temperature monitoring thresholds adjusted for early warning.","timestamp":"2023-07-15 12:00:00"},

    # CENTRAL (5 incidents - already has 2, add more)
    {"alarm_id":"SYN-5G-C01","network_region":"Central","technology_type":"5G-NR","severity":"P1-Critical","alarm_type":"Handover Failure","device_vendor":"Nokia","outage_duration":55,"affected_subscribers":27000,"recurrence_count":1,"service_impact":"Central 5G mobility failure","resolution_time_minutes":70,"incident_description":"5G-NR handover failure in Central region. Nokia 5G-NR network experiencing intra-frequency handover failures due to X2 interface congestion. Handover success rate dropped from 99.2% to 71% in Central region. UEs stuck in source cell unable to complete HO procedures. Nokia RAN software bug triggered during peak hour. 27,000 Central subscribers affected.","resolution_notes":"Nokia emergency patch NPOS23Q4-5G applied. X2 interface buffer flush executed. Handover optimization re-ran. Success rate restored to 99.1%.","timestamp":"2023-10-25 19:30:00"},
    {"alarm_id":"SYN-5G-C02","network_region":"Central","technology_type":"5G-NR","severity":"P2-High","alarm_type":"Link Flap","device_vendor":"Huawei","outage_duration":28,"affected_subscribers":13000,"recurrence_count":8,"service_impact":"Central 5G intermittent outages","resolution_time_minutes":40,"incident_description":"5G-NR fronthaul instability in Central region. Huawei CPRI fronthaul links between DU and RU experiencing repeated flapping due to SFP transceiver degradation. Central region 5G cells cycling down and up every 12-15 minutes. 13,000 subscribers experiencing intermittent 5G service. Optical power levels showing erratic -3dBm fluctuation.","resolution_notes":"SFP transceivers replaced on affected fronthaul paths. Optical power verified within -8 to -3 dBm range. Link stability confirmed.","timestamp":"2023-09-03 10:45:00"},
]

def main():
    import pandas as pd
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'telecom_incidents.csv')
    csv_path = os.path.normpath(csv_path)

    df = pd.read_csv(csv_path)
    print(f"Original rows: {len(df)}")

    # Check for duplicates before adding
    existing_ids = set(df['alarm_id'].tolist())
    new_records = [r for r in SYNTHETIC_5G if r['alarm_id'] not in existing_ids]
    print(f"Adding {len(new_records)} new 5G-NR incidents")

    if not new_records:
        print("All synthetic incidents already in dataset. Skipping.")
        return

    new_df = pd.DataFrame(new_records)
    combined = pd.concat([df, new_df], ignore_index=True)
    combined.to_csv(csv_path, index=False)
    print(f"New CSV rows: {len(combined)}")

    # Rebuild BM25 index
    print("\nRebuilding BM25 index...")
    import pickle, re, pandas as _pd
    from rank_bm25 import BM25Okapi
    from config import settings

    def _tokenize(text):
        return re.findall(r"\b\w+\b", str(text).lower())

    _df = _pd.read_csv(csv_path)
    corpus_texts = (_df.get("incident_description", _pd.Series()).fillna("").astype(str)
                    + " " + _df.get("resolution_notes", _pd.Series()).fillna("").astype(str))
    alarm_ids = _df["alarm_id"].tolist()
    tokenized = [_tokenize(t) for t in corpus_texts]
    bm25_obj = BM25Okapi(tokenized)
    with open(settings.BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25_obj, "alarm_ids": alarm_ids}, f)
    # Reset cached index so it reloads on next query
    import rag.bm25_search as _bm
    _bm._bm25 = None
    _bm._alarm_ids = None
    print("BM25 index rebuilt.")

    # Try to add to ChromaDB (requires embeddings)
    print("\nAttempting to add to ChromaDB (needs gateway)...")
    try:
        from rag.embeddings import embed_query
        from rag.vector_store import get_collection
        collection = get_collection()

        existing_chroma_ids = set(collection.get(include=[])['ids'])
        to_embed = [r for r in new_records if r['alarm_id'] not in existing_chroma_ids]
        print(f"  {len(to_embed)} incidents to embed for ChromaDB")

        batch_size = 10
        for i in range(0, len(to_embed), batch_size):
            batch = to_embed[i:i+batch_size]
            texts = [
                f"Alarm: {r['alarm_id']} | {r['incident_description']} Resolution: {r['resolution_notes']}"
                for r in batch
            ]
            print(f"  Embedding batch {i//batch_size + 1}/{(len(to_embed)+batch_size-1)//batch_size}...")
            embeddings = [embed_query(t) for t in texts]
            metadatas = [{
                'alarm_id': r['alarm_id'],
                'network_region': r['network_region'],
                'technology_type': r['technology_type'],
                'severity': r['severity'],
                'alarm_type': r['alarm_type'],
                'device_vendor': r['device_vendor'],
                'outage_duration': r['outage_duration'],
                'affected_subscribers': r['affected_subscribers'],
                'recurrence_count': r['recurrence_count'],
                'service_impact': r['service_impact'],
                'resolution_notes': r['resolution_notes'],
                'timestamp': r['timestamp'],
                'resolution_time_minutes': r['resolution_time_minutes'],
            } for r in batch]
            collection.upsert(
                ids=[r['alarm_id'] for r in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            print(f"  Batch {i//batch_size + 1} stored in ChromaDB.")

        print(f"ChromaDB updated. New total: {collection.count()}")
    except Exception as e:
        print(f"ChromaDB update skipped (gateway issue): {e}")
        print("BM25 was rebuilt — partial improvement active.")
        print("Run /api/ingest when gateway is available to complete ChromaDB update.")


if __name__ == '__main__':
    main()
