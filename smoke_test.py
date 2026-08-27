import os
import db
import stats

DB_FILE = 'study_dash.db'

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

print('Initializing database...')
db.init_db()
print('Adding sample tests...')
db.add_test('2026-08-01', 'CET #1', 30, 28, 35)
db.add_test('2026-08-08', 'CET #2', 32, 30, 36)
db.add_test('2026-08-15', 'CET #3', 34, 33, 38)
print('Adding a sample goal...')
db.add_goal('CET #4', 'test', 120, '2026-08-22', None, None)

tests = db.get_tests(order_desc=False)
goals = db.get_goals()

print(f"\nSaved {len(tests)} tests:")
for t in tests:
    print(f"- {t['date']} {t['test_name']}: P{t['physics']} C{t['chemistry']} M{t['maths']} = {t['total']}")

print(f"\nSaved {len(goals)} goals:")
for g in goals:
    print(f"- {g['name']} ({g['type']}): target {g['target']} start {g.get('start_date')}")

print('\nComputing stats...')
st = stats.compute_basic_stats(tests)
for k,v in st.items():
    if isinstance(v, dict):
        print(f"{k}: {v}")
    else:
        print(f"{k}: {v}")

print('\nAnalysis:')
for line in stats.generate_analysis(tests):
    print('-', line)

print('\nSmoke test completed.')
