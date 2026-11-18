"""Start a local Uvicorn process and open the Qt network client."""
import os
import socket
import subprocess
import sys
from time import monotonic, sleep

from config import BASE_DIR, DATA_DIR
from run_client import main as open_client
from ui.api_client import ApiClient, ApiError


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.setdefault("COLLEGE_DB_URL", f"sqlite:///{(DATA_DIR / 'network_demo.db').as_posix()}")
    command = [sys.executable, "-B", "-m", "uvicorn", "server.api:app",
               "--host", "127.0.0.1", "--port", str(port)]
    with subprocess.Popen(command, cwd=BASE_DIR, env=env) as server:
        try:
            client = ApiClient(url)
            deadline = monotonic() + 20
            while monotonic() < deadline and server.poll() is None:
                try:
                    client.request("/health")
                except ApiError:
                    sleep(0.15)
                else:
                    return open_client(["--url", url])
            print("Не удалось запустить локальный сервер.", file=sys.stderr)
            return 1
        finally:
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == "__main__":
    sys.exit(main())
