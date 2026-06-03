"""만세력·신살·대운 관련 순수 계산 함수.

2차 정리: 루트 `app.py` 의존 제거를 위해 여기서 직접 구현합니다.
"""

from __future__ import annotations

import datetime
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from korean_lunar_calendar import KoreanLunarCalendar


GAN_ORDER = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
JIAZI_60 = [GAN_ORDER[i % 10] + ZHI_ORDER[i % 12] for i in range(60)]

# 자시(子時) 경계: 23:30 ~ 다음날 01:29 (표준 30분 경계)
ZI_HOUR_START_MIN = 23 * 60 + 30
ZI_HOUR_END_MIN = 1 * 60 + 29


def solar_ymd_for_birth(
    y: int, m: int, d: int, is_lunar: bool, is_leap: bool
) -> tuple[int, int, int]:
    if not is_lunar:
        return int(y), int(m), int(d)
    klc = KoreanLunarCalendar()
    if not klc.setLunarDate(int(y), int(m), int(d), bool(is_leap)):
        return int(y), int(m), int(d)
    return int(klc.solarYear), int(klc.solarMonth), int(klc.solarDay)


def parse_chinese_gapja_three_pillars(klc: KoreanLunarCalendar) -> tuple[str, str, str]:
    raw = klc.getChineseGapJaString()
    parts = raw.split()
    pillars: list[str] = []
    for tok in parts:
        t = str(tok).strip()
        if not t or t.startswith("("):
            break
        if len(t) < 2:
            continue
        pillars.append(t[0] + t[1])
        if len(pillars) >= 3:
            break
    if len(pillars) < 3:
        raise ValueError(f"gapja parse fail: {raw!r}")
    return pillars[0], pillars[1], pillars[2]


