// Writes a function inventory and one decompilation for the imported program.
// The program is not executed.
//@category Noctivis

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.framework.Application;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DumpEvidence extends GhidraScript {
	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			throw new IllegalArgumentException("expected an output path and a sha256");
		}
		List<Function> functions = new ArrayList<>();
		Function chosen = null;
		FunctionIterator iterator = currentProgram.getFunctionManager().getFunctions(true);
		while (iterator.hasNext() && !monitor.isCancelled()) {
			Function function = iterator.next();
			if (function.isExternal()) {
				continue;
			}
			functions.add(function);
			if (chosen == null || (function.getName().equals("main") && !chosen.getName().equals("main"))) {
				chosen = function;
			}
		}
		String chosenName = "";
		String chosenEntry = "";
		String decompiled = "";
		if (chosen != null) {
			chosenName = chosen.getName();
			chosenEntry = chosen.getEntryPoint().toString();
			DecompInterface decompiler = new DecompInterface();
			if (!decompiler.openProgram(currentProgram)) {
				throw new IllegalStateException("decompiler could not open the program: " + decompiler.getLastMessage());
			}
			try {
				DecompileResults result = decompiler.decompileFunction(chosen, 30, monitor);
				if (result != null && result.decompileCompleted() && result.getDecompiledFunction() != null) {
					decompiled = result.getDecompiledFunction().getC();
				}
			}
			finally {
				decompiler.dispose();
			}
		}
		String json = toJson(args[1], Application.getApplicationVersion(), functions, chosenName, chosenEntry, decompiled);
		Files.writeString(Path.of(args[0]), json, StandardCharsets.UTF_8);
	}

	private static String toJson(
		String sha256,
		String version,
		List<Function> functions,
		String chosenName,
		String chosenEntry,
		String decompiled
	) {
		StringBuilder out = new StringBuilder();
		out.append("{\"sha256\":\"").append(escape(sha256));
		out.append("\",\"tool\":\"ghidra\",\"tool_version\":\"").append(escape(version));
		out.append("\",\"functions\":[");
		for (int index = 0; index < functions.size(); index++) {
			Function function = functions.get(index);
			if (index > 0) {
				out.append(',');
			}
			out.append("{\"name\":\"").append(escape(function.getName()));
			out.append("\",\"entry\":\"").append(escape(function.getEntryPoint().toString())).append("\"}");
		}
		out.append("],\"decompilation\":{\"name\":\"").append(escape(chosenName));
		out.append("\",\"entry\":\"").append(escape(chosenEntry));
		out.append("\",\"text\":\"").append(escape(decompiled)).append("\"}}");
		return out.toString();
	}

	private static String escape(String value) {
		if (value == null) {
			return "";
		}
		StringBuilder out = new StringBuilder();
		for (int index = 0; index < value.length(); index++) {
			char character = value.charAt(index);
			switch (character) {
				case '\\':
					out.append("\\\\");
					break;
				case '"':
					out.append("\\\"");
					break;
				case '\n':
					out.append("\\n");
					break;
				case '\r':
					out.append("\\r");
					break;
				case '\t':
					out.append("\\t");
					break;
				default:
					if (character < 0x20) {
						out.append(String.format("\\u%04x", (int) character));
					}
					else {
						out.append(character);
					}
					break;
			}
		}
		return out.toString();
	}
}
