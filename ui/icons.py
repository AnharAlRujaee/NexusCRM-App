"""Crisp vector icons drawn with QPainter (no image files needed).

Every icon is designed on a 24x24 grid and scaled to whatever rectangle
the caller asks for, so they stay sharp on any screen density.
"""

import math

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen


def _path(points, close=False) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(points[0][0], points[0][1])
    for x, y in points[1:]:
        path.lineTo(x, y)
    if close:
        path.closeSubpath()
    return path


def _dot(p: QPainter, color: QColor, x: float, y: float, r: float) -> None:
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawEllipse(QPointF(x, y), r, r)
    p.restore()


def _line(p: QPainter, x1, y1, x2, y2) -> None:
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


# --------------------------------------------------------------------------
# Individual icons
# --------------------------------------------------------------------------
def _apps(p, c):
    for x, y in ((3, 3), (14, 3), (3, 14), (14, 14)):
        p.drawRoundedRect(QRectF(x, y, 7, 7), 1.8, 1.8)


def _mentor(p, c):
    p.drawRoundedRect(QRectF(3, 4, 18, 12), 3, 3)
    p.drawPath(_path([(8, 16), (8, 20.5), (12.5, 16)]))
    for x in (8, 12, 16):
        _dot(p, c, x, 10, 1.2)


def _interviews(p, c):
    _line(p, 4, 8, 20, 8)
    p.drawPath(_path([(16, 4), (20, 8), (16, 12)]))
    _line(p, 20, 16, 4, 16)
    p.drawPath(_path([(8, 12), (4, 16), (8, 20)]))


def _admin(p, c):
    path = QPainterPath()
    path.moveTo(12, 3)
    path.lineTo(20, 6)
    path.lineTo(20, 12)
    path.cubicTo(20, 17, 16, 20, 12, 21)
    path.cubicTo(8, 20, 4, 17, 4, 12)
    path.lineTo(4, 6)
    path.closeSubpath()
    p.drawPath(path)
    p.drawPath(_path([(8.5, 12), (11, 14.5), (15.5, 9.5)]))


def _calendar(p, c):
    p.drawRoundedRect(QRectF(3, 5, 18, 16), 2.5, 2.5)
    _line(p, 3, 10, 21, 10)
    _line(p, 8, 3, 8, 7)
    _line(p, 16, 3, 16, 7)
    for x, y in ((8, 14), (12, 14), (16, 14), (8, 18)):
        _dot(p, c, x, y, 1.0)


def _mail(p, c):
    p.drawRoundedRect(QRectF(3, 5, 18, 14), 2.5, 2.5)
    p.drawPath(_path([(3.5, 7), (12, 13), (20.5, 7)]))


def _search(p, c):
    p.drawEllipse(QPointF(10.5, 10.5), 6.5, 6.5)
    _line(p, 15.5, 15.5, 20.5, 20.5)


def _back(p, c):
    _line(p, 20, 12, 5, 12)
    p.drawPath(_path([(11, 6), (5, 12), (11, 18)]))


def _arrow(p, c):
    _line(p, 4, 12, 19, 12)
    p.drawPath(_path([(13, 6), (19, 12), (13, 18)]))


def _power(p, c):
    p.drawArc(QRectF(5, 5, 14, 14), 125 * 16, 290 * 16)
    _line(p, 12, 3, 12, 11)



def _refresh(p, c):
    p.drawArc(QRectF(4, 4, 16, 16), 35 * 16, 285 * 16)
    p.drawPath(_path([(18, 3), (20, 8), (15, 8)]))
    p.drawPath(_path([(6, 21), (4, 16), (9, 16)]))


def _plus(p, c):
    _line(p, 12, 4, 12, 20)
    _line(p, 4, 12, 20, 12)


def _edit(p, c):
    p.drawPath(_path([(4, 17), (3, 21), (7, 20), (20, 7), (17, 4), (4, 17)]))
    _line(p, 14, 7, 17, 10)

def _user(p, c):
    p.drawEllipse(QPointF(12, 8), 4, 4)
    p.drawArc(QRectF(4, 13, 16, 16), 0, 180 * 16)