def _hour_branch_from_hour(h: int) -> str:
    # 2시간 단위. 23시는 子로 취급(단순). (레거시·대표시각용)
    idx = ((int(h) + 1) // 2) % 12
    return ZHI_ORDER[idx]


def _in_minute_range(minute_of_day: int, start_min: int, end_min: int) -> bool:
    if start_min <= end_min:
        return start_min <= minute_of_day <= end_min
    return minute_of_day >= start_min or minute_of_day <= end_min


def minute_of_day_to_branch(minute_of_day: int, *, zi_boundary: str | None = None) -> str:
    """30분 경계 시진(地支). 자시는 23:30~01:29 고정."""
    _ = zi_boundary
    minute = int(minute_of_day)
    if _in_minute_range(minute, ZI_HOUR_START_MIN, ZI_HOUR_END_MIN):
        return "子"
    if _in_minute_range(minute, 1 * 60 + 30, 3 * 60 + 29):
        return "丑"
    if _in_minute_range(minute, 3 * 60 + 30, 5 * 60 + 29):
        return "寅"
    if _in_minute_range(minute, 5 * 60 + 30, 7 * 60 + 29):
        return "卯"
    if _in_minute_range(minute, 7 * 60 + 30, 9 * 60 + 29):
        return "辰"
    if _in_minute_range(minute, 9 * 60 + 30, 11 * 60 + 29):
        return "巳"
    if _in_minute_range(minute, 11 * 60 + 30, 13 * 60 + 29):
        return "午"
    if _in_minute_range(minute, 13 * 60 + 30, 15 * 60 + 29):
        return "未"
    if _in_minute_range(minute, 15 * 60 + 30, 17 * 60 + 29):
        return "申"
    if _in_minute_range(minute, 17 * 60 + 30, 19 * 60 + 29):
        return "酉"
    if _in_minute_range(minute, 19 * 60 + 30, 21 * 60 + 29):
        return "戌"
    if _in_minute_range(minute, 21 * 60 + 30, 23 * 60 + 29):
        return "亥"
    return "子"


_BIRTH_TIME_LABEL_BRANCH: dict[str, str] = {
    "자(23:30~01:29)": "子",
    "축(01:30~03:29)": "丑",
    "인(03:30~05:29)": "寅",
    "묘(05:30~07:29)": "卯",
    "진(07:30~09:29)": "辰",
    "사(09:30~11:29)": "巳",
    "오(11:30~13:29)": "午",
    "미(13:30~15:29)": "未",
    "신(15:30~17:29)": "申",
    "유(17:30~19:29)": "酉",
    "술(19:30~21:29)": "戌",
    "해(21:30~23:29)": "亥",
}


def birth_time_str_to_branch(t_str: str, *, zi_boundary: str | None = None) -> str | None:
    """입력 시각(시계·시지 선택) → 시진 지지."""
    _ = zi_boundary
    label = str(t_str or "").strip()
    if not label or label == "모름":
        return None
    if label in _BIRTH_TIME_LABEL_BRANCH:
        return _BIRTH_TIME_LABEL_BRANCH[label]
    minute = time_str_to_minute_of_day(label)
    if minute is not None:
        return minute_of_day_to_branch(minute)
    rep_h = convert_time_str_to_hour(label)
    if rep_h is None:
        return None
    return _hour_branch_from_hour(rep_h)


def _calculate_siju_with_branch(day_stem: str, branch: str) -> str:
    start_map = {
        "甲": "甲",
        "己": "甲",
        "乙": "丙",
        "庚": "丙",
        "丙": "戊",
        "辛": "戊",
        "丁": "庚",
        "壬": "庚",
        "戊": "壬",
        "癸": "壬",
    }
    start = start_map.get(day_stem, "甲")
    stem = GAN_ORDER[(GAN_ORDER.index(start) + ZHI_ORDER.index(branch)) % 10]
    return stem + branch


def calculate_siju_from_birth_time(
    day_stem: str,
    birth_time_str: str,
    *,
    zi_boundary: str | None = None,
) -> str:
    """일간 + 사용자 입력 시각(30분 경계)으로 시주 간지."""
    branch = birth_time_str_to_branch(birth_time_str, zi_boundary=zi_boundary)
    if not branch:
        raise ValueError(f"시각 해석 실패: {birth_time_str!r}")
    return _calculate_siju_with_branch(day_stem, branch)


def calculate_siju(day_stem: str, hour: int) -> str:
    """일간 + 시각(0~23)으로 시주 간지(간단)."""
    br = _hour_branch_from_hour(hour)
    return _calculate_siju_with_branch(day_stem, br)


def time_str_to_minute_of_day(t_str: str) -> int | None:
    """HH:MM 입력만 분 단위로 해석합니다. 선택형 시지 라벨은 None을 반환합니다."""
    try:
        s = str(t_str or "").strip()
        if ":" not in s:
            return None
        hh_s, mm_s = s.split(":", 1)
        hh = int(hh_s.strip())
        mm = int(mm_s.strip())
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh * 60 + mm
    except Exception:
        return None
    return None


def get_saju_data(
    y: int,
    m: int,
    d: int,
    h: int | None,
    is_lunar: bool,
    is_leap: bool,
    birth_time_str: str | None = None,
    month_method: str = "lichun_lunar",
    **_: Any,
) -> list[str]:
    """사주 계산(연/월/일/시).

    month_method:
      - "library": KLC(만세력) 연/월/일 그대로 사용
      - "lichun_lunar": 입춘 연주 + (만세력 월지) + 연간에 맞춘 월간 재합성
      - "solar_terms" / "solar_terms_precise": 입춘 연주 + 12절(절입) 월지로 월주 구성
    """
    klc = KoreanLunarCalendar()
    if is_lunar:
        if not klc.setLunarDate(int(y), int(m), int(d), bool(is_leap)):
            raise ValueError("음력 날짜가 지원 범위를 벗어났습니다.")
    else:
        if not klc.setSolarDate(int(y), int(m), int(d)):
            raise ValueError("양력 날짜가 지원 범위를 벗어났습니다.")

    sy, sm, sd = int(klc.solarYear), int(klc.solarMonth), int(klc.solarDay)
    birth_label = str(birth_time_str or "").strip()

    klc.setSolarDate(sy, sm, sd)
    ch_y, ch_m, ch_d = parse_chinese_gapja_three_pillars(klc)

    if month_method == "library":
        out = [ch_y, ch_m, ch_d]
    else:
        year_pillar = get_bazi_year_pillar_lichun(sy, sm, sd, h)
        kst = ZoneInfo("Asia/Seoul")
        hour_for_terms = int(h) if h is not None else 12
        dt_kst = datetime.datetime(sy, sm, sd, hour_for_terms, 0, tzinfo=kst)

        if month_method in ("solar_terms", "solar_terms_precise"):
            month_branch = get_month_branch_by_solar_terms(sy, sm, sd, dt_kst=dt_kst)
        else:
            month_branch = ch_m[1] if len(ch_m) >= 2 else "寅"

        month_pillar = calc_month_stem(year_pillar[0], month_branch) + month_branch
        out = [year_pillar, month_pillar, ch_d]

    if h is None:
        out.append("모름")
    else:
        day_stem = out[2][0] if len(out) > 2 and out[2] else "甲"
        if birth_label and birth_label != "모름":
            out.append(calculate_siju_from_birth_time(day_stem, birth_label))
        else:
            out.append(calculate_siju(day_stem, int(h)))
    return out


def convert_time_str_to_hour(t_str: str, zi_boundary: str | None = None) -> int | None:
    """태어난 시간 문자열을 24시간 정수(시진 대표 시각)로 변환. 자시는 23:30~01:29."""
    _ = zi_boundary
    if t_str == "모름":
        return None

    try:
        s = str(t_str).strip()
        if ":" in s:
            minute_of_day = time_str_to_minute_of_day(s)
            if minute_of_day is not None:
                branch = minute_of_day_to_branch(minute_of_day)
                branch_to_rep_hour = {
                    "子": 0,
                    "丑": 2,
                    "寅": 4,
                    "卯": 6,
                    "辰": 8,
                    "巳": 10,
                    "午": 12,
                    "未": 14,
                    "申": 16,
                    "酉": 18,
                    "戌": 20,
                    "亥": 22,
                }
                return branch_to_rep_hour.get(branch, 12)
    except Exception:
        pass

    mapping = {
        "자(23:30~01:29)": 0,
        "축(01:30~03:29)": 2,
        "인(03:30~05:29)": 4,
        "묘(05:30~07:29)": 6,
        "진(07:30~09:29)": 8,
        "사(09:30~11:29)": 10,
        "오(11:30~13:29)": 12,
        "미(13:30~15:29)": 14,
        "신(15:30~17:29)": 16,
        "유(17:30~19:29)": 18,
        "술(19:30~21:29)": 20,
        "해(21:30~23:29)": 22,
    }
    return mapping.get(str(t_str), 12)


def _ephem_sun_ecliptic_lon_deg(ephem_mod, dt_utc: datetime.datetime) -> float:
    obs = ephem_mod.Observer()
    obs.date = ephem_mod.Date(dt_utc)
    sun = ephem_mod.Sun(obs)
    ecl = ephem_mod.Ecliptic(sun)
    lon = float(ecl.lon)  # radians
    return (lon * 180.0 / 3.141592653589793) % 360.0


def _ang_diff_deg(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


@lru_cache(maxsize=256)
def get_jeolip_times_kst(year: int) -> dict[str, datetime.datetime]:
    """12절(절입) 시각(KST). ephem 필요."""
    try:
        import ephem as ephem_mod  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("ephem not installed") from e

    targets: list[tuple[str, float, tuple[int, int]]] = [
        ("寅", 315.0, (2, 4)),
        ("卯", 345.0, (3, 6)),
        ("辰", 15.0, (4, 5)),
        ("巳", 45.0, (5, 6)),
        ("午", 75.0, (6, 6)),
        ("未", 105.0, (7, 7)),
        ("申", 135.0, (8, 7)),
        ("酉", 165.0, (9, 8)),
        ("戌", 195.0, (10, 8)),
        ("亥", 225.0, (11, 7)),
        ("子", 255.0, (12, 7)),
        ("丑", 285.0, (1, 5)),
    ]

    def find_crossing_kst(branch: str, target_lon: float, approx_md: tuple[int, int]) -> datetime.datetime:
        kst = ZoneInfo("Asia/Seoul")
        approx_local = datetime.datetime(year, approx_md[0], approx_md[1], 12, 0, tzinfo=kst)
        center_utc = approx_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        step = datetime.timedelta(hours=3)
        start = center_utc - datetime.timedelta(days=3)
        end = center_utc + datetime.timedelta(days=3)

        prev_t = start
        prev_f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, prev_t), target_lon)

        t = start + step
        bracket: tuple[datetime.datetime, datetime.datetime] | None = None
        while t <= end:
            f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, t), target_lon)
            if (prev_f <= 0 <= f) or (f <= 0 <= prev_f):
                bracket = (prev_t, t)
                break
            prev_t, prev_f = t, f
            t += step

        if not bracket:
            start2 = center_utc - datetime.timedelta(days=8)
            end2 = center_utc + datetime.timedelta(days=8)
            prev_t = start2
            prev_f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, prev_t), target_lon)
            t = start2 + step
            while t <= end2:
                f = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, t), target_lon)
                if (prev_f <= 0 <= f) or (f <= 0 <= prev_f):
                    bracket = (prev_t, t)
                    break
                prev_t, prev_f = t, f
                t += step

        if not bracket:
            raise RuntimeError(f"Failed to bracket term {branch} {target_lon}")

        lo, hi = bracket
        for _ in range(60):
            mid = lo + (hi - lo) / 2
            fmid = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, mid), target_lon)
            flo = _ang_diff_deg(_ephem_sun_ecliptic_lon_deg(ephem_mod, lo), target_lon)
            if (flo <= 0 <= fmid) or (fmid <= 0 <= flo):
                hi = mid
            else:
                lo = mid
            if (hi - lo).total_seconds() < 1:
                break
        best_utc = hi
        return best_utc.replace(tzinfo=datetime.timezone.utc).astimezone(kst)

    out: dict[str, datetime.datetime] = {}
    for br, lon, md in targets:
        out[br] = find_crossing_kst(br, lon, md)
    return out


