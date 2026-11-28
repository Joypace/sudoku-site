"""Bind certified search events to real, visible tutorial inputs."""
import math


def require(ok, message):
    if not ok:
        raise ValueError(message)


def cell(i, **extra):
    return {'part': 'cell', 'cell': [i // 9, i % 9], **extra}


def actions_for(event):
    op = event['op']
    if op in ('guess', 'strike'):
        i, d = event['choice']
        row, col = divmod(d - 1, 3)
        dx, dy = col - 1, row - 1
        require(d != 5, 'This lesson uses outer-digit directional choices')
        down = {'do': 'down', 'at': cell(i)}
        scale = 1.2
        if op == 'strike':
            down['inputDelay'] = 440
            scale = 1.617 / (math.sqrt(2) if dx and dy else 1)
        result = [down, {'do': 'move', 'at': cell(i, offset=[scale * dx, scale * dy])}]
        if op == 'guess':
            result.append({'do': 'ready', 'digit': d})
        return result + [{'do': 'up'}]
    if op == 'forced':
        return [{'do': 'tap', 'at': cell(event['choice'][0]), 'count': 2}]
    if op == 'lightning':
        return [{'do': 'tap', 'at': {'part': 'element', 'index': 2}, 'count': 1}]
    if op in ('copy', 'select', 'unstack'):
        return [{'do': 'tap', 'at': {'part': 'slot', 'slot': event['slot'] + 1}, 'count': 1}]
    if op in ('undoDouble', 'redoDouble'):
        offsets = [[0, 0], [.6305555555555555, -.24166666666666667]]
        if op == 'redoDouble':
            offsets = [[0, 0], [.28888888888888886, -.4777777777777778],
                       [.7833333333333333, -.6944444444444444]]
        return [{'do': 'tap', 'count': 2, 'touches': [
            {'finger': n, 'at': cell(12, offset=q)} for n, q in enumerate(offsets)]}]
    if op == 'overlay':
        source = event.get('source', event.get('slot'))
        target = event.get('target', event.get('host', 0))
        # Logical events use target=slot; caption targets live in cueTarget.
        require(type(source) is int and type(target) is int, 'Overlay slots required')
        return [{'do': 'down', 'at': {'part': 'slot', 'slot': source + 1}},
                {'do': 'move', 'at': {'part': 'slot', 'slot': target + 1}}, {'do': 'up'}]
    if op == 'inspect':
        return []
    raise ValueError('Unsupported search input')


def validate_story(data, example):
    require(data.get('style') == 'chill' and data.get('setup') == []
            and data.get('final', []) == [], 'No hidden search setup or final edits')
    require(data.get('grid') == example['grid'], 'Search starts at the shared clues')
    require(data.get('expected', {}).get('initialStatus') == 'dilemma',
            'Search must assert its real initial Dilemma')
    expected = [f for e in example['events'] for f in actions_for(e)]
    actual = []
    frames = data['frames']
    previous = -1
    for n, f in enumerate(frames):
        require(f.get('do') in {'hover', 'depart', 'hide', 'tap', 'down', 'move', 'ready', 'up'},
                'Unsupported hidden tutorial action')
        time, duration = f.get('time'), f.get('ms', 0)
        require(type(time) is int and time > previous and type(duration) is int and duration >= 0,
                'Search inputs must be ordered and finish their movement')
        if n + 1 < len(frames):
            require(time + duration <= frames[n + 1]['time'], 'Search gestures overlap')
        previous = time
        if f['do'] in {'tap', 'down', 'move', 'ready', 'up'}:
            actual.append({k: v for k, v in f.items() if k not in {'time', 'ms'}})
    require(actual == expected, 'Execute exactly the proved guesses, forced fills, history and note strikes')
    require(type(data['presentation'].get('duration')) is int
            and data['presentation']['duration'] >= previous + frames[-1].get('ms', 0),
            'Search must finish its final input')
    checks = data['presentation'].get('searchCheckpoints')
    bound = [e['checkpoint'] for e in example['events'] if 'checkpoint' in e]
    require(type(checks) is list and bound and [c.get('state') for c in checks] == bound,
            'Every declared actual search state must be checked during native capture')
    windows = data['presentation'].get('searchEventWindows')
    require(type(windows) is list and len(windows) == len(example['events']),
            'Every search event needs a bounded input window')
    check_index = 0
    previous_end = -1
    for n, (event, window) in enumerate(zip(example['events'], windows)):
        start, end = window.get('start'), window.get('end')
        require(type(start) is int and type(end) is int and previous_end <= start < end,
                'Search event windows must be disjoint and ordered')
        require(end <= data['presentation']['duration'], 'Search window exceeds the animation')
        inside = [f for f in frames if start <= f['time'] < end
                  and f['do'] in {'tap', 'down', 'move', 'ready', 'up'}]
        require([{k: v for k, v in f.items() if k not in {'time', 'ms'}} for f in inside]
                == actions_for(event), 'Search inputs must stay in their own event window')
        require(all(f['time'] + f.get('ms', 0) < end for f in inside),
                'Finish the event before checking its state')
        if 'checkpoint' in event:
            at = checks[check_index].get('time')
            following = windows[n + 1]['start'] if n + 1 < len(windows) else data['presentation']['duration']
            require(type(at) is int and end <= at < following,
                    'Check each state after its event and before the next event')
            check_index += 1
        previous_end = end
    times = [c.get('time') for c in checks]
    require(all(type(t) is int and 0 <= t <= data['presentation']['duration'] for t in times)
            and times == sorted(set(times)), 'Checkpoint times must be unique and ordered')
    if example.get('mode') == 'single-board':
        require(all(s.get('boardCount') == 1 for s in bound), 'DFS must keep exactly one board')
    cues = {s['redo']['kind'] for s in bound if s.get('redo')}
    require(set(example.get('requireCues', [])) <= cues, 'Missing real redo cue evidence')
