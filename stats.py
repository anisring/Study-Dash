from typing import List, Dict, Optional


def compute_basic_stats(tests: List[Dict]) -> Dict:
    if not tests:
        return {}
    totals = [t['total'] for t in tests]
    latest = tests[-1]
    best = max(totals)
    worst = min(totals)
    avg = sum(totals) / len(totals)
    improvement_from_first = latest['total'] - tests[0]['total'] if len(tests) >= 1 else 0
    improvement_from_prev = None
    if len(tests) >= 2:
        improvement_from_prev = latest['total'] - tests[-2]['total']
    # average improvement per test
    improvements = []
    for i in range(1, len(tests)):
        improvements.append(tests[i]['total'] - tests[i-1]['total'])
    avg_improvement = sum(improvements) / len(improvements) if improvements else None

    # subject totals
    subjects = ['physics', 'chemistry', 'maths']
    subj_avg = {s: sum(t[s] for t in tests) / len(tests) for s in subjects}
    subj_latest = {s: latest[s] for s in subjects}
    highest_subj = max(subj_avg, key=subj_avg.get)
    lowest_subj = min(subj_avg, key=subj_avg.get)

    return {
        'latest': latest['total'],
        'latest_obj': latest,
        'best': best,
        'worst': worst,
        'average': avg,
        'improvement_from_first': improvement_from_first,
        'improvement_from_prev': improvement_from_prev,
        'avg_improvement': avg_improvement,
        'highest_subject': highest_subj,
        'lowest_subject': lowest_subj,
        'subject_averages': subj_avg,
        'subject_latest': subj_latest,
    }


def generate_analysis(tests: List[Dict]) -> List[str]:
    lines = []
    stats = compute_basic_stats(tests)
    if not stats:
        return lines
    if stats.get('improvement_from_prev') is not None:
        d = stats['improvement_from_prev']
        if d > 0:
            lines.append(f"Your latest score is {d} marks higher than your previous test.")
        elif d < 0:
            lines.append(f"Your latest score is {abs(d)} marks lower than your previous test.")
    if stats.get('improvement_from_first'):
        d = stats['improvement_from_first']
        if d > 0:
            lines.append(f"You have improved by {d} marks since your first recorded test.")
        elif d < 0:
            lines.append(f"You have dropped by {abs(d)} marks since your first recorded test.")
    if stats.get('highest_subject'):
        lines.append(f"{stats['highest_subject'].title()} is currently your strongest subject.")
    if stats.get('avg_improvement'):
        ai = stats['avg_improvement']
        lines.append(f"Average improvement between tests: {ai:.1f} marks.")
    return lines
