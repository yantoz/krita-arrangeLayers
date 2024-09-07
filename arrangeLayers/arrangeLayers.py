import krita

from functools import cmp_to_key
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

def moveBy(layer, dx, dy):
    dx = round(dx)
    dy = round(dy)
    pos = layer.position()
    layer.move(pos.x()+dx, pos.y()+dy)
    for child in layer.childNodes():
        moveBy(child, dx, dy)

def moveTo(layer, x, y):
    pos = layer.bounds()
    moveBy(layer, x-pos.x(), y-pos.y())
    
def testEnable():
    
    enableA = False
    enableD = False
    
    doc = Application.activeDocument()
    if doc is None:
        return (enableA, enableD, None, None)
        
    topLevelLayers = doc.topLevelNodes()
    activeLayer = doc.activeNode()
    
    selectedLayers = Krita.instance().activeWindow().activeView().selectedNodes()
    processLayers = []
        
    for layer in selectedLayers:
        if layer in topLevelLayers and layer != activeLayer:
            processLayers.append(layer)

    activeLayerExists = activeLayer is not None

    enableA = activeLayerExists and len(processLayers) > 0
    enableD = activeLayerExists and len(processLayers) > 1
    
    return (enableA, enableD, activeLayer, processLayers)
            
def processArrange(alignH, alignV): # 0: NOP, 1: L/T, 2: C/C, 3: R/B, 4: D/D

    def processAlign(layer, refBounds):
        bounds = layer.bounds()
        if alignH == 1:
            moveTo(layer, refBounds.x(), bounds.y())
        elif alignH == 2:
            moveTo(layer, refBounds.x()+(refBounds.width()-bounds.width())/2, bounds.y())
        elif alignH == 3:
            moveTo(layer, refBounds.x()+refBounds.width()-bounds.width(), bounds.y())
        elif alignV == 1:
            moveTo(layer, bounds.x(), refBounds.y())
        elif alignV == 2:
            moveTo(layer, bounds.x(), refBounds.y()+(refBounds.height()-bounds.height())/2)
        elif alignV == 3:
            moveTo(layer, bounds.x(), refBounds.y()+refBounds.height()-bounds.height())

    enableA, enableD, activeLayer, processLayers = testEnable()
            
    if alignH == 4:
        if not enableD:
            return
        layers = [activeLayer] + processLayers
        layers = sorted(layers, key=cmp_to_key(lambda item1, item2: item1.bounds().x()-item2.bounds().x()))
        width = 0
        for layer in layers:
            width += layer.bounds().width()
        left = layers[0].bounds().x()
        right = left
        for layer in layers:
            r = layer.bounds().x() + layer.bounds().width() - 1
            if r > right:
                right = r
        span = right - left + 1
        gap = (span - width) / len(processLayers)
        x = layers[0].bounds().x() + layers[0].bounds().width() - 1 + gap + 1 
        for layer in layers[1:]:
            moveTo(layer, x, layer.bounds().y())
            x += layer.bounds().width() - 1 + gap + 1                
    elif alignV == 4:
        if not enableD:
            return
        layers = [activeLayer] + processLayers
        layers = sorted(layers, key=cmp_to_key(lambda item1, item2: item1.bounds().y()-item2.bounds().y()))
        height = 0
        for layer in layers:
            height += layer.bounds().height()
        top = layers[0].bounds().y()
        bottom = top
        for layer in layers:
            b = layer.bounds().y() + layer.bounds().height() - 1
            if b > bottom:
                bottom = b
        span = bottom - top + 1
        gap = (span - height) / len(processLayers)
        y = layers[0].bounds().y() + layers[0].bounds().height() - 1 + gap + 1 
        for layer in layers[1:]:
            moveTo(layer, layer.bounds().x(), y)
            y += layer.bounds().height() - 1 + gap + 1                
    elif enableA:
        # align selected layers to active layer
        activeBounds = activeLayer.bounds()
        for layer in processLayers:
            processAlign(layer, activeBounds)
    else:
        # align active layer to page
        pageBounds = Application.activeDocument().bounds()
        processAlign(activeLayer, pageBounds)
 
    Application.activeDocument().refreshProjection()

def e_alignLeft():
    processArrange(1, 0)
    
def e_alignCenter():
    processArrange(2, 0)

def e_alignRight():
    processArrange(3, 0)
    
def e_alignTop():
    processArrange(0, 1)
    
def e_alignMiddle():
    processArrange(0, 2)

def e_alignBottom():
    processArrange(0, 3)
    
def e_distributeH():
    processArrange(4, 0)
    
def e_distributeV():
    processArrange(0, 4)

