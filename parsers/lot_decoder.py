#! python3
#
# Created by Joe Moran on 4/1/26.
# Copyright © 2026 Joe Moran. All rights reserved.
#

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
import argparse
import json

PRODUCT_CODE = {
    0x04: "D1", # 'D'ash (gen 4) U100
    0x18: "D2", # 'D'ash (gen 4) U200
    0x36: "D5", # 'D'ash (gen 4) U500

    0x07: "H1", # 'H'orizon (Omnipod 5) U100
    0x1B: "H2", # 'H'orizon (Omnipod 5) U200
    0x39: "H5", # 'H'orizon (Omnipod 5) U300

    0x02: "E1", # 'E' pod (Omnipod 6?) U100
    0x16: "E2", # 'E' pod (Omnipod 6?) U200
    0x34: "E5", # 'E' pod (Omnipod 6?) U500

    0x05: "P1", # 'P're-production? U100
    0x19: "P2", # 'P're-production? U200
    0x37: "P5", # 'P're-production? U500

    0x03: "A0",
    0x09: "R1",
}

MFG_LOC = {
    0: "C", # China
    1: "U", # USA
    2: "K", # Kunshan (China)
    6: "M", # Malaysia
}


@dataclass
class LotDecode:
    lot: int
    lot_hex: str
    prefix: str
    product_num: int
    product_code: str
    location_num: int
    location_code: str
    date_MM: str
    date_DD: str
    date_YY: int
    line: int
    batch: str
    printable_version: str


def _mask(n: int) -> int:
    return (1 << n) - 1


def decode_lot_numeric(dec_or_hex_str: str) -> LotDecode:
    if dec_or_hex_str.startswith(("0x","0X")):
        lotVal = int(dec_or_hex_str.replace("_", "").strip(), 16)
    else:
        lotVal = int(dec_or_hex_str)
    return decode_lot(lotVal)

def decode_lot(lotVal: int) -> LotDecode:
    lot = lotVal & 0xFFFFFFFF
    prefix = "P" if (lot & 0x80000000) == 0 else "E"

    product_num = (lot >> 25) & _mask(6)
    product_code = PRODUCT_CODE.get(product_num, "??")

    location_num = (lot >> 22) & _mask(3)
    location_code = MFG_LOC.get(location_num, "?")

    dayNumber = (lot >> 7) & _mask(15)
    date_YY = (dayNumber >> 9)
    dayOfYear = dayNumber - (date_YY << 9)

    if dayOfYear > 0:
        d = date(2000 + 1, 1, 1) + timedelta(days=dayOfYear - 1)
        date_MM = d.strftime("%m")
        date_DD = d.strftime("%d")
    else:
        date_MM = "00"
        date_DD = "00"

    line = (lot >> 4) & _mask(3)
    batch = f"{lot & _mask(4):X}"

    printable_version = (
        f"{prefix}{product_code}{location_code}"
        f"{date_MM}{date_DD}{date_YY}{line}{batch}"
    )

    return LotDecode(
        lot=lot,
        lot_hex=f"0x{lot:08X}",
        prefix=prefix,
        product_num=product_num,
        product_code=product_code,
        location_num=location_num,
        location_code=location_code,
        date_MM=date_MM,
        date_DD=date_DD,
        date_YY=date_YY,
        line=line,
        batch=batch,
        printable_version=printable_version,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="numeric DASH or Omnipod 5 lot # to printed alphanumeric lot string")
    parser.add_argument("numeric_lot", help="numeric decimal or hex value, e.g. 135556529 (decimal) or 0x8146DB1 (hex)")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    decoded = decode_lot_numeric(args.numeric_lot)

    if args.json:
        print(json.dumps(asdict(decoded), indent=2))
    else:
        data = asdict(decoded)
        if args.verbose:
            for k, v in data.items():
                print(f"{k}: {v}")
        else:
            print(f"{args.numeric_lot} => {data['printable_version']}")


if __name__ == "__main__":
    main()

