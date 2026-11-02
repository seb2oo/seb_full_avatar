import os
if os.getenv("RUN_ALT_APP") == "1":
    import log_retrieve
else:
    # import test_volume_access
    # import app_original_from_HF
    import chat
