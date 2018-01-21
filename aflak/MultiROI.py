import enum

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class RectROI(pg.ROI):
    def __init__(self, size, parent=None):
        super().__init__(pos=[0, 0], size=size, parent=parent)
        self.addScaleHandle([1, 1], [0, 0])
        self.addRotateHandle([0, 0], [0.5, 0.5])


class EllipseROI(pg.EllipseROI):
    def getArrayRegion(self, arr, img=None, axes=(0, 1),
                       returnMappedCoords=False, **kwds):
        """
        Fix a bug in pg.EllipseROI
        https://github.com/pyqtgraph/pyqtgraph/pull/618
        """
        if returnMappedCoords:
            arr, mappedCoords = pg.ROI.getArrayRegion(self, arr, img, axes,
                                                      returnMappedCoords,
                                                      **kwds)
        else:
            arr = pg.ROI.getArrayRegion(self, arr, img, axes,
                                        returnMappedCoords, **kwds)
        if arr is None or arr.shape[axes[0]] == 0 or arr.shape[axes[1]] == 0:
            if returnMappedCoords:
                return arr, mappedCoords
            else:
                return arr
        w = arr.shape[axes[0]]
        h = arr.shape[axes[1]]

        # generate an ellipsoidal mask
        mask = np.fromfunction(lambda x, y: (((x+0.5)/(w/2.)-1)**2 +
                                             ((y+0.5)/(h/2.)-1)**2)**0.5 < 1,
                               (w, h))

        # reshape to match array axes
        if axes[0] > axes[1]:
            mask = mask.T
        shape = [(n if i in axes else 1) for i, n in enumerate(arr.shape)]
        mask = mask.reshape(shape)

        if returnMappedCoords:
            return arr * mask, mappedCoords * mask
        else:
            return arr * mask


class ROIType(enum.Enum):
    ELLIPSE = EllipseROI
    RECTANGLE = RectROI


class MultiROI(QtGui.QGraphicsObject):
    """
    Container for several type of ROIs.
    This class in itself is only defining the interface between the currently
    selected ROI type and the outside world.

    A few abstract methods from QGraphicsObject must be overridden
    (*boundingRect* and *paint*) for integration with Qt.
    """
    sigRegionChangeFinished = QtCore.Signal(object)
    sigRegionChangeStarted = QtCore.Signal(object)
    sigRegionChanged = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        self.currentRoi = None
        self.setROIType(ROIType.RECTANGLE)

        # Wrap methods from *currentRoi*
        for fnName in ['setZValue', 'zValue', 'scene', 'setPen',
                       'getArrayRegion']:
            def _create_method(name):
                def method(*args, **kwargs):
                    fn = getattr(self.currentRoi, name)
                    return fn(*args, **kwargs)
                method.__name__ = name
                return method
            setattr(self, fnName, _create_method(fnName))
        del _create_method

    def boundingRect(self):
        return QtCore.QRectF()

    def paint(self, *args):
        pass

    def setROIType(self, roiType):
        self._disconnectAll()

        if roiType == ROIType.ELLIPSE:
            self.currentRoi = EllipseROI([10, 10], [10, 10], parent=self)
        elif roiType == ROIType.RECTANGLE:
            self.currentRoi = RectROI(10, parent=self)
        else:
            raise NotImplemented('Unhandled ROIType: %s' % repr(roiType))

        self._connectAll()
        self.sigRegionChanged.emit(self)

    def _disconnectAll(self):
        if self.currentRoi is not None:
            self.currentRoi.sigRegionChanged.disconnect(self.roiChangedEvent)
            self.currentRoi.sigRegionChangeStarted.disconnect(
                self.roiChangeStartedEvent)
            self.currentRoi.sigRegionChangeFinished.disconnect(
                self.roiChangeFinishedEvent)

    def _connectAll(self):
        self.currentRoi.sigRegionChanged.connect(self.roiChangedEvent)
        self.currentRoi.sigRegionChangeStarted.connect(
            self.roiChangeStartedEvent)
        self.currentRoi.sigRegionChangeFinished.connect(
            self.roiChangeFinishedEvent)

    def roiChangedEvent(self):
        self.sigRegionChanged.emit(self)

    def roiChangeStartedEvent(self):
        self.sigRegionChangeStarted.emit(self)

    def roiChangeFinishedEvent(self):
        self.sigRegionChangeFinished.emit(self)