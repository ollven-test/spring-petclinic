"""Render Surefire XML reports as a Markdown table for the GitHub job summary."""

import glob
import sys
import xml.etree.ElementTree as ET

reports_dir = sys.argv[1] if len(sys.argv) > 1 else "target/surefire-reports"
files = sorted(glob.glob(f"{reports_dir}/TEST-*.xml"))

if not files:
    print("## Test results\n\nNo test reports found.")
    sys.exit(0)

rows = []
failed = []
totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}

for path in files:
    suite = ET.parse(path).getroot()
    name = suite.get("name", "").rsplit(".", 1)[-1]
    tests = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    time = float(suite.get("time", 0) or 0)

    for key, value in zip(totals, (tests, failures, errors, skipped, time)):
        totals[key] += value

    status = "❌" if failures or errors else "✅"
    passed = tests - failures - errors - skipped
    rows.append(f"| {status} | `{name}` | {tests} | {passed} | {failures + errors} | {skipped} | {time:.1f}s |")

    for case in suite.iter("testcase"):
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        if problem is not None:
            message = (problem.get("message") or problem.get("type") or "").splitlines()
            failed.append(f"- `{name}.{case.get('name')}`: {message[0] if message else ''}")

bad = totals["failures"] + totals["errors"]
passed = totals["tests"] - bad - totals["skipped"]
headline = "❌ Some tests failed" if bad else "✅ All tests passed"

print(f"## Test results: {headline}\n")
print(
    f"**{totals['tests']}** tests: **{passed}** passed, **{bad}** failed, "
    f"**{totals['skipped']}** skipped in {totals['time']:.1f}s\n"
)

if failed:
    print("### Failed tests\n")
    print("\n".join(failed))
    print()

print("<details><summary>Results by test class</summary>\n")
print("| | Class | Tests | Passed | Failed | Skipped | Time |")
print("|---|---|---:|---:|---:|---:|---:|")
print("\n".join(rows))
print("\n</details>")
