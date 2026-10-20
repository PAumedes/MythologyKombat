// ExportAllFunctions.java - T2.2
// Dumps the entry point of EVERY function in the program (named or not), one line each:
//   0xADDRESS<TAB>name<TAB>memory-block
// Usage (headless post-script): -postScript ExportAllFunctions.java <output.txt>
// Output is deterministic: sorted by address, LF line endings, no timestamps, no absolute paths.
//@category PSX
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.MemoryBlock;
import java.io.*;
import java.util.*;

public class ExportAllFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) throw new IllegalArgumentException("usage: ExportAllFunctions.java <output.txt>");
        File out = new File(args[0]);
        TreeMap<Long, String> rows = new TreeMap<>();
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext()) {
            Function f = it.next();
            long a = f.getEntryPoint().getOffset() & 0xFFFFFFFFL;
            MemoryBlock b = currentProgram.getMemory().getBlock(f.getEntryPoint());
            rows.put(a, String.format("0x%08X\t%s\t%s", a, f.getName(), b == null ? "" : b.getName()));
        }
        File parent = out.getAbsoluteFile().getParentFile();
        if (parent != null) parent.mkdirs();
        try (Writer w = new OutputStreamWriter(new FileOutputStream(out), "UTF-8")) {
            for (String r : rows.values()) w.write(r + "\n");
        }
        println("ExportAllFunctions: wrote " + rows.size() + " functions");
    }
}