class arrangeLayersExtension(krita.Extension):
 
    def __init__(self, parent):
        super().__init__(parent)
        self.actions = []
        self.menu = None

    def setup(self):
        pass
 
    def createActions(self, window):
    
        action = window.createAction("separator0", "", "layer")
        action.setSeparator(True)
        
        action = window.createAction("arrangeLayers", "Arrange Layers", "layer")
        menu = krita.QtWidgets.QMenu("arrangeLayers", window.qwindow())
        action.setMenu(menu)

        self.menu = menu

        actions = [
            ["arrangeLayersLeft", "Align Left Edges", e_alignLeft],
            ["arrangeLayersCenter", "Align Horizontal Centers", e_alignCenter],
            ["arrangeLayersRight", "Align Right Edges", e_alignRight],
            None,
            ["arrangeLayersTop", "Align Top Edges", e_alignTop],
            ["arrangeLayersMiddle", "Align Vertical Centers", e_alignMiddle],
            ["arrangeLayersBottom", "Align Bottom Edges", e_alignBottom],
            None,
            ["arrangeLayersDistH", "Distribute Horizontally", e_distributeH],
            ["arrangeLayersDistV", "Distribute Vertically", e_distributeV],
        ]

        self.actions = []

        for i, action in enumerate(actions):
            if action:
                subaction = window.createAction(action[0], action[1], "layer/arrangeLayers")
                subaction.triggered.connect(action[2])
                self.actions.append(subaction)
            else:
                subaction = window.createAction("separator{}".format(i+1), "", "layer/arrangeLayers")
                subaction.setSeparator(True)

        self.setEnable(False, False)

    def setEnable(self, enableA, enableD):
        if not self.actions:
            return
        if self.menu:
            self.menu.setEnabled(enableA or enableD)
        for i in range(6):
            try:
                self.actions[i].setEnabled(enableA)
            except:
                pass
        for i in range(2):
            try:
                self.actions[i+6].setEnabled(enableD)
            except:
                pass

class ArrangeLayersDocker(krita.DockWidget):

    def __init__(self):
        super().__init__()
        self.buttons = []
        self.setWindowTitle("Arrange Layers")
        self.__createDocker()

    def __createDocker(self):

        arrangements = [
            ["object-align-horizontal-left-calligra", "Align Left Edges", e_alignLeft],
            ["object-align-horizontal-center-calligra", "Align Horizontal Centers", e_alignCenter],
            ["object-align-horizontal-right-calligra", "Align Right Edges", e_alignRight],
            None,
            ["object-align-vertical-top-calligra", "Align Top Edges", e_alignTop],
            ["object-align-vertical-center-calligra", "Align Vertical Centers", e_alignMiddle],
            ["object-align-vertical-bottom-calligra", "Align Bottom Edges", e_alignBottom],
            None,
            ["distribute-horizontal", "Distribute Horizontally", e_distributeH],
            ["distribute-vertical", "Distribute Vertically", e_distributeV],        
        ]
    
        arrangeLayout = QHBoxLayout()
        arrangeLayout.setSpacing(2)
        arrangeLayout.setAlignment(krita.Qt.AlignLeft | krita.Qt.AlignTop)

        self.buttons = []
        
        for arrangement in arrangements:
            if arrangement:
                button = QPushButton()
                button.setIcon(Krita.instance().icon(arrangement[0]))
                button.setToolTip(arrangement[1])
                button.clicked.connect(arrangement[2])
                arrangeLayout.addWidget(button)
                self.buttons.append(button)
            else:
                arrangeLayout.addWidget(QLabel("  "))
            
        widget = QWidget()
        widget.setLayout(arrangeLayout)
        widget.resize(0,0)
    
        self.setWidget(widget)
        self.setMinimumHeight(45)
        self.resize(0,0)

        global docker
        docker = self

    def setEnable(self, enableA, enableD):
        if not self.buttons:
            return
        for i in range(6):
            try:
                self.buttons[i].setEnabled(enableA)
            except:
                pass
        for i in range(2):
            try:
                self.buttons[i+6].setEnabled(enableD)
            except:
                pass

    def canvasChanged(self, canvas):
        pass

KI = Krita.instance()
extension = arrangeLayersExtension(KI)
docker = None

KI.addExtension(extension)
KI.addDockWidgetFactory(krita.DockWidgetFactory("Arrange Layers", krita.DockWidgetFactoryBase.DockRight, ArrangeLayersDocker))

def layerChanged():
    enableA, enableD, activeLayer, _ = testEnable()
    enableA = enableA or (activeLayer is not None)
    extension.setEnable(enableA, enableD)
    if docker:
        docker.setEnable(enableA, enableD)

def windowCreated():
    qwin = Krita.instance().activeWindow().qwindow()
    layerBox = qwin.findChild(krita.QtWidgets.QDockWidget, "KisLayerBox")
    layerList = layerBox.findChild(krita.QtWidgets.QTreeView,"listLayers")
    layerList.selectionModel().selectionChanged.connect(layerChanged)

KI.notifier().windowCreated.connect(windowCreated)
