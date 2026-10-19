"""Render the Scaler 助手 application icon (256x256 PNG): a coarse pixel block scaled up
into a sharp frame — upscaling."""
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QGuiApplication, QImage, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPolygonF)

app = QGuiApplication(sys.argv)
size = 256
image = QImage(size, size, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)
p = QPainter(image)
p.setRenderHint(QPainter.RenderHint.Antialiasing)

bg = QLinearGradient(0, 0, size, size)
bg.setColorAt(0, QColor("#0f8a6b"))
bg.setColorAt(1, QColor("#2f4fd6"))
frame = QPainterPath()
frame.addRoundedRect(QRectF(8, 8, size - 16, size - 16), 52, 52)
p.fillPath(frame, bg)

# The sharp, large picture: a frame in the upper right.
big = QRectF(98, 40, 118, 118)
fill = QLinearGradient(big.topLeft(), big.bottomRight())
fill.setColorAt(0, QColor(255, 255, 255, 70))
fill.setColorAt(1, QColor(255, 255, 255, 25))
p.setPen(QPen(QColor(255, 255, 255, 245), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
              Qt.PenJoinStyle.RoundJoin))
p.setBrush(fill)
p.drawRoundedRect(big, 18, 18)

# The coarse, small picture: a 3x3 pixel block in the lower left.
cell, gap, x0, y0 = 20, 4, 40, 148
shades = (235, 150, 200, 120, 255, 170, 190, 140, 225)
p.setPen(Qt.PenStyle.NoPen)
for i, shade in enumerate(shades):
    r, c = divmod(i, 3)
    p.setBrush(QColor(255, 255, 255, shade))
    p.drawRoundedRect(QRectF(x0 + c * (cell + gap), y0 + r * (cell + gap), cell, cell), 4, 4)

# The arrow from the small picture to the large one.
p.setPen(QPen(QColor("white"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
start, end = QPointF(112, 144), QPointF(150, 106)
p.drawLine(start, end)
p.setPen(Qt.PenStyle.NoPen)
p.setBrush(QColor("white"))
p.drawPolygon(QPolygonF([QPointF(162, 94), QPointF(128, 100), QPointF(156, 128)]))
p.end()
image.save(sys.argv[1])
