from PySide2 import QtCore, QtWidgets
import shiboken2

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as mui


class MyDialog(QtWidgets.QDialog):
    def keyPressEvent(self, e):
        print "Hahahahhahaha"
        #on escape delete all created nodes, enable viewport and exit application

    def __init__(self, parent, **kwargs):
        super(MyDialog, self).__init__(parent, **kwargs)
        
        self.setObjectName("MyWindow")
        self.resize(800, 600)
        self.setWindowTitle("PyQt ModelPanel Test")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0,0,0,0)

        # need to set a name so it can be referenced by maya node path
        self.verticalLayout.setObjectName("mainLayout")
        
        # First use SIP to unwrap the layout into a pointer
        # Then get the full path to the UI in maya as a string
        layout = mui.MQtUtil.fullName(long(shiboken2.getCppPointer(self.verticalLayout)[0]))
        cmds.setParent(layout)

        paneLayoutName = cmds.paneLayout()
        
        # Find a pointer to the paneLayout that we just created
        ptr = mui.MQtUtil.findControl(paneLayoutName)
        
        # Wrap the pointer into a python QObject
        self.paneLayout = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

        self.cameraName = cmds.camera()[0]
        self.modelPanelName = cmds.modelPanel("customModelPanel", label="ModelPanel Test", cam=self.cameraName)
        
        # Find a pointer to the modelPanel that we just created
        ptr = mui.MQtUtil.findControl(self.modelPanelName)
        
        # Wrap the pointer into a python QObject
        self.modelPanel = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

        # add our QObject reference to the paneLayout to our layout
        self.verticalLayout.addWidget(self.paneLayout)

    def showEvent(self, event):
        super(MyDialog, self).showEvent(event)

        # maya can lag in how it repaints UI. Force it to repaint
        # when we show the window.
        self.modelPanel.repaint()
                    

def show():
    # get a pointer to the maya main window
    ptr = mui.MQtUtil.mainWindow()
    # use sip to wrap the pointer into a QObject
    win = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
    d = MyDialog(win)
    d.show()

    return d

#disable main viewport
mel.eval("paneLayout -e -manage false $gMainPane")
dialog = show()