@lru_cache(maxsize=4096)
def get_month_branch_by_solar_terms(
    y: int, m: int, d: int, dt_kst: datetime.datetime | None = None
) -> str:
    kst = ZoneInfo("Asia/Seoul")
    dt_kst = dt_kst or datetime.datetime(y, m, d, 12, 0, tzinfo=kst)
    try:
        this_year = get_jeolip_times_kst(y)
        prev_year = get_jeolip_times_kst(y - 1)
        candidates: list[tuple[datetime.datetime, str]] = []
        candidates.append((prev_year["子"], "子"))
        for br, t in this_year.items():
            candidates.append((t, br))
        candidates.sort(key=lambda x: x[0])
        latest = "丑"
        for t, br in candidates:
            if t <= dt_kst:
                latest = br
            else:
                break
        return latest
    except Exception:
        terms = [
            ((1, 5), "丑"),
            ((2, 4), "寅"),
            ((3, 6), "卯"),
            ((4, 5), "辰"),
            ((5, 6), "巳"),
            ((6, 6), "午"),
            ((7, 7), "未"),
            ((8, 7), "申"),
            ((9, 8), "酉"),
            ((10, 8), "戌"),
            ((11, 7), "亥"),
            ((12, 7), "子"),
        ]
        today = dt_kst.date()
        candidates2: list[tuple[datetime.date, str]] = []
        for (tm, td), br in terms:
            candidates2.append((datetime.date(y, tm, td), br))
        candidates2.sort(key=lambda x: x[0])
        latest2: str | None = None
        for t_date, br in candidates2:
            if t_date <= today:
                latest2 = br
            else:
                break
        return latest2 or "丑"


