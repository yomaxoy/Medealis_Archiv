"""
SharePoint Graph Client - Microsoft Graph API Implementation

Verwendet Microsoft Graph API statt SharePoint REST API.
Einfacher und moderner als SharePoint App Principal Registration.
"""

import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time

from ....shared.config.environment_config import env_config

logger = logging.getLogger(__name__)


@dataclass
class SharePointUploadResult:
    """Ergebnis eines SharePoint-Uploads."""
    success: bool
    sharepoint_path: str = ""
    file_url: str = ""
    file_size: int = 0
    error: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class SharePointGraphClient:
    """
    SharePoint Client über Microsoft Graph API.

    Verwendet Azure AD OAuth und Microsoft Graph API.
    Einfacher als SharePoint App Principal Registration.
    """

    def __init__(self):
        self.logger = logger

        # SharePoint Konfiguration
        sp_config = env_config.get_sharepoint_config()
        self.site_url = sp_config['site_url']
        self.client_id = sp_config['client_id']
        self.client_secret = sp_config['client_secret']
        self.tenant_id = sp_config['tenant_id']

        # Graph API Base URL
        self.graph_api_base = "https://graph.microsoft.com/v1.0"

        # Token Cache
        self._access_token = None
        self._token_expires_at = 0

        # Site ID Cache
        self._site_id = None

        # Configuration Status
        self._is_configured = self._check_configuration()

    def _check_configuration(self) -> bool:
        """Prüft ob alle erforderlichen Konfigurationen vorhanden sind."""
        return all([
            self.site_url,
            self.client_id,
            self.client_secret,
            self.tenant_id
        ])

    def _get_access_token(self) -> str:
        """
        Holt Azure AD Access Token für Microsoft Graph.

        Returns:
            Access Token String

        Raises:
            Exception: Wenn Token-Abruf fehlschlägt
        """
        # Prüfe ob cached token noch gültig ist (mit 5 Min Puffer)
        if self._access_token and time.time() < (self._token_expires_at - 300):
            return self._access_token

        try:
            # Azure AD v2 Endpoint
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

            # Scope für Microsoft Graph
            scope = "https://graph.microsoft.com/.default"

            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': scope
            }

            self.logger.debug(f"Requesting Microsoft Graph token")

            response = requests.post(token_url, data=payload, timeout=30)

            if response.status_code != 200:
                error_msg = f"Token request failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

            token_data = response.json()
            self._access_token = token_data['access_token']

            # Berechne Ablaufzeit
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires_at = time.time() + expires_in

            self.logger.debug(f"Microsoft Graph token acquired, expires in {expires_in} seconds")

            return self._access_token

        except Exception as e:
            self.logger.error(f"Failed to acquire Graph API token: {e}")
            raise

    def _get_request_headers(self) -> Dict[str, str]:
        """
        Gibt Request-Headers mit Access Token zurück.

        Returns:
            Dictionary mit Headers
        """
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _get_site_id(self) -> str:
        """
        Holt SharePoint Site ID über Graph API.

        Returns:
            Site ID String

        Raises:
            Exception: Wenn Site ID nicht abgerufen werden kann
        """
        if self._site_id:
            return self._site_id

        try:
            # Extrahiere Hostname und Site Path aus URL
            # Format: https://medealis.sharepoint.com
            site_url_parts = self.site_url.replace('https://', '').replace('http://', '').split('/')
            hostname = site_url_parts[0]

            # Hole Root Site
            url = f"{self.graph_api_base}/sites/{hostname}:/"
            headers = self._get_request_headers()

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                site_data = response.json()
                self._site_id = site_data['id']
                self.logger.debug(f"Site ID retrieved: {self._site_id}")
                return self._site_id
            else:
                error_msg = f"Failed to get site ID: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            self.logger.error(f"Failed to retrieve site ID: {e}")
            raise

    def is_available(self) -> bool:
        """Prüft ob SharePoint Client verfügbar und konfiguriert ist."""
        return self._is_configured

    def test_connection(self) -> Dict[str, Any]:
        """
        Testet SharePoint-Verbindung via Graph API.

        Returns:
            Dictionary mit Verbindungstest-Ergebnissen
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "SharePoint client not properly configured",
                "configured": self._is_configured
            }

        try:
            # Teste Verbindung durch Abruf der Site-Informationen
            site_id = self._get_site_id()

            url = f"{self.graph_api_base}/sites/{site_id}"
            headers = self._get_request_headers()

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                site_data = response.json()

                return {
                    "success": True,
                    "site_title": site_data.get('displayName', 'N/A'),
                    "site_url": site_data.get('webUrl', self.site_url),
                    "site_id": site_id,
                    "connected_at": datetime.now().isoformat(),
                    "authentication": "Microsoft Graph API"
                }
            else:
                error_msg = f"Connection test failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        except Exception as e:
            error_msg = f"SharePoint connection test failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def upload_document(
        self,
        document_data: bytes,
        sharepoint_path: str,
        filename: str,
        overwrite: bool = True
    ) -> SharePointUploadResult:
        """
        Lädt Dokument zu SharePoint hoch via Graph API.

        Args:
            document_data: Binärdaten des Dokuments
            sharepoint_path: SharePoint-Pfad (z.B. "/Supplier/...")
            filename: Dateiname
            overwrite: Ob existierende Dateien überschrieben werden sollen

        Returns:
            SharePointUploadResult mit Upload-Informationen
        """
        if not self.is_available():
            return SharePointUploadResult(
                success=False,
                error="SharePoint client not available"
            )

        try:
            self.logger.info(f"Uploading document to SharePoint via Graph: {sharepoint_path}/{filename}")

            # Bereinige Pfad (Graph API verwendet relativen Pfad ohne /Shared Documents)
            clean_path = sharepoint_path.replace("\\", "/").strip("/")

            # Entferne "Shared Documents" falls vorhanden (wird durch /drive/root: ersetzt)
            if clean_path.startswith("Shared Documents/"):
                clean_path = clean_path[len("Shared Documents/"):]
            elif clean_path == "Shared Documents":
                clean_path = ""

            # Hole Site ID
            site_id = self._get_site_id()

            # Erstelle Ordnerstruktur falls nötig
            if clean_path:
                folder_creation_result = self._ensure_folder_exists(site_id, clean_path)
                if not folder_creation_result["success"]:
                    return SharePointUploadResult(
                        success=False,
                        error=f"Failed to create folder structure: {folder_creation_result['error']}"
                    )

            # Upload Datei über Graph API
            # Für kleine Dateien (<4MB): PUT Request
            # Für große Dateien: Upload Session (TODO)

            if len(document_data) < 4 * 1024 * 1024:  # 4 MB
                # Einfacher Upload für kleine Dateien
                path_part = f":/{clean_path}/{filename}:" if clean_path else f":/{filename}:"
                upload_url = f"{self.graph_api_base}/sites/{site_id}/drive/root{path_part}/content"

                headers = self._get_request_headers()
                headers['Content-Type'] = 'application/octet-stream'

                response = requests.put(upload_url, headers=headers, data=document_data, timeout=120)

                if response.status_code in [200, 201]:
                    file_data = response.json()

                    # Erstelle Erfolgs-Result
                    result = SharePointUploadResult(
                        success=True,
                        sharepoint_path=f"{clean_path}/{filename}" if clean_path else filename,
                        file_url=file_data.get('webUrl', ''),
                        file_size=len(document_data)
                    )

                    # Füge Metadaten hinzu
                    result.metadata.update({
                        "upload_time": datetime.now().isoformat(),
                        "file_name": filename,
                        "folder_path": clean_path,
                        "file_size_mb": round(len(document_data) / 1024 / 1024, 2),
                        "file_id": file_data.get('id', ''),
                        "authentication": "Microsoft Graph API"
                    })

                    self.logger.info(f"Document uploaded successfully: {result.file_url}")
                    return result
                else:
                    error_msg = f"Upload failed: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    return SharePointUploadResult(
                        success=False,
                        error=error_msg,
                        sharepoint_path=sharepoint_path
                    )
            else:
                # TODO: Upload Session für große Dateien
                return SharePointUploadResult(
                    success=False,
                    error="Files larger than 4MB not yet supported (requires upload session)",
                    sharepoint_path=sharepoint_path
                )

        except Exception as e:
            error_msg = f"SharePoint upload failed: {str(e)}"
            self.logger.error(error_msg)
            return SharePointUploadResult(
                success=False,
                error=error_msg,
                sharepoint_path=sharepoint_path
            )

    def _ensure_folder_exists(self, site_id: str, folder_path: str) -> Dict[str, Any]:
        """
        Stellt sicher dass Ordnerstruktur in SharePoint existiert.

        Args:
            site_id: SharePoint Site ID
            folder_path: Relativer Ordnerpfad (ohne /Shared Documents)

        Returns:
            Dictionary mit Erstellungs-Ergebnis
        """
        try:
            # Teile Pfad in Komponenten auf
            path_parts = [part for part in folder_path.split("/") if part]

            created_folders = []
            warnings = []
            current_path = ""

            headers = self._get_request_headers()

            # Erstelle jeden Ordner in der Hierarchie
            for folder_name in path_parts:
                parent_path = current_path
                current_path = f"{current_path}/{folder_name}" if current_path else folder_name

                try:
                    # Prüfe ob Ordner existiert
                    check_url = f"{self.graph_api_base}/sites/{site_id}/drive/root:/{current_path}"
                    response = requests.get(check_url, headers=headers, timeout=30)

                    if response.status_code == 200:
                        # Ordner existiert bereits
                        continue
                    else:
                        # Ordner existiert nicht, erstelle ihn
                        parent_ref = f"/sites/{site_id}/drive/root:/{parent_path}" if parent_path else f"/sites/{site_id}/drive/root"

                        create_url = f"{self.graph_api_base}/sites/{site_id}/drive/root" + (f":/{parent_path}:" if parent_path else "") + "/children"

                        create_data = {
                            "name": folder_name,
                            "folder": {},
                            "@microsoft.graph.conflictBehavior": "fail"
                        }

                        create_response = requests.post(
                            create_url,
                            headers=headers,
                            json=create_data,
                            timeout=30
                        )

                        if create_response.status_code in [200, 201]:
                            created_folders.append(current_path)
                            self.logger.debug(f"Created SharePoint folder: {current_path}")
                        elif create_response.status_code == 409:
                            # Folder already exists (conflict)
                            self.logger.debug(f"Folder already exists: {current_path}")
                        else:
                            warning_msg = f"Could not create folder {current_path}: {create_response.text}"
                            warnings.append(warning_msg)
                            self.logger.warning(warning_msg)

                except Exception as e:
                    warning_msg = f"Error checking/creating folder {current_path}: {str(e)}"
                    warnings.append(warning_msg)
                    self.logger.warning(warning_msg)

            return {
                "success": True,
                "created_folders": created_folders,
                "warnings": warnings
            }

        except Exception as e:
            error_msg = f"Error ensuring folder structure: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "warnings": []
            }

    def list_files(self, sharepoint_path: str) -> List[Dict[str, Any]]:
        """
        Listet Dateien in SharePoint-Ordner auf.

        Args:
            sharepoint_path: SharePoint-Ordnerpfad

        Returns:
            Liste von Datei-Informationen
        """
        if not self.is_available():
            self.logger.warning("SharePoint client not available for file listing")
            return []

        try:
            # Bereinige Pfad
            clean_path = sharepoint_path.replace("\\", "/").strip("/")

            # Entferne "Shared Documents" falls vorhanden
            if clean_path.startswith("Shared Documents/"):
                clean_path = clean_path[len("Shared Documents/"):]
            elif clean_path == "Shared Documents":
                clean_path = ""

            # Hole Site ID
            site_id = self._get_site_id()

            # Hole Ordner-Inhalt
            if clean_path:
                files_url = f"{self.graph_api_base}/sites/{site_id}/drive/root:/{clean_path}:/children"
            else:
                files_url = f"{self.graph_api_base}/sites/{site_id}/drive/root/children"

            headers = self._get_request_headers()

            response = requests.get(files_url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                items = data.get('value', [])

                # Filtere nur Dateien (keine Ordner)
                file_list = []
                for item in items:
                    if 'file' in item:  # Ist eine Datei
                        file_info = {
                            "name": item.get('name', ''),
                            "url": item.get('webUrl', ''),
                            "size": item.get('size', 0),
                            "modified": item.get('lastModifiedDateTime', ''),
                            "created": item.get('createdDateTime', '')
                        }
                        file_list.append(file_info)

                self.logger.info(f"Listed {len(file_list)} files from {sharepoint_path}")
                return file_list
            else:
                error_msg = f"Error listing files: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return []

        except Exception as e:
            error_msg = f"Error listing SharePoint files: {str(e)}"
            self.logger.error(error_msg)
            return []

    def download_document(
        self,
        sharepoint_path: str,
        filename: str
    ) -> Optional[bytes]:
        """
        Lädt ein Dokument von SharePoint herunter.

        Args:
            sharepoint_path: SharePoint-Pfad zum Ordner (z.B. "QM_System_Neu/.../Produktionsunterlagen/...")
            filename: Dateiname des zu ladenden Dokuments

        Returns:
            Document bytes oder None bei Fehler
        """
        if not self.is_available():
            self.logger.warning("SharePoint client not available for download")
            return None

        try:
            # Site ID holen
            site_id = self._get_site_id()
            if not site_id:
                self.logger.error("Could not get site ID for download")
                return None

            # Authentifizieren
            token = self._get_access_token()

            # Konstruiere Download-URL
            # Microsoft Graph API: /sites/{site-id}/drive/root:/{path}/{filename}:/content
            # Wichtig: Leerzeichen im Pfad müssen NICHT encoded werden, Graph API macht das automatisch
            file_path = f"{sharepoint_path}/{filename}"
            download_url = f"{self.graph_api_base}/sites/{site_id}/drive/root:/{file_path}:/content"

            self.logger.info(f"Downloading document from SharePoint: {filename}")
            self.logger.debug(f"Download URL path: {file_path}")

            # Download-Request
            headers = {
                "Authorization": f"Bearer {token}",
            }

            response = requests.get(download_url, headers=headers, timeout=120)

            if response.status_code == 200:
                document_bytes = response.content
                self.logger.info(f"Document downloaded successfully: {filename} ({len(document_bytes)} bytes)")
                return document_bytes

            elif response.status_code == 404:
                self.logger.warning(f"Document not found on SharePoint: {filename}")
                return None

            else:
                error_msg = f"Error downloading document: {response.status_code} - {response.text[:200]}"
                self.logger.error(error_msg)
                return None

        except Exception as e:
            error_msg = f"Error downloading document from SharePoint: {str(e)}"
            self.logger.error(error_msg)
            return None

    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Gibt aktuellen Konfigurationsstatus zurück.

        Returns:
            Dictionary mit Konfigurations-Informationen
        """
        return {
            "is_configured": self._is_configured,
            "is_available": self.is_available(),
            "site_url_configured": bool(self.site_url),
            "client_id_configured": bool(self.client_id),
            "client_secret_configured": bool(self.client_secret),
            "tenant_id_configured": bool(self.tenant_id),
            "authentication_type": "Microsoft Graph API",
            "missing_config": [
                var for var, configured in [
                    ("SHAREPOINT_SITE_URL", bool(self.site_url)),
                    ("SHAREPOINT_CLIENT_ID", bool(self.client_id)),
                    ("SHAREPOINT_CLIENT_SECRET", bool(self.client_secret)),
                    ("SHAREPOINT_TENANT_ID", bool(self.tenant_id))
                ] if not configured
            ]
        }


# Global instance - SINGLE POINT OF ACCESS
sharepoint_graph_client = SharePointGraphClient()