def _users(p, c):
    # Three simple person silhouettes for the trainee directory.
    p.drawEllipse(QPointF(12, 7), 3.2, 3.2)
    p.drawArc(QRectF(6, 11, 12, 11), 0, 180 * 16)
    p.drawEllipse(QPointF(5.5, 9), 2.2, 2.2)
    p.drawArc(QRectF(1, 12, 9, 8), 0, 180 * 16)
    p.drawEllipse(QPointF(18.5, 9), 2.2, 2.2)
    p.drawArc(QRectF(14, 12, 9, 8), 0, 180 * 16)

def _lock(p, c):
    p.drawRoundedRect(QRectF(5, 11, 14, 10), 2.5, 2.5)
    p.drawArc(QRectF(8, 3, 8, 10), 0, 180 * 16)
    _line(p, 8, 8, 8, 11)
    _line(p, 16, 8, 16, 11)
    _dot(p, c, 12, 16, 1.3)


def _eye(p, c):
    path = QPainterPath()
    path.moveTo(2, 12)
    path.cubicTo(5, 6.5, 8.5, 5, 12, 5)
    path.cubicTo(15.5, 5, 19, 6.5, 22, 12)
    path.cubicTo(19, 17.5, 15.5, 19, 12, 19)
    path.cubicTo(8.5, 19, 5, 17.5, 2, 12)
    path.closeSubpath()
    p.drawPath(path)
    p.drawEllipse(QPointF(12, 12), 3.2, 3.2)


def _eye_off(p, c):
    _eye(p, c)
    _line(p, 4, 3.5, 20, 20.5)


def _hex(p, c):
    outer = QPainterPath()
    inner = QPainterPath()
    for path, radius in ((outer, 10.0), (inner, 4.2)):
        for i in range(6):
            a = math.radians(60 * i - 90)
            x = 12 + radius * math.cos(a)
            y = 12 + radius * math.sin(a)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
    p.drawPath(outer)
    p.save()
    p.setBrush(c)
    p.drawPath(inner)
    p.restore()


def _logout(p, c):
    p.drawPath(_path([(10, 4), (5, 4), (5, 20), (10, 20)]))
    _line(p, 9, 12, 20, 12)
    p.drawPath(_path([(16, 8), (20, 12), (16, 16)]))


def _upload(p, c):
    _line(p, 12, 16, 12, 4)
    p.drawPath(_path([(7, 9), (12, 4), (17, 9)]))
    p.drawPath(_path([(4, 15), (4, 20), (20, 20), (20, 15)]))


def _download(p, c):
    _line(p, 12, 4, 12, 16)
    p.drawPath(_path([(7, 11), (12, 16), (17, 11)]))
    p.drawPath(_path([(4, 15), (4, 20), (20, 20), (20, 15)]))


def _list(p, c):
    for y in (6, 12, 18):
        _line(p, 9, y, 20, y)
        _dot(p, c, 4.5, y, 1.3)


def _check_circle(p, c):
    p.drawEllipse(QPointF(12, 12), 9, 9)
    p.drawPath(_path([(7.8, 12.3), (10.8, 15.2), (16.2, 9.2)]))


def _cross_circle(p, c):
    p.drawEllipse(QPointF(12, 12), 9, 9)
    _line(p, 8.5, 8.5, 15.5, 15.5)
    _line(p, 15.5, 8.5, 8.5, 15.5)


_ICONS = {
    "apps": _apps,
    "mentor": _mentor,
    "interviews": _interviews,
    "admin": _admin,
    "calendar": _calendar,
    "mail": _mail,
    "search": _search,
    "back": _back,
    "arrow": _arrow,
    "power": _power,
    "user": _user,
    "users": _users,
    "lock": _lock,
    "eye": _eye,
    "eye_off": _eye_off,
    "hex": _hex,
    "logout": _logout,
    "upload": _upload,
    "download": _download,
    "refresh": _refresh,
    "plus": _plus,
    "edit": _edit,
    "list": _list,
    "check": _check_circle,
    "cross": _cross_circle,
}


def draw_icon(p: QPainter, name: str, rect: QRectF, color, stroke: float = 1.8) -> None:
    """Draw the named icon inside ``rect`` using ``color``."""
    fn = _ICONS.get(name)
    if fn is None:
        return
    color = QColor(color)
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.x(), rect.y())
    p.scale(rect.width() / 24.0, rect.height() / 24.0)
    pen = QPen(color, stroke)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    fn(p, color)
    p.restore()
