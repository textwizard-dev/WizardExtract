# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import json
from wizardextract.utils.errors.errors import JsonFileError


class JsonReader:
    def __init__(self):
        pass

    @staticmethod
    def json_reader(json_data: io.BytesIO) -> str:
        """
        Extracts and formats JSON content.

        Args:
            json_data (io.BytesIO): Binary stream containing JSON data.

        Returns:
            str: Pretty-printed JSON content.

        Raises:
            JsonFileError: If the JSON content cannot be decoded or parsed.
        """
        try:
            # Decode binary stream into a string
            content = json_data.getvalue().decode()

            # Parse JSON and reformat it for readability
            data = json.loads(content)
            return json.dumps(data, indent=4)

        except UnicodeDecodeError as e:
            raise JsonFileError(f"Error decoding JSON content: {e}")
        except json.JSONDecodeError as e:
            raise JsonFileError(f"Invalid JSON format: {e}")
