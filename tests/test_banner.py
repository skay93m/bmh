from __future__ import annotations

import io
from rich.console import Console
from unittest.mock import patch
from bmh.ui.banner import render_banner


def test_render_banner():
    with patch("bmh.ui.banner.console.print") as mock_print:
        render_banner()
        mock_print.assert_called_once()
