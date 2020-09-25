import platform
import time
from datetime import datetime

start_time = datetime.now()
time.sleep(1)
end_time = datetime.now()
print('{}'.format((end_time - start_time).seconds))
