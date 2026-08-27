# KCET Performance Tracker

Simple desktop dashboard built with Python, Tkinter, Matplotlib and SQLite.

Installation

1. Create a Python 3.10+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Run

```bash
python study.py
```

Database

- The SQLite database file `study_dash.db` is created in the same folder as the app.

Files

Run (Web UI)

```bash
# Start the local Flask web server and open http://127.0.0.1:5000
python app.py
```

- study.py: Main Tkinter application and UI.
- db.py: SQLite helpers and CRUD for tests and goals.
- charts.py: Matplotlib helper functions for embedding plots.
- stats.py: Compute statistics and generate analysis strings.
- requirements.txt: Python package requirements.

Data flow

1. Enter scores on the Home page.
2. `db.add_test()` saves the record to `study_dash.db`.
3. UI functions reload data via `db.get_tests()` and refresh graphs, tables and analysis.

Extending

- Add new subjects by updating `db` schema and UI fields.
- Add more graphs in `charts.py` and wire them in `study.py`.