def calc_month_stem(year_stem: str, month_branch: str) -> str:
    start_map = {
        "甲": "丙",
        "己": "丙",
        "乙": "戊",
        "庚": "戊",
        "丙": "庚",
        "辛": "庚",
        "丁": "壬",
        "壬": "壬",
        "戊": "甲",
        "癸": "甲",
    }
    branches = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
    start = start_map.get(year_stem, "丙")
    try:
        idx = branches.index(month_branch)
    except ValueError:
        idx = 0
    return GAN_ORDER[(GAN_ORDER.index(start) + idx) % 10]


@lru_cache(maxsize=4096)
def get_bazi_year_pillar_lichun(y: int, m: int, d: int, h: int | None) -> str:
    hh = int(h) if h is not None else 12
    kst = ZoneInfo("Asia/Seoul")
    dt_kst = datetime.datetime(y, m, d, hh, 0, tzinfo=kst)
    try:
        lip_this = get_jeolip_times_kst(y)["寅"]
        y_ref = y - 1 if dt_kst < lip_this else y
    except Exception:
        lip_approx = datetime.datetime(y, 2, 4, 12, 0, tzinfo=kst)
        y_ref = y - 1 if dt_kst < lip_approx else y
    idx = (int(y_ref) - 1984) % 60
    return JIAZI_60[idx]


def daewoon_is_forward(year_stem: str, gender: str) -> bool:
    yang = year_stem in ("甲", "丙", "戊", "庚", "壬")
    g = str(gender or "")
    male = any(x in g for x in ("남", "男", "M", "m"))
    return (yang and male) or (not yang and not male)


