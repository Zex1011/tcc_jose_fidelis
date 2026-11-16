"""Read-only structural check of the imported R04; not KiCad DRC/ERC.

Uses the bounded S-expression reader from verificar_r02.py and Python stdlib.
Run from any directory. Optional --output writes a report only inside analise/.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile

from verificar_r02 import child, children, connected, near, parse, point_key, require, xy


ROOT = Path(__file__).resolve().parents[1]
R04 = ROOT / "R04"
STEM = "Juca_PiZero2_Shield_R04"


def inspect():
    manifest = json.loads((ROOT / "analise/manifesto_origem_R04.json").read_text(encoding="utf-8"))
    archive_info = manifest["source_archive"]
    archive = ROOT / archive_info["path"]
    blob = archive.read_bytes()
    require(len(blob) == archive_info["size_bytes"], "Archive size differs")
    require(hashlib.sha256(blob).hexdigest() == archive_info["sha256"], "Archive hash differs")
    records = manifest["files"]
    actual_files = {p.relative_to(ROOT).as_posix() for p in R04.rglob("*") if p.is_file()}
    require(actual_files == {r["path"] for r in records}, "Original inventory differs")
    require(len(records) == manifest["file_count"] == 37, "Expected 37 original files")
    with zipfile.ZipFile(archive) as z:
        require(sum(not i.is_dir() for i in z.infolist()) == 37, "ZIP inventory differs")
        for row in records:
            data = (ROOT / row["path"]).read_bytes()
            require(len(data) == row["size_bytes"], "Original file size differs")
            require(hashlib.sha256(data).hexdigest() == row["sha256"], "Original file hash differs")
            require(data == z.read(STEM + "/" + row["path"].removeprefix("R04/")), "ZIP bytes differ")

    geometry = json.loads((R04 / "geometria_e_conexoes.json").read_text(encoding="utf-8"))
    mapping = json.loads((R04 / "mapeamento_pinos.json").read_text(encoding="utf-8"))
    pro = json.loads((R04 / (STEM + ".kicad_pro")).read_text(encoding="utf-8"))
    pcb = parse(R04 / (STEM + ".kicad_pcb"))
    sch = parse(R04 / (STEM + ".kicad_sch"))
    origin = geometry["kicad_origin"]
    local = lambda p: tuple(a - b for a, b in zip(p, origin))
    nets = {n[1]: n[2] for n in children(pcb, "net")}
    require(len([n for n in nets.values() if n]) == 28, "Expected 28 named nets")
    pads, holes, footprints, instance_paths = {}, {}, {}, {}
    for footprint in children(pcb, "footprint"):
        ref = next(n[2] for n in children(footprint, "fp_text") if n[1] == "reference")
        footprints[ref] = footprint[1]
        position = child(footprint, "at")
        require(len(position) == 3 or float(position[3]) == 0, "Unsupported footprint rotation")
        if child(footprint, "path"):
            instance_paths[ref] = child(footprint, "path")[1]
        for pad in children(footprint, "pad"):
            absolute = tuple(a + b for a, b in zip(xy(position), xy(child(pad, "at"))))
            drill = child(pad, "drill")
            data = {"position": local(absolute), "size": xy(child(pad, "size")),
                    "drill": float(drill[1]) if drill else 0, "kind": pad[2],
                    "net": child(pad, "net", ["net", "0", ""])[2],
                    "layers": child(pad, "layers")[1:]}
            if pad[2] == "np_thru_hole":
                holes[ref] = data
            else:
                pads[(ref, pad[1])] = data
    require(len(pads) == len(geometry["pads"]) == 83, "Expected 83 electrical pads")
    require(len(holes) == len(geometry["holes"]) == 8, "Expected 8 mounting holes")
    for row in geometry["pads"]:
        actual = pads[(row["ref"], row["pin"])]
        require(near(actual["position"], [row["x"], row["y"]]), "Pad position differs")
        require(actual["net"] == row["net"], "Pad net differs")
        require(near(actual["size"], row.get("size", [row.get("diam", 0)] * 2)), "Pad size differs")
        require(near([actual["drill"]], [row["drill"]]), "Pad drill differs")
        require(actual["kind"] == ("smd" if row["kind"] == "smd" else "thru_hole"), "Pad technology differs")
        expected_layers = ["F.Cu", "F.Paste", "F.Mask"] if row["kind"] == "smd" else ["F&B.Cu", "*.Mask"]
        require(actual["layers"] == expected_layers, "Pad layers differ")
    previous = json.loads((ROOT / "R02/geometria_e_conexoes.json").read_text(encoding="utf-8"))
    require(geometry["board_size"] == previous["board_size"] == [48, 88], "Board dimensions differ")
    require(geometry["holes"] == previous["holes"], "Mounting geometry differs from R02")
    for row in geometry["holes"]:
        actual = holes[row["ref"]]
        require(near(actual["position"], [row["x"], row["y"]]), "Mounting hole position differs")
        require(near([actual["drill"]], [row["drill"]]), "Mounting drill differs")
    for row in previous["pads"]:
        if row["ref"] in ("J5", "J11", "JPI1"):
            require(near(pads[(row["ref"], row["pin"])]["position"], [row["x"], row["y"]]), "Connector position differs from R02")
    outline = [n for n in children(pcb, "gr_line") if child(n, "layer")[1] == "Edge.Cuts"]
    corners = [point_key(local(xy(child(n, end)))) for n in outline for end in ("start", "end")]
    require(Counter(corners) == Counter({(0, 0): 2, (48, 0): 2, (48, 88): 2, (0, 88): 2}), "Outline differs")

    # Compare serialized routing; this does not calculate copper clearance.
    signature = lambda net, a, b, width, layer: (net, tuple(sorted((point_key(a), point_key(b)))), round(float(width), 6), layer)
    tracks = children(pcb, "segment")
    expected_tracks = Counter(signature(t["net"], t["a"], t["b"], t["width"], t["layer"]) for t in geometry["tracks"])
    actual_tracks = Counter(signature(nets[child(t, "net")[1]], local(xy(child(t, "start"))), local(xy(child(t, "end"))), child(t, "width")[1], child(t, "layer")[1]) for t in tracks)
    require(actual_tracks == expected_tracks and len(tracks) == 452, "Routing differs")
    vias = children(pcb, "via")
    actual_vias = Counter((nets[child(v, "net")[1]], point_key(local(xy(child(v, "at")))), float(child(v, "size")[1]), float(child(v, "drill")[1])) for v in vias)
    expected_vias = Counter((v["net"], point_key((v["x"], v["y"])), v["diam"], v["drill"]) for v in geometry["vias"])
    require(actual_vias == expected_vias and len(vias) == 23, "Vias differ")
    require(all(child(v, "layers")[1:] == ["F.Cu", "B.Cu"] for v in vias), "Unexpected via layers")
    require(not children(pcb, "zone") and not children(pcb, "arc"), "Unexpected routing technology")
    widths = sorted({float(child(t, "width")[1]) for t in tracks})
    require(widths == [0.508, 0.762, 1.8], "Unexpected trace widths")
    rules = pro["board"]["design_settings"]["rules"]
    for key, expected in {"min_clearance": 0.508, "min_track_width": 0.508,
                          "min_copper_edge_clearance": 0.508, "min_hole_clearance": 0.508,
                          "min_hole_to_hole": 0.508, "min_through_hole_diameter": 0.6,
                          "min_via_diameter": 1.8}.items():
        require(rules[key] == expected, f"Project rule differs: {key}")

    libraries = {n[1]: n for n in children(child(sch, "lib_symbols"), "symbol")}
    labels = {point_key(xy(child(n, "at"))): n[1] for n in children(sch, "global_label")}
    no_connect = {point_key(xy(child(n, "at"))) for n in children(sch, "no_connect")}
    graph = defaultdict(set)
    for wire in children(sch, "wire"):
        ends = children(child(wire, "pts"), "xy")
        require(len(ends) == 2, "Unexpected wire")
        a, b = [point_key(xy(n)) for n in ends]
        graph[a].add(b)
        graph[b].add(a)
    schematic_pads, dnp = {}, set()
    for symbol in children(sch, "symbol"):
        props = {n[1]: n[2] for n in children(symbol, "property")}
        ref = props["Reference"]
        at = child(symbol, "at")
        require(float(at[3]) == 0 and not child(symbol, "mirror"), "Unsupported schematic transform")
        require(props["Footprint"] == footprints[ref], "Footprint reference differs")
        require(instance_paths[ref] == "/" + child(sch, "uuid")[1] + "/" + child(symbol, "uuid")[1], "Schematic instance differs")
        if child(symbol, "dnp", ["dnp", "no"])[1] == "yes":
            dnp.add(ref)
        for unit in children(libraries[child(symbol, "lib_id")[1]], "symbol"):
            for pin in children(unit, "pin"):
                px, py = xy(child(pin, "at"))
                pos = point_key((float(at[1]) + px, float(at[2]) - py))
                found = {labels[p] for p in connected(graph, pos) if p in labels}
                require(len(found) <= 1 and bool(found) != (pos in no_connect), "Ambiguous pin labeling")
                schematic_pads[(ref, child(pin, "number")[1])] = next(iter(found)) if found else ""
    require(schematic_pads == {key: p["net"] for key, p in pads.items()}, "Schematic/PCB pin mapping differs")
    require(dnp == {f"JP{i}" for i in range(1, 14)}, "Unexpected DNP selectors")
    require("JW3" not in footprints, "Old wire jumper is still present")
    require(len(mapping) == 13, "Expected 13 mapping rows")
    for row in mapping:
        require(row["default"] == "DNP_OPEN", "Selector is not initially open")
        for key, net in [(("J5", str(row["j5_pin"])), row["juca_net"]),
                         ((row["jumper"], "1"), row["juca_net"]),
                         ((row["jumper"], "2"), row["pi_net"]),
                         (("JPI1", str(row["pi_physical"])), row["pi_net"])]:
            require(pads[key]["net"] == net, "Selector mapping differs")
        require(row["juca_net"] != row["pi_net"], "Selector sides are not separate nets")
    require(pads[("J11", "2")]["net"] == pads[("JPI1", "2")]["net"] == pads[("JPI1", "4")]["net"] == "+5V", "Power mapping differs")
    require(pads[("J11", "4")]["net"] == pads[("JPI1", "9")]["net"] == "GND", "Ground mapping differs")
    require(all(pads[key]["net"] == "" for key in [("J11", "1"), ("J11", "3"), ("JPI1", "6"), ("JPI1", "27"), ("JPI1", "28")]), "Reserved pin connected")
    with (R04 / "pinagem_R04.csv").open(encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))
    require(len(csv_rows) == 13, "CSV row count differs")
    for row, exported in zip(mapping, csv_rows):
        for field, column in {"jumper": "Jumper", "j5_pin": "J5 pino", "esp_gpio": "GPIO ESP32-S3", "pi_physical": "Raspberry pino fisico", "pi_bcm": "Raspberry BCM"}.items():
            require(str(row[field]) == exported[column], "CSV mapping differs")

    expected_drills = [(p["position"], p["drill"]) for p in [*pads.values(), *holes.values()] if p["drill"]]
    expected_drills += [((v["x"], v["y"]), v["drill"]) for v in geometry["vias"]]
    tools, selected, drills = {}, None, []
    for line in (R04 / "fabricacao" / (STEM + ".drl")).read_text().splitlines():
        definition = re.fullmatch(r"T(\d+)C([\d.]+)", line)
        selection = re.fullmatch(r"T(\d+)", line)
        coord = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line)
        if definition:
            tools[definition[1]] = float(definition[2])
        elif selection:
            selected = selection[1]
        elif coord:
            drills.append((local((float(coord[1]), -float(coord[2]))), tools[selected]))
    require(len(drills) == len(expected_drills) == 88, "Expected 88 drill hits")
    for point, diameter in expected_drills:
        matches = [r for r in drills if near(r[0], point, 0.00051) and r[1] == diameter]
        require(len(matches) == 1, "Drill coordinate/diameter differs")
        drills.remove(matches[0])
    job = json.loads((R04 / "fabricacao" / (STEM + "-job.gbrjob")).read_text())
    require(job["GeneralSpecs"]["LayerNumber"] == 2, "Expected two-layer export")
    for suffix in ("F_Cu.gtl", "B_Cu.gbl", "Edge_Cuts.gm1"):
        require((R04 / "fabricacao" / (STEM + "-" + suffix)).is_file(), "Missing fabrication layer")
    return {
        "result": "PASS_STRUCTURAL_CHECKS_ONLY", "revision": "R04",
        "original_files_unchanged": len(records), "archive_sha256": archive_info["sha256"],
        "pcb_dimensions_mm": geometry["board_size"], "electrical_pads": len(pads),
        "tracks": len(tracks), "vias": len(vias), "mounting_holes": len(holes),
        "named_nets": 28, "signal_selectors_initially_dnp": len(dnp),
        "schematic_pcb_geometry_mapping_csv_parity": True,
        "routing_and_vias_match_geometry_manifest": True,
        "connector_and_hole_positions_match_R02": True,
        "drill_hits_match_pcb": 88, "trace_widths_mm": widths,
        "project_rules_match_declared_R04_values": True, "gerber_job_layer_count": 2,
        "limitations": [
            "No native KiCad DRC/ERC run; original reports are supplied evidence.",
            "Named nets and serialized routes are not geometric connectivity or clearance verification.",
            "Gerber copper geometry, CAM process, and CNC rules source PDF were not independently verified.",
            "ESP GPIO identities follow supplied mapping; complete Juca source and physical module variant are not included.",
            "DNP flags describe design intent; actual selector assembly and via continuity require inspection.",
            "No physical power, connector, firmware, UART, or motor test was performed.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        target = args.output.resolve()
        require(target == Path(__file__).with_name("revisao_estrutural_R04.json"), "Output must be analise/revisao_estrutural_R04.json")
    result = inspect()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target.write_text(text, encoding="utf-8")
    print(text, end="")
