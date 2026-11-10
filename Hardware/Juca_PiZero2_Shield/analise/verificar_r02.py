"""Inspect the frozen R02 import using only Python's standard library.

Run from any directory: python path/to/verificar_r02.py
Optional: --output path/to/revisao_estrutural.json

This is a bounded structural cross-check, not a KiCad DRC/ERC implementation.
It does not validate Gerber copper geometry, clearance, current capacity,
connector mating, or the actual Juca board. Original files are never written.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
R02 = ROOT / "R02"
STEM = "Juca_PiZero2_Shield_R02"
TOL = 0.00001  # KiCad coordinates contain micrometre-scale rounding.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def children(node, key):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == key]


def child(node, key, default=None):
    found = children(node, key)
    require(len(found) <= 1, f"Expected at most one {key}")
    return found[0] if found else default


def parse(path):
    """Parse balanced KiCad S-expressions; no input code is evaluated."""
    source = path.read_text(encoding="utf-8")
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', source)
    stack, roots = [], []
    for token in tokens:
        if token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ")":
            require(bool(stack), "Unexpected closing parenthesis")
            stack.pop()
        else:
            require(bool(stack), "Atom outside root")
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    require(not stack and len(roots) == 1, "Unbalanced S-expression")
    return roots[0]


def xy(node):
    return tuple(float(x) for x in node[1:3])


def near(a, b, tolerance=TOL):
    return len(a) == len(b) and all(abs(x - y) <= tolerance for x, y in zip(a, b))


def point_key(p):
    return tuple(round(x, 4) for x in p)


def local(p, origin):
    return tuple(x - y for x, y in zip(p, origin))


def connected(graph, start):
    reached, pending = set(), [start]
    while pending:
        item = pending.pop()
        if item not in reached:
            reached.add(item)
            pending.extend(graph[item] - reached)
    return reached


def inspect():
    manifest = json.loads((ROOT / "analise/manifesto_origem.json").read_text(encoding="utf-8"))
    archive_record = manifest["source_archive"]
    archive = ROOT / archive_record["path"]
    blob = archive.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == archive_record["sha256"], "ZIP hash mismatch")
    require(len(blob) == archive_record["size_bytes"], "ZIP size mismatch")
    records = manifest["files"]
    require(len(records) == manifest["file_count"] == 31, "Expected 31 original files")
    expected_paths = {row["path"] for row in records}
    actual_paths = {p.relative_to(ROOT).as_posix() for p in R02.rglob("*") if p.is_file()}
    require(actual_paths == expected_paths, "R02 file inventory differs from import")
    with zipfile.ZipFile(archive) as z:
        require(sum(not info.is_dir() for info in z.infolist()) == 31, "ZIP inventory mismatch")
        for row in records:
            content = (ROOT / row["path"]).read_bytes()
            require(len(content) == row["size_bytes"], f"Size changed: {row['path']}")
            require(hashlib.sha256(content).hexdigest() == row["sha256"], f"Hash changed: {row['path']}")
            archived_path = STEM + "/" + row["path"].removeprefix("R02/")
            require(content == z.read(archived_path), f"Bytes differ from ZIP: {row['path']}")

    geometry = json.loads((R02 / "geometria_e_conexoes.json").read_text(encoding="utf-8"))
    supplied = json.loads((R02 / "verificacao_conexoes.json").read_text(encoding="utf-8"))
    pcb, sch = parse(R02 / (STEM + ".kicad_pcb")), parse(R02 / (STEM + ".kicad_sch"))
    origin = geometry["kicad_origin"]
    nets = {node[1]: node[2] for node in children(pcb, "net")}
    pads, holes, footprint_paths, footprint_names = {}, {}, {}, {}
    for footprint in children(pcb, "footprint"):
        reference = next(node[2] for node in children(footprint, "fp_text") if node[1] == "reference")
        footprint_names[reference] = footprint[1]
        position = child(footprint, "at")
        require(len(position) == 3 or float(position[3]) == 0, "Only unrotated R02 footprints supported")
        base = xy(position)
        if child(footprint, "path"):
            footprint_paths[reference] = child(footprint, "path")[1]
        for pad in children(footprint, "pad"):
            absolute = tuple(a + b for a, b in zip(base, xy(child(pad, "at"))))
            if pad[2] == "np_thru_hole":
                circle = child(footprint, "fp_circle")
                holes[reference] = {
                    "position": local(absolute, origin), "drill": float(child(pad, "drill")[1]),
                    "clear_radius": math.dist(xy(child(circle, "center")), xy(child(circle, "end"))),
                }
                continue
            require(pad[2] == "thru_hole", "Unexpected pad technology")
            net = child(pad, "net", ["net", "0", ""])
            require(nets[net[1]] == net[2], "Pad net ID/name mismatch")
            pads[(reference, pad[1])] = {
                "position": local(absolute, origin), "net": net[2],
                "size": xy(child(pad, "size")), "drill": float(child(pad, "drill")[1]),
                "shape": pad[3], "layers": child(pad, "layers")[1:],
            }
    require(len(pads) == len(geometry["pads"]) == 59, "Electrical pad count mismatch")
    require(len(holes) == len(geometry["holes"]) == 8, "Mounting hole count mismatch")
    for row in geometry["pads"]:
        pad = pads[(row["ref"], row["pin"])]
        require(near(pad["position"], [row["x"], row["y"]]), "Pad position mismatch")
        require(pad["net"] == row["net"], "Pad net mismatch")
        require(near(pad["size"], [row["diam"]] * 2), "Pad size mismatch")
        require(abs(pad["drill"] - row["drill"]) <= TOL, "Pad drill mismatch")
        require(pad["shape"] == ("rect" if row["square"] else "circle"), "Pad shape mismatch")
        require(pad["layers"] == ["B.Cu", "B.Mask"], "Unexpected electrical pad layers")
    for row in geometry["holes"]:
        hole = holes[row["ref"]]
        require(near(hole["position"], [row["x"], row["y"]]), "Hole position mismatch")
        require(near([hole["drill"], hole["clear_radius"]], [row["drill"], row["clear_radius"]]), "Hole dimensions mismatch")

    outline = [n for n in children(pcb, "gr_line") if child(n, "layer")[1] == "Edge.Cuts"]
    require(len(outline) == 4, "Expected rectangular four-edge outline")
    corners = [local(xy(child(n, end)), origin) for n in outline for end in ("start", "end")]
    width, height = geometry["board_size"]
    require(Counter(point_key(p) for p in corners) == Counter({(0, 0): 2, (width, 0): 2, (width, height): 2, (0, height): 2}), "Outline mismatch")
    tracks = []
    graphs = defaultdict(lambda: defaultdict(set))
    for track in children(pcb, "segment"):
        require(child(track, "layer")[1] == "B.Cu", "Track outside B.Cu")
        net = nets[child(track, "net")[1]]
        a, b = [local(xy(child(track, end)), origin) for end in ("start", "end")]
        tracks.append({"net": net, "a": a, "b": b, "width": float(child(track, "width")[1])})
        ka, kb = point_key(a), point_key(b)
        graphs[net][ka].add(kb)
        graphs[net][kb].add(ka)
    require(len(tracks) == len(geometry["tracks"]) == 24, "Track count mismatch")
    unmatched = tracks.copy()
    for row in geometry["tracks"]:
        matches = [t for t in unmatched if t["net"] == row["net"] and abs(t["width"] - row["width"]) <= TOL and
                   ((near(t["a"], row["a"]) and near(t["b"], row["b"])) or
                    (near(t["a"], row["b"]) and near(t["b"], row["a"])))]
        require(len(matches) == 1, "Track geometry mismatch")
        unmatched.remove(matches[0])
    require(not children(pcb, "via") and not children(pcb, "zone") and not children(pcb, "arc"), "Unexpected copper item")
    for item in pcb[1:]:
        if isinstance(item, list) and item and item[0].startswith("gr_"):
            require(child(item, "layer")[1] not in ("F.Cu", "B.Cu"), "Unexpected graphic copper")
    for net, graph in graphs.items():
        reached = connected(graph, next(iter(graph)))
        require(reached == set(graph), f"Disconnected endpoint graph for {net}")
        for key, pad in pads.items():
            if pad["net"] == net:
                require(point_key(pad["position"]) in reached, f"Pad not on track endpoint: {key}")

    # Schematic is intentionally simple: every connected pin has a direct wire
    # to one global label. Unsupported rotations/mirroring fail closed.
    libraries = {s[1]: s for s in children(child(sch, "lib_symbols"), "symbol")}
    labels = {point_key(xy(child(n, "at"))): n[1] for n in children(sch, "global_label")}
    no_connect = {point_key(xy(child(n, "at"))) for n in children(sch, "no_connect")}
    wire_graph = defaultdict(set)
    for wire in children(sch, "wire"):
        ends = children(child(wire, "pts"), "xy")
        require(len(ends) == 2, "Unexpected schematic wire")
        a, b = [point_key(xy(n)) for n in ends]
        wire_graph[a].add(b)
        wire_graph[b].add(a)
    schematic_pads = {}
    for symbol in children(sch, "symbol"):
        properties = {p[1]: p[2] for p in children(symbol, "property")}
        ref = properties["Reference"]
        require(properties["Footprint"] == footprint_names[ref], "Schematic/PCB footprint name mismatch")
        at = child(symbol, "at")
        require(float(at[3]) == 0 and not child(symbol, "mirror"), "Unsupported symbol transform")
        require(footprint_paths[ref] == "/" + child(sch, "uuid")[1] + "/" + child(symbol, "uuid")[1], "PCB/schematic instance mismatch")
        lib = libraries[child(symbol, "lib_id")[1]]
        for unit in children(lib, "symbol"):
            for pin in children(unit, "pin"):
                pin_at = xy(child(pin, "at"))
                pos = point_key((float(at[1]) + pin_at[0], float(at[2]) - pin_at[1]))
                reached = connected(wire_graph, pos)
                found = {labels[p] for p in reached if p in labels}
                require(len(found) <= 1, "Multiple labels on schematic pin")
                require(bool(found) != (pos in no_connect), "Pin must be wired OR explicitly NC")
                schematic_pads[(ref, child(pin, "number")[1])] = next(iter(found)) if found else ""
    require(schematic_pads == {key: pad["net"] for key, pad in pads.items()}, "Schematic/PCB pin-net mismatch")

    jumpers = geometry["jumpers"]
    require(len(jumpers) == 1 and jumpers[0]["ref"] == "JW3", "Unexpected jumper inventory")
    require(pads[("JW3", "1")]["net"] == "GND_JUCA" and pads[("JW3", "2")]["net"] == "GND_PI", "Unexpected jumper nets")
    require(near(jumpers[0]["a"], pads[("JW3", "1")]["position"]) and near(jumpers[0]["b"], pads[("JW3", "2")]["position"]), "Jumper location mismatch")
    external_ports = defaultdict(list)
    for key, pad in pads.items():
        if pad["net"] and key[0] != "JW3":
            external_ports["GND" if pad["net"] in ("GND_JUCA", "GND_PI") else pad["net"]].append(list(key))
    normalized = lambda groups: sorted(sorted(tuple(port) for port in group) for group in groups)
    require(normalized(external_ports.values()) == normalized(supplied["external_connector_ports"]), "Supplied port map differs")

    # Compare drill files against CAD coordinates; Excellon export rounds to .001 mm.
    drill_counts = {}
    for suffix, expected in (
        ("PTH", [(p["position"], p["drill"]) for p in pads.values()]),
        ("NPTH", [(p["position"], p["drill"]) for p in holes.values()]),
    ):
        tools, tool_id, drilled = {}, None, []
        for line in (R02 / "fabricacao" / f"{STEM}-{suffix}.drl").read_text().splitlines():
            definition = re.fullmatch(r"T(\d+)C([\d.]+)", line)
            selection = re.fullmatch(r"T(\d+)", line)
            coordinate = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line)
            if definition:
                tools[definition[1]] = float(definition[2])
            elif selection:
                tool_id = selection[1]
            elif coordinate:
                require(tool_id in tools, "Unknown drill tool")
                drilled.append((local((float(coordinate[1]), -float(coordinate[2])), origin), tools[tool_id]))
        require(len(drilled) == len(expected), f"{suffix} drill count mismatch")
        for position, diameter in expected:
            matches = [row for row in drilled if near(row[0], position, 0.00051) and abs(row[1] - diameter) <= TOL]
            require(len(matches) == 1, f"{suffix} drill coordinate/diameter mismatch")
            drilled.remove(matches[0])
        drill_counts[suffix] = len(expected)

    pairs = [(math.dist(a["position"], b["position"]) - a["clear_radius"] - b["clear_radius"], ra, rb)
             for ra, a in holes.items() for rb, b in holes.items() if ra < rb]
    gap, ra, rb = min(pairs)
    pi_holes = [holes[ref]["position"] for ref in ("H5", "H6", "H7", "H8")]
    pi_span = [max(p[axis] for p in pi_holes) - min(p[axis] for p in pi_holes) for axis in (0, 1)]
    require(near(pi_span, [23, 58]), "Pi mounting-hole span mismatch")
    track_lengths = {net: round(sum(math.dist(t["a"], t["b"]) for t in tracks if t["net"] == net), 6) for net in sorted(graphs)}
    job = json.loads((R02 / "fabricacao" / f"{STEM}-job.gbrjob").read_text())
    return {
        "result": "PASS_STRUCTURAL_CHECKS_ONLY",
        "verification": "Independent Python stdlib parsing and byte comparison; not native KiCad DRC/ERC.",
        "archive_sha256": archive_record["sha256"],
        "original_files_unchanged": len(records),
        "pcb_dimensions_mm": geometry["board_size"],
        "pcb_thickness_mm": float(child(child(pcb, "general"), "thickness")[1]),
        "electrical_pads": len(pads), "mounting_holes": len(holes), "tracks": len(tracks),
        "electrical_copper_layers": ["B.Cu"], "vias": 0, "zones": 0,
        "schematic_pcb_manifest_pad_parity": True,
        "track_endpoints_connected_within_each_net": True,
        "track_centerline_lengths_mm": track_lengths,
        "drill_files_match_pcb": drill_counts,
        "external_ports_with_JW3_installed": dict(sorted(external_ports.items())),
        "unrouted_external_pins": [f"{ref}-{pin}" for (ref, pin), p in pads.items() if not p["net"]],
        "minimum_mounting_clearance_circle_gap_mm": round(gap, 6),
        "minimum_mounting_clearance_circle_pair": [ra, rb],
        "pi_mounting_hole_span_xy_mm": pi_span,
        "gerber_job_layer_count": job["GeneralSpecs"]["LayerNumber"],
        "gerber_job_size_including_outline_stroke_mm": job["GeneralSpecs"]["Size"],
        "limitations": [
            "No native KiCad DRC/ERC run; supplied reports remain external evidence.",
            "Endpoint connectivity is not a geometric copper/short-circuit/clearance test.",
            "Gerber copper and silkscreen were not geometrically reconstructed.",
            "Ground connection between GND_JUCA and GND_PI assumes physical JW3 installation.",
            "Mounting-circle gap is 2D drawing geometry, not actual spacer/component clearance.",
            "No verification of Juca source schematic, current capacity, logic levels, firmware, or assembled hardware.",
            "Job declares two CAD layers and PTH drill plating; manufacturing process must be specified separately.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON output outside the original R02 tree")
    args = parser.parse_args()
    if args.output:
        target = args.output.resolve()
        require(target.suffix.lower() == ".json", "Output must be a JSON file")
        require(not target.is_relative_to(R02.resolve()), "Refusing to write inside frozen R02")
        require(target != Path(__file__).resolve() and target != (ROOT / "analise/manifesto_origem.json"), "Refusing to overwrite source/provenance")
        require(target.is_relative_to((ROOT / "analise").resolve()), "Output must stay in analise/")
    result = inspect()
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        target.write_text(output, encoding="utf-8")
    print(output, end="")
