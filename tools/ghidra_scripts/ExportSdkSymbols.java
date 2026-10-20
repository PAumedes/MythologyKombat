// ExportSdkSymbols.java - T1.6
// Exports every function whose name was assigned by the ghidra_psx_ldr "PsyQ Signatures"
// analyzer (i.e. not a Ghidra default FUN_/SUB_ name), plus the detected PsyQ version, to JSON.
// Also lists string-xref hints (functions that reference Sony-library strings).
// Usage (headless post-script): -postScript ExportSdkSymbols.java <output.json>
// Output is deterministic: sorted by address, no timestamps, no absolute paths.
//@category PSX
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.framework.options.Options;
import java.io.*;
import java.util.*;

public class ExportSdkSymbols extends GhidraScript {
    // Sony library debug-string keywords used for xref hints (case-sensitive substrings).
    private static final String[] KEYS = {
        "VSync", "ResetGraph", "DrawSync", "CdInit", "CdRead", "CdSync", "CdControl", "LoadImage",
        "StoreImage", "ClearOTag", "DrawOTag", "PutDrawEnv", "PutDispEnv", "MDEC", "DecDCT", "CD_",
        "TAP", "intr", "bios", "sys.c", "libcd", "libgpu", "Library", "SetRCnt", "EnterCriticalSection",
        "MemCard", "memcard", "PadInit", "Pad", "SPU", "Spu", "Sound", "ChangeClearPad", "StartPAD"
    };

