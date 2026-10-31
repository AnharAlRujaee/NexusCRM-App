"""Page transition engine: parallax slide + cross-fade + a neon light-beam
that sweeps across the window every time you change pages."""

from PyQt6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPoint, QPointF, QPropertyAnimation, QRectF, Qt,
    pyqtProperty,
)
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget

from ui.theme import mix, qcolor


class TransitionBeam(QWidget):
    TRAIL = 300.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._progress = -1.0
        self._color = QColor("#FFFFFF")
        self._direction = 1

    def _get_progress(self):
        return self._progress

    def _set_progress(self, v):
        self._progress = float(v)
        self.update()

    progress = pyqtProperty(float, _get_progress, _set_progress)

    def configure(self, color, direction):
        self._color = QColor(color)
        self._direction = 1 if direction >= 0 else -1

    def paintEvent(self, _event):
        pr = self._progress
        if pr < 0.0 or pr > 1.0:
            return
        w, h = float(self.width()), float(self.height())
        travel = w + 2 * self.TRAIL
        pos = pr if self._direction > 0 else 1.0 - pr
        x = pos * travel - self.TRAIL

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        acc = self._color

        if self._direction > 0:
            trail = QLinearGradient(x - self.TRAIL, 0, x, 0)
            trail.setColorAt(0.0, qcolor(acc, 0))
            trail.setColorAt(1.0, qcolor(acc, 60))
            p.fillRect(QRectF(x - self.TRAIL, 0, self.TRAIL, h), QBrush(trail))
        else:
            trail = QLinearGradient(x, 0, x + self.TRAIL, 0)
            trail.setColorAt(0.0, qcolor(acc, 60))
            trail.setColorAt(1.0, qcolor(acc, 0))
            p.fillRect(QRectF(x, 0, self.TRAIL, h), QBrush(trail))

        core = QLinearGradient(0, 0, 0, h)
        core.setColorAt(0.0, qcolor(acc, 0))
        core.setColorAt(0.5, qcolor(mix(acc, QColor(255, 255, 255), 0.6), 235))
        core.setColorAt(1.0, qcolor(acc, 0))
        p.setPen(QPen(QBrush(core), 14.0))
        p.setOpacity(0.18)
        p.drawLine(QPointF(x, 0), QPointF(x, h))
        p.setOpacity(1.0)
        p.setPen(QPen(QBrush(core), 2.0))
        p.drawLine(QPointF(x, 0), QPointF(x, h))


class AnimatedStack(QWidget):
    """Holds all pages; only one is visible except while transitioning."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages = {}
        self._current = None
        self._old = None
        self._group = None
        self.beam = TransitionBeam(self)

    def add_page(self, key, page):
        page.setParent(self)
        page.hide()
        self._pages[key] = page
        self.beam.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.beam.setGeometry(self.rect())
        if self._group is None:
            if self._current is not None:
                self._current.setGeometry(self.rect())
        else:
            for page in (self._current, self._old):
                if page is not None:
                    page.resize(self.size())

    def go(self, key, direction=1, animate=True, accent="#FFFFFF"):
        new = self._pages[key]
        old = self._current
        if new is old:
            return

        self._finish_now()
        self._current = new
        new.setGeometry(self.rect())

        if old is None or not animate:
            if old is not None:
                old.hide()
            new.move(0, 0)
            new.show()
            new.raise_()
            self.beam.raise_()
            return

        dx = int(self.width() * 0.09) * (1 if direction >= 0 else -1)
        new.move(dx, 0)
        new.show()
        new.raise_()
        self.beam.raise_()

        eff_new = QGraphicsOpacityEffect(new)
        eff_new.setOpacity(0.0)
        new.setGraphicsEffect(eff_new)
        eff_old = QGraphicsOpacityEffect(old)
        eff_old.setOpacity(1.0)
        old.setGraphicsEffect(eff_old)

        group = QParallelAnimationGroup(self)

        def add(target, name, start, end, ms, curve):
            anim = QPropertyAnimation(target, name)
            anim.setDuration(ms)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.setEasingCurve(curve)
            group.addAnimation(anim)

        add(new, b"pos", QPoint(dx, 0), QPoint(0, 0), 620, QEasingCurve.Type.OutCubic)
        add(eff_new, b"opacity", 0.0, 1.0, 520, QEasingCurve.Type.InOutSine)
        add(old, b"pos", QPoint(0, 0), QPoint(-dx, 0), 420, QEasingCurve.Type.InCubic)
        add(eff_old, b"opacity", 1.0, 0.0, 340, QEasingCurve.Type.InOutSine)

        self.beam.configure(accent, direction)
        add(self.beam, b"progress", 0.0, 1.0, 640, QEasingCurve.Type.InOutCubic)

        self._old = old
        self._group = group
        group.finished.connect(self._cleanup)
        group.start()

    def _finish_now(self):
        group = self._group
        if group is None:
            return
        group.stop()
        self._cleanup()

    def _cleanup(self):
        group = self._group
        if group is None:
            return
        self._group = None
        old = self._old
        self._old = None

        self.beam._set_progress(-1.0)
        if old is not None and old is not self._current:
            old.setGraphicsEffect(None)
            old.hide()
            old.move(0, 0)
        cur = self._current
        if cur is not None:
            cur.setGraphicsEffect(None)
            cur.move(0, 0)
            cur.setGeometry(self.rect())
        group.deleteLater()
