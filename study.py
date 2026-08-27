"""
Simple CLI for Study-Dash to allow running without GUI dependencies.
Use this when Tkinter/Matplotlib are unavailable on the system.
"""
import sys
from datetime import datetime
import db
import stats


def prompt_add_test():
    date = input('Date (YYYY-MM-DD) [today]: ').strip() or datetime.now().strftime('%Y-%m-%d')
    name = input('Test name: ').strip()
    if not name:
        print('Test name required')
        return
    try:
        p = int(input('Physics (0-60): ').strip())
        c = int(input('Chemistry (0-60): ').strip())
        m = int(input('Maths (0-60): ').strip())
    except Exception:
        print('Invalid scores')
        return
    for v in (p, c, m):
        if v < 0 or v > 60:
            print('Scores must be 0-60')
            return
    db.init_db()
    tid = db.add_test(date, name, p, c, m)
    print(f'Saved test id={tid}')


def cmd_list_tests():
    db.init_db()
    tests = db.get_tests(order_desc=False)
    if not tests:
        print('No tests recorded')
        return
    for t in tests:
        print(f"{t['id']}: {t['date']} {t['test_name']} — P{t['physics']} C{t['chemistry']} M{t['maths']} = {t['total']}/180")


def cmd_stats():
    db.init_db()
    tests = db.get_tests(order_desc=False)
    if not tests:
        print('No tests to compute stats')
        return
    s = stats.compute_basic_stats(tests)
    print('LATEST:', s.get('latest'))
    print('AVERAGE:', f"{s.get('average'):.1f}")
    print('BEST:', s.get('best'))
    print('LOWEST:', s.get('worst'))
    print('IMPROVEMENT FROM FIRST:', s.get('improvement_from_first'))
    print('\nAnalysis:')
    for line in stats.generate_analysis(tests):
        print('-', line)


def print_help():
    print('Commands:')
    print('  add     - Add a new test')
    print('  list    - List saved tests')
    print('  stats   - Show statistics and analysis')
    print('  smoke   - Create sample data (overwrites DB)')
    print('  quit    - Exit')


def cmd_smoke():
    import os
    if os.path.exists('study_dash.db'):
        os.remove('study_dash.db')
    print('Initializing DB and adding sample tests...')
    db.init_db()
    db.add_test('2026-08-01', 'CET #1', 30, 28, 35)
    db.add_test('2026-08-08', 'CET #2', 32, 30, 36)
    db.add_test('2026-08-15', 'CET #3', 34, 33, 38)
    print('Sample data created.')


def main():
    print('Study-Dash (CLI) — local only')
    print_help()
    while True:
        cmd = input('> ').strip().lower()
        if cmd in ('q', 'quit', 'exit'):
            break
        if cmd == 'add':
            prompt_add_test()
        elif cmd == 'list':
            cmd_list_tests()
        elif cmd == 'stats':
            cmd_stats()
        elif cmd == 'smoke':
            cmd_smoke()
        elif cmd in ('h', 'help'):
            print_help()
        else:
            print('Unknown command; type help')


