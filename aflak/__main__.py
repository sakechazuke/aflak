import argparse

from pyqtgraph.Qt import QtGui

import window


parser = argparse.ArgumentParser(description='Provide FITS file as input')
parser.add_argument('fits', metavar='fits-file', help='FITS file to open')

args = parser.parse_args()

app = QtGui.QApplication([])
aflak = window.MainWindow()
aflak.set_fits_file(args.fits)

QtGui.QApplication.instance().exec_()
