from datetime import date, timedelta

# Thursday-based window (local)
def week_start_thu(d: date) -> date:
    # Monday=0 ... Thursday=3
    offset = (d.weekday() - 3) % 7
    return d - timedelta(days=offset)

def window_for(d: date):
    start = week_start_thu(d)
    end   = start + timedelta(days=6)
    return start, end

def outcome(home:int, away:int) -> int:
    # home win=1, draw=0, away win=-1
    return (home>away) - (away>home)

def points_for(pred_home, pred_away, real_home, real_away) -> int:
    if real_home is None or real_away is None: return 0
    if pred_home==real_home and pred_away==real_away: return 3
    return 1 if outcome(pred_home, pred_away)==outcome(real_home, real_away) else 0