"""أدوات مشتركة للاختبارات: خادم محلي ومتصفح."""
import os, socket, threading, functools, http.server, shutil, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tests', 'out'); os.makedirs(OUT, exist_ok=True)
CHROME = os.environ.get('CHROME') or (shutil.which('google-chrome') or shutil.which('chromium') or None)

def serve(directory=ROOT):
    """يشغّل خادماً محلياً على منفذ حر ويعيد رابط index.html."""
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=directory)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f'http://localhost:{port}/index.html', srv

def copy_with_config(api='TESTKEY', project='himaya-test'):
    """نسخة مؤقتة من الموقع مع config.js مملوء لاختبار Firebase."""
    d = tempfile.mkdtemp(); shutil.copytree(ROOT, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns('tests', '.git'))
    open(os.path.join(d, 'config.js'), 'w').write(f"window.HIMAYA_FB = {{apiKey:'{api}', projectId:'{project}'}};\n")
    return d

def launch_args():
    return {'executable_path': CHROME, 'args': ['--no-sandbox']} if CHROME else {'args': ['--no-sandbox']}
