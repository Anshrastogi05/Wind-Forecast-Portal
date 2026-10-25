"""Command line: ``windportal ingest`` (real Elexon data) / ``windportal demo-data`` (synthetic)."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import get_settings


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level="INFO", format="%(message)s")
    p = argparse.ArgumentParser(prog="windportal")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("ingest", "download real wind actuals + forecasts from Elexon"),
                           ("demo-data", "generate SYNTHETIC demo data (offline)")):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("--out", type=Path, default=get_settings().data_dir)
    args = p.parse_args(argv)

    if args.cmd == "ingest":
        from .ingest.elexon import run
        run(args.out)
    else:
        from .ingest.synthetic import generate
        print(generate(args.out))


if __name__ == "__main__":
    main()
