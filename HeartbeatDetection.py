
import os
os.environ['QT_API'] = 'PySide6' # For qasync to know which binding is being used
os.environ['QT_LOGGING_RULES'] = 'qt.pointer.dispatch=false' # Disable pointer logging

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from Controller import Controller

if __name__ == "__main__":

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    controller = Controller()

    loop.run_until_complete(controller.main())
