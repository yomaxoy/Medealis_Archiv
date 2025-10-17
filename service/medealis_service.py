#!/usr/bin/env python3
"""
Windows Service Wrapper für Medealis Warehouse Management System.

Dieser Service startet automatisch beim Windows-Start und hält
die Streamlit-Anwendung dauerhaft am Laufen.

Installation:
    python medealis_service.py install

Start:
    python medealis_service.py start

Stop:
    python medealis_service.py stop

Deinstallation:
    python medealis_service.py remove
"""

import sys
import os
from pathlib import Path
import subprocess
import socket
import servicemanager
import win32event
import win32service
import win32serviceutil

# Load environment variables from .env file for API keys
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        # Don't use servicemanager here as it might not be initialized yet
except ImportError:
    pass  # python-dotenv not available
except Exception:
    pass  # Ignore errors during environment loading


class MedealisService(win32serviceutil.ServiceFramework):
    """Windows Service für Medealis Streamlit Application."""

    # Service-Informationen
    _svc_name_ = "MedealisWarehouse"
    _svc_display_name_ = "Medealis Warehouse Management System"
    _svc_description_ = (
        "Streamlit-basiertes Warehouse Management System für Medizinprodukte. "
        "Admin App: http://localhost:8501 | User App: http://localhost:8502"
    )

    # Explizit den Python-Interpreter aus der .venv verwenden
    _exe_name_ = str(Path(__file__).parent.parent / ".venv" / "pythonservice.exe")
    _exe_args_ = '"{}"'.format(str(Path(__file__).resolve()))

    def __init__(self, args):
        """Initialisiert den Service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        self.admin_process = None
        self.user_process = None

        # Pfade konfigurieren
        self.project_root = Path(__file__).parent.parent
        self.python_exe = sys.executable
        self.admin_app = (
            self.project_root
            / "src"
            / "warehouse"
            / "presentation"
            / "admin"
            / "main_admin_app.py"
        )
        self.user_app = (
            self.project_root
            / "src"
            / "warehouse"
            / "presentation"
            / "user"
            / "main_user_app.py"
        )

    def SvcStop(self):
        """Stoppt den Service."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False

        # Admin-Prozess beenden
        if self.admin_process:
            try:
                self.admin_process.terminate()
                self.admin_process.wait(timeout=10)
            except Exception as e:
                servicemanager.LogErrorMsg(f"Fehler beim Beenden (Admin): {e}")

        # User-Prozess beenden
        if self.user_process:
            try:
                self.user_process.terminate()
                self.user_process.wait(timeout=10)
            except Exception as e:
                servicemanager.LogErrorMsg(f"Fehler beim Beenden (User): {e}")

    def SvcDoRun(self):
        """Startet den Service."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        self.main()

    def main(self):
        """Hauptfunktion - startet und überwacht beide Streamlit-Apps."""
        try:
            # Warte bis Ports frei sind
            self.wait_for_port_available(8501, timeout=30)
            self.wait_for_port_available(8502, timeout=30)

            # Prepare environment variables (including API keys from .env)
            env = os.environ.copy()

            # Log API key availability
            if env.get('ANTHROPIC_API_KEY'):
                servicemanager.LogInfoMsg("ANTHROPIC_API_KEY is set - Claude features enabled")
            else:
                servicemanager.LogWarningMsg("ANTHROPIC_API_KEY not set - Claude features will be unavailable")

            # Admin App Kommando (Port 8501)
            admin_cmd = [
                self.python_exe,
                "-m",
                "streamlit",
                "run",
                str(self.admin_app),
                "--server.port=8501",
                "--server.address=0.0.0.0",  # Erreichbar im Netzwerk
                "--server.headless=true",
                "--server.runOnSave=false",
                "--browser.gatherUsageStats=false",
            ]

            # User App Kommando (Port 8502)
            user_cmd = [
                self.python_exe,
                "-m",
                "streamlit",
                "run",
                str(self.user_app),
                "--server.port=8502",
                "--server.address=0.0.0.0",  # Erreichbar im Netzwerk
                "--server.headless=true",
                "--server.runOnSave=false",
                "--browser.gatherUsageStats=false",
            ]

            servicemanager.LogInfoMsg(f"Starte Admin App: {' '.join(admin_cmd)}")

            # Admin App starten (mit Umgebungsvariablen inkl. API Keys)
            self.admin_process = subprocess.Popen(
                admin_cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env,  # Pass environment variables including API keys
            )

            servicemanager.LogInfoMsg("Admin App erfolgreich gestartet")

            servicemanager.LogInfoMsg(f"Starte User App: {' '.join(user_cmd)}")

            # User App starten (mit Umgebungsvariablen inkl. API Keys)
            self.user_process = subprocess.Popen(
                user_cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env,  # Pass environment variables including API keys
            )

            servicemanager.LogInfoMsg("User App erfolgreich gestartet")

            # Überwache beide Prozesse
            while self.is_running:
                # Prüfe ob Admin App noch läuft
                if self.admin_process.poll() is not None:
                    # Prozess ist beendet - neu starten
                    servicemanager.LogWarningMsg(
                        "Admin App beendet - starte neu..."
                    )
                    self.admin_process = subprocess.Popen(
                        admin_cmd,
                        cwd=str(self.project_root),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        env=env,
                    )

                # Prüfe ob User App noch läuft
                if self.user_process.poll() is not None:
                    # Prozess ist beendet - neu starten
                    servicemanager.LogWarningMsg(
                        "User App beendet - starte neu..."
                    )
                    self.user_process = subprocess.Popen(
                        user_cmd,
                        cwd=str(self.project_root),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        env=env,
                    )

                # Warte 5 Sekunden oder bis Stop-Event
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop wurde angefordert
                    break

        except Exception as e:
            servicemanager.LogErrorMsg(f"Service-Fehler: {e}")
            raise

    def wait_for_port_available(self, port: int, timeout: int = 30):
        """
        Wartet bis ein Port verfügbar ist.

        Args:
            port: Port-Nummer
            timeout: Maximale Wartezeit in Sekunden
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Versuche Port zu binden
                sock.bind(("", port))
                sock.close()
                return True
            except OSError:
                # Port ist besetzt
                sock.close()
                time.sleep(1)

        raise TimeoutError(f"Port {port} ist nach {timeout}s immer noch besetzt")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Service wurde ohne Parameter gestartet - normaler Service-Modus
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MedealisService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Kommandozeilen-Parameter (install, start, stop, remove)
        win32serviceutil.HandleCommandLine(MedealisService)
