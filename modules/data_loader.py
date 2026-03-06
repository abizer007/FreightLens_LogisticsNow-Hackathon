"""
Load LR, POD, and Invoice CSV datasets from Streamlit file uploaders.
"""

from typing import Optional, Tuple

import pandas as pd


def load_lr_pod_invoice(
    lr_file: Optional[object],
    pod_file: Optional[object],
    invoice_file: Optional[object],
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load three CSV datasets from file-like upload objects.
    Returns (lr_df, pod_df, inv_df). Any missing file returns None for that DataFrame.
    """
    lr_df: Optional[pd.DataFrame] = None
    pod_df: Optional[pd.DataFrame] = None
    inv_df: Optional[pd.DataFrame] = None

    if lr_file is not None:
        lr_df = pd.read_csv(lr_file)
    if pod_file is not None:
        pod_df = pd.read_csv(pod_file)
    if invoice_file is not None:
        inv_df = pd.read_csv(invoice_file)

    return lr_df, pod_df, inv_df
