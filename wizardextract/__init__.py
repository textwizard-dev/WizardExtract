# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from .wizard_extract import WizardExtract
from .wizard_ner.wizard_ner import EntitiesResult, Entity, TokenAnalysis

_wizard = WizardExtract()

extract_text       = _wizard.extract_text
extract_text_azure  = _wizard.extract_text_azure


__all__ = [
    "WizardExtract",
    "extract_text",
    "extract_text_azure",

]
