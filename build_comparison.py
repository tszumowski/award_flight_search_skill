#!/usr/bin/env python3
"""Extract flight data from JSONL detail files into compact JSON for HTML comparison.

Usage:
    python build_comparison.py --outbound file1.jsonl [file2.jsonl ...] --return file3.jsonl [file4.jsonl ...] --output flights.json

Reads JSONL detail files (produced by main.py --fetch-details), extracts departure/arrival
times from flight segments, and outputs compact JSON arrays suitable for embedding in an
interactive HTML comparison page.

Output JSON format:
{
  "outbound": [[date, origin, dest, carrier, flight, program, dep_hour, arr_hour,
                 dep_time, arr_time, miles, tax, cabin, seats, stops, layover_min,
                 duration_min, transfer_programs], ...],
  "return": [...]
}

Field indices:
  0=date (MM-DD), 1=origin, 2=dest, 3=carrier, 4=flight_nums, 5=program,
  6=dep_hour (float), 7=arr_hour (float), 8=dep_time (HH:MM), 9=arr_time (HH:MM or HH:MM+1),
  10=miles, 11=tax, 12=cabin, 13=seats, 14=stops, 15=layover_min, 16=duration_min,
  17=transfer_programs (semicolon-separated)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_jsonl_file(filepath: str) -> list[dict]:
    """Read a JSONL file and return list of parsed JSON objects."""
    results = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def normalize_cabin(cabin: str) -> str:
    """Normalize airline-specific cabin names to standard classes."""
    c = cabin.lower().strip()
    if any(k in c for k in ["first"]):
        return "First"
    if any(k in c for k in ["business"]):
        return "Business"
    if any(k in c for k in ["premium"]):
        return "Premium Economy"
    # Economy variants: Blue Basic, Blue, Blue Extra, Main, Main Basic, Comfort, Economy, Saver, etc.
    return "Economy"


def extract_route_data(record: dict, route: dict) -> list | None:
    """Extract compact flight data from a single route within a JSONL record.

    Each JSONL record contains a top-level program/carrier and multiple routes[],
    where each route is a distinct flight itinerary with its own pricing.

    Returns a compact array or None if the route is invalid.
    """
    try:
        segments = route.get("segments", [])
        if not segments:
            return None

        # Get actual airport codes from first/last segments
        first_seg = segments[0]
        last_seg = segments[-1]

        origin_code = first_seg.get("departure_info", {}).get("airport", {}).get("airport_code", "")
        dest_code = last_seg.get("arrival_info", {}).get("airport", {}).get("airport_code", "")

        if not origin_code or not dest_code:
            return None

        # Parse departure and arrival times
        dep_str = first_seg.get("departure_info", {}).get("date_time", "")
        arr_str = last_seg.get("arrival_info", {}).get("date_time", "")

        if not dep_str or not arr_str:
            return None

        # Extract time components
        dep_time_str = dep_str.split("T")[1].split("+")[0].split("Z")[0][:5]  # HH:MM
        arr_time_str = arr_str.split("T")[1].split("+")[0].split("Z")[0][:5]

        dep_h = int(dep_time_str[:2])
        dep_m = int(dep_time_str[3:5])
        arr_h = int(arr_time_str[:2])
        arr_m = int(arr_time_str[3:5])

        dep_hour = round(dep_h + dep_m / 60, 2)
        arr_hour = round(arr_h + arr_m / 60, 2)

        # Check if arrival is next day
        dep_date_only = dep_str.split("T")[0]
        arr_date_only = arr_str.split("T")[0]
        if dep_date_only != arr_date_only:
            arr_hour += 24
            arr_time_display = f"{arr_time_str}+1"
        else:
            arr_time_display = arr_time_str

        # Date as MM-DD
        date_parts = dep_date_only.split("-")
        date_mmdd = f"{date_parts[1]}-{date_parts[2]}"

        # Route-level fields (pricing, cabin, seats, transfers)
        payment = route.get("payment", {})
        miles = payment.get("miles", 0)
        tax = payment.get("tax", 0)
        cabin_raw = route.get("cabin", {}).get("display", "Economy")
        cabin = normalize_cabin(cabin_raw)
        seats = payment.get("seats", 0)

        # Program info from route level (falls back to record level)
        carrier = route.get("code", record.get("code", ""))
        program = route.get("program", record.get("program", ""))

        # Transfer programs from route.transfer array
        transfers = route.get("transfer") or []
        transfer_programs = ";".join(t.get("bank", "") for t in transfers if isinstance(t, dict) and t.get("bank"))

        # Build flight number string from segments
        flight_nums = "+".join(
            seg.get("carrier_code", "") + seg.get("flight_number", "")
            for seg in segments
        )

        # Stops and layover
        stops = len(segments) - 1
        layover_min = 0
        if stops > 0:
            for i in range(len(segments) - 1):
                seg_arr = segments[i].get("arrival_info", {}).get("date_time", "")
                seg_dep = segments[i + 1].get("departure_info", {}).get("date_time", "")
                if seg_arr and seg_dep:
                    a = datetime.fromisoformat(seg_arr.replace("Z", "").split("+")[0])
                    d = datetime.fromisoformat(seg_dep.replace("Z", "").split("+")[0])
                    layover_min += int((d - a).total_seconds() / 60)

        # Duration in minutes
        duration_min = route.get("duration", 0)
        if not duration_min:
            d1 = datetime.fromisoformat(dep_str.replace("Z", "").split("+")[0])
            d2 = datetime.fromisoformat(arr_str.replace("Z", "").split("+")[0])
            duration_min = int((d2 - d1).total_seconds() / 60)

        return [
            date_mmdd,        # 0
            origin_code,      # 1
            dest_code,        # 2
            carrier,          # 3
            flight_nums,      # 4
            program,          # 5
            dep_hour,         # 6
            arr_hour,         # 7
            dep_time_str,     # 8
            arr_time_display, # 9
            miles,            # 10
            tax,              # 11
            cabin,            # 12
            seats,            # 13
            stops,            # 14
            layover_min,      # 15
            duration_min,     # 16
            transfer_programs or "",  # 17
        ]

    except (KeyError, ValueError, IndexError) as e:
        print(f"Warning: skipping route: {e}", file=sys.stderr)
        return None


def process_jsonl_files(filepaths: list[str]) -> list[list]:
    """Process multiple JSONL files and return deduplicated compact arrays.

    Each JSONL record may contain multiple routes (flight options).
    All routes are extracted and deduplicated.
    """
    seen = set()
    results = []

    for filepath in filepaths:
        records = parse_jsonl_file(filepath)
        for record in records:
            routes = record.get("routes", [])
            for route in routes:
                data = extract_route_data(record, route)
                if data is None:
                    continue
                # Deduplicate by: date, origin, dest, carrier, flight, program, cabin, miles
                key = (data[0], data[1], data[2], data[3], data[4], data[5], data[12], data[10])
                if key in seen:
                    continue
                seen.add(key)
                results.append(data)

    # Sort by miles
    results.sort(key=lambda x: x[10])
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract flight data from JSONL files into compact JSON for HTML comparison."
    )
    parser.add_argument(
        "--outbound", nargs="+", required=True,
        help="JSONL files containing outbound flight details"
    )
    parser.add_argument(
        "--return", dest="return_files", nargs="+", required=True,
        help="JSONL files containing return flight details"
    )
    parser.add_argument(
        "--output", default="flight_data.json",
        help="Output JSON file path (default: flight_data.json)"
    )

    args = parser.parse_args()

    # Process files
    print(f"Processing {len(args.outbound)} outbound file(s)...", file=sys.stderr)
    outbound = process_jsonl_files(args.outbound)
    print(f"  → {len(outbound)} outbound flights", file=sys.stderr)

    print(f"Processing {len(args.return_files)} return file(s)...", file=sys.stderr)
    returns = process_jsonl_files(args.return_files)
    print(f"  → {len(returns)} return flights", file=sys.stderr)

    # Write output
    output = {"outbound": outbound, "return": returns}
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    size_kb = output_path.stat().st_size / 1024
    print(f"Written: {output_path} ({size_kb:.1f} KB)", file=sys.stderr)
    print(f"Total: {len(outbound)} outbound + {len(returns)} return = {len(outbound) + len(returns)} flights", file=sys.stderr)


if __name__ == "__main__":
    main()
