import sys
sys.path.append('.')
from logic.mission_controller import MissionController
import os
mc = MissionController(os.path.normpath(os.path.join(os.path.expanduser("~"), "CancerDetectionDashboard")))
mc.restore_session()
df = mc.data_manager.uploaded_df
if df is not None:
    print("Columns:", df.columns.tolist())
    print("Head:\n", df.head(5))
else:
    print("No DF")
