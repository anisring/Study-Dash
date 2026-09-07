# Study-Dash

KCET study dashboard with a Flask web UI, a Tkinter desktop UI, SQLite storage,
performance analysis, goals, paper storage, profile customization, and upcoming
test reminders.

Installation

1. Create a Python 3.10+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Run the desktop UI

```bash
python study.py
```

Run the web UI

```bash
# Start the local Flask web server at http://127.0.0.1:5000
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

Database

- The SQLite database file `study_dash.db` is created in the same folder as the app.

Email reminders

- Add your email on the Profile page.
- In The Library, add upcoming tests manually or import a CSV, TSV, or XLSX sheet.
- Sheets should include a date column and a test/exam/title column. Optional columns are `time` and `portions`, `topics`, or `syllabus`.
- Dates are entered and displayed as `DD/MM/YYYY`.
- Gmail reminders require a Gmail App Password. Set `STUDY_DASH_GMAIL_ADDRESS` and `STUDY_DASH_GMAIL_APP_PASSWORD` before starting the app.
- The app checks for due reminders while it is being used. The Library page also has a manual `Send due reminders` button.
- Gmail OAuth is not implemented yet; the App Password is used only as a server-side environment variable and is never stored in SQLite.

Web features

- Dashboard greeting and profile page with name, email, and profile picture.
- Persistent color customization for the background, panels, inputs, text, borders, and buttons.
- Overall performance graph with a fixed 0-180 scale and custom graph color.
- Marks History analysis and comparison of any two tests by total and subject.
- The Library supports PDF, TXT, and Markdown question papers, question counting up to 200, paper difficulty estimates, and keyword-based doubt lookup.
- The Library also stores upcoming test dates and portions for reminder emails.

Files

- study.py: Main Tkinter application and UI.
- db.py: SQLite helpers and CRUD for tests and goals.
- charts.py: Matplotlib helper functions for embedding plots.
- stats.py: Compute statistics and generate analysis strings.
- requirements.txt: Python package requirements.
- templates/library.html: Question paper and test schedule library.
- templates/profile.html: User profile page.

Data flow

1. Enter scores on the Dashboard.
2. `db.add_test()` saves the record to `study_dash.db`.
3. UI functions reload data via `db.get_tests()` and refresh graphs, tables, comparisons, and analysis.

Extending

- Add new subjects by updating `db` schema and UI fields.
- Add more graphs in `charts.py` and wire them in `study.py`.
