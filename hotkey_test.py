from functools import partial
from maya import OpenMayaUI as OpenMayaUI, cmds as cmds

# try:
from PySide2.QtCore import QEvent, QCoreApplication
from PySide2.QtGui import QKeyEvent, Qt, QKeySequence
from PySide2.QtWidgets import QWidget, QShortcut
from shiboken2 import wrapInstance
# except ImportError:
#     from PySide.QtCore import QWidget,QEvent, QCoreApplication
#     from PySide.QtGui import QKeyEvent, Qt, QKeySequence
#     from shiboken import wrapInstance


def get_main_maya_window():
    mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
    return mayaMainWindow


def shortcut_activated(shortcut):
    shortcut.setEnabled(0)
    e = QKeyEvent(QEvent.KeyPress, Qt.Key_H, Qt.CTRL)
    QCoreApplication.postEvent(get_main_maya_window(), e)
    cmds.evalDeferred(partial(shortcut.setEnabled, 1))
    print "tralalalal1"


def init_shortcut():
    shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_H), get_main_maya_window())
    shortcut.setContext(Qt.ApplicationShortcut)
    shortcut.activated.connect(partial(shortcut_activated, shortcut))
    #shortcut.activated.connect(lambda: QMessageBox.information(self,'Message', 'Ctrl + M initiated'))

init_shortcut()