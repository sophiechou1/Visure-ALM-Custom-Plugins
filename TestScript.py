# ======================= CONFIGURATION ===========================

# ================================================================

import re
import Visure

def Visure_beforeCreateBaseline(bl, lBaselineID):
    try:
        bl.Trace_INFO("==== Before Baseline Script Success ====")

    except Exception as e:
        bl.Trace_ERROR(f"Script failed: {e}")