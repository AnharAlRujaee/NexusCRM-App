"""Living background: aurora glow, moving perspective grid and a particle
constellation that reacts subtly to the mouse. Its colour smoothly morphs
to the accent of whichever page is active."""

import math
import random
import time

from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QLinearGradient, QPainter, QPen, QRadialGradient,
)
from PyQt6.QtWidgets import QWidget

from ui.theme import ACCENTS, mix, now, qcolor


class FuturisticBackground(QWidget):
    PARTICLES = 46
    LINK_DIST = 140.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent = QColor(ACCENTS["login"])
        self._mx = 0.0  # smoothed mouse offset, -0.5 .. 0.5
        self._my = 0.0
        self._last = time.perf_counter()

        rnd = random.Random(7)
        # x, y (0..1), vx, vy, radius
        self._particles = [
            [rnd.random(), rnd.random(),
             (rnd.random() - 0.5) * 0.018, (rnd.random() - 0.5) * 0.018,
             rnd.uniform(1.0, 2.4)]
            for _ in range(self.PARTICLES)
        ]

        self._accent_anim = QVariantAnimation(self)
        self._accent_anim.setDuration(900)
        self._accent_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._accent_anim.valueChanged.connect(self._on_accent)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._step)
        self._timer.start()

        self.setMinimumSize(600, 400)

    # -- accent ------------------------------------------------------------
    def set_accent(self, hex_color: str) -> None:
        self._accent_anim.stop()
        self._accent_anim.setStartValue(QColor(self._accent))
        self._accent_anim.setEndValue(QColor(hex_color))
        self._accent_anim.start()

    def _on_accent(self, value) -> None:
        self._accent = QColor(value)

    # -- simulation --------------------------------------------------------
    def _step(self) -> None:
        t = time.perf_counter()
        dt = min(0.1, t - self._last)
        self._last = t

        for prt in self._particles:
            prt[0] = (prt[0] + prt[2] * dt) % 1.0
            prt[1] = (prt[1] + prt[3] * dt) % 1.0

        w, h = max(1, self.width()), max(1, self.height())
        local = self.mapFromGlobal(QCursor.pos())
        tx = max(-0.5, min(0.5, local.x() / w - 0.5))
        ty = max(-0.5, min(0.5, local.y() / h - 0.5))
        self._mx += (tx - self._mx) * 0.06
        self._my += (ty - self._my) * 0.06
        self.update()

    # -- painting ----------------------------------------------------------
    def paintEvent(self, _event) -> None:
        w, h = self.width(), self.height()
        if w < 2 or h < 2:
            return
        t = now()
        acc = self._accent
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. base gradient
        base = QLinearGradient(0, 0, 0, h)
        base.setColorAt(0.0, QColor("#070C1C"))
        base.setColorAt(0.6, QColor("#050816"))
        base.setColorAt(1.0, QColor("#03040B"))
        p.fillRect(self.rect(), QBrush(base))

        # 2. aurora glows (accent + complementary hue)
        big = max(w, h)
        c1 = QPointF(w * (0.18 + 0.05 * math.sin(t * 0.25)) - self._mx * 50,
                     h * (0.20 + 0.05 * math.cos(t * 0.21)) - self._my * 30)
        g1 = QRadialGradient(c1, big * 0.55)
        g1.setColorAt(0.0, qcolor(acc, 78))
        g1.setColorAt(1.0, qcolor(acc, 0))
        p.fillRect(self.rect(), QBrush(g1))

        comp = QColor.fromHsv((max(0, acc.hue()) + 150) % 360, 200, 255)
        c2 = QPointF(w * (0.86 + 0.04 * math.cos(t * 0.19)) + self._mx * 60,
                     h * (0.88 + 0.04 * math.sin(t * 0.23)) + self._my * 30)
        g2 = QRadialGradient(c2, big * 0.5)
        g2.setColorAt(0.0, qcolor(comp, 50))
        g2.setColorAt(1.0, qcolor(comp, 0))
        p.fillRect(self.rect(), QBrush(g2))

        # 3. perspective grid
        horizon = h * 0.58
        span = h - horizon
        glow = QLinearGradient(0, horizon - 70, 0, horizon)
        glow.setColorAt(0.0, qcolor(acc, 0))
        glow.setColorAt(1.0, qcolor(acc, 34))
        p.fillRect(QRectF(0, horizon - 70, w, 70), QBrush(glow))

        vx = w * 0.5 + self._mx * w * 0.10
        fade = QLinearGradient(0, horizon, 0, h)
        fade.setColorAt(0.0, qcolor(acc, 0))
        fade.setColorAt(1.0, qcolor(acc, 85))
        p.setPen(QPen(QBrush(fade), 1.0))
        for i in range(-24, 25):
            xb = w * 0.5 + i * w * 0.115
            p.drawLine(QPointF(vx, horizon), QPointF(xb, h))

        rows = 16
        phase = (t * 0.30) % 1.0
        for k in range(rows):
            f = (k + phase) / rows
            y = horizon + span * (f ** 2.3)
            p.setPen(QPen(qcolor(acc, 8 + 90 * f), 1.0))
            p.drawLine(QPointF(0, y), QPointF(w, y))

        # 4. particle constellation
        pts = []
        for x, y, _vx, _vy, r in self._particles:
            pts.append((x * w + self._mx * r * 26, y * h + self._my * r * 26, r))

        link = mix(acc, QColor(255, 255, 255), 0.30)
        max_d = self.LINK_DIST
        for i in range(len(pts)):
            xi, yi, _ = pts[i]
            for j in range(i + 1, len(pts)):
                dx = xi - pts[j][0]
                dy = yi - pts[j][1]
                d2 = dx * dx + dy * dy
                if d2 < max_d * max_d:
                    a = (1.0 - math.sqrt(d2) / max_d) * 70
                    p.setPen(QPen(qcolor(link, a), 0.8))
                    p.drawLine(QPointF(xi, yi), QPointF(pts[j][0], pts[j][1]))

        p.setPen(Qt.PenStyle.NoPen)
        for x, y, r in pts:
            p.setBrush(qcolor(link, 40))
            p.drawEllipse(QPointF(x, y), r * 3.2, r * 3.2)
            p.setBrush(qcolor(link, 190))
            p.drawEllipse(QPointF(x, y), r, r)

        # 5. slow scan line
        sy = (t * 38) % (h + 240) - 120
        scan = QLinearGradient(0, sy - 40, 0, sy + 40)
        scan.setColorAt(0.0, qcolor(acc, 0))
        scan.setColorAt(0.5, qcolor(acc, 16))
        scan.setColorAt(1.0, qcolor(acc, 0))
        p.fillRect(QRectF(0, sy - 40, w, 80), QBrush(scan))

        # 6. vignette
        vig = QRadialGradient(QPointF(w / 2, h / 2), big * 0.78)
        vig.setColorAt(0.0, QColor(0, 0, 0, 0))
        vig.setColorAt(0.62, QColor(0, 0, 0, 0))
        vig.setColorAt(1.0, QColor(0, 0, 0, 190))
        p.fillRect(self.rect(), QBrush(vig))

