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


class MedealisService(win32serviceutil.ServiceFramework):
    """Windows Service für Medealis Streamlit Application."""

    # Service-Informationen
    _svc_name_ = "MedealisWarehouse"
    _svc_display_name_ = "Medealis Warehouse Management System"
    _svc_description_ = (
        "Streamlit-basiertes Warehouse Management System für Medizinprodukte. "
        "Läuft auf http://localhost:8501"
    )

    def __init__(self, args):
        """Initialisiert den Service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        self.streamlit_process = None

        # Pfade konfigurieren
        self.project_root = Path(__file__).parent.parent
        self.python_exe = sys.executable
        self.streamlit_app = (
            self.project_root
            / "src"
            / "warehouse"
            / "presentation"
            / "admin"
            / "main_admin_app.py"
        )

    def SvcStop(self):
        """Stoppt den Service."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False

        # Streamlit-Prozess beenden
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=10)
            except Exception as e:
                servicemanager.LogErrorMsg(f"Fehler beim Beenden: {e}")

    def SvcDoRun(self):
        """Startet den Service."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        self.main()

    def main(self):
        """Hauptfunktion - startet und überwacht Streamlit."""
        try:
            # Warte bis Port 8501 frei ist
            self.wait_for_port_available(8501, timeout=30)

            # Streamlit-Kommando
            cmd = [
                self.python_exe,
                "-m",
                "streamlit",
                "run",
                str(self.streamlit_app),
                "--server.port=8501",
                "--server.address=0.0.0.0",  # Erreichbar im Netzwerk
                "--server.headless=true",
                "--server.runOnSave=false",
                "--browser.gatherUsageStats=false",
            ]

            servicemanager.LogInfoMsg(f"Starte Streamlit: {' '.join(cmd)}")

            # Streamlit starten
            self.streamlit_process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            servicemanager.LogInfoMsg("Streamlit erfolgreich gestartet")

            # Überwache den Prozess
            while self.is_running:
                # Prüfe ob Streamlit noch läuft
                if self.streamlit_process.poll() is not None:
                    # Prozess ist beendet - neu starten
                    servicemanager.LogWarningMsg(
                        "Streamlit-Prozess beendet - starte neu..."
                    )
                    self.streamlit_process = subprocess.Popen(
                        cmd,
                        cwd=str(self.project_root),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW,
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
