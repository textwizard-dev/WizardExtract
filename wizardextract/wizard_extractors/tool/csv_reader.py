# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

class CsvReader:
    def __init__(self):
        pass

    @staticmethod
    def csv_reader(csv) -> str:
        """
        Extracts text from a CSV file.

        Args:
            csv (io.BytesIO): Binary stream containing CSV data.

        Returns:
            str: Decoded CSV content.

        Raises:
            UnicodeDecodeError: If the input CSV cannot be decoded.
        """
        return csv.getvalue().decode()
