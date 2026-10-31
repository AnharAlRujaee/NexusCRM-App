"""Reusable futuristic widgets: glow buttons, glass panels, nav cards,
animated headers, inputs, toasts and decorative HUD elements."""

import math
import time

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, pyqtProperty,
)
from PyQt6.QtGui import (
    QBrush, QColor, QFontMetrics, QGradient, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QAbstractButton, QAbstractItemView, QComboBox, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QTableWidget, QVBoxLayout, QWidget,
)

from ui.icons import draw_icon
from ui.theme import (
    BAD, OK, TEXT, TEXT_DIM, TEXT_FAINT, flags, mix, now, qcolor, ui_font,
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def make_label(text, px=13, color=TEXT, bold=False, spacing=0.0, mono=False, wrap=False):
    label = QLabel(text)
    label.setFont(ui_font(px, bold, spacing, mono))
    label.setStyleSheet(f"color: {color}; background: transparent;")
    label.setWordWrap(wrap)
    return label


def hex_path(cx, cy, r, rot=0.0) -> QPainterPath:
    path = QPainterPath()
    for i in range(6):
        a = math.radians(60 * i - 90 + rot)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


def fade_in(widget: QWidget, delay: int = 0, duration: int = 520) -> None:
    """Fade a widget from transparent to opaque after ``delay`` ms."""
    previous = getattr(widget, "_fade_anim", None)
    if previous is not None:
        previous.stop()

    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    widget._fade_anim = anim

    def finished():
        if getattr(widget, "_fade_anim", None) is anim:
            widget.setGraphicsEffect(None)

    def start():
        if getattr(widget, "_fade_anim", None) is anim:
            anim.start()

    anim.finished.connect(finished)
    QTimer.singleShot(max(0, int(delay)), start)


def stagger(widgets, base: int = 100, step: int = 85) -> None:
    """Reveal widgets one after another (cards rise, panels fade)."""
    for i, w in enumerate(widgets):
        delay = base + i * step
        if isinstance(w, GlowBase):
            w.prepare_appear()
            w.play_appear(delay)
        else:
            fade_in(w, delay)


# ---------------------------------------------------------------------------
# Glow button base (hover halo, shine sweep, appear animation)
# ---------------------------------------------------------------------------
class GlowBase(QPushButton):
    M = 8  # margin reserved around the body for the outer halo

    def __init__(self, accent, parent=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self._hover = 0.0
        self._appear = 1.0
        self._shine = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

        self._hover_anim = QPropertyAnimation(self, b"hoverT", self)
        self._hover_anim.setDuration(220)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._shine_anim = QPropertyAnimation(self, b"shineT", self)
        self._shine_anim.setDuration(760)
        self._shine_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._appear_anim = QPropertyAnimation(self, b"appearT", self)
        self._appear_anim.setDuration(560)
        self._appear_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # animated properties
    def _get_hover(self):
        return self._hover

    def _set_hover(self, v):
        self._hover = float(v)
        self.update()

    hoverT = pyqtProperty(float, _get_hover, _set_hover)

    def _get_shine(self):
        return self._shine

    def _set_shine(self, v):
        self._shine = float(v)
        self.update()

    shineT = pyqtProperty(float, _get_shine, _set_shine)

    def _get_appear(self):
        return self._appear

    def _set_appear(self, v):
        self._appear = float(v)
        self.update()

    appearT = pyqtProperty(float, _get_appear, _set_appear)

    # events
    def _animate_hover(self, target):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover)
        self._hover_anim.setEndValue(float(target))
        self._hover_anim.start()

    def enterEvent(self, event):
        if self.isEnabled():
            self._animate_hover(1.0)
            self._shine_anim.stop()
            self._shine_anim.setStartValue(0.0)
            self._shine_anim.setEndValue(1.0)
            self._shine_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    # appear animation
    def prepare_appear(self):
        self._appear_anim.stop()
        self._appear = 0.0
        self.update()

    def play_appear(self, delay=0):
        def go():
            self._appear_anim.stop()
            self._appear_anim.setStartValue(0.0)
            self._appear_anim.setEndValue(1.0)
            self._appear_anim.start()

        QTimer.singleShot(max(0, int(delay)), go)

    # painting helpers
    def _apply_appear(self, p: QPainter):
        if self._appear < 1.0:
            p.setOpacity(max(0.0, self._appear))
            p.translate(0, (1.0 - self._appear) * 18)

    def paint_halo(self, p, body: QRectF, radius, color, strength):
        if strength <= 0.01:
            return
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(1, 8):
            alpha = strength * ((1 - i / 8.0) ** 2) * 80
            p.setPen(QPen(qcolor(color, alpha), 1.6))
            p.drawRoundedRect(body.adjusted(-i, -i, i, i), radius + i, radius + i)

    def paint_shine(self, p, body: QRectF, clip: QPainterPath):
        s = self._shine
        if not (0.0 < s < 1.0):
            return
        p.save()
        p.setClipPath(clip)
        x = body.left() - body.width() * 0.35 + body.width() * 1.7 * s
        g = QLinearGradient(x, body.top(), x + body.width() * 0.30, body.bottom())
        g.setColorAt(0.0, QColor(255, 255, 255, 0))
        g.setColorAt(0.5, QColor(255, 255, 255, 46))
        g.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(body, QBrush(g))
        p.restore()


# ---------------------------------------------------------------------------
# NeonButton
# ---------------------------------------------------------------------------
class NeonButton(GlowBase):
    def __init__(self, text, accent, icon=None, variant="solid", height=46, parent=None):
        super().__init__(accent, parent)
        self.setText(text)
        self._icon = icon
        self._variant = variant
        self.setFont(ui_font(14, bold=True))
        self.setFixedHeight(height + 2 * self.M)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self.text()) + 48 + (28 if self._icon else 0) + 2 * self.M
        return QSize(max(w, 130), self.height())

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._apply_appear(p)
        if not self.isEnabled():
            p.setOpacity(p.opacity() * 0.4)

        M = self.M
        body = QRectF(self.rect()).adjusted(M, M, -M, -M)
        if self.isDown():
            body = body.adjusted(1.5, 1.5, -1.5, -1.5)

        ht = self._hover
        active = self.isCheckable() and self.isChecked()
        acc = self.accent
        radius = 13.0

        path = QPainterPath()
        path.addRoundedRect(body, radius, radius)

        if self._variant == "solid":
            self.paint_halo(p, body, radius, acc, 0.28 + 0.72 * ht)
            top = mix(acc, QColor(255, 255, 255), 0.22 + 0.14 * ht)
            bot = mix(acc, QColor(0, 0, 0), 0.45 if self.isDown() else 0.28)
            g = QLinearGradient(body.topLeft(), body.bottomRight())
            g.setColorAt(0.0, top)
            g.setColorAt(1.0, bot)
            p.fillPath(path, QBrush(g))
            self.paint_shine(p, body, path)
            text_col = QColor("#04101F")
        else:
            self.paint_halo(p, body, radius, acc, max(ht * 0.8, 0.55 if active else 0.0))
            if active:
                fill = qcolor(acc, 60 + 30 * ht)
            else:
                fill = QColor(255, 255, 255, int(8 + 16 * ht))
            p.fillPath(path, QBrush(fill))
            self.paint_shine(p, body, path)
            border = qcolor(acc, 255 if active else 90 + 150 * ht)
            p.setPen(QPen(border, 1.3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            text_col = QColor("#FFFFFF") if active else mix(TEXT_DIM, TEXT, ht)

        if self.hasFocus():
            p.setPen(QPen(QColor(255, 255, 255, 150), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(body.adjusted(-3, -3, 3, 3), radius + 3, radius + 3)

        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(self.text())
        iw = 18 if self._icon else 0
        gap = 10 if self._icon else 0
        x0 = body.center().x() - (iw + gap + tw) / 2.0
        if self._icon:
            draw_icon(p, self._icon, QRectF(x0, body.center().y() - 9, 18, 18), text_col, 1.9)
        p.setPen(text_col)
        p.setFont(self.font())
        p.drawText(
            QRectF(x0 + iw + gap, body.top(), tw + 6, body.height()),
            flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignVCenter),
            self.text(),
        )


# ---------------------------------------------------------------------------
# NavCard - big module tile
# ---------------------------------------------------------------------------
class NavCard(GlowBase):
    M = 10

    def __init__(self, icon, title, subtitle, accent, tag="01", cta="OPEN MODULE", parent=None):
        super().__init__(accent, parent)
        self._icon = icon
        self._title = title
        self._subtitle = subtitle
        self._tag = tag
        self._cta = cta
        self.setMinimumHeight(190 + 2 * self.M)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self):
        return QSize(260, 210 + 2 * self.M)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._apply_appear(p)

        M = self.M
        body = QRectF(self.rect()).adjusted(M, M, -M, -M)
        if self.isDown():
            body = body.adjusted(2, 2, -2, -2)
        ht = self._hover
        acc = self.accent
        radius = 20.0

        path = QPainterPath()
        path.addRoundedRect(body, radius, radius)

        self.paint_halo(p, body, radius, acc, ht)

        g = QLinearGradient(body.topLeft(), body.bottomLeft())
        g.setColorAt(0.0, mix(QColor(18, 28, 60, 205), acc, 0.10 * ht))
        g.setColorAt(1.0, mix(QColor(8, 12, 30, 220), acc, 0.18 * ht))
        p.fillPath(path, QBrush(g))
        self.paint_shine(p, body, path)

        p.setPen(QPen(qcolor(acc, 70 + 185 * ht), 1.2 + 0.6 * ht))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        if self.hasFocus():
            p.setPen(QPen(QColor(255, 255, 255, 150), 1.2))
            p.drawRoundedRect(body.adjusted(-3, -3, 3, 3), radius + 3, radius + 3)

        # icon tile
        ix, iy, isz = body.left() + 24, body.top() + 24, 64.0
        tile = QPainterPath()
        tile.addRoundedRect(QRectF(ix, iy, isz, isz), 18, 18)
        p.fillPath(tile, QBrush(qcolor(acc, 30 + 55 * ht)))
        p.setPen(QPen(qcolor(acc, 130 + 100 * ht), 1.2))
        p.drawPath(tile)
        draw_icon(p, self._icon, QRectF(ix + 16, iy + 16, 32, 32), mix(acc, QColor(255, 255, 255), 0.35), 1.7)

        # index tag
        p.setFont(ui_font(12, True, 1.8, mono=True))
        p.setPen(qcolor(acc, 170))
        p.drawText(
            QRectF(body.right() - 100, body.top() + 24, 76, 20),
            flags(Qt.AlignmentFlag.AlignRight, Qt.AlignmentFlag.AlignVCenter),
            self._tag,
        )

        # title + subtitle
        tx = body.left() + 24
        ty = iy + isz + 20
        p.setFont(ui_font(20, True))
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(tx, ty, body.width() - 48, 28),
                   flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignVCenter), self._title)
        p.setFont(ui_font(13))
        p.setPen(QColor(TEXT_DIM))
        p.drawText(QRectF(tx, ty + 32, body.width() - 48, 44),
                   flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignTop, Qt.TextFlag.TextWordWrap),
                   self._subtitle)

        # CTA row
        cy = body.bottom() - 30
        p.setFont(ui_font(11, True, 2.0, mono=True))
        p.setPen(qcolor(acc, 200))
        p.drawText(QRectF(tx, cy - 10, 170, 20),
                   flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignVCenter), self._cta)
        draw_icon(p, "arrow", QRectF(body.right() - 24 - 18 + 8 * ht, cy - 9, 18, 18), acc, 2.0)

        # growing underline
        if ht > 0.01:
            line_w = (body.width() - 48) * ht
            p.setPen(QPen(qcolor(acc, 220), 2.0))
            p.drawLine(QPointF(tx, body.bottom() - 12), QPointF(tx + line_w, body.bottom() - 12))