def compute_daewoon_schedule(
    u_gapja: list[str],
    record,
    gender: str,
    birth_year: int,
    *,
    zi_boundary: str = "23:30",
    n_terms: int = 10,
) -> dict[str, Any]:
    """월주·연간·성별로 대운 순역 + 출생 시각과 절입 간 일수로 첫 대운 입연 나이 산출.

    record 불완전/절입 계산 실패 시 start_age=0 (구버전 호환).
    """
    month_ganji = u_gapja[1] if len(u_gapja) > 1 else "丙寅"
    year_stem = u_gapja[0][0] if u_gapja and u_gapja[0] else "甲"
    forward = daewoon_is_forward(year_stem, gender)
    try:
        start_idx = JIAZI_60.index(month_ganji)
    except Exception:
        start_idx = 0

    birth_dt = birth_kst_datetime_from_record(record, zi_boundary=zi_boundary)
    start_age = 0
    days_to_jie = 0
    if birth_dt:
        adj = _adjacent_jie_for_daewoon(birth_dt, forward)
        if adj is not None:
            if forward:
                days_to_jie = max(1, int((adj - birth_dt).total_seconds() // 86400))
            else:
                days_to_jie = max(1, int((birth_dt - adj).total_seconds() // 86400))
            start_age = daewoon_start_age_years_from_days(days_to_jie)

    rows: list[dict[str, Any]] = []
    for k in range(1, n_terms + 1):
        idx = (start_idx + k) % 60 if forward else (start_idx - k) % 60
        pillar = JIAZI_60[idx]
        if start_age == 0 and birth_dt is None:
            age_start = (k - 1) * 10
        else:
            age_start = start_age + (k - 1) * 10
        age_end = age_start + 9
        rows.append(
            {
                "k": k,
                "pillar": pillar,
                "age_start": age_start,
                "age_end": age_end,
                "year_start": int(birth_year) + age_start,
                "year_end": int(birth_year) + age_end,
            }
        )

    return {
        "forward": forward,
        "year_stem": year_stem,
        "start_age": start_age,
        "days_to_jie": days_to_jie,
        "rows": rows,
    }


def birth_kst_datetime_from_record(
    record,
    *,
    zi_boundary: str = "23:30",
) -> datetime.datetime | None:
    if not record or not isinstance(record, (list, tuple)) or len(record) < 6:
        return None
    y, m, d, t_str, is_lunar, is_leap = record[:6]
    try:
        h = convert_time_str_to_hour(str(t_str), zi_boundary=zi_boundary)
        hour_for_dt = int(h) if h is not None else 12
        sy, sm, sd = solar_ymd_for_birth(int(y), int(m), int(d), bool(is_lunar), bool(is_leap))
        kst = ZoneInfo("Asia/Seoul")
        return datetime.datetime(sy, sm, sd, hour_for_dt, tzinfo=kst)
    except Exception:
        return None


def _collect_jie_datetimes(y0: int, y1: int) -> list[datetime.datetime]:
    out: list[datetime.datetime] = []
    for yy in range(int(y0), int(y1) + 1):
        try:
            out.extend(list(get_jeolip_times_kst(yy).values()))
        except Exception:
            continue
    out.sort()
    uniq: list[datetime.datetime] = []
    for t in out:
        if not uniq or abs((t - uniq[-1]).total_seconds()) > 30:
            uniq.append(t)
    return uniq


def _adjacent_jie_for_daewoon(birth_dt: datetime.datetime, forward: bool) -> datetime.datetime | None:
    times = _collect_jie_datetimes(birth_dt.year - 1, birth_dt.year + 2)
    if not times:
        return None
    prev_t = max((t for t in times if t < birth_dt), default=None)
    next_t = min((t for t in times if t > birth_dt), default=None)
    if forward:
        if next_t is None:
            times2 = _collect_jie_datetimes(birth_dt.year + 2, birth_dt.year + 6)
            next_t = min((t for t in times2 if t > birth_dt), default=None)
        return next_t
    if prev_t is None:
        times2 = _collect_jie_datetimes(birth_dt.year - 6, birth_dt.year - 1)
        prev_t = max((t for t in times2 if t < birth_dt), default=None)
    return prev_t


def daewoon_start_age_years_from_days(days: int) -> int:
    return max(1, (int(days) + 2) // 3)



