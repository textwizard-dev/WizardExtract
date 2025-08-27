# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
from wizardextract.utils.errors.errors import HtmlFileError


class HtmlReader:
    def __init__(self):
        pass

    @staticmethod
    def html_reader(html: io.BytesIO) -> str:
        """
        Reads and returns the raw HTML content as a string.

        Args:
            html (io.BytesIO): Binary stream containing HTML data.

        Returns:
            str: Decoded HTML content.

        Raises:
            HtmlFileError: If the input HTML cannot be decoded.
        """
        try:
            return html.getvalue().decode()
        except UnicodeDecodeError as e:
            raise HtmlFileError(f"Error decoding HTML content: {e}")

