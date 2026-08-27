from flask import Flask, jsonify, request, render_template, send_from_directory
import db
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/goals')
def goals_page():
    return render_template('goals.html')


@app.route('/api/tests', methods=['GET', 'POST'])
def api_tests():
    if request.method == 'GET':
        tests = db.get_tests(order_desc=False)
        return jsonify(tests)
    data = request.get_json() or {}
    # validate
    date = data.get('date')
    name = data.get('test_name')
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'Invalid date'}), 400
    if not name:
        return jsonify({'error': 'Test name required'}), 400
    try:
        p = int(data.get('physics', 0))
        c = int(data.get('chemistry', 0))
        m = int(data.get('maths', 0))
    except Exception:
        return jsonify({'error': 'Scores must be integers'}), 400
    for v in (p, c, m):
        if v < 0 or v > 60:
            return jsonify({'error': 'Scores must be 0-60'}), 400
    tid = db.add_test(date, name, p, c, m)
    return jsonify({'id': tid}), 201


@app.route('/api/tests/<int:tid>', methods=['PUT', 'DELETE'])
def api_test_modify(tid):
    if request.method == 'DELETE':
        db.delete_test(tid)
        return jsonify({'deleted': tid})
    data = request.get_json() or {}
    date = data.get('date')
    name = data.get('test_name')
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'Invalid date'}), 400
    try:
        p = int(data.get('physics', 0))
        c = int(data.get('chemistry', 0))
        m = int(data.get('maths', 0))
    except Exception:
        return jsonify({'error': 'Scores must be integers'}), 400
    db.update_test(tid, date, name, p, c, m)
    return jsonify({'updated': tid})


@app.route('/api/goals', methods=['GET', 'POST'])
def api_goals():
    if request.method == 'GET':
        goals = db.get_goals()
        # enhance goals with a computed current score and status
        enhanced = []
        tests_all = db.get_tests(order_desc=False)
        for g in goals:
            eg = dict(g)
            eg['current_score'] = None
            eg['status'] = 'no data'
            # if the goal references a specific test, include that test's total
            if eg.get('test_id'):
                t = db.get_test_by_id(eg['test_id'])
                if t:
                    eg['current_score'] = t.get('total')
                    eg['status'] = 'met' if t.get('total', 0) >= eg.get('target', 0) else 'pending'
                else:
                    eg['status'] = 'missing test'
            # otherwise if start/end provided, compute best total in that window
            elif eg.get('start_date') and eg.get('end_date'):
                try:
                    from datetime import datetime
                    sd = datetime.strptime(eg['start_date'], '%Y-%m-%d')
                    ed = datetime.strptime(eg['end_date'], '%Y-%m-%d')
                    best = None
                    for t in tests_all:
                        try:
                            td = datetime.strptime(t['date'], '%Y-%m-%d')
                        except Exception:
                            continue
                        if sd <= td <= ed:
                            if best is None or t.get('total', 0) > best:
                                best = t.get('total', 0)
                    if best is not None:
                        eg['current_score'] = best
                        eg['status'] = 'met' if best >= eg.get('target', 0) else 'pending'
                    else:
                        eg['status'] = 'no tests in window'
                except Exception:
                    eg['status'] = 'invalid window'
            enhanced.append(eg)
        return jsonify(enhanced)
    data = request.get_json() or {}
    name = data.get('name')
    gtype = data.get('type')
    try:
        target = int(data.get('target'))
    except Exception:
        return jsonify({'error': 'Target must be integer'}), 400
    start = data.get('start_date')
    end = data.get('end_date')
    test_id = data.get('test_id')
    gid = db.add_goal(name, gtype, target, start, end, test_id)
    return jsonify({'id': gid}), 201


@app.route('/api/goals/<int:gid>', methods=['PUT', 'DELETE'])
def api_goal_modify(gid):
    if request.method == 'DELETE':
        db.delete_goal(gid)
        return jsonify({'deleted': gid})
    data = request.get_json() or {}
    name = data.get('name')
    gtype = data.get('type')
    try:
        target = int(data.get('target'))
    except Exception:
        return jsonify({'error': 'Target must be integer'}), 400
    start = data.get('start_date')
    end = data.get('end_date')
    test_id = data.get('test_id')
    db.update_goal(gid, name, gtype, target, start, end, test_id)
    return jsonify({'updated': gid})


if __name__ == '__main__':
    db.init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
