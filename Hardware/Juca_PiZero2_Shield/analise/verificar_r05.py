"""Independent, bounded checks of R05 CAD sources (Python standard library).

This is NOT a DRC/ERC engine. It does not validate copper clearance, current,
Gerber artwork, connector mating or a manufactured assembly. Native KiCad
reports can be supplied separately; coordinate/topology/style checks do not
replace them. The reviewed R05 pinout and mechanical contract are declared
below; historical revisions are not required to run this checker.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

TOL = 0.00002  # mm; admits KiCad nanometre serialization rounding.
MIN_COPPER_CLEARANCE_MM = 0.31
SIGNAL_TRACK_WIDTH_MM = 1.0
POWER_TRACK_WIDTH_MM = 2.0

# Reviewed R05 design contract, independent of the PCB being checked.
# Local coordinates use the top-left board corner, X right and Y down.
# The Pi faces down, with CSI opposite J5: odd header pins are on the right.
BOARD_ORIGIN_MM = (100.0, 60.0)
BOARD_SIZE_MM = (48.0, 88.0)
JUCA_SIGNAL_NETS = (
    'JUCA_SDA', 'JUCA_SCL', 'JUCA_TXD0', 'JUCA_RXD0',
    'JUCA_GPIO38', 'JUCA_GPIO37', 'JUCA_GPIO36', 'JUCA_GPIO35',
    'JUCA_GPIO45', 'JUCA_GPIO48', 'JUCA_GPIO47', 'JUCA_GPIO46', 'JUCA_GPIO3',
)
JP_PI_PHYSICAL_PINS = (3, 5, 10, 8, 24, 21, 23, 19, 15, 12, 33, 16, 11)
PI_SIGNAL_BCM = {
    3: 2, 5: 3, 10: 15, 8: 14, 24: 8, 21: 9, 23: 11,
    19: 10, 15: 22, 12: 18, 33: 13, 16: 23, 11: 17,
}
MOUNTING_HOLES = {
    'H1': (4.30, 43.21, 3.2), 'H2': (4.35, 68.00, 3.2),
    'H3': (39.00, 68.00, 3.2), 'H4': (4.30, 82.14, 3.2),
    'H5': (14.50, 23.50, 2.75), 'H6': (37.50, 23.50, 2.75),
    'H7': (14.50, 81.50, 2.75), 'H8': (37.50, 81.50, 2.75),
}


def expected_connector_pads():
    """Declared R05 positions/nets, never inferred from the input board."""
    expected = {}
    for pin, net in enumerate(JUCA_SIGNAL_NETS, 1):
        expected[('J5', str(pin))] = ((7.4744+(pin-1)*2.54, 3.0927), net)
    for pin in range(1, 5):
        net = {2: '+5V', 4: 'GND'}.get(pin, f'unconnected-(J11-Pad{pin})')
        expected[('J11', str(pin))] = ((45.1794, 77.2477+(pin-1)*2.54), net)
    for pin in range(1, 41):
        net = (f'PI_GPIO{PI_SIGNAL_BCM[pin]}' if pin in PI_SIGNAL_BCM else
               {2: '+5V', 4: '+5V', 9: 'GND'}.get(pin, f'unconnected-(JPI1-Pad{pin})'))
        expected[('JPI1', str(pin))] = ((15.77 if pin % 2 else 13.23,
                                       28.37+((pin-1)//2)*2.54), net)
    return expected


def repository():
    for p in [*Path(__file__).resolve().parents, Path.cwd(), *Path.cwd().parents]:
        if (p / 'Hardware/Juca_PiZero2_Shield/R05/Juca_PiZero2_Shield_R05.kicad_pcb').is_file():
            return p
    raise ValueError('Repository containing the R05 PCB not found')


def parse(path):
    stack, roots = [], []
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', path.read_text(encoding='utf-8')):
        if token == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ')':
            if not stack:
                raise ValueError('Unexpected closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('Atom outside root')
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack or len(roots) != 1:
        raise ValueError('Unbalanced S-expression')
    return roots[0]


def children(node, key):
    return [n for n in node[1:] if isinstance(n, list) and n and n[0] == key]


def child(node, key, default=None):
    rows = children(node, key)
    if len(rows) > 1:
        raise ValueError(f'Duplicate {key}')
    return rows[0] if rows else default


def xy(node):
    return tuple(float(v) for v in node[1:3])


def near(a, b):
    return len(a) == len(b) and all(abs(x-y) <= TOL for x, y in zip(a, b))


def key(p):
    return tuple(round(v, 5) for v in p)


def reference(fp):
    properties = {n[1]: n[2] for n in children(fp, 'property')}
    if 'Reference' in properties:
        return properties['Reference']
    return next(n[2] for n in children(fp, 'fp_text') if n[1] == 'reference')


def point_segment(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    size = dx*dx+dy*dy
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/size)) if size else 0
    q = (a[0]+t*dx, a[1]+t*dy)
    return math.dist(p, q)


def in_pad(p, pad):
    # All R05 footprints are unrotated; individual pad rotation is handled.
    theta = math.radians(pad['angle'])
    dx, dy = p[0]-pad['position'][0], p[1]-pad['position'][1]
    px, py = abs(dx*math.cos(theta)-dy*math.sin(theta)), abs(dx*math.sin(theta)+dy*math.cos(theta))
    hx, hy = (v/2 for v in pad['size'])
    if pad['shape'] == 'circle':
        return math.hypot(px, py) <= min(hx, hy)+TOL
    if pad['shape'] == 'rect':
        return px <= hx+TOL and py <= hy+TOL
    if pad['shape'] == 'oval':
        radius = min(hx, hy)
        return math.hypot(max(0, px-(hx-radius)), max(0, py-(hy-radius))) <= radius+TOL
    if pad['shape'] == 'roundrect':
        radius = pad['roundrect_ratio']*min(pad['size'])
        return math.hypot(max(0, px-(hx-radius)), max(0, py-(hy-radius))) <= radius+TOL
    raise ValueError(f"Unsupported pad shape {pad['shape']}")


def track_touches_pad(track, pad):
    """Same-face copper contact only; a drilled pad is not a vertical bridge."""
    if track['layer'] not in pad['layers'] or track['net'] != pad['net']:
        return False
    radius = track['width']/2
    if pad['shape'] == 'circle':
        return point_segment(pad['position'], track['start'], track['end']) <= min(pad['size'])/2+radius+TOL
    if pad['shape'] != 'rect':
        raise ValueError(f"Solder-face contact check requires circle/rect pads, found {pad['shape']}")

    # Exact distance between a segment and the rectangular pad, including
    # corner contact by the trace's round copper edge. Current R05 has both
    # circular pads and square first contacts.
    theta = math.radians(pad['angle'])
    def local(point):
        dx, dy = point[0]-pad['position'][0], point[1]-pad['position'][1]
        return (dx*math.cos(theta)-dy*math.sin(theta), dx*math.sin(theta)+dy*math.cos(theta))
    a, b = local(track['start']), local(track['end'])
    hx, hy = (v/2 for v in pad['size'])
    lower, upper = 0.0, 1.0
    for start, end, extent in zip(a, b, (hx, hy)):
        delta = end-start
        if abs(delta) <= TOL:
            if abs(start) > extent+TOL:
                lower, upper = 1.0, 0.0
                break
        else:
            first, last = sorted(((-extent-start)/delta, (extent-start)/delta))
            lower, upper = max(lower, first), min(upper, last)
    if lower <= upper:
        return True
    distances = [math.hypot(max(abs(x)-hx, 0), max(abs(y)-hy, 0)) for x, y in (a, b)]
    distances.extend(point_segment(corner, a, b) for corner in ((-hx, -hy), (-hx, hy), (hx, -hy), (hx, hy)))
    return min(distances) <= radius+TOL


def load_board(path):
    pcb = parse(path)
    nets = {n[1]: n[2] for n in children(pcb, 'net')}
    pads, holes, fps = {}, {}, {}
    for fp in children(pcb, 'footprint'):
        ref = reference(fp)
        at = child(fp, 'at')
        if len(at) > 3 and abs(float(at[3])) > TOL:
            raise ValueError('This bounded R05 checker requires unrotated footprints')
        base = xy(at)
        fps[ref] = fp
        for node in children(fp, 'pad'):
            place = child(node, 'at')
            position = tuple(a+b for a, b in zip(base, xy(place)))
            drill = child(node, 'drill', ['drill', '0'])
            if len(drill) != 2:
                raise ValueError('Slotted or offset drills are not supported')
            if node[2] == 'np_thru_hole':
                holes[ref] = {'position': position, 'drill': float(drill[1])}
                continue
            net = child(node, 'net', ['net', '0', ''])
            if nets.get(net[1]) != net[2]:
                raise ValueError('Pad net id/name mismatch')
            layers = child(node, 'layers')[1:]
            copper = ['F.Cu', 'B.Cu'] if '*.Cu' in layers else [x for x in layers if x.endswith('.Cu')]
            pads[(ref, node[1])] = {
                'position': position, 'drill': float(drill[1]), 'technology': node[2],
                'net': net[2], 'size': xy(child(node, 'size')), 'shape': node[3],
                'angle': float(place[3]) if len(place) > 3 else 0,
                'roundrect_ratio': float(child(node, 'roundrect_rratio', ['', '0'])[1]),
                'layers': copper,
            }
    tracks = [{'start': xy(child(n, 'start')), 'end': xy(child(n, 'end')),
               'width': float(child(n, 'width')[1]), 'layer': child(n, 'layer')[1],
               'net': nets[child(n, 'net')[1]]} for n in children(pcb, 'segment')]
    vias = [{'position': xy(child(n, 'at')), 'diameter': float(child(n, 'size')[1]),
             'drill': float(child(n, 'drill')[1]), 'net': nets[child(n, 'net')[1]],
             'layers': child(n, 'layers')[1:]} for n in children(pcb, 'via')]
    return pcb, pads, holes, fps, tracks, vias


def netlist(path):
    tree = parse(path)
    return {child(n, 'name')[1]: sorted((child(v, 'ref')[1], child(v, 'pin')[1])
            for v in children(n, 'node')) for n in children(child(tree, 'nets'), 'net')}


def check_project_settings(path, check):
    """Reject weakened saved rules, including pcbnew.SaveBoard() defaults."""
    try:
        content = path.read_bytes()
    except OSError as error:
        check(False, f'Project settings file can be read: {path} ({error})')
        return None
    project_hash = hashlib.sha256(content).hexdigest()
    try:
        project = json.loads(content)
        rules = project['board']['design_settings']['rules']
        classes = project['net_settings']['classes']
        if not isinstance(rules, dict) or not isinstance(classes, list):
            raise ValueError('rules must be an object and netclasses must be a list')
    except (ValueError, KeyError, TypeError) as error:
        check(False, f'Project settings contain readable design rules and netclasses ({error})')
        return project_hash
    check(True, 'Project settings contain readable design rules and netclasses')

    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

    for name, limit in {
        'min_clearance': MIN_COPPER_CLEARANCE_MM,
        'min_track_width': SIGNAL_TRACK_WIDTH_MM,
        'min_copper_edge_clearance': 0.508,
        'min_hole_clearance': 0.508,
        'min_hole_to_hole': 0.508,
        'min_through_hole_diameter': 1.0,
        'min_via_diameter': 2.0,
        'min_via_annular_width': 0.5,
    }.items():
        value = rules.get(name)
        check(number(value) and value + 1e-9 >= limit,
              f'Project rule {name} >= {limit} mm (found {value!r})')

    check(bool(classes) and all(isinstance(row, dict) for row in classes),
          'Project has nonempty, valid netclasses')
    valid_classes = [row for row in classes if isinstance(row, dict)]
    check(any(row.get('name') == 'Default' for row in valid_classes), 'Project has the Default netclass')
    for row in valid_classes:
        name = row.get('name', '<unnamed>')
        for field, limit in (('clearance', MIN_COPPER_CLEARANCE_MM),
                             ('track_width', SIGNAL_TRACK_WIDTH_MM)):
            value = row.get(field)
            check(number(value) and value + 1e-9 >= limit,
                  f'Netclass {name} {field} >= {limit} mm (found {value!r})')
        for field, required in (('via_drill', 1.0), ('via_diameter', 2.0)):
            value = row.get(field)
            check(number(value) and abs(value-required) <= 1e-9,
                  f'Netclass {name} {field} = {required} mm (found {value!r})')
    for name, required in {'Default': SIGNAL_TRACK_WIDTH_MM, 'JucaSignals': SIGNAL_TRACK_WIDTH_MM,
                           'Power': POWER_TRACK_WIDTH_MM}.items():
        matching = [row for row in valid_classes if row.get('name') == name]
        value = matching[0].get('track_width') if len(matching) == 1 else None
        check(number(value) and abs(value-required) <= 1e-9,
              f'Netclass {name} has one definition with track_width = {required} mm (found {value!r})')
    patterns = project['net_settings'].get('netclass_patterns')
    expected_patterns = {('+5V', 'Power'), ('GND', 'Power'), ('JUCA_*', 'JucaSignals')}
    valid_patterns = isinstance(patterns, list) and all(isinstance(row, dict) for row in patterns)
    check(valid_patterns and len(patterns) == len(expected_patterns) and
          {(row.get('pattern'), row.get('netclass')) for row in patterns} == expected_patterns,
          'R05 netclass patterns assign +5V/GND to Power and JUCA_* to JucaSignals')
    return project_hash


def inspect(args):
    repo = repository()
    shield = repo / 'Hardware/Juca_PiZero2_Shield'
    board_path = args.pcb or shield / 'R05/Juca_PiZero2_Shield_R05.kicad_pcb'
    netlist_path = args.netlist or shield / 'R05/verificacao/netlist_R05.net'
    pcb, pads, holes, fps, tracks, vias = load_board(board_path)
    failures, checks = [], []
    def check(condition, label):
        (checks if condition else failures).append(label)

    project_path = board_path.with_suffix('.kicad_pro')
    project_hash = check_project_settings(project_path, check)

    origin = BOARD_ORIGIN_MM
    expected_pads = expected_connector_pads()
    check(len(pads) == 83, '83 electrical pads')
    check(len(holes) == 8, '8 mounting holes')
    check(all(p['technology'] == 'thru_hole' and abs(p['drill']-1) <= TOL for p in pads.values()),
          'Every electrical pad is PTH with 1.0 mm drill')
    check(all(abs(v['drill']-1) <= TOL and abs(v['diameter']-2) <= TOL for v in vias),
          'Every via uses 2.0 mm diameter / 1.0 mm drill')
    connector_pairs = {pair for pair in pads if pair[0] in ('J5', 'J11', 'JPI1')}
    check(connector_pairs == set(expected_pads), 'J5/J11/JPI1 contain exactly the declared R05 pins')
    for (ref, pin), (local_position, expected_net) in expected_pads.items():
        pad = pads.get((ref, pin))
        if pad is None:
            continue  # Missing identities are reported by the exact-set check.
        expected = tuple(a+b for a, b in zip(origin, local_position))
        check(near(pad['position'], expected), f'{ref}.{pin} matches declared R05 mechanical position')
        check(pad['net'] == expected_net, f'{ref}.{pin} matches declared R05 net {expected_net}')
    check(set(holes) == set(MOUNTING_HOLES), 'Mounting-hole identities are H1 through H8')
    for ref, (x, y, drill) in MOUNTING_HOLES.items():
        hole = holes.get(ref)
        if hole is None:
            continue
        check(near(hole['position'], (origin[0]+x, origin[1]+y)),
              f'{ref} matches declared R05 mounting position')
        check(abs(hole['drill']-drill) <= TOL, f'{ref} mounting drill is {drill} mm')
    for i in range(1, 14):
        ref = f'JP{i}'
        group = {p: v for (r, p), v in pads.items() if r == ref}
        check(set(group) == {'1', '2'}, f'{ref} has two contacts')
        if set(group) != {'1', '2'}:
            continue
        check(abs(math.dist(group['1']['position'], group['2']['position'])-2.54) <= TOL,
              f'{ref} has 2.54 mm contact pitch')
        check(group['1']['net'] != group['2']['net'], f'{ref} remains open in CAD')
        for pin in ('1', '2'):
            physical_pin = JP_PI_PHYSICAL_PINS[i-1]
            expected_net = (JUCA_SIGNAL_NETS[i-1] if pin == '1'
                            else f'PI_GPIO{PI_SIGNAL_BCM[physical_pin]}')
            check(group[pin]['net'] == expected_net,
                  f'{ref}.{pin} matches declared R05 net {expected_net}')
        check(fps[ref][1] == 'JucaShield:Jumper_PTH_1x02_P2_54mm', f'{ref} uses PTH footprint')
        attrs = child(fps[ref], 'attr', ['attr'])
        check('dnp' not in attrs, f'{ref} header is populated (shunt absent)')
    check(fps['JPI1'][1] == 'JucaShield:Pi_2x20_FaceDown', 'Pi uses face-down footprint')
    outline = [n for n in children(pcb, 'gr_rect') if child(n, 'layer', ['', ''])[1] == 'Edge.Cuts']
    lines = [n for n in children(pcb, 'gr_line') if child(n, 'layer', ['', ''])[1] == 'Edge.Cuts']
    if len(outline) == 1:
        check(near(xy(child(outline[0], 'start')), origin) and
              near(xy(child(outline[0], 'end')), tuple(a+b for a, b in zip(origin, BOARD_SIZE_MM))),
              '48 x 88 mm outline preserved')
    elif not outline and len(lines) == 4:
        w, h = BOARD_SIZE_MM
        corners = [origin, (origin[0]+w, origin[1]), (origin[0]+w, origin[1]+h), (origin[0], origin[1]+h)]
        expected_edges = {tuple(sorted((key(corners[i]), key(corners[(i+1) % 4])))) for i in range(4)}
        actual_edges = {tuple(sorted((key(xy(child(n, 'start'))), key(xy(child(n, 'end')))))) for n in lines}
        check(actual_edges == expected_edges, '48 x 88 mm outline preserved')
    else:
        failures.append('Expected one rectangle or four straight Edge.Cuts edges')
    check(not children(pcb, 'arc') and all(child(n, 'keepout') is not None for n in children(pcb, 'zone')),
          'No unsupported copper arcs or filled zones (rule-area keepouts are allowed)')

    exported = netlist(netlist_path)
    actual = defaultdict(list)
    for pair, pad in pads.items():
        actual[pad['net']].append(pair)
    actual = {n: sorted(v) for n, v in actual.items()}
    check(len(exported) == 54, 'Native schematic netlist contains 54 nets')
    check(sum(n.startswith('unconnected-') for n in exported) == 26, '26 explicit NC nets')
    check(actual == exported, 'PCB pin-to-net assignments equal native schematic netlist')
    check(exported.get('PI_GPIO17') == [('JP13', '2'), ('JPI1', '11')],
          'Native schematic connects JP13 only to GPIO17 / Pi physical pin 11')
    check(exported.get('unconnected-(JPI1-Pad18)') == [('JPI1', '18')] and 'PI_GPIO24' not in exported,
          'Native schematic leaves former GPIO24 / Pi physical pin 18 explicitly NC')
    native_components = children(child(parse(netlist_path), 'components'), 'comp')
    check(len(native_components) == 16, 'Native schematic netlist contains 16 electrical components')
    for component in native_components:
        ref = child(component, 'ref')[1]
        fp = fps[ref]
        properties = {n[1]: n[2] for n in children(fp, 'property')}
        check(properties.get('Value') == child(component, 'value')[1], f'{ref} PCB/schematic value parity')
        check(fp[1] == child(component, 'footprint')[1], f'{ref} PCB/schematic footprint parity')
        check(child(fp, 'path', ['', ''])[1].endswith('/'+child(component, 'tstamps')[1]),
              f'{ref} PCB/schematic instance identity parity')

    pads_by_net = defaultdict(list)
    for p in pads.values():
        pads_by_net[p['net']].append(p)
    widths = defaultdict(set)
    for track in tracks:
        widths[track['net']].add(track['width'])
    widths_by_net = {net: sorted(values) for net, values in sorted(widths.items())}
    solder_faces = []
    missing_solder_faces = []
    for (ref, pin), pad in sorted(pads.items()):
        if not pad['net'] or pad['net'].startswith('unconnected-'):
            continue
        required_face = 'F.Cu' if ref in ('J5', 'J11') else 'B.Cu'
        known_connector = ref in ('J5', 'J11', 'JPI1') or re.fullmatch(r'JP(?:[1-9]|1[0-3])', ref)
        if not known_connector:
            raise ValueError(f'No defined solderable face for {ref}')
        contacts = [i for i, track in enumerate(tracks)
                    if track['layer'] == required_face and track_touches_pad(track, pad)]
        row = {'reference': ref, 'pin': pin, 'net': pad['net'],
               'required_face': required_face, 'same_face_track_indices': contacts}
        solder_faces.append(row)
        if not contacts:
            missing_solder_faces.append(row)
        if not args.allow_unrouted:
            check(bool(contacts), f'{ref}.{pin} has direct same-net track contact on solderable {required_face}')
    if not args.allow_unrouted:
        expected_routed_nets = {net for net in exported if net and not net.startswith('unconnected-')}
        check(set(widths_by_net) == expected_routed_nets, 'Every used net has tracks and NC nets have no tracks')
        for net, values in widths_by_net.items():
            expected_width = (POWER_TRACK_WIDTH_MM if net in ('+5V', 'GND')
                              else SIGNAL_TRACK_WIDTH_MM if net.startswith(('PI_GPIO', 'JUCA_')) else None)
            check(len(values) == 1, f'{net} uses one uniform track width (found {values} mm)')
            check(expected_width is not None and all(abs(v-expected_width) <= TOL for v in values),
                  f'{net} track width is {expected_width} mm (found {values})')
    def anchored(p, net, layer, with_vias=True):
        return any(layer in a['layers'] and in_pad(p, a) for a in pads_by_net[net]) or (
            with_vias and any(v['net'] == net and layer in v['layers'] and
                             math.dist(p, v['position']) <= v['diameter']/2+TOL for v in vias))

    directions, ends, duplicates, zero_lengths = [], [], [], []
    vertices, segment_keys = defaultdict(list), {}
    for i, segment in enumerate(tracks):
        a, b = segment['start'], segment['end']
        dx, dy = abs(b[0]-a[0]), abs(b[1]-a[1])
        if math.dist(a, b) <= TOL:
            zero_lengths.append(i)
        signature = (segment['net'], segment['layer'], *sorted((key(a), key(b))))
        if signature in segment_keys:
            duplicates.append([segment_keys[signature], i])
        segment_keys[signature] = i
        if min(dx, dy) > TOL and abs(dx-dy) > TOL:
            inside = any(segment['layer'] in p['layers'] and in_pad(a, p) and in_pad(b, p)
                         for p in pads_by_net[segment['net']])
            if not inside:
                directions.append({'track': i, **segment})
        for p, other in ((a, b), (b, a)):
            vertices[(segment['net'], segment['layer'], key(p))].append((i, other))
            if anchored(p, segment['net'], segment['layer']):
                continue
            touch = any(j != i and other_seg['net'] == segment['net'] and
                        other_seg['layer'] == segment['layer'] and
                        point_segment(p, other_seg['start'], other_seg['end']) <= other_seg['width']/2+TOL
                        for j, other_seg in enumerate(tracks))
            if not touch:
                ends.append({'track': i, 'point': p, 'net': segment['net'], 'layer': segment['layer']})
    turns = []
    for (net, layer, vertex), incident in vertices.items():
        if len(incident) != 2 or anchored(vertex, net, layer):
            continue
        vectors = [(q[0]-vertex[0], q[1]-vertex[1]) for _, q in incident]
        lengths = [math.hypot(*v) for v in vectors]
        if min(lengths) <= TOL:
            continue
        cosine = sum(a*b for a, b in zip(*vectors))/(lengths[0]*lengths[1])
        turn = 180-math.degrees(math.acos(max(-1, min(1, cosine))))
        if turn > 45.02:
            turns.append({'tracks': [i for i, _ in incident], 'point': vertex, 'deflection_degrees': turn,
                          'net': net, 'layer': layer})
    one_sided_vias = []
    for i, via in enumerate(vias):
        used = sorted({s['layer'] for s in tracks if s['net'] == via['net'] and
                       point_segment(via['position'], s['start'], s['end']) <= (via['diameter']+s['width'])/2+TOL})
        if set(used) != {'F.Cu', 'B.Cu'}:
            one_sided_vias.append({'via': i, 'layers_used': used, **via})
    style = {'non_0_45_segments_outside_pads': directions, 'turns_over_45_outside_pads_vias': turns,
             'dangling_endpoint_candidates': ends, 'duplicate_segments': duplicates,
             'zero_length_segments': zero_lengths, 'one_sided_via_candidates': one_sided_vias,
             'pads_missing_solder_face_contact': missing_solder_faces}
    if not args.allow_unrouted:
        check(bool(tracks), 'Routing is present')
        for name, findings in style.items():
            check(not findings, name)

    native = {}
    for kind, report_path in [('drc', args.drc), ('erc', args.erc)]:
        if report_path is None:
            native[kind] = {'status': 'NOT_SUPPLIED'}
            continue
        report = json.loads(report_path.read_text(encoding='utf-8'))
        rows = ([*report.get('violations', []), *report.get('unconnected_items', []), *report.get('schematic_parity', [])]
                if kind == 'drc' else [v for s in report.get('sheets', []) for v in s.get('violations', [])])
        native[kind] = {'status': 'PASS' if not rows else 'FINDINGS', 'count': len(rows),
                        'types': dict(Counter(v.get('type', 'unknown') for v in rows)),
                        'version': report.get('kicad_version'), 'report': str(report_path)}
        check(not rows, f'Native KiCad {kind.upper()} report contains no violations/warnings')
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {'status': 'FAIL' if failures else ('PASS_PLACEMENT_ONLY' if args.allow_unrouted else 'PASS_BOUNDED_CHECKS_ONLY'),
            'board': str(board_path), 'board_sha256': digest(board_path),
            'project': str(project_path), 'project_sha256': project_hash,
            'netlist_sha256': digest(netlist_path), 'checks_passed': len(checks), 'failures': failures,
            'counts': {'electrical_pads': len(pads), 'mounting_holes': len(holes), 'tracks': len(tracks),
                       'vias': len(vias), 'nets': len(exported), 'used_pads': len(solder_faces)},
            'widths_by_net_mm': widths_by_net, 'solder_face_contacts': solder_faces, 'routing_findings': style,
            'native_reports': native,
            'limits': ['No clearance, short-circuit or full geometric-connectivity computation.',
                       'Dangling-end checks use same-net copper contact candidates, not a connectivity proof.',
                       'Solder-face checks require a directly touching same-net track on the intended solder side; '
                       'they do not assume plating through connector holes or prove full nonplated-board connectivity.',
                       'Two-sided via copper contact still requires a physical wire/rivet soldered on both faces; '
                       'plastic-body, solder-fillet and assembly-height clearance are not checked.',
                       'Turn checks cover degree-two endpoint junctions outside pads/vias; not every geometric junction.',
                       'Does not identify all redundant detours, overlapping segments or cycles.',
                       'Provided native reports are not rerun; caller must ensure reports were generated for this board.',
                       'No Gerber/Excellon, machine process, current, mechanical mating or physical validation.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path)
    parser.add_argument('--netlist', type=Path)
    parser.add_argument('--drc', type=Path)
    parser.add_argument('--erc', type=Path)
    parser.add_argument('--allow-unrouted', action='store_true', help='Check placement only; report routing findings without failing')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect(args)
    if args.output:
        target = args.output.resolve()
        root = repository().resolve()
        if target.suffix.lower() != '.json' or not target.is_relative_to(root) or any(
                p in ('R02', 'R04', 'origem') for p in target.relative_to(root).parts):
            raise ValueError('Output must be JSON inside the repository, outside preserved sources')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'checks_passed', 'counts', 'failures')}, indent=2))
    return 1 if result['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