if __name__ == '__main__':
    main()

    def clear_entry_fields(self):
        self.testname_var.set('')
        self.phys_var.set('0')
        self.chem_var.set('0')
        self.math_var.set('0')
        self.total_label.config(text='TOTAL: 0 / 180')

    def refresh_all(self):
        self.tests = db.get_tests(order_desc=False)
        self.goals = db.get_goals()
        self.update_latest_card()
        self.update_graph()
        self.update_goals_table()
        self.update_history_table()
        self.refresh_history_graph()
        self.update_goal_page()
        self.update_stats_and_analysis()

    def update_latest_card(self):
        for w in self.latest_card.winfo_children():
            w.destroy()
        if not self.tests:
            ttk.Label(self.latest_card, text='No tests recorded yet.').pack()
            return
        t = self.tests[-1]
        lines = [f"{t['test_name']} — {t['date']}",
                 f"Physics {t['physics']}/60", f"Chemistry {t['chemistry']}/60",
                 f"Maths {t['maths']}/60", f"TOTAL {t['total']}/180"]
        for ln in lines:
            ttk.Label(self.latest_card, text=ln, font=('Segoe UI', 11)).pack(anchor='w')

    def update_graph(self):
        for w in self.graph_holder.winfo_children():
            w.destroy()
        canvas = charts.make_total_plot(self.graph_holder, self.tests)
        canvas.pack(fill='both')

    def update_goals_table(self):
        for r in self.goals_table.get_children():
            self.goals_table.delete(r)
        # compact table: show recent and upcoming goals
        for g in self.goals:
            # find a matching test if test-specific
            score = ''
            diff = ''
            status = ''
            if g['test_id']:
                t = db.get_test_by_id(g['test_id'])
                if t:
                    score = f"{t['total']}"
                    diff_v = t['total'] - g['target']
                    diff = f"{diff_v:+d}"
                    status = 'Goal exceeded' if diff_v > 0 else f"{abs(diff_v)} marks short" if diff_v<0 else 'On target'
            else:
                # for weekly/monthly, find latest within range
                score = '-'
                diff = '-'
                status = '-'
            self.goals_table.insert('', 'end', values=(g.get('start_date') or '-', g['name'], g['target'], score, diff, status))

    def update_history_table(self):
        for r in self.history_table.get_children():
            self.history_table.delete(r)
        for t in self.tests:
            self.history_table.insert('', 'end', iid=t['id'], values=(t['date'], t['test_name'], t['physics'], t['chemistry'], t['maths'], t['total']))

    def refresh_history_graph(self):
        for w in self.hist_graph_holder.winfo_children():
            w.destroy()
        subj = self.subj_var.get()
        canvas = charts.make_subjects_plot(self.hist_graph_holder, self.tests, subject=subj)
        canvas.pack(fill='both')

    def update_stats_and_analysis(self):
        s = stats.compute_basic_stats(self.tests) if self.tests else {}
        lines = []
        if s:
            lines.append(f"LATEST: {s['latest']}/180")
            lines.append(f"AVERAGE: {s['average']:.1f}/180")
            lines.append(f"BEST: {s['best']}/180")
            lines.append(f"LOWEST: {s['worst']}/180")
            lines.append(f"IMPROVEMENT: {s['improvement_from_first']} from first test")
        self.analysis_box.delete('1.0', 'end')
        for L in stats.generate_analysis(self.tests):
            self.analysis_box.insert('end', L + '\n')

    # History actions
    def edit_selected(self):
        sel = self.history_table.selection()
        if not sel:
            messagebox.showinfo('Select', 'Please select a test to edit')
            return
        tid = int(sel[0])
        t = db.get_test_by_id(tid)
        if not t:
            return
        self.open_edit_dialog(t)

    def open_edit_dialog(self, test):
        w = tk.Toplevel(self)
        w.title('Edit Test')
        ttk.Label(w, text='Date (YYYY-MM-DD)').grid(row=0, column=0)
        dvar = tk.StringVar(value=test['date'])
        ttk.Entry(w, textvariable=dvar).grid(row=0, column=1)
        ttk.Label(w, text='Test name').grid(row=1, column=0)
        tn = tk.StringVar(value=test['test_name'])
        ttk.Entry(w, textvariable=tn).grid(row=1, column=1)
        pvar = tk.StringVar(value=str(test['physics']))
        cvar = tk.StringVar(value=str(test['chemistry']))
        mvar = tk.StringVar(value=str(test['maths']))
        ttk.Label(w, text='Physics').grid(row=2, column=0)
        ttk.Entry(w, textvariable=pvar).grid(row=2, column=1)
        ttk.Label(w, text='Chemistry').grid(row=3, column=0)
        ttk.Entry(w, textvariable=cvar).grid(row=3, column=1)
        ttk.Label(w, text='Maths').grid(row=4, column=0)
        ttk.Entry(w, textvariable=mvar).grid(row=4, column=1)

        def save_edit():
            try:
                dt = datetime.strptime(dvar.get(), '%Y-%m-%d')
            except Exception:
                messagebox.showerror('Invalid date', 'Date invalid')
                return
            try:
                p = int(pvar.get()); c = int(cvar.get()); m = int(mvar.get())
            except Exception:
                messagebox.showerror('Invalid scores', 'Scores must be integers')
                return
            for v in (p,c,m):
                if v < 0 or v > 60:
                    messagebox.showerror('Invalid scores', 'Scores must be 0-60')
                    return
            db.update_test(test['id'], dvar.get(), tn.get(), p, c, m)
            w.destroy()
            self.refresh_all()

        ttk.Button(w, text='Save', command=save_edit).grid(row=6, column=0, columnspan=2)

    def delete_selected(self):
        sel = self.history_table.selection()
        if not sel:
            messagebox.showinfo('Select', 'Please select a test to delete')
            return
        if not messagebox.askyesno('Confirm', 'Delete selected test?'):
            return
        tid = int(sel[0])
        db.delete_test(tid)
        self.refresh_all()

    # Goals page actions
    def add_goal_dialog(self):
        w = tk.Toplevel(self)
        w.title('Add Goal')
        name = tk.StringVar(); gtype = tk.StringVar(value='test'); target = tk.StringVar(value='120')
        start = tk.StringVar(); end = tk.StringVar(); testid = tk.StringVar()
        ttk.Label(w, text='Name').grid(row=0, column=0); ttk.Entry(w, textvariable=name).grid(row=0, column=1)
        ttk.Label(w, text='Type (test/weekly/monthly)').grid(row=1, column=0); ttk.Entry(w, textvariable=gtype).grid(row=1, column=1)
        ttk.Label(w, text='Target').grid(row=2, column=0); ttk.Entry(w, textvariable=target).grid(row=2, column=1)
        ttk.Label(w, text='Start YYYY-MM-DD').grid(row=3, column=0); ttk.Entry(w, textvariable=start).grid(row=3, column=1)
        ttk.Label(w, text='End YYYY-MM-DD').grid(row=4, column=0); ttk.Entry(w, textvariable=end).grid(row=4, column=1)
        ttk.Label(w, text='Test id (optional)').grid(row=5, column=0); ttk.Entry(w, textvariable=testid).grid(row=5, column=1)

        def save():
            try:
                tgt = int(target.get())
            except Exception:
                messagebox.showerror('Invalid target', 'Target must be integer')
                return
            tid = int(testid.get()) if testid.get().strip().isdigit() else None
            db.add_goal(name.get(), gtype.get(), tgt, start.get() or None, end.get() or None, tid)
            w.destroy(); self.refresh_all()

        ttk.Button(w, text='Save', command=save).grid(row=6, column=0, columnspan=2)

    def edit_goal_dialog(self):
        sel = self.goal_table.selection()
        if not sel:
            messagebox.showinfo('Select', 'Select a goal to edit')
            return
        gid = int(sel[0])
        # load goal
        goals = db.get_goals()
        g = next((x for x in goals if x['id']==gid), None)
        if not g:
            return
        w = tk.Toplevel(self)
        name = tk.StringVar(value=g['name']); gtype = tk.StringVar(value=g['type']); target = tk.StringVar(value=str(g['target']))
        start = tk.StringVar(value=g.get('start_date') or ''); end = tk.StringVar(value=g.get('end_date') or ''); testid = tk.StringVar(value=str(g.get('test_id') or ''))
        ttk.Label(w, text='Name').grid(row=0, column=0); ttk.Entry(w, textvariable=name).grid(row=0, column=1)
        ttk.Label(w, text='Type').grid(row=1, column=0); ttk.Entry(w, textvariable=gtype).grid(row=1, column=1)
        ttk.Label(w, text='Target').grid(row=2, column=0); ttk.Entry(w, textvariable=target).grid(row=2, column=1)
        ttk.Label(w, text='Start').grid(row=3, column=0); ttk.Entry(w, textvariable=start).grid(row=3, column=1)
        ttk.Label(w, text='End').grid(row=4, column=0); ttk.Entry(w, textvariable=end).grid(row=4, column=1)
        ttk.Label(w, text='Test id').grid(row=5, column=0); ttk.Entry(w, textvariable=testid).grid(row=5, column=1)

        def save():
            try:
                tgt = int(target.get())
            except Exception:
                messagebox.showerror('Invalid', 'Target must be integer'); return
            tid = int(testid.get()) if testid.get().strip().isdigit() else None
            db.update_goal(g['id'], name.get(), gtype.get(), tgt, start.get() or None, end.get() or None, tid)
            w.destroy(); self.refresh_all()

        ttk.Button(w, text='Save', command=save).grid(row=6, column=0, columnspan=2)

    def delete_goal(self):
        sel = self.goal_table.selection()
        if not sel:
            messagebox.showinfo('Select', 'Select a goal to delete')
            return
        gid = int(sel[0])
        if not messagebox.askyesno('Confirm', 'Delete goal?'):
            return
        db.delete_goal(gid)
        self.refresh_all()

    def update_goal_page(self):
        for r in self.goal_table.get_children():
            self.goal_table.delete(r)
        for g in self.goals:
            current = '-'
            diff = '-'
            pct = '-'
            if g['test_id']:
                t = db.get_test_by_id(g['test_id'])
                if t:
                    current = f"{t['total']}"
                    diff_v = t['total'] - g['target']
                    diff = f"{diff_v:+d}"
                    pct = f"{(t['total']/g['target']*100):.0f}%"
            self.goal_table.insert('', 'end', iid=g['id'], values=(g['name'], g['type'], g['target'], g.get('start_date') or '-', g.get('end_date') or '-', current, diff, pct))


if __name__ == '__main__':
    app = StudyDashApp()
    app.show_home()
    app.mainloop()
