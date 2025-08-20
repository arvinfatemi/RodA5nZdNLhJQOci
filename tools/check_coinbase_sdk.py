import sys
import importlib

print('Python:', sys.version)

names = [
    'coinbase',
    'coinbase.websocket',
    'coinbase.rest',
    'coinbase_advanced',
    'coinbase_advanced_py',
]

for name in names:
    try:
        m = importlib.import_module(name)
        print(f'OK import {name}:', getattr(m, '__file__', m))
    except Exception as e:
        print(f'FAIL import {name}:', repr(e))

try:
    import importlib.metadata as md  # type: ignore
except Exception:
    try:
        import importlib_metadata as md  # type: ignore
    except Exception as e:
        md = None
        print('No importlib.metadata available:', repr(e))

if md:
    print('--- Installed distributions containing "coinbase" ---')
    for dist in md.distributions():
        name = dist.metadata.get('Name') or dist.metadata.get('name') or ''
        if 'coinbase' in name.lower():
            print('Dist:', name, 'Version:', dist.version)
            try:
                loc = dist.locate_file('')
            except Exception:
                loc = 'n/a'
            print('  Location:', loc)

