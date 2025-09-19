import csv
import os
from pathlib import Path

from psengine.enrich import SoarMgr

OUTPUT_DIR = os.path.join(os.getcwd(), "enrich")
os.makedirs(OUTPUT_DIR, exist_ok=True)

to_enrich_file = Path(os.path.join(OUTPUT_DIR, "to_enrich.csv"))
to_enrich_file.write_text("ip\n1.1.1.1\n2.2.2.2")

enriched_file = Path(os.path.join(OUTPUT_DIR, "enriched.csv"))

mgr = SoarMgr()

with to_enrich_file.open(newline="") as f:
    reader = csv.DictReader(f)
    ips_to_enrich = [row["ip"] for row in reader]

enriched_ips = mgr.soar(ip=ips_to_enrich)

with enriched_file.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ip", "score"])
    for ip, enriched in zip(ips_to_enrich, enriched_ips):
        writer.writerow([ip, enriched.content.risk.score])
