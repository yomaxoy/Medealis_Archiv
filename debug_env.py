#!/usr/bin/env python
"""Debug environment configuration."""

import os
from warehouse.shared.config.environment_config import env_config

print("=== ENVIRONMENT CONFIG DEBUG ===\n")

# Check raw .env values
print("Raw environment variables:")
print(f"  USE_SERVER_STORAGE_DB: {os.getenv('USE_SERVER_STORAGE_DB')}")
print(f"  USE_SERVER_STORAGE_DOCUMENTS: {os.getenv('USE_SERVER_STORAGE_DOCUMENTS')}")
print(f"  USE_SERVER_STORAGE (legacy): {os.getenv('USE_SERVER_STORAGE')}")
print()

# Check parsed config
print("Parsed EnvironmentConfig:")
print(f"  is_server_storage_db_enabled(): {env_config.is_server_storage_db_enabled()}")
print(f"  is_server_storage_documents_enabled(): {env_config.is_server_storage_documents_enabled()}")
print(f"  is_server_storage_enabled() [legacy]: {env_config.is_server_storage_enabled()}")
print(f"  get_db_storage_mode(): {env_config.get_db_storage_mode()}")
print(f"  get_documents_storage_mode(): {env_config.get_documents_storage_mode()}")
print()

# Full status
print("Full config status:")
status = env_config.get_config_status()
for key, value in status.items():
    print(f"  {key}: {value}")
