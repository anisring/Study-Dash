import tkinter as tk
from tkinter import messagebox
from typing import List, Dict


def _draw_basic_plot(parent, tests: List[Dict], field: str = 'total') -> tk.Canvas:
    width, height = 720, 240
    margin_x, margin_y = 40, 30
    canvas = tk.Canvas(parent, width=width, height=height, bg='white')
    if not tests:
        canvas.create_text(width // 2, height // 2, text='No data', fill='gray')
        return canvas

    # values and labels
    labels = [t.get('test_name') or t.get('date') for t in tests]
    vals = [t.get(field, 0) for t in tests]
    n = len(vals)

    # scales
    max_y = 180
    plot_w = width - 2 * margin_x
    plot_h = height - 2 * margin_y

    def x_pos(i):
        return margin_x + (i / max(1, n - 1)) * plot_w if n > 1 else margin_x + plot_w / 2

    def y_pos(v):
        return margin_y + (1 - v / max_y) * plot_h

    # axes
    canvas.create_line(margin_x, margin_y, margin_x, height - margin_y, fill='#333')
    canvas.create_line(margin_x, height - margin_y, width - margin_x, height - margin_y, fill='#333')
    # y ticks
    for yv in range(0, max_y + 1, 30):
        y = y_pos(yv)
        canvas.create_line(margin_x - 5, y, margin_x, y, fill='#666')
        canvas.create_text(margin_x - 28, y, text=str(yv), anchor='e', fill='#333', font=('Arial', 8))

    # plot polyline
    points = []
    for i, v in enumerate(vals):
        x = x_pos(i)
        y = y_pos(v)
        points.append((x, y))

    # draw area fill
    poly = []
    for x, y in points:
        poly.extend([x, y])
    # close to baseline
    poly.extend([points[-1][0], height - margin_y, points[0][0], height - margin_y])
    canvas.create_polygon(poly, fill='#a6bddb', outline='', stipple='')

    # line and points
    for i, (x, y) in enumerate(points):
        if i > 0:
            x0, y0 = points[i - 1]
            canvas.create_line(x0, y0, x, y, fill='#2b8cbe', width=2)
        tag = f'pt{i}'
        canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill='#1f78b4', outline='', tags=(tag,))
        # bind click to show detail
        def make_cb(t):
            return lambda ev: messagebox.showinfo('Test', f"{t['test_name']}\n{t['date']}\n{field.title()}: {t.get(field,0)}/180\nTotal: {t.get('total','-')}")

        canvas.tag_bind(tag, '<Button-1>', make_cb(tests[i]))

    # x labels
    for i, lbl in enumerate(labels):
        x = x_pos(i)
        canvas.create_text(x, height - margin_y + 12, text=lbl, anchor='n', angle=30, font=('Arial', 9))

    return canvas


def make_total_plot(parent, tests: List[Dict]):
    return _draw_basic_plot(parent, tests, field='total')


def make_subjects_plot(parent, tests: List[Dict], subject: str = 'total'):
    return _draw_basic_plot(parent, tests, field=subject)

