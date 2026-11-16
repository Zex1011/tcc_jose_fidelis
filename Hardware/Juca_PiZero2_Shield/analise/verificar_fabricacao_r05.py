"""Compare R05 drill exports with CAD and check the Gerber export inventory.

Python standard library only. Supports the combined, absolute, metric, decimal
Excellon file exported by KiCad: circular drills, explicit X/Y hits, no slots.
Does not verify Gerber copper geometry or replace DRC/ERC or CAM inspection.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import verificar_r05 as cad


# KiCad's decimal metric Excellon export rounds positions to 0.001 mm.
POSITION_TOLERANCE_MM = 0.000501
DIAMETER_TOLERANCE_MM = 1e-9
STEM = 'Juca_PiZero2_Shield_R05'
GERBERS = {
    '-F_Cu.gtl': ('Copper,L1,Top', 'Positive'),
    '-B_Cu.gbl': ('Copper,L2,Bot', 'Positive'),
    '-F_Mask.gts': ('SolderMask,Top', 'Negative'),
    '-B_Mask.gbs': ('SolderMask,Bot', 'Negative'),
    '-F_Silkscreen.gto': ('Legend,Top', 'Positive'),
    '-B_Silkscreen.gbo': ('Legend,Bot', 'Positive'),
    '-Edge_Cuts.gm1': ('Profile', 'Positive'),
}


def artifact(path, root):
    record = {'path': path.relative_to(root).as_posix(), 'exists': path.is_file()}
    if record['exists']:
        content = path.read_bytes()
        record.update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    return record


def read_excellon(path):
    """Fail closed on syntax outside the documented KiCad export profile."""
    text = path.read_text(encoding='utf-8-sig')
    if not re.search(r';\s*FORMAT=\{[^}]*absolute\s*/\s*metric\s*/\s*decimal\}', text, re.I):
        raise ValueError('Expected an absolute / metric / decimal Excellon format declaration')
    tools, hits = {}, []
    header, metric, absolute, ended, started = True, False, False, False, False
    selected = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        if ended:
            raise ValueError(f'Commands after M30 at line {number}')
        if not started:
            if line != 'M48':
                raise ValueError('Expected M48 as first Excellon command')
            started = True
            continue
        if header:
            if line == 'METRIC':
                metric = True
            elif line == 'FMAT,2':
                pass
            elif line == '%':
                header = False
            else:
                match = re.fullmatch(r'T(\d+)C(\d+(?:\.\d+)?)', line)
                if not match or int(match[1]) in tools:
                    raise ValueError(f'Unsupported or duplicate header command at line {number}: {line}')
                tools[int(match[1])] = float(match[2])
            continue
        if line == 'G90':
            absolute = True
        elif line == 'G05':
            pass
        elif line == 'M30':
            ended = True
        elif re.fullmatch(r'T\d+', line):
            selected = int(line[1:])
            if selected not in tools:
                raise ValueError(f'Undefined drill tool at line {number}: {line}')
        else:
            match = re.fullmatch(r'X([+-]?\d+(?:\.\d*)?)Y([+-]?\d+(?:\.\d*)?)', line)
            if not match or selected is None or not metric or not absolute:
                raise ValueError(f'Unsupported or unconfigured drill command at line {number}: {line}')
            hits.append({'tool': selected, 'diameter': tools[selected],
                         'position': [float(match[1]), float(match[2])], 'line': number})
    if header or not ended or not metric or not absolute:
        raise ValueError('Incomplete Excellon header, coordinate mode or M30 terminator')
    return tools, hits


def inspect():
    root = cad.repository()
    revision = root / 'Hardware/Juca_PiZero2_Shield/R05'
    fabrication = revision / 'fabricacao'
    board_path = revision / (STEM + '.kicad_pcb')
    drill_path = fabrication / (STEM + '.drl')
    job_path = fabrication / (STEM + '-job.gbrjob')
    checks, failures = [], []

    def check(condition, message):
        (checks if condition else failures).append(message)

    inputs = [artifact(path, root) for path in (
        board_path, board_path.with_suffix('.kicad_pro'), Path(__file__).resolve(), Path(cad.__file__).resolve())]
    check(all(row['exists'] for row in inputs), 'CAD, project and verifier inputs exist')
    expected_exports = [drill_path, job_path, *(fabrication / (STEM+suffix) for suffix in GERBERS)]
    inventory = [artifact(path, root) for path in expected_exports]
    for row in inventory:
        check(row['exists'] and row.get('bytes', 0) > 0, f'Nonempty export exists: {row["path"]}')

    expected, hits, tools = [], [], {}
    counts = {}
    missing, unexpected, ambiguous = [], [], []
    try:
        _, pads, holes, _, _, vias = cad.load_board(board_path)
        check(len(pads) == 83 and all(p['technology'] == 'thru_hole' for p in pads.values()),
              'CAD contains 83 PTH contact pads')
        check(len(holes) == 8, 'CAD contains eight mechanical NPTH holes')
        check(all(abs(p['drill']-1.0) <= DIAMETER_TOLERANCE_MM for p in pads.values()),
              'All 83 contact pad drills are 1.0 mm')
        check(all(abs(v['drill']-1.0) <= DIAMETER_TOLERANCE_MM for v in vias),
              'All via drills are 1.0 mm')
        check(Counter(round(h['drill'], 6) for h in holes.values()) == Counter({2.75: 4, 3.2: 4}),
              'Mechanical drills: four 2.75 mm and four 3.2 mm')
        for label, row in [
            *((f'{ref}.{pin}', value) for (ref, pin), value in pads.items()),
            *((f'via[{i}]', value) for i, value in enumerate(vias)),
            *holes.items(),
        ]:
            x, y = row['position']
            expected.append({'source': label, 'diameter': row['drill'], 'position': [x, -y]})
        counts.update(contact_pads=len(pads), vias=len(vias), mechanical_holes=len(holes),
                      expected_drill_hits=len(expected))
    except (OSError, ValueError, KeyError, TypeError) as error:
        check(False, f'CAD drill geometry can be read: {error}')

    try:
        tools, hits = read_excellon(drill_path)
        # KiCad assigns separate tool IDs to vias and component pads even when
        # their physical drill diameter is identical (T1/T2 are both 1.0 mm).
        check(set(tools.values()) == {1.0, 2.75, 3.2},
              'Excellon uses exactly three drill diameters: 1.0, 2.75 and 3.2 mm')
        check(set(tools) == {hit['tool'] for hit in hits}, 'Every declared drill tool is used')
        check(len(hits) == len(expected), 'Excellon hit count equals CAD contact pads + vias + mechanical holes')
        remaining = set(range(len(hits)))
        for hole in expected:
            candidates = [index for index in remaining
                          if abs(hits[index]['diameter']-hole['diameter']) <= DIAMETER_TOLERANCE_MM
                          and all(abs(a-b) <= POSITION_TOLERANCE_MM
                                  for a, b in zip(hits[index]['position'], hole['position']))]
            if len(candidates) == 1:
                remaining.remove(candidates[0])
            elif not candidates:
                missing.append(hole)
            else:
                ambiguous.append({'cad': hole, 'export_hits': [hits[index] for index in candidates]})
        unexpected = [hits[index] for index in sorted(remaining)]
        check(not missing and not unexpected and not ambiguous,
              'Every drill diameter/position matches CAD once (absolute X, inverted Y, 0.000501 mm tolerance)')
        counts['export_drill_hits'] = len(hits)
    except (OSError, ValueError) as error:
        check(False, f'Combined Excellon can be read: {error}')

    try:
        job = json.loads(job_path.read_bytes())
        check(job['GeneralSpecs']['LayerNumber'] == 2, 'Gerber job declares two copper layers')
        attributes = job['FilesAttributes']
        expected_names = {STEM+suffix for suffix in GERBERS}
        check(len(attributes) == 7 and {row['Path'] for row in attributes} == expected_names,
              'Gerber job lists exactly the seven expected layer filenames')
        by_name = {row['Path']: row for row in attributes}
        for suffix, (function, polarity) in GERBERS.items():
            name = STEM+suffix
            row = by_name.get(name, {})
            check(row.get('FileFunction') == function and row.get('FilePolarity') == polarity,
                  f'Gerber job layer role/polarity matches {name}')
        copper = [row for row in attributes if str(row.get('FileFunction', '')).startswith('Copper,')]
        check(len(copper) == 2, 'Gerber job lists exactly two copper files')
    except (OSError, ValueError, KeyError, TypeError) as error:
        check(False, f'Gerber job can be read: {error}')

    extra_exports = []
    if fabrication.is_dir():
        known = set(expected_exports)
        extra_exports = [artifact(path, root) for path in sorted(fabrication.iterdir())
                         if path.is_file() and path not in known]
    return {
        'status': 'FAIL' if failures else 'PASS_BOUNDED_CHECKS_ONLY',
        'checks_passed': len(checks), 'failures': failures, 'counts': counts,
        'excellon': {'tools_mm': {str(key): value for key, value in sorted(tools.items())},
                     'coordinate_transform': 'Excellon X = absolute CAD X; Excellon Y = -absolute CAD Y',
                     'position_tolerance_mm': POSITION_TOLERANCE_MM,
                     'missing_hits': missing, 'unexpected_hits': unexpected, 'ambiguous_hits': ambiguous},
        'inputs': inputs, 'exports': inventory, 'additional_export_files': extra_exports,
        'limits': [
            'Gerber copper geometry has NOT been compared against PCB geometry.',
            'Gerber checks cover file inventory and job metadata only; no aperture, mask or outline geometry validation.',
            'Does not run or replace native DRC/ERC, connectivity or solder-access checks.',
            'Does not validate CNC toolpaths, tool compensation, layer registration, plating, current or mechanical assembly.',
            'Extra fabrication files are inventoried and hashed, not geometrically checked.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optional JSON report inside R05/verificacao')
    args = parser.parse_args()
    target = args.output.resolve() if args.output else None
    if target is not None:
        allowed = (cad.repository() / 'Hardware/Juca_PiZero2_Shield/R05/verificacao').resolve()
        if target.parent != allowed or target.suffix.lower() != '.json':
            raise ValueError('Output must be a JSON file directly inside R05/verificacao')
    report = inspect()
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({name: report[name] for name in ('status', 'checks_passed', 'counts', 'failures')},
                     indent=2, ensure_ascii=False))
    return 1 if report['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
