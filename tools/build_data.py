#!/usr/bin/env python3
"""Build the public data file for the Signal City website.

Usage: python3 tools/build_data.py <export_dir> <out_file>

<export_dir> holds the database export: signals/*.json, stocks/*.json and
city/pulse.json. Only public research goes into <out_file>. Private material
(the Pitch book, private-company profiles, fund/pitch work, watch flags and
anything identifying the owner) is removed here, and the script refuses to
write the file if anything that looks private slips through.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

# Sentences mentioning pitch / fund work are dropped from any text field.
PRIVATE_TEXT = re.compile(
    r"pitch|the fund\b|fund's|our fund|simulat|\bLBO\b|buyout case|pension club|student|sleeve",
    re.I,
)
# Final safety net: never publish these.
FORBIDDEN = re.compile(r"carter|parass|@gmail|\bu_[A-Za-z0-9]{22}\b", re.I)

SIGNAL_FIELDS = ["sector", "kind", "stance", "title", "body", "tickers", "source",
                 "url", "date", "added", "links"]
STOCK_FIELDS = ["name", "tower", "price", "mcap", "pe", "fpe", "ps", "pb", "ev", "beta",
                "rev", "revG", "margin", "div", "target", "rating", "short", "hi52", "lo52",
                "cap", "src", "asOf", "about", "bull", "bear", "take", "risk", "cash", "debt",
                "fcf", "dil", "insider", "catalyst", "when", "runway"]
TEXT_FIELDS = {"title", "body", "about", "bull", "bear", "take", "catalyst", "runway", "why"}


def load(path):
    with open(path) as f:
        d = json.load(f)
    return d.get("data", d)


def scrub(text):
    """Drop whole sentences that touch private pitch/fund work."""
    if not isinstance(text, str):
        return text
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [p for p in parts if not PRIVATE_TEXT.search(p)]
    return " ".join(kept)


def main(src, out):
    signals, stocks = [], {}

    # Private profiles never get published. They are read only to find the
    # simulated-buyout targets, whose follow-up signals are pitch work too.
    pdir = os.path.join(src, "privates")
    if not os.path.isdir(pdir):
        sys.exit("Export the privates collection too, so pitch work can be filtered out.")
    sim_targets = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(pdir, "*.json"))
                   if load(f).get("simNote")}

    for f in sorted(glob.glob(os.path.join(src, "signals", "*.json"))):
        sid = os.path.basename(f)[:-5]
        s = load(f)
        # The Pitch book (private-company pitches) stays private.
        if s.get("sector") == "private" and s.get("kind") == "idea":
            continue
        if s.get("p"):
            continue
        # Follow-ups on a simulated buyout target are part of the pitch.
        if any(l.get("p") in sim_targets and l.get("role") == "direct"
               for l in s.get("links") or []):
            continue
        # Signals whose headline is about pitch/fund work stay private too.
        if PRIVATE_TEXT.search(s.get("title", "")):
            continue
        pub = {k: s[k] for k in SIGNAL_FIELDS if k in s}
        pub["id"] = sid
        pub["body"] = scrub(pub.get("body", ""))
        links = []
        for l in s.get("links") or []:
            if l.get("p"):  # links to private-company profiles
                continue
            why = scrub(l.get("why", ""))
            links.append({"t": l.get("t"), "role": l.get("role"), "why": why})
        pub["links"] = links
        pub["tickers"] = [l["t"] for l in links]
        if not pub["body"] and not links:
            continue
        signals.append(pub)

    used = {l["t"] for s in signals for l in s["links"]}
    for f in sorted(glob.glob(os.path.join(src, "stocks", "*.json"))):
        t = os.path.basename(f)[:-5]
        if t not in used:
            continue
        s = load(f)
        pub = {k: s[k] for k in STOCK_FIELDS if k in s and s[k] is not None}
        for k in TEXT_FIELDS & pub.keys():
            pub[k] = scrub(pub[k])
            if not pub[k]:
                del pub[k]
        pub["ticker"] = t
        stocks[t] = pub

    pulse = None
    pp = os.path.join(src, "city", "pulse.json")
    if os.path.exists(pp):
        p = load(pp)
        tape = [{k: scrub(x.get(k, "")) for k in ("label", "value", "note")}
                for x in p.get("tape", [])]
        pulse = {"updated": p.get("updated"), "tape": tape}

    data = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": signals,
        "stocks": stocks,
        "pulse": pulse,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    bad = FORBIDDEN.search(blob) or PRIVATE_TEXT.search(blob)
    if bad:
        sys.exit(f"Refusing to publish: private-looking text found near {blob[max(0, bad.start()-80):bad.end()+80]!r}")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        f.write(blob)
    print(f"wrote {out}: {len(signals)} signals, {len(stocks)} stocks")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
