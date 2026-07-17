import csv, os
from datetime import date

OUT = "/mnt/user-data/outputs/intern/mock"
os.makedirs(OUT, exist_ok=True)

# ---------------- rate card (14 July) ----------------
rates = [
    # carrier_code, carrier_name, truck_id, base_fee_usd, rate_per_km_usd, currency, valid_from
    ("VLY", "Valley Haul Co",      "TRK-03", 240.00, 1.85, "USD", "2026-07-01"),
    ("PCF", "Pacific Freightways", "TRK-11", 310.00, 2.10, "USD", "2026-07-01"),
    ("GRN", "Grand Line Trucking", "TRK-07", 180.00, 1.40, "USD", "2026-07-01"),
    ("SRA", "Sierra Cartage",      "TRK-22", 265.00, 1.95, "USD", "2026-07-01"),
    ("DLT", "Delta Road LLC",      "TRK-15", 205.00, 1.62, "USD", "2026-07-01"),
    ("BAY", "Bayline Transport",   "TRK-09", 290.00, 2.35, "USD", "2026-07-01"),
]

# ---------------- manifest 14 July ----------------
# shipment_id, date, origin, destination, cargo_type, weight_kg, distance_km, carrier_code
manifest14 = [
    ("SHP-1041", "2026-07-14", "Oakland", "Fresno",      "palletised",  1240, 300, "PCF"),
    ("SHP-1042", "2026-07-14", "Oakland", "Bakersfield", "palletised",   480, 460, "VLY"),  # <500 -> drop
    ("SHP-1043", "2026-07-14", "Stockton","Fresno",      "bulk",        2900, 210, "VLY"),
    ("SHP-1044", "2026-07-14", "Oakland", "Sacramento",  "refrigerated", 860, 130, "GRN"),
    ("SHP-1045", "2026-07-14", "Fremont", "Bakersfield", "palletised",  3150, 440, "SRA"),
    ("SHP-1046", "2026-07-14", "Stockton","Sacramento",  "palletised",   320,  75, "DLT"),  # <500 -> drop
    ("SHP-1047", "2026-07-14", "Oakland", "Fresno",      "bulk",        4020, 305, "BAY"),
    ("SHP-1048", "2026-07-14", "Fremont", "Modesto",     "palletised",   940, 145, "GRN"),
    ("SHP-1049", "2026-07-14", "Oakland", "Bakersfield", "refrigerated",1780, 455, "DLT"),
    ("SHP-1050", "2026-07-14", "Stockton","Modesto",     "palletised",   150,  60, "VLY"),  # <500 -> drop
    ("SHP-1051", "2026-07-14", "Fremont", "Sacramento",  "bulk",        2260, 140, "MTN"),  # carrier not on card -> TBC
    ("SHP-1052", "2026-07-14", "Oakland", "Modesto",     "palletised",   410, 150, "SRA"),  # <500 -> drop
    ("SHP-1053", "2026-07-14", "Stockton","Fresno",      "palletised",  1595, 215, "SRA"),
]

# ---------------- manifest 17 July (the live demo run) ----------------
manifest17 = [
    ("SHP-1102", "2026-07-17", "Oakland", "Fresno",      "palletised",  2180, 300, "PCF"),
    ("SHP-1103", "2026-07-17", "Fremont", "Bakersfield", "bulk",        3640, 440, "SRA"),
    ("SHP-1104", "2026-07-17", "Stockton","Sacramento",  "palletised",   295,  75, "GRN"),  # drop
    ("SHP-1105", "2026-07-17", "Oakland", "Modesto",     "refrigerated",1120, 150, "DLT"),
    ("SHP-1106", "2026-07-17", "Oakland", "Fresno",      "bulk",        5310, 305, "BAY"),
    ("SHP-1107", "2026-07-17", "Fremont", "Sacramento",  "palletised",   770, 140, "VLY"),
    ("SHP-1108", "2026-07-17", "Stockton","Bakersfield", "palletised",  1450, 470, "MTN"),  # TBC
    ("SHP-1109", "2026-07-17", "Oakland", "Sacramento",  "palletised",   455, 130, "GRN"),  # drop
    ("SHP-1110", "2026-07-17", "Stockton","Modesto",     "bulk",        2640, 60,  "VLY"),
]

MANIFEST_HDR = ["shipment_id","date","origin","destination","cargo_type",
                "weight_kg","distance_km","carrier_code"]
RATES_HDR = ["carrier_code","carrier_name","truck_id","base_fee_usd",
             "rate_per_km_usd","currency","valid_from"]


def write(path, hdr, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)


def build_summary(manifest, rates):
    """The 7 hidden rules, applied by hand — this is Andrei's Tuesday."""
    rmap = {r[0]: r for r in rates}
    out = []
    for sid, d, origin, dest, cargo, kg, km, cc in manifest:
        if kg < 500:                                   # rule: skip little stuff
            continue
        r = rmap.get(cc)
        y, m, day = d.split("-")
        date_s = f"{day}.{m}.{y}"                      # rule: DD.MM.YYYY
        load = f"{kg/1000:.2f}"                        # rule: kg -> t, 2dp
        if r is None:
            truck, cost_n, cost_s = "TBC", -1, "TBC"   # rule: unknown carrier -> TBC
        else:
            truck = r[2]
            cost_n = round(r[3] + r[4] * km)           # rule: base + rate*km, whole dollars
            cost_s = f"{cost_n:,}"                     # rule: comma thousands, no cents
        out.append([date_s, dest, truck, load, cost_s, cost_n, kg])
    # rule: sort by Route A->Z, then dearest first (TBC last within a route)
    out.sort(key=lambda r: (r[1], -r[5]))
    rows = [r[:5] for r in out]
    # rule: TOTAL row — load and cost summed, other columns empty. TBC excluded from cost.
    tl = sum(float(r[3]) for r in out)
    tc = sum(r[5] for r in out if r[5] >= 0)
    rows.append(["", "", "TOTAL", f"{tl:.2f}", f"{tc:,}"])
    return rows


SUMMARY_HDR = ["Date","Route","Truck","Load (t)","Cost ($)"]

write(f"{OUT}/manifest_2026-07-14.csv", MANIFEST_HDR, manifest14)
rates_fmt = [(c,n,t,f"{b:.2f}",f"{r:.2f}",cur,v) for c,n,t,b,r,cur,v in rates]
write(f"{OUT}/carrier_rates_2026-07.csv", RATES_HDR, rates_fmt)
s14 = build_summary(manifest14, rates)
write(f"{OUT}/dispatch_summary_14.07.csv", SUMMARY_HDR, s14)

write(f"{OUT}/manifest_2026-07-17.csv", MANIFEST_HDR, manifest17)
write(f"{OUT}/carrier_rates_2026-07b.csv", RATES_HDR, rates_fmt)
s17 = build_summary(manifest17, rates)
write(f"{OUT}/_reference_summary_17.07.csv", SUMMARY_HDR, s17)

print("=== dispatch_summary_14.07.csv (GROUND TRUTH) ===")
print(",".join(SUMMARY_HDR))
for r in s14:
    print(",".join(r))
print(f"\nrows(data+total) = {len(s14)}  cells = {len(s14)*5}")
print("\n=== reference for 17.07 (live demo output) ===")
for r in s17:
    print(",".join(r))
print(f"rows = {len(s17)} cells = {len(s17)*5}")
