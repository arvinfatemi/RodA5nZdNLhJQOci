import importlib
import pkgutil

import coinbase
print('coinbase package:', coinbase.__file__)

try:
    import coinbase.websocket as ws
except Exception as e:
    print('Failed to import coinbase.websocket:', repr(e))
else:
    print('ws module:', getattr(ws, '__file__', None))
    print('ws attrs:', [n for n in dir(ws) if not n.startswith('_')])
    if hasattr(ws, '__path__'):
        subs = [m.name for m in pkgutil.iter_modules(ws.__path__)]
        print('submodules:', subs)
        for name in subs:
            try:
                mod = importlib.import_module(f'{ws.__name__}.{name}')
                exported = [n for n in dir(mod) if 'Client' in n or 'Websocket' in n or 'WebSocket' in n]
                print(' ', name, '->', exported)
            except Exception as e:
                print(' ', name, 'import error:', repr(e))