    private static String esc(String s) {
        StringBuilder sb = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') sb.append('\\').append(c);
            else if (c < 0x20 || c > 0x7e) sb.append(String.format("\\u%04x", (int) c));
            else sb.append(c);
        }
        return sb.toString();
    }

    private static String hex(long v) { return String.format("0x%08X", v & 0xFFFFFFFFL); }

    private static boolean isDefaultName(String n) {
        return n.startsWith("FUN_") || n.startsWith("SUB_") || n.startsWith("thunk_FUN_");
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) throw new IllegalArgumentException("usage: ExportSdkSymbols.java <output.json>");
        File out = new File(args[0]);

        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"program\": \"").append(esc(currentProgram.getName())).append("\",\n");
        sb.append("  \"language\": \"").append(esc(currentProgram.getLanguageID().toString())).append("\",\n");
        sb.append("  \"ghidra_version\": \"").append(esc(ghidra.framework.Application.getApplicationVersion())).append("\",\n");

        // program info options (includes 'PsyQ Version' written by the PSX loader)
        Options info = currentProgram.getOptions(Program.PROGRAM_INFO);
        List<String> names = new ArrayList<>(info.getOptionNames());
        Collections.sort(names);
        sb.append("  \"program_info\": {");
        boolean first = true;
        String psyq = "";
        for (String n : names) {
            if (n.contains("Date") || n.contains("Path") || n.contains("Location") || n.contains("FSRL")
                || n.contains("Times")) continue; // keep output free of dates, timings and absolute paths
            String v = info.getValueAsString(n);
            if (n.contains("PsyQ")) psyq = v == null ? "" : v;
            sb.append(first ? "\n" : ",\n").append("    \"").append(esc(n)).append("\": \"").append(esc(v == null ? "" : v)).append("\"");
            first = false;
        }
        sb.append("\n  },\n");
        sb.append("  \"psyq_version_detected\": \"").append(esc(psyq)).append("\",\n");

        // functions
        FunctionManager fm = currentProgram.getFunctionManager();
        int total = 0;
        List<String> rows = new ArrayList<>();
        Map<String, Integer> bySource = new TreeMap<>();
        for (Function f : fm.getFunctions(true)) {
            total++;
            String n = f.getName();
            Symbol s = f.getSymbol();
            SourceType st = s.getSource();
            if (st == SourceType.DEFAULT || isDefaultName(n)) continue;
            bySource.merge(st.toString(), 1, Integer::sum);
            StringBuilder r = new StringBuilder();
            r.append("    {\"address\": \"").append(hex(f.getEntryPoint().getOffset())).append("\"");
            r.append(", \"name\": \"").append(esc(n)).append("\"");
            r.append(", \"size\": ").append(f.getBody().getNumAddresses());
            String blk = currentProgram.getMemory().getBlock(f.getEntryPoint()) == null ? ""
                : currentProgram.getMemory().getBlock(f.getEntryPoint()).getName();
            String kind = blk.toLowerCase().contains("gte") ? "gte_macro"
                : n.matches(".*_OBJ_[0-9A-F]+$") ? "obj_label" : "sdk";
            // 'start' and 'main' are named by the PSX loader from crt0, not by PsyQ signatures.
            String origin = (n.equals("start") || n.equals("main")) ? "loader" : "psyq_sig";
            r.append(", \"origin\": \"").append(origin).append("\"");
            r.append(", \"kind\": \"").append(kind).append("\"");
            r.append(", \"block\": \"").append(esc(blk)).append("\"");
            r.append(", \"namespace\": \"").append(esc(f.getParentNamespace().getName(true))).append("\"");
            r.append(", \"source\": \"").append(st).append("\"");
            String sig = f.getSignature().getPrototypeString();
            r.append(", \"signature\": \"").append(esc(sig)).append("\"");
            r.append("}");
            rows.add(r.toString());
        }
        sb.append("  \"function_count_total\": ").append(total).append(",\n");
        sb.append("  \"named_function_count\": ").append(rows.size()).append(",\n");
        sb.append("  \"named_by_source\": {");
        first = true;
        for (Map.Entry<String, Integer> e : bySource.entrySet()) {
            sb.append(first ? "" : ", ").append("\"").append(e.getKey()).append("\": ").append(e.getValue());
            first = false;
        }
        sb.append("},\n");
        sb.append("  \"functions\": [\n").append(String.join(",\n", rows)).append("\n  ],\n");

        // string xref hints: functions referencing Sony-library strings
        List<String> hints = new ArrayList<>();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        DataIterator di = listing.getDefinedData(true);
        while (di.hasNext()) {
            Data d = di.next();
            if (!(d.getValue() instanceof String)) continue;
            String v = (String) d.getValue();
            boolean hit = false;
            for (String k : KEYS) if (v.contains(k)) { hit = true; break; }
            if (!hit) continue;
            if (v.length() > 120) v = v.substring(0, 120);
            TreeSet<String> fns = new TreeSet<>();
            for (Reference ref : rm.getReferencesTo(d.getAddress())) {
                Function f = fm.getFunctionContaining(ref.getFromAddress());
                if (f == null) continue;
                fns.add(hex(f.getEntryPoint().getOffset()) + "|" + f.getName());
            }
            StringBuilder r = new StringBuilder();
            r.append("    {\"string_address\": \"").append(hex(d.getAddress().getOffset())).append("\"");
            r.append(", \"string\": \"").append(esc(v)).append("\", \"referencing_functions\": [");
            boolean ff = true;
            for (String x : fns) {
                String[] p = x.split("\\|", 2);
                r.append(ff ? "" : ", ").append("{\"address\": \"").append(p[0]).append("\", \"name\": \"").append(esc(p[1])).append("\"}");
                ff = false;
            }
            r.append("]}");
            hints.add(r.toString());
        }
        sb.append("  \"string_xref_hints\": [\n").append(String.join(",\n", hints)).append("\n  ]\n");
        sb.append("}\n");

        File parent = out.getAbsoluteFile().getParentFile();
        if (parent != null) parent.mkdirs();
        try (Writer w = new OutputStreamWriter(new FileOutputStream(out), "UTF-8")) { w.write(sb.toString()); }
        println("ExportSdkSymbols: wrote " + rows.size() + " named functions of " + total + ", " + hints.size() + " string hints");
    }
}
