import os

import together
import time
if os.path.exists(".fzx2-persistent"):
    print("writing to persistent_data")
    with open(".fzx2-persistent/test.txt", "w") as f:
        f.write("test")
        f.flush()