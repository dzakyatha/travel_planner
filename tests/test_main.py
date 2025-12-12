# Test for main app entry point
import pytest
from unittest.mock import patch

def test_main_entry_point():
    with patch('main.uvicorn.run') as mock_run:
        from main import main
        main()
        mock_run.assert_called_once()