#!/usr/bin/env python3
"""Export PsyQ SDK function names found by Ghidra's PsyQ signature analyzer (T1.6).

Runs Ghidra headless on the boot EXE with the ghidra_psx_ldr extension (its
"PsyQ Signatures" analyzer names the SDK functions during auto-analysis), then a
post-script (tools/ghidra_scripts/ExportSdkSymbols.java) writes the named
functions, the detected PsyQ version and string-xref hints to JSON.

Input  : work/disc/SLUS_004.76 (boot EXE, read only)
Output : work/symbols_sdk.json  (deterministic: sorted by address, no dates/paths)
Scratch: work/ghidra-sdk/ (Ghidra project; rebuilt from scratch unless --reuse)

Usage:
  python -I tools/ghidra_sdk_names.py [--root PATH] [--ghidra DIR] [--jdk DIR]
                                      [--exe PATH] [--out PATH] [--reuse]
                                      [--all-funcs]
--reuse re-opens the existing project with -process -noanalysis (fast, ~20 s)
instead of a full import and analysis (~3 min).
--all-funcs (T2.2) instead dumps every function entry point (named or not) to
work/ghidra_funcs_all.txt via ExportAllFunctions.java; requires the existing
project (implies --reuse) and does not touch symbols_sdk.json.
Stdlib only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

RETRO_TOOLS = os.environ.get("RETRO_TOOLS_DIR") or os.path.join(os.path.expanduser("~"), "retro-tools")
DEFAULT_GHIDRA = os.path.join(RETRO_TOOLS, "ghidra", "ghidra_12.1.4_PUBLIC")
DEFAULT_JDK = os.path.join(RETRO_TOOLS, "jdk", "jdk-21.0.12.1+1")
PROJ_NAME = "SDK"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--ghidra", default=os.environ.get("GHIDRA_HOME", DEFAULT_GHIDRA))
    ap.add_argument("--jdk", default=os.environ.get("JAVA_HOME", DEFAULT_JDK))
    ap.add_argument("--exe", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--all-funcs", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    exe = os.path.abspath(a.exe or os.path.join(root, "work", "disc", "SLUS_004.76"))
    out = os.path.abspath(a.out or os.path.join(root, "work", "symbols_sdk.json"))
    projdir = os.path.join(root, "work", "ghidra-sdk")
    scripts = os.path.join(root, "tools", "ghidra_scripts")
    headless = os.path.join(a.ghidra, "support", "analyzeHeadless.bat")

    for label, p in (("EXE", exe), ("analyzeHeadless", headless), ("JDK", os.path.join(a.jdk, "bin", "java.exe"))):
        if not os.path.exists(p):
            sys.exit("missing %s: %s" % (label, p))

    env = dict(os.environ)
    env["JAVA_HOME"] = a.jdk
    env["PATH"] = os.path.join(a.jdk, "bin") + os.pathsep + env.get("PATH", "")

    if a.all_funcs:
        if not os.path.exists(os.path.join(projdir, PROJ_NAME + ".gpr")):
            sys.exit("--all-funcs needs the existing project; run without it first")
        outp = os.path.abspath(a.out or os.path.join(root, "work", "ghidra_funcs_all.txt"))
        cmd = [headless, projdir, PROJ_NAME, "-process", "SLUS_004.76", "-noanalysis",
               "-scriptPath", scripts, "-postScript", "ExportAllFunctions.java", outp]
        if os.path.exists(outp):
            os.remove(outp)
        with open(os.path.join(root, "work", "ghidra_all_funcs.log"), "wb") as log:
            rc = subprocess.call(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
        if rc != 0 or not os.path.exists(outp):
            sys.exit("analyzeHeadless failed (rc=%s); see work/ghidra_all_funcs.log" % rc)
        print("wrote", os.path.relpath(outp, root))
        return
    if a.reuse and os.path.exists(os.path.join(projdir, PROJ_NAME + ".gpr")):
        step = ["-process", "SLUS_004.76", "-noanalysis"]
    else:
        if os.path.isdir(projdir):
            shutil.rmtree(projdir)
        os.makedirs(projdir)
        step = ["-import", exe, "-overwrite"]
    cmd = [headless, projdir, PROJ_NAME] + step + [
        "-scriptPath", scripts, "-postScript", "ExportSdkSymbols.java", out]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    log_path = os.path.join(root, "work", "ghidra_sdk_names.log")
    print("running:", " ".join(cmd[:1] + ["<projdir>", PROJ_NAME] + step[:1]), flush=True)
    with open(log_path, "wb") as log:
        rc = subprocess.call(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    if rc != 0 or not os.path.exists(out):
        sys.exit("analyzeHeadless failed (rc=%s); see %s" % (rc, log_path))

    with open(out, encoding="utf-8") as f:
        d = json.load(f)
    print("PsyQ version detected : %r" % d["psyq_version_detected"])
    print("functions total       : %d" % d["function_count_total"])
    print("named (non-default)   : %d  by source %s" % (d["named_function_count"], d["named_by_source"]))
    print("string xref hints     : %d" % len(d["string_xref_hints"]))
    print("wrote", os.path.relpath(out, root))


if __name__ == "__main__":
    main()
