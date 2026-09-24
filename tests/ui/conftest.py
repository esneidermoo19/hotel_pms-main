"""
Fixtures de la suite de pruebas de UI (Playwright).

Responsabilidades de este módulo:
- Exponer ``base_url`` (configurable vía ``PLAYWRIGHT_BASE_URL``).
- Garantizar (autouse, scope session) que exista un servidor Flask de UI
  respondiendo antes de ejecutar cualquier prueba:
    * Si ``http://<base_url>/health`` ya responde, se reutiliza el servidor
      externo (arrancado manualmente o por CI).
    * Si no responde, el fixture lanza un subproceso con
      ``python -m tests.ui.server`` y lo termina al final de la sesión.
- Proveer ``ui_login``: helper que autentica un usuario del panel staff.

De esta forma las pruebas funcionan igual en local y en GitHub Actions sin
depender de que el desarrollador recuerde arrancar el servidor.
"""
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

import pytest

BASE_URL = os.environ.get('PLAYWRIGHT_BASE_URL', 'http://127.0.0.1:5151')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STARTUP_TIMEOUT = 60  # segundos


def _health_ok(url, timeout=3.0):
    """True si el endpoint /health responde 200 en la URL indicada."""
    try:
        with urllib.request.urlopen(url + '/health', timeout=timeout) as resp:
            return resp.status == 200
    except (URLError, HTTPError, OSError):
        return False


def _port_from_base_url(base_url):
    parsed = urllib.parse.urlparse(base_url)
    return parsed.port or 5151


@pytest.fixture(scope='session')
def base_url(request):
    """URL base del servidor de UI.

    Prioridad de resolución:
    1. ``--base-url`` (CLI / ini de pytest-base-url).
    2. Env ``PLAYWRIGHT_BASE_URL``.
    3. Default local ``http://127.0.0.1:5151``.
    """
    cli = request.config.getoption('--base-url', default=None)
    if cli:
        return cli
    return BASE_URL


@pytest.fixture(scope='session', autouse=True)
def ui_server(base_url):
    """Levanta (o reutiliza) el servidor de UI para toda la sesión de pruebas."""
    if _health_ok(base_url):
        yield None
        return

    port = _port_from_base_url(base_url)
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, 'ui-server.log')
    # El log va a archivo (no a PIPE): un pipe de stdout lleno bloquearía al
    # servidor a mitad de la sesión y deja evidencia en `logs/ui-server.log`.
    log = open(log_path, 'w', encoding='utf-8')
    proc = subprocess.Popen(
        [sys.executable, '-m', 'tests.ui.server', '--port', str(port)],
        cwd=PROJECT_ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        if _health_ok(base_url):
            break
        if proc.poll() is not None:
            log.flush()
            raise RuntimeError(
                f'El servidor de UI terminó antes de responder /health.\n'
                f'--- LOG ({log_path}) ---\n{open(log_path, encoding="utf-8").read()}'
            )
        time.sleep(0.5)
    else:
        proc.kill()
        log.close()
        raise RuntimeError(f'Timeout esperando /health en {base_url} ({STARTUP_TIMEOUT}s).')

    yield proc

    print('\n[ui-tests] Deteniendo servidor de UI.', flush=True)
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    log.close()


@pytest.fixture
def ui_login(page, base_url):
    """Autentica en el panel staff y espera la redirección posterior."""
    def _login(username: str, password: str):
        page.goto(f'{base_url}/staff/login')
        page.fill('#username', username)
        page.fill('#password', password)
        page.click('#login-button')
    return _login


@pytest.fixture
def hab_url(base_url):
    """Helper de URLs del módulo de habitaciones (admin)."""
    return lambda sufijo='': f'{base_url}/staff/admin/habitaciones{sufijo}'


@pytest.fixture
def coincidir():
    """Compiladores de regex para aserciones de URL con parámetros de ruta."""
    def _regex(base_url, patron):
        return re.compile(re.escape(base_url) + patron)
    return _regex