"""Render the HelixSR 助手 application icon (256x256 PNG): a double helix over "SR"."""
import math
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter,
                         QPainterPath, QPen)

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

# Double helix across the upper half: two phase-shifted strands with rungs.
left, right, mid, amp = 40, 216, 86, 34
strands = [QPainterPath(), QPainterPath()]
for i in range(0, 101):
    x = left + (right - left) * i / 100
    angle = 2 * math.pi * 1.5 * i / 100
    for k, path in enumerate(strands):
        y = mid + amp * math.sin(angle + k * math.pi)
        (path.moveTo if i == 0 else path.lineTo)(QPointF(x, y))
p.setPen(QPen(QColor(255, 255, 255, 120), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
for i in range(2, 100, 8):
    x = left + (right - left) * i / 100
    angle = 2 * math.pi * 1.5 * i / 100
    p.drawLine(QPointF(x, mid + amp * math.sin(angle)), QPointF(x, mid - amp * math.sin(angle)))
p.setPen(QPen(QColor(255, 255, 255, 240), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
for path in strands:
    p.drawPath(path)

font = QFont("Sans", 62)
font.setBold(True)
p.setFont(font)
p.setPen(QColor("white"))
p.drawText(QRectF(0, 132, size, 100), Qt.AlignmentFlag.AlignCenter, "SR")
p.end()
image.save(sys.argv[1])