# ---------------------------------------------------------------------------
# GlassPanel
# ---------------------------------------------------------------------------
class GlassPanel(QFrame):
    def __init__(self, accent, radius=18, parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self._radius = float(radius)
        self._seed = (id(self) % 97) / 97.0
        self._flash = 0.0
        self._flash_color = QColor(BAD)
        self._flash_anim = QPropertyAnimation(self, b"flashT", self)
        self._flash_anim.setDuration(900)
        self._flash_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_flash(self):
        return self._flash

    def _set_flash(self, v):
        self._flash = float(v)
        self.update()

    flashT = pyqtProperty(float, _get_flash, _set_flash)

    def flash(self, color):
        """Briefly tint the panel border (used for login errors / success)."""
        self._flash_color = QColor(color)
        self._flash_anim.stop()
        self._flash_anim.setStartValue(1.0)
        self._flash_anim.setEndValue(0.0)
        self._flash_anim.start()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        rad = self._radius
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)

        fill = QLinearGradient(r.topLeft(), r.bottomRight())
        fill.setColorAt(0.0, QColor(20, 30, 64, 176))
        fill.setColorAt(1.0, QColor(8, 12, 32, 198))
        p.fillPath(path, QBrush(fill))

        sheen = QLinearGradient(r.topLeft(), QPointF(r.left(), r.top() + r.height() * 0.5))
        sheen.setColorAt(0.0, QColor(255, 255, 255, 14))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(sheen))

        f = self._flash
        col = mix(self._accent, self._flash_color, f)
        border = QLinearGradient(r.topLeft(), r.bottomRight())
        border.setColorAt(0.0, qcolor(col, 190))
        border.setColorAt(0.5, QColor(110, 140, 230, 50))
        border.setColorAt(1.0, qcolor(col, 120))
        p.setPen(QPen(QBrush(border), 1.2 + f))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # corner marks
        pen = QPen(qcolor(col, 255), 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        L = 26
        p.drawLine(QPointF(r.left() + rad, r.top()), QPointF(r.left() + rad + L, r.top()))
        p.drawLine(QPointF(r.right() - rad - L, r.bottom()), QPointF(r.right() - rad, r.bottom()))

        # travelling glint on the top edge
        span = max(10.0, r.width() - 2 * rad - 70)
        x = r.left() + rad + ((now() * 0.12 + self._seed) % 1.0) * span
        glint = QLinearGradient(x, 0, x + 70, 0)
        glint.setColorAt(0.0, qcolor(col, 0))
        glint.setColorAt(0.5, QColor(255, 255, 255, 190))
        glint.setColorAt(1.0, qcolor(col, 0))
        p.setPen(QPen(QBrush(glint), 1.6))
        p.drawLine(QPointF(x, r.top()), QPointF(x + 70, r.top()))


# ---------------------------------------------------------------------------
# Icon label, badge, chips, clock, top bar, header
# ---------------------------------------------------------------------------
class IconLabel(QWidget):
    def __init__(self, name, color, size=20, parent=None):
        super().__init__(parent)
        self._name = name
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        draw_icon(p, self._name, QRectF(self.rect()), self._color, 1.9)


class IconBadge(QWidget):
    """Hexagonal badge with a slowly rotating halo."""

    def __init__(self, icon, accent, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._accent = QColor(accent)
        self.setFixedSize(72, 72)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = now()
        cx, cy = self.width() / 2.0, self.height() / 2.0
        pulse = 0.5 + 0.5 * math.sin(t * 2.0)

        pen = QPen(qcolor(self._accent, 50 + 70 * pulse), 1.2)
        pen.setDashPattern([2.0, 4.0])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(hex_path(cx, cy, 34, rot=t * 14))

        inner = hex_path(cx, cy, 28)
        p.fillPath(inner, QBrush(qcolor(self._accent, 34 + 20 * pulse)))
        p.setPen(QPen(qcolor(self._accent, 210), 1.6))
        p.drawPath(inner)
        draw_icon(p, self._icon, QRectF(cx - 14, cy - 14, 28, 28),
                  mix(self._accent, QColor(255, 255, 255), 0.4), 1.8)


class StatusChip(QWidget):
    def __init__(self, text, color, pulse=True, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(color)
        self._pulse = pulse
        self._font = ui_font(11, True, 1.4, mono=True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._fit()

    def _fit(self):
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance(self._text) + 46, 28)

    def setText(self, text):
        self._text = text
        self._fit()
        self.update()

    def setColor(self, color):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(qcolor(self._color, 120), 1.0))
        p.setBrush(qcolor(self._color, 26))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        cy = self.height() / 2.0
        if self._pulse:
            ph = (now() * 1.4) % 1.0
            p.setPen(QPen(qcolor(self._color, 170 * (1 - ph)), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(16, cy), 3.0 + 6.0 * ph, 3.0 + 6.0 * ph)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        p.drawEllipse(QPointF(16, cy), 3.0, 3.0)

        p.setFont(self._font)
        p.setPen(mix(self._color, QColor(255, 255, 255), 0.35))
        p.drawText(QRectF(28, 0, self.width() - 32, self.height()),
                   flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignVCenter), self._text)


class ClockWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(92, 28)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setFont(ui_font(13, True, 1.6, mono=True))
        p.setPen(QColor(TEXT_DIM))
        p.drawText(QRectF(self.rect()),
                   flags(Qt.AlignmentFlag.AlignCenter), time.strftime("%H:%M:%S"))


class TopBar(QWidget):
    def __init__(self, accent, crumb, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(IconLabel("hex", accent, 28))
        lay.addWidget(make_label("NEXUS", 17, TEXT, True, 3.0))
        lay.addWidget(make_label("CRM", 17, accent, True, 3.0))
        lay.addSpacing(6)
        lay.addWidget(make_label("/", 14, TEXT_FAINT))
        lay.addWidget(make_label(crumb, 12, TEXT_DIM, True, 2.2, mono=True))
        lay.addStretch()
        lay.addWidget(ClockWidget())
        self.user_chip = StatusChip("GUEST", TEXT_DIM, pulse=False)
        self.role_chip = StatusChip("USER", accent)
        lay.addWidget(self.user_chip)
        lay.addWidget(self.role_chip)
        self._accent = accent

    def set_session(self, username, is_admin):
        self.user_chip.setText((username or "GUEST").upper()[:18])
        self.role_chip.setVisible(bool(username))
        self.role_chip.setText("ADMIN" if is_admin else "USER")
        self.role_chip.setColor("#FF3D81" if is_admin else self._accent)


class PageHeader(GlassPanel):
    def __init__(self, icon, eyebrow, title, subtitle, accent, parent=None):
        super().__init__(accent, parent=parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.setSpacing(18)
        lay.addWidget(IconBadge(icon, accent))

        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label(eyebrow.upper(), 11, accent, True, 2.6, mono=True))
        col.addWidget(make_label(title, 27, TEXT, True))
        col.addWidget(make_label(subtitle, 13, TEXT_DIM))
        lay.addLayout(col, 1)

        self._chips = QVBoxLayout()
        self._chips.setSpacing(8)
        lay.addLayout(self._chips)

    def add_chip(self, chip):
        self._chips.addWidget(chip, 0, Qt.AlignmentFlag.AlignRight)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
class EyeButton(QAbstractButton):
    """Show / hide toggle that sits inside a password field.

    Unchecked = password hidden (open eye: click to reveal).
    Checked   = password visible (slashed eye: click to hide).
    """

    def __init__(self, accent, parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self._hover = False
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # keep the caret in the text field
        self.setToolTip("Show password")

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lit = self.isChecked() or self._hover
        if self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(qcolor(self._accent, 34))
            p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))
        color = self._accent if lit else QColor(TEXT_DIM)
        draw_icon(p, "eye_off" if self.isChecked() else "eye", QRectF(6, 6, 20, 20), color, 1.8)


class NeonLineEdit(QLineEdit):
    def __init__(self, placeholder, icon, accent, parent=None, password=False):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._icon = icon
        self._accent = QColor(accent)
        self._focus = 0.0
        self._eye = None

        padding = ""
        if icon:
            padding += "padding-left: 46px;"
        if password:
            padding += " padding-right: 50px;"
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye = EyeButton(accent, self)
            self._eye.toggled.connect(self._on_eye_toggled)
        if padding:
            self.setStyleSheet(padding)

        self._anim = QPropertyAnimation(self, b"focusT", self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # -- password reveal ---------------------------------------------------
    def _on_eye_toggled(self, shown):
        self.setEchoMode(QLineEdit.EchoMode.Normal if shown else QLineEdit.EchoMode.Password)
        self._eye.setToolTip("Hide password" if shown else "Show password")

    def set_revealed(self, shown):
        """Programmatically show / hide the text (no-op for ordinary fields)."""
        if self._eye is not None:
            self._eye.setChecked(bool(shown))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._eye is not None:
            self._eye.move(self.width() - self._eye.width() - 10,
                           (self.height() - self._eye.height()) // 2)

    def _get_focus(self):
        return self._focus

    def _set_focus(self, v):
        self._focus = float(v)
        self.update()

    focusT = pyqtProperty(float, _get_focus, _set_focus)

    def _animate(self, target):
        self._anim.stop()
        self._anim.setStartValue(self._focus)
        self._anim.setEndValue(float(target))
        self._anim.start()

    def focusInEvent(self, event):
        self._animate(1.0)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._animate(0.0)
        super().focusOutEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = self._focus
        if self._icon:
            col = mix(TEXT_FAINT, self._accent, f)
            draw_icon(p, self._icon, QRectF(16, (self.height() - 18) / 2.0, 18, 18), col, 1.9)
        if f > 0.01:
            half = (self.width() - 30) / 2.0 * f
            y = self.height() - 1.5
            p.setPen(QPen(qcolor(self._accent, 255), 2.0))
            p.drawLine(QPointF(self.width() / 2.0 - half, y), QPointF(self.width() / 2.0 + half, y))


class NeonComboBox(QComboBox):
    def __init__(self, accent, parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMaxVisibleItems(8)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() - 24.0, self.height() / 2.0
        pen = QPen(self._accent, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        path = QPainterPath()
        path.moveTo(cx - 5, cy - 2.5)
        path.lineTo(cx, cy + 2.5)
        path.lineTo(cx + 5, cy - 2.5)
        p.drawPath(path)


def style_table(table: QTableWidget) -> None:
    """Common behaviour for the glass data tables."""
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(46)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setHighlightSections(False)
    table.setFrameShape(QFrame.Shape.NoFrame)
    table.viewport().setAutoFillBackground(False)


# ---------------------------------------------------------------------------
# Decorative HUD elements
# ---------------------------------------------------------------------------
class GradientLabel(QWidget):
    """Big title text filled with a flowing two-colour gradient."""

    def __init__(self, text, px, c1, c2, spacing=0.0, parent=None):
        super().__init__(parent)
        self._text = text
        self._c1 = QColor(c1)
        self._c2 = QColor(c2)
        self._font = ui_font(px, True, spacing)
        fm = QFontMetrics(self._font)
        self.setFixedSize(fm.horizontalAdvance(text) + 8, int(fm.height() * 1.08))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = QFontMetrics(self._font)
        path = QPainterPath()
        path.addText(2.0, float(fm.ascent()), self._font, self._text)
        w = float(self.width())
        x0 = (now() * 55.0) % (2 * w) - w
        g = QLinearGradient(x0, 0, x0 + w, 0)
        g.setSpread(QGradient.Spread.ReflectSpread)
        g.setColorAt(0.0, self._c1)
        g.setColorAt(1.0, self._c2)
        p.fillPath(path, QBrush(g))


class OrbitRings(QWidget):
    """Rotating reactor-style rings with an orbiting node."""

    def __init__(self, accent, size=240, parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = now()
        s = float(min(self.width(), self.height()))
        c = QPointF(self.width() / 2.0, self.height() / 2.0)
        acc = self._accent

        rg = QRadialGradient(c, s * 0.5)
        rg.setColorAt(0.0, qcolor(acc, 80))
        rg.setColorAt(1.0, qcolor(acc, 0))
        p.fillRect(self.rect(), QBrush(rg))

        # outer dotted ring
        p.save()
        p.translate(c)
        p.rotate(t * 12)
        pen = QPen(qcolor(acc, 160), 1.6)
        pen.setDashPattern([1.0, 5.0])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), s * 0.46, s * 0.46)
        p.restore()

        # counter-rotating arcs
        p.save()
        p.translate(c)
        p.rotate(-t * 32)
        pen = QPen(qcolor(acc, 230), 3.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        rr = s * 0.36
        rect = QRectF(-rr, -rr, 2 * rr, 2 * rr)
        for i in range(3):
            p.drawArc(rect, int((i * 120 + 10) * 16), int(70 * 16))
        p.restore()

        # inner fast arcs
        p.save()
        p.translate(c)
        p.rotate(t * 70)
        pen = QPen(QColor(255, 255, 255, 150), 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        ri = s * 0.26
        rect = QRectF(-ri, -ri, 2 * ri, 2 * ri)
        p.drawArc(rect, 30 * 16, 50 * 16)
        p.drawArc(rect, 210 * 16, 50 * 16)
        p.restore()

        # pulsing core
        pulse = 1.0 + 0.06 * math.sin(t * 3.0)
        core = hex_path(c.x(), c.y(), s * 0.16 * pulse, rot=t * 8)
        p.fillPath(core, QBrush(qcolor(acc, 70)))
        p.setPen(QPen(qcolor(acc, 255), 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(core)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 230))
        p.drawEllipse(c, 3.2, 3.2)

        # orbiting node
        a = t * 1.4
        node = QPointF(c.x() + math.cos(a) * s * 0.36, c.y() + math.sin(a) * s * 0.36)
        p.setBrush(qcolor(acc, 70))
        p.drawEllipse(node, 9.0, 9.0)
        p.setBrush(QColor(255, 255, 255, 240))
        p.drawEllipse(node, 3.4, 3.4)


class WaveWidget(QWidget):
    """Animated 'signal' waveform used as a live-data placeholder."""

    def __init__(self, accent, parent=None):
        super().__init__(parent)
        self._accent = QColor(accent)
        self.setMinimumHeight(90)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w < 4:
            return
        t = now()
        for k in range(3):
            path = QPainterPath()
            amp = h * (0.34 - 0.08 * k)
            for x in range(0, w + 4, 4):
                env = math.sin(math.pi * x / w)
                y = h / 2.0 + amp * env * math.sin(x * (0.02 + 0.006 * k) + t * (2.2 + 0.7 * k) + k)
                if x == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            p.setPen(QPen(qcolor(self._accent, 220 - 70 * k), 2.2 - 0.5 * k))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)


# ---------------------------------------------------------------------------
# Toast notification
# ---------------------------------------------------------------------------
class Toast(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._text = ""
        self._accent = QColor("#FFFFFF")
        self._fading_out = False

        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)

        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.finished.connect(self._on_fade_done)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._begin_hide)
        self.hide()

    def popup(self, text, accent):
        self._text = text
        self._accent = QColor(accent)
        fm = QFontMetrics(ui_font(13, True))
        parent = self.parentWidget()
        pw, ph = parent.width(), parent.height()
        w = min(max(240, pw - 40), fm.horizontalAdvance(text) + 80)
        h = 50
        self.setGeometry(int((pw - w) / 2), int(ph - h - 36), w, h)
        self.show()
        self.raise_()

        self._timer.stop()
        self._fade.stop()
        self._fading_out = False
        self._fade.setDuration(220)
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._timer.start(2600)
        self.update()

    def _begin_hide(self):
        self._fading_out = True
        self._fade.stop()
        self._fade.setDuration(380)
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _on_fade_done(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(r, r.height() / 2, r.height() / 2)
        p.fillPath(path, QBrush(QColor(8, 14, 36, 235)))
        p.setPen(QPen(qcolor(self._accent, 200), 1.4))
        p.drawPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._accent)
        p.drawEllipse(QPointF(r.left() + 24, r.center().y()), 4.5, 4.5)
        p.setFont(ui_font(13, True))
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(r.left() + 40, r.top(), r.width() - 56, r.height()),
                   flags(Qt.AlignmentFlag.AlignLeft, Qt.AlignmentFlag.AlignVCenter), self._text)
