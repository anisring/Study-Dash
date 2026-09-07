# Study-Dash

Study-Dash is a locally run study and KCET performance dashboard built with Python.

It allows students to record test scores, track progress over time, compare performances, set goals, and analyse their strengths and weaknesses across subjects.

---

## Features

### Dashboard
- Enter Physics, Chemistry and Mathematics test scores.
- Automatically calculates the total score out of 180.
- Displays your latest test performance.
- Tracks your overall performance through a progress graph.
- Set and track score goals.

### Marks History
- Stores all previously entered test scores.
- Displays detailed test-wise performance.
- Compare two tests to see improvements or drops in each subject.
- Visualise overall progress and score changes.
- View performance analysis based on your recorded marks.

### Goals
- Create test, weekly or monthly score goals.
- Track your current performance against a target.
- See how many marks above or below your target you are.

### Customisation
- Personalise the application's colour palette.
- Customise the background, panels, text, buttons and graph colours.
- Save your preferences locally.

### Library
- Store question papers and study material.
- Supports PDF, TXT and Markdown files.
- Store upcoming test dates and portions.
- Import dates and portions from CSV, TSV or Excel sheets.
- Estimate paper difficulty and search saved papers for doubts.

### Profile
- Create a personal profile with your name, email and profile picture.
- Display a personalised greeting on the dashboard.

### Reminders
- Add upcoming tests and their portions.
- The application can check for upcoming reminders while running.
- Optional Gmail reminders can be configured using environment variables.

---

## Tech Stack

- **Python**
- **Flask** – Web interface
- **Tkinter** – Desktop interface
- **SQLite** – Local data storage
- **Matplotlib** – Performance graphs

All data is stored locally on the user's device.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/anisring/Study-Dash.git
cd Study-Dash
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package:

```bash
pip install .
```

This installs the `study-dash` command and includes the application templates and static files. Personal data is not included in the package.

### Publish and install from GitHub Packages

The repository includes a GitHub Actions workflow that publishes a package when a version tag such as `v0.1.1` is pushed. To publish a new version:

```bash
git tag v0.1.2
git push origin v0.1.2
```

After the workflow completes, GitHub Packages will show the package. To install it from another device, create a GitHub token with package-read access and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --index-url https://__token__:YOUR_GITHUB_TOKEN@pypi.pkg.github.com/anisring/simple study-dash
```

Replace `YOUR_GITHUB_TOKEN` with a token that has package read access. The package workflow uses GitHub's automatic repository token for publishing.

---

## Running the Web App

```bash
study-dash
```

Open http://127.0.0.1:5000 in your browser.

You can also run directly from the repository:

```bash
python app.py
```

## Running the Desktop App

```bash
python study.py
```

---

## Local Data

The app creates local data in the directory from which it is run:

- `study_dash.db` – marks, goals, profile, and schedules.
- `profile/` – profile pictures.
- `thelibrary/` – uploaded question papers.

These files are ignored by Git and are not included when another user installs the package. A fresh installation therefore starts with an empty profile, empty marks history, and empty Library.

---

## Gmail Reminders

Add an email address on the Profile page. Gmail reminders use a Gmail App Password, not your regular Gmail password:

```bash
export STUDY_DASH_GMAIL_ADDRESS="your-gmail@gmail.com"
export STUDY_DASH_GMAIL_APP_PASSWORD="your-gmail-app-password"
study-dash
```

The Library checks for reminders while the app is being used and also provides a manual reminder button. Gmail OAuth is not implemented yet, and the App Password is read from environment variables rather than stored in the database.

### GitHub Packages authentication

If the GitHub Actions package upload returns `404 Not Found`, create a GitHub classic personal access token with the `write:packages` scope and add it to the repository as an Actions secret named `PACKAGES_TOKEN`:

**Repository Settings → Secrets and variables → Actions → New repository secret**

Use `PACKAGES_TOKEN` as the name. The publishing workflow will use it for GitHub Packages uploads.

---

## License

This project is for personal and educational use.
