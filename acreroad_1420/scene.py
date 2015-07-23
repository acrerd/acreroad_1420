from PyQt4 import QtGui,QtCore
import sys

class MyFirstScene(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.scene=QtGui.QGraphicsScene(self)
        self.scene.addText("Hello, world!")
        self.view = QtGui.QGraphicsView(self.scene, self)
        self.show()

    def initGUI(self):
        pass

    def paintEvent(self):
        pass


if __name__=="__main__":
    app=QtGui.QApplication(sys.argv)
    firstScene = MyFirstScene()
    sys.exit(app.exec_())
