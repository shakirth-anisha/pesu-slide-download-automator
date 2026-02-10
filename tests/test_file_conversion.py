import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_conversion import get_batches, convert_pptx_to_pdf


def test_get_batches_single_batch(temp_dir):
    for i in range(2):
        pptx_path = os.path.join(temp_dir, f"slide{i}.pptx")
        with open(pptx_path, 'w') as f:
            f.write("x")

    batches = list(get_batches(temp_dir, batch_size=3))

    assert len(batches) == 1
    assert len(batches[0]) == 2


def test_convert_pptx_to_pdf_missing_folder(temp_dir):
    missing = os.path.join(temp_dir, "missing")
    with patch('builtins.print'):
        convert_pptx_to_pdf(missing)
