#!/usr/bin/env python3
"""Reuse the baseline evidence checks with the new batch's frozen evaluator."""

import importlib.util
import json
from pathlib import Path
import sys


def main():
    batch = Path(__file__).resolve().parent
    root = batch.parents[2]
    source = root / 'results/vehicle_tracking_validation/two_scenario_frozen_repeat_20261011_01/independent_check.py'
    spec = importlib.util.spec_from_file_location('baseline_evidence_check', source)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    checker.BATCH, checker.ROOT = batch, root
    sys.path.insert(0, str(batch / 'frozen_files/scripts'))
    code = checker.main()
    path = batch / 'INDEPENDENT_CHECK.json'
    report = json.loads(path.read_text())
    report.update(checker_source=str(source.relative_to(root)),
                  invocation_script_sha256=checker.sha(Path(__file__)),
                  frozen_evaluator_source='frozen_files/scripts/vehicle_crossing_validation.py')
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
