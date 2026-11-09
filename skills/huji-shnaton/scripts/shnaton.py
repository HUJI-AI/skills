#!/usr/bin/env python3
"""Read the Hebrew University course catalog (the Shnaton) from its public API.

Read-only. Every command sends GET requests, except `search`, which sends the
same POST query that the catalog website sends for its course search. Uses
only the Python standard library (3.8 or later); no login or key is needed.

Examples:

  python3 shnaton.py years
  python3 shnaton.py course 67101 --sessions
  python3 shnaton.py syllabus 67101 --lang en
  python3 shnaton.py exams 67101
  python3 shnaton.py prereqs 67504
  python3 shnaton.py search "machine learning" --semester B --language en
  python3 shnaton.py programs "מדעי המחשב" --start-year 2026
  python3 shnaton.py program 521-3010 --start-year 2026
  python3 shnaton.py programs-with 67101 --start-year 2026
  python3 shnaton.py cornerstone --semester A
  python3 shnaton.py timetable 67101:1-01,2-02 80131 80134 --semester A

Common options, after the command: --year (catalog year, default: the current
one), --lang he|en (default he), --json (print the raw API response instead).
"""

import argparse
import html
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

BASE = os.environ.get("SHNATON_API", "https://shnaton.huji.ac.il/api").rstrip("/")
SITE = "https://shnaton.huji.ac.il"
USER_AGENT = (
    "huji-shnaton-skill/1.0 "
    "(+https://ai.huji.ac.il/skills/huji-shnaton/)"
)
CORNERSTONE_DEPARTMENT = "334"  # what the website's cornerstone page reads

# Course periods, as `coursePeriod` and the search's `semesters` use them.
SEMESTERS = {"a": 1, "b": 2, "a-or-b": 3, "summer": 4, "yearly": 5}
# Group and session periods are numbered differently: 1 = A, 2 = B,
# 3 = summer, 4 = A + B (a yearly group, whose sessions carry 1 or 2).
SESSION_PERIODS = {"a": {1}, "b": {2}, "summer": {3}}
DAYS = {
    "he": ["יום א'", "יום ב'", "יום ג'", "יום ד'", "יום ה'", "יום ו'", "שבת"],
    "en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
}
DAY_INPUT = {d: i for i, d in enumerate(["sun", "mon", "tue", "wed", "thu", "fri"])}
LANGUAGES = {"he": "0", "hebrew": "0", "en": "2", "english": "2", "ar": "1", "arabic": "1"}
MOED = {
    "he": {1: "מועד א'", 2: "מועד ב'", 3: "מועד ג'", 4: "מועד מיוחד"},
    "en": {1: "Moed A", 2: "Moed B", 3: "Moed C", 4: "Special term"},
}
WORDS = {
    "he": {
        "all": "כל אלה:", "one": "אחד מאלה:", "min_grade": "ציון מינימלי",
        "years": "שנים", "year": "שנה", "at_least": "לפחות", "at_most": "לכל היותר",
        "recorded": "מוקלט", "live": "שידור חי", "every": "אחת ל־{} שבועות",
        "no_time": "ללא מועד קבוע", "no_room": "ללא חדר", "dates": "מפגשים",
    },
    "en": {
        "all": "all of:", "one": "one of:", "min_grade": "minimum grade",
        "years": "years", "year": "year", "at_least": "at least", "at_most": "at most",
        "recorded": "recorded", "live": "live broadcast", "every": "every {} weeks",
        "no_time": "no fixed time", "no_room": "no room listed", "dates": "meetings",
    },
}


class Failure(Exception):
    pass


# ── HTTP ────────────────────────────────────────────────────────────────


def api(path, params=None, body=None, missing_ok=False):
    url = BASE + path
    if params:
        url += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=data, headers=headers), timeout=60) as response:
            raw = response.read()
            kind = response.headers.get("Content-Type", "")
    except HTTPError as e:
        if e.code == 404 and missing_ok:
            return None
        detail = e.read()[:300].decode("utf-8", "replace").strip()
        raise Failure(f"HTTP {e.code} from {url}: {detail}")
    except URLError as e:
        raise Failure(f"could not reach {url}: {e.reason}")
    if not raw:
        return None
    if "json" not in kind:
        raise Failure(
            f"{url} returned {kind or 'an unknown type'}, not data. The service may be "
            f"unavailable or asking for a browser check; use {SITE} in a browser."
        )
    return json.loads(raw)


def current_year():
    years = api("/reference-data/active-years") or []
    for y in years:
        if y.get("current"):
            return y["year"]
    if not years:
        raise Failure("the catalog listed no years")
    return max(y["year"] for y in years)


# ── Formatting ──────────────────────────────────────────────────────────


def say(pair, lang):
    """A {"he": ..., "en": ...} value in the chosen language, else the other."""
    if not isinstance(pair, dict):
        return "" if pair is None else str(pair).strip()
    other = "en" if lang == "he" else "he"
    return (pair.get(lang) or "").strip() or (pair.get(other) or "").strip()


def plain(value):
    """Catalog notes are HTML; print them as text."""
    if not value:
        return ""
    value = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</div>", "\n", value)
    value = re.sub(r"(?i)<li[^>]*>", "- ", value)
    value = html.unescape(re.sub(r"<[^>]+>", "", value)).replace("\r", "")
    lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in value.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def clock(ms):
    if ms is None:
        return "?"
    minutes = ms // 60000
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def day_name(day, lang):
    return DAYS[lang][day] if isinstance(day, int) and 0 <= day < 7 else "?"


def points(value):
    if value is None:
        return "?"
    return str(int(value)) if float(value).is_integer() else str(value)


def credits(value, lang):
    if lang == "he":
        return f'{points(value)} נ"ז'
    return f"{points(value)} credit" + ("" if value is not None and float(value) == 1 else "s")


def date_only(stamp):
    return (stamp or "")[:10]


def exam_rows(tasks, lang, periods=None):
    """(date or "", printable line, course period) for each scheduled exam term,
    in date order with undated terms last."""
    rows = []
    for t in tasks:
        what = say((t.get("assignmentDefinition") or {}).get("name"), lang)
        for e in t.get("schedules") or []:
            if periods and e.get("period") not in periods:
                continue
            day = date_only(e.get("startTime"))
            when = day or ("טרם נקבע מועד" if lang == "he" else "Date TBD")
            hour = (e.get("startTime") or "")[11:16]
            if hour and hour != "00:00":
                when += f" {hour}"
            rooms = ", ".join(say(r.get("name"), lang) if isinstance(r, dict) else str(r) for r in e.get("rooms") or [])
            moed = MOED[lang].get(e.get("moed"), str(e.get("moed")))
            parts = [say(e.get("periodName"), lang), moed, when, what, rooms]
            rows.append((day, " · ".join(p for p in parts if p), e.get("period") or 0))
    return sorted(rows, key=lambda r: (r[0] == "", r[0], r[2]))


def heading(c, lang):
    other = "en" if lang == "he" else "he"
    name, alt = say(c.get("name"), lang), (c.get("name") or {}).get(other) or ""
    alt = alt.strip()
    return f"{c.get('code')}  {name}" + (f" ({alt})" if alt and alt != name else "")


def course_line(c, lang):
    parts = [heading(c, lang), credits(c.get("academicPoints"), lang)]
    if c.get("coursePeriodName"):
        parts.append(say(c["coursePeriodName"], lang))
    if c.get("departmentName"):
        parts.append(say(c["departmentName"], lang))
    return " · ".join(parts)


def show_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def requirement_tree(node, lang, depth=0):
    """Prerequisite trees are COURSE leaves under AND / OR nodes."""
    w, pad = WORDS[lang], "  " * depth
    kind = node.get("type")
    if kind == "COURSE":
        grade = f" ({w['min_grade']} {node['minGrade']})" if node.get("minGrade") is not None else ""
        return [f"{pad}- {node.get('courseCode')} {say(node.get('courseName'), lang)}{grade}"]
    if kind in ("AND", "OR"):
        lines = [f"{pad}- {w['all'] if kind == 'AND' else w['one']}"]
        for child in node.get("children") or []:
            lines += requirement_tree(child, lang, depth + 1)
        return lines
    return [f"{pad}- {json.dumps(node, ensure_ascii=False)}"]


def parse_tree(value):
    if not value:
        return None
    return json.loads(value) if isinstance(value, str) else value


# ── Lookups ─────────────────────────────────────────────────────────────


def find_course(code, year, include):
    found = api(f"/courses/code/{quote(code)}", {"year": year, "include": include}, missing_ok=True)
    if not found:
        raise Failure(
            f"course {code} is not in the {year} catalog. Check the number, or try "
            f"another --year or a `search` by name."
        )
    return found[0]


def session_line(s, lang):
    w = WORDS[lang]
    if s.get("dayOfWeek") is None or s.get("startTime") is None:
        when = w["no_time"]
    else:
        when = f"{day_name(s['dayOfWeek'], lang)} {clock(s['startTime'])}-{clock(s.get('endTime'))}"
    parts = [when]
    room = s.get("room")
    if room:
        place = say(room.get("name"), lang)
        building = room.get("building") or {}
        if building and say(building.get("name"), lang) not in place:
            place += f", {say(building.get('name'), lang)}"
            campus = building.get("campus") or {}
            if campus:
                place += f" ({say(campus.get('name'), lang)})"
        parts.append(place)
    elif s.get("dayOfWeek") is not None:
        parts.append(w["no_room"])
    teachers = [say(t.get("name"), lang) for t in s.get("teachers") or []]
    if teachers:
        parts.append(", ".join(t for t in teachers if t))
    if s.get("isRecorded"):
        parts.append(w["recorded"])
    if s.get("isLiveBroadcast"):
        parts.append(w["live"])
    if s.get("calendarFrequency"):
        parts.append(w["every"].format(s["calendarFrequency"]))
    dates = sorted(date_only(d.get("date")) for d in s.get("studySessionSchedules") or [] if d.get("date"))
    if dates:
        parts.append(f"{len(dates)} {w['dates']} {dates[0]} – {dates[-1]}")
    return " · ".join(parts)


def group_title(g, lang):
    parts = [g.get("code") or "?", say(g.get("studySessionTypeName"), lang), say(g.get("periodName"), lang)]
    if g.get("languageName"):
        parts.append(say(g["languageName"], lang))
    return " · ".join(p for p in parts if p)


# ── Commands ────────────────────────────────────────────────────────────


def cmd_years(a):
    years = api("/reference-data/active-years")
    if a.json:
        return show_json(years)
    for y in sorted(years, key=lambda y: -y["year"]):
        mark = "  (current)" if y.get("current") else ""
        print(f"{y['year']}  {y.get('hebrewYear', '')}{mark}")


def cmd_faculties(a):
    faculties = api("/faculties")
    if a.json:
        return show_json(faculties)
    for f in sorted(faculties, key=lambda f: f["code"]):
        print(f"{f['code']}  {say(f['name'], a.lang)}")


def cmd_departments(a):
    code = a.faculty.zfill(3)
    departments = api(f"/faculties/{quote(code)}/departments", {"year": a.year})
    if a.json:
        return show_json(departments)
    if not departments:
        raise Failure(f"no departments for faculty {code} in {a.year}; see `faculties` for codes")
    for d in sorted(departments, key=lambda d: d["code"]):
        print(f"{d['code']}  {say(d['name'], a.lang)}")


def cmd_course(a):
    c = find_course(a.code, a.year, 2 if a.sessions else 1)
    if a.json:
        return show_json(c)
    print(heading(c, a.lang))
    print(f"{say(c.get('departmentName'), a.lang)} · {say(c.get('facultyName'), a.lang)}")
    facts = [credits(c.get("academicPoints"), a.lang), say(c.get("coursePeriodName"), a.lang)]
    if c.get("courseStructureType"):
        facts.append(c["courseStructureType"].strip())
    if c.get("totalHours"):
        facts.append(f"{c['totalHours']} h" if a.lang == "en" else f"{c['totalHours']} שעות")
    print(" · ".join(f for f in facts if f))
    note = plain(say(c.get("remark"), a.lang))
    if note:
        print(f"\n{note}")
    groups = sorted(c.get("groups") or [], key=lambda g: (g.get("period") or 0, g.get("code") or ""))
    if groups:
        print()
    for g in groups:
        print(f"[{group_title(g, a.lang)}]")
        mine, course = g.get("remark") or {}, c.get("remark") or {}
        repeated = any(plain(mine.get(k)) and plain(mine.get(k)) == plain(course.get(k)) for k in ("he", "en"))
        own = plain(say(mine, a.lang))
        if own and not repeated:
            print(f"  {own}")
        for s in sorted(g.get("studySessions") or [], key=lambda s: (s.get("period") or 0, s.get("dayOfWeek") or 0, s.get("startTime") or 0)):
            print(f"  {session_line(s, a.lang)}")
    if groups and not a.sessions:
        print("\n(add --sessions for days, times, rooms and lecturers)")
    print(f"\n{SITE}/course/{a.code}/year/{a.year}")


SYLLABUS_FIELDS = [
    ("teachers", "מרצים", "Teachers"),
    ("courseCoordinator", "רכז הקורס", "Course coordinator"),
    ("officeHours", "שעות קבלה", "Office hours"),
    ("teachingLanguage", "שפת הוראה", "Language of instruction"),
    ("courseDescription", "תיאור הקורס", "Description"),
    ("courseAims", "מטרות הקורס", "Aims"),
    ("learningOutcomes", "תוצרי למידה", "Learning outcomes"),
    ("courseContent", "תוכן הקורס", "Content"),
    ("teachingMethod", "שיטת הוראה", "Teaching method"),
    ("attendanceRequirements", "דרישות נוכחות", "Attendance requirements"),
    ("requiredReading", "קריאת חובה", "Required reading"),
    ("additionalReading", "קריאה נוספת", "Additional reading"),
    ("evaluation", "הערכה", "Evaluation"),
    ("additionalInfo", "מידע נוסף", "Additional information"),
]


def grade_lines(grades, lang):
    lines = []
    for g in grades or []:
        group = say(g.get("groupName"), lang)
        weight = f"{points(g['weight'])}%" if g.get("weight") is not None else "?"
        lines.append(f"- {say(g.get('name'), lang)}" + (f" ({group})" if group else "") + f": {weight}")
    return lines


def cmd_syllabus(a):
    s = api("/syllabus", {"courseCode": a.code, "year": a.year}, missing_ok=True)
    if a.json:
        return show_json(s)
    if not s or not say(s.get("courseName"), a.lang):
        raise Failure(f"no syllabus published for {a.code} in {a.year}")
    he = a.lang == "he"
    print(f"{s.get('courseCode')}  {say(s.get('courseName'), a.lang)}")
    print(" · ".join(x for x in [
        say(s.get("department"), a.lang), say(s.get("degreeName"), a.lang), say(s.get("periodName"), a.lang),
        credits(s["creditPoints"], a.lang) if s.get("creditPoints") else "",
    ] if x))
    for key, label_he, label_en in SYLLABUS_FIELDS:
        value = plain(say(s.get(key), a.lang))
        if value:
            print(f"\n## {label_he if he else label_en}\n{value}")
    grades = grade_lines(s.get("grades"), a.lang)
    if grades:
        print(f"\n## {'מרכיבי הציון' if he else 'Grade components'}")
        print("\n".join(grades))
    if s.get("updateDate"):
        print(f"\n({'עודכן' if he else 'Updated'} {date_only(s['updateDate'])})")
    print(f"{SITE}/course/{a.code}/syllabus/year/{a.year}")


def cmd_exams(a):
    he = a.lang == "he"
    c = find_course(a.code, a.year, 1)
    grades = api(f"/courses/code/{quote(a.code)}/grades", {"year": a.year}, missing_ok=True)
    tasks = api("/assignments", {"year": a.year, "courseId": c["id"]}) or []
    if a.json:
        return show_json({"grades": grades, "assignments": tasks})
    print(heading(c, a.lang))
    print(f"\n## {'מרכיבי הציון' if he else 'Grade components'}")
    lines = grade_lines((grades or {}).get("grades"), a.lang)
    print("\n".join(lines) if lines else ("טרם פורסם" if he else "Not yet published"))
    if lines:
        print("ייתכנו שינויים" if he else "Subject to change")
    print(f"\n## {'מועדי בחינות' if he else 'Exam dates'}")
    rows = exam_rows(tasks, a.lang)
    for _, line, _ in rows:
        print(f"- {line}")
    if not rows:
        print("טרם נקבע מועד" if he else "Date TBD")
    print("\n" + ("פרטי הבחינה מופיעים במידע האישי." if he else "Exam details appear in the personal information system."))


def cmd_prereqs(a):
    he = a.lang == "he"
    req = api(f"/courses/code/{quote(a.code)}/requirements", {"year": a.year}, missing_ok=True) or {}
    alt = api(f"/courses/code/{quote(a.code)}/replacements", {"year": a.year}, missing_ok=True) or []
    needed_by = api(f"/courses/code/{quote(a.code)}/with-requirement", {"year": a.year}, missing_ok=True) or []
    if a.json:
        return show_json({"requirements": req, "replacements": alt, "requiredFor": needed_by})
    positive, negative = parse_tree(req.get("positiveRequirements")), parse_tree(req.get("negativeRequirements"))
    # The labels are the catalog website's own.
    print(f"## {'דרישות קדם' if he else 'Prerequisites'} — {a.code}")
    if positive:
        print("מותר רק למי שביצע/ה תנאי זה:" if he else "Only permitted for those who have fulfilled this condition:")
        print("\n".join(requirement_tree(positive, a.lang)))
    if negative:
        if positive:
            print("ובתנאי שלא ביצע/ה את תנאי זה:" if he else "Provided that this condition has not been fulfilled:")
        else:
            print("מותר רק למי שלא ביצע/ה תנאי זה:" if he else "Only permitted for those who have not fulfilled this condition:")
        print("\n".join(requirement_tree(negative, a.lang)))
    if not positive and not negative:
        print("לא רשומות דרישות קדם לקורס" if he else "No course prerequisites are listed")
    if req.get("additionalRequirements"):
        print(
            "ישנם תנאי קדם נוספים ברמת החוג ו/או המסלול, שאינם מפורטים כאן."
            if he else
            "There are additional prerequisites at the department and/or track level that are not detailed here."
        )
    if alt:
        print(f"\n## {'קורסים חליפיים' if he else 'Alternative courses'}")
        for r in alt:
            tree = parse_tree(r.get("parsedReplacements"))
            where = say(r.get("roadmapName"), a.lang)
            if where:
                print(("במסלול " if he else "In track ") + where + ":")
            if tree:
                print("\n".join(requirement_tree(tree, a.lang)))
    if needed_by:
        print(f"\n## {'הקורס הוא דרישת קדם עבור' if he else 'This course is a prerequisite for'}")
        print(", ".join(str(x) for x in needed_by))


def search_body(a):
    body = {"year": a.year}
    if a.text:
        body["q"] = a.text
    if a.faculty:
        body["facultyCodes"] = [f.zfill(3) for f in a.faculty]
    if a.department:
        body["departmentCodes"] = a.department
    if a.semester:
        body["semesters"] = [SEMESTERS[s] for s in a.semester]
    if a.day:
        body["daysOfWeek"] = [DAY_INPUT[d] for d in a.day]
    if a.language:
        body["languageCodes"] = [LANGUAGES.get(x.lower(), x) for x in a.language]
    if a.min_credits is not None:
        body["creditPointsMin"] = a.min_credits
    if a.max_credits is not None:
        body["creditPointsMax"] = a.max_credits
    if a.teacher:
        body["teacherQuery"] = a.teacher
    if a.include_untaught:
        body["includeUntaught"] = True
    return body


def cmd_search(a):
    if a.text and a.text.strip().isdigit():
        raise Failure(f"search matches names, not numbers; use: course {a.text.strip()}")
    body = search_body(a)
    if len(body) == 1:
        raise Failure("give search text or at least one filter; the whole catalog is thousands of courses")
    found = api("/courses/search-advanced", {"include": 1}, body=body) or []
    if a.json:
        return show_json(found)
    found.sort(key=lambda c: say(c.get("name"), a.lang))
    print(f"{len(found)} {'קורסים' if a.lang == 'he' else 'courses'} ({a.year})")
    for c in found[: a.limit]:
        print(course_line(c, a.lang))
    if len(found) > a.limit:
        print(f"... {len(found) - a.limit} more; narrow the search or raise --limit")


def program_header(r, lang):
    level = say(r.get("learningProgramDisplayName"), lang) or say(r.get("learningProgramName"), lang)
    return " · ".join(x for x in [
        r.get("roadmapCode") or r.get("code"),
        say((r.get("roadmap") or {}).get("name") or r.get("name"), lang),
        level, say(r.get("diplomaDegreeTypeName"), lang).strip("."), say(r.get("scopeName"), lang),
    ] if x)


def cmd_programs(a):
    if len(a.name.strip()) < 2:
        raise Failure("give at least two letters of the program name")
    roadmaps = api("/yearly-roadmaps/search", {"name": a.name, "year": a.start_year}) or []
    specs = api("/specializations/search", {"name": a.name, "year": a.start_year}) or []
    if a.json:
        return show_json({"roadmaps": roadmaps, "specializations": specs})
    he = a.lang == "he"
    print(f"## {'תוכניות לימודים' if he else 'Study programs'} ({len(roadmaps)})")
    for r in sorted(roadmaps, key=lambda r: (r.get("learningProgramSortOrder") or 0, r.get("roadmapCode") or "")):
        print(program_header(r, a.lang))
    seen = set()
    shown = []
    for s in specs:
        key = (s.get("code"), s.get("learningProgramCode"))
        if key not in seen:
            seen.add(key)
            shown.append(s)
    if shown:
        print(f"\n## {'התמחויות' if he else 'Specializations'} ({len(shown)})")
        for s in shown:
            level = say(s.get("learningProgramDisplayName"), a.lang) or say(s.get("learningProgramName"), a.lang)
            print(f"{s.get('code')} · {say(s.get('name'), a.lang)} · {level} (--level {s.get('learningProgramCode')})")


def block_title(t, lang):
    w = WORDS[lang]
    years = t.get("fromToAcademicYear") or []
    when = ""
    if years:
        span = f"{years[0]}–{years[-1]}" if len(years) > 1 else str(years[0])
        when = f"{w['years'] if len(years) > 1 else w['year']} {span}"
    limits = []
    if t.get("minNaz"):
        limits.append(f"{w['at_least']} {credits(t['minNaz'], lang)}")
    if t.get("maxNaz") is not None and t.get("maxNaz") != t.get("minNaz"):
        limits.append(f"{w['at_most']} {credits(t['maxNaz'], lang)}")
    if t.get("maxCourseCount"):
        limits.append(f"{w['at_most']} {t['maxCourseCount']}" + (" קורסים" if lang == "he" else " courses"))
    return " · ".join(x for x in [when, say(t.get("subChapter"), lang), ", ".join(limits)] if x)


def print_blocks(blocks, lang, keep=None, times=None):
    """Requirement blocks with their courses. `keep` filters courses;
    `times` returns a course's meeting times to print after it."""
    for t in sorted(blocks, key=lambda t: (t.get("displayAcademicYear") or 0, t.get("subChapterOrder") or 0)):
        if t.get("notIncludeInShnaton"):
            continue
        courses = [c for c in t.get("courses") or [] if keep is None or keep(c)]
        note = plain(t.get("hebrewNote") if lang == "he" else (t.get("englishNote") or t.get("hebrewNote")))
        if not courses and (not note or keep is not None):
            continue
        print(f"\n## {block_title(t, lang)}")
        if note:
            print(note)
        for c in sorted(courses, key=lambda c: c.get("code") or ""):
            when = ", ".join(times(c)) if times else ""
            print(f"- {course_line(c, lang)}" + (f" · {when}" if when else ""))


def cmd_program(a):
    he = a.lang == "he"
    params = {"activeYear": a.year, "thresholdYear": a.start_year}
    if "-" in a.code:
        data = api(f"/yearly-roadmaps/{quote(a.code)}/thresholds", params, missing_ok=True)
        link = f"{SITE}/roadmap/{a.code}/year/{a.year}"
    else:
        params["learningProgramCode"] = a.level
        data = api(f"/specializations/{quote(a.code)}/thresholds", params, missing_ok=True)
        link = f"{SITE}/specialization/{a.code}/year/{a.year}"
    if a.json:
        return show_json(data)
    if isinstance(data, list):
        data = {"thresholds": data}
    if not data or not data.get("thresholds"):
        raise Failure(
            f"no requirements found for {a.code} (catalog {a.year}, start year {a.start_year}). "
            "Check the code with `programs`, and the start year."
        )
    print(program_header(data, a.lang))
    print(
        f"שנתון {a.year}, לסטודנטים שהתחילו את הלימודים בתוכנית ב־{a.start_year}"
        if he else f"Catalog {a.year}, for students who began the program in {a.start_year}"
    )
    info = data.get("academicInfo") or {}
    scope = sorted(info.get("studiesScopeSections") or [], key=lambda s: s.get("displayOrder") or 0)
    if scope:
        print(f"\n## {'היקפי לימודים' if he else 'Scope of studies'}")
        for s in scope:
            print(f"- {say(s.get('description'), a.lang)}: {s.get('units')}")
    general = plain(say(info.get("shnatonInfo"), a.lang))
    if general:
        print(f"\n## {'מידע כללי' if he else 'General information'}\n{general}")
    print_blocks(data["thresholds"], a.lang)
    print(f"\n{link}")


def cmd_programs_with(a):
    roadmaps = api("/yearly-roadmaps/search-by-course", {"courseCode": a.code, "thresholdYear": a.start_year}) or []
    specs = api("/specializations/search-by-course", {"courseCode": a.code, "thresholdYear": a.start_year}) or []
    if a.json:
        return show_json({"roadmaps": roadmaps, "specializations": specs})
    he = a.lang == "he"
    w = WORDS[a.lang]
    print(f"## {'תוכניות שבהן מופיע הקורס' if he else 'Programs that list the course'} {a.code} ({len(roadmaps)})")
    for item in roadmaps:
        years = ", ".join(str(y) for y in item.get("studyYears") or [])
        print(program_header(item.get("roadmap") or {}, a.lang) + (f" · {w['years']} {years}" if years else ""))
    if specs:
        print(f"\n## {'התמחויות' if he else 'Specializations'} ({len(specs)})")
        for item in specs:
            s = item.get("specialization") or {}
            print(f"{s.get('code')} · {say(s.get('name'), a.lang)} · {say(s.get('learningProgramDisplayName'), a.lang)}")


def cmd_cornerstone(a):
    blocks = api(
        f"/departments/{CORNERSTONE_DEPARTMENT}/thresholds",
        {"activeYear": a.year, "thresholdYear": a.start_year},
    ) or []
    if a.json:
        return show_json(blocks)
    semester = {SEMESTERS[s] for s in a.semester} if a.semester else None
    # Session periods, when the semesters asked for are A, B or summer only.
    periods = set()
    for s in a.semester or []:
        periods |= SESSION_PERIODS.get(s, set())
    if a.semester and not all(s in SESSION_PERIODS for s in a.semester):
        periods = set()
    days = {DAY_INPUT[d] for d in a.day} if a.day else None

    def sessions(c):
        return [
            s for g in c.get("groups") or [] for s in g.get("studySessions") or []
            if s.get("dayOfWeek") is not None and s.get("startTime") is not None
            and (not periods or s.get("period") in periods)
        ]

    def keep(c):
        if semester and c.get("coursePeriod") not in semester:
            return False
        return days is None or any(s["dayOfWeek"] in days for s in sessions(c))

    def times(c):
        found = []
        for s in sorted(sessions(c), key=lambda s: (s["dayOfWeek"], s["startTime"])):
            when = f"{day_name(s['dayOfWeek'], a.lang)} {clock(s['startTime'])}-{clock(s.get('endTime'))}"
            if when not in found:
                found.append(when)
        return found

    print(("קורסי אבני פינה" if a.lang == "he" else "Cornerstone courses") + f" ({a.year})")
    print_blocks(blocks, a.lang, keep if (semester or days) else None, times)
    print(f"\n{SITE}/cornerstone-courses")


def cmd_timetable(a):
    he = a.lang == "he"
    periods = SESSION_PERIODS[a.semester]
    fetched = []
    for item in a.courses:
        code, _, wanted = item.partition(":")
        c = find_course(code, a.year, 2)
        tasks = api("/assignments", {"year": a.year, "courseId": c["id"]}) or []
        fetched.append((code, {g.strip() for g in wanted.split(",") if g.strip()}, c, tasks))
    if a.json:
        return show_json({code: {"course": c, "assignments": tasks} for code, _, c, tasks in fetched})
    chosen = []  # (course code, group code, sessions)
    exams = []
    for code, wanted, c, tasks in fetched:
        groups = []
        for g in c.get("groups") or []:
            sessions = [s for s in g.get("studySessions") or [] if s.get("period") in periods]
            if sessions or (g.get("period") in periods and not g.get("studySessions")):
                groups.append((g, sessions))
        print(f"\n# {heading(c, a.lang)}")
        if not groups:
            print("אין קבוצות בסמסטר הזה" if he else "No groups in this semester")
        by_type = {}
        for g, sessions in sorted(groups, key=lambda x: x[0].get("code") or ""):
            by_type.setdefault(say(g.get("studySessionTypeName"), a.lang), []).append((g, sessions))
        # Within each kind of meeting (lecture, exercise ...) use the groups
        # asked for, or the only one there is.
        for options in by_type.values():
            asked = [g.get("code") for g, _ in options if g.get("code") in wanted]
            for g, sessions in options:
                pick = g.get("code") in asked or (not asked and len(options) == 1)
                print(f"{'*' if pick else ' '} [{group_title(g, a.lang)}]")
                for s in sorted(sessions, key=lambda s: (s.get("dayOfWeek") or 0, s.get("startTime") or 0)):
                    print(f"    {session_line(s, a.lang)}")
                if pick:
                    chosen.append((code, g.get("code"), sessions))
            if not asked and len(options) > 1:
                print(("  ← יש לבחור קבוצה אחת: " if he else "  ← choose one group: ")
                      + ",".join(g.get("code") for g, _ in options))
        unknown = wanted - {g.get("code") for g, _ in groups}
        if unknown:
            print(("! אין בסמסטר הזה קבוצות: " if he else "! No such groups this semester: ") + ", ".join(sorted(unknown)))
        exams += [(day, code, line) for day, line, _ in exam_rows(tasks, a.lang, periods)]
    print(f"\n# {'התנגשויות בין הקבוצות המסומנות ב־*' if he else 'Clashes between the groups marked *'}")
    clashes = 0
    timed = [
        (code, group, s) for code, group, sessions in chosen for s in sessions
        if s.get("dayOfWeek") is not None and s.get("startTime") is not None and s.get("endTime") is not None
    ]
    for i, (c1, g1, s1) in enumerate(timed):
        for c2, g2, s2 in timed[i + 1:]:
            if (c1, g1) == (c2, g2) or s1["dayOfWeek"] != s2["dayOfWeek"]:
                continue
            if s1["startTime"] < s2["endTime"] and s2["startTime"] < s1["endTime"]:
                clashes += 1
                print(
                    f"- {day_name(s1['dayOfWeek'], a.lang)}: {c1} {g1} {clock(s1['startTime'])}-{clock(s1['endTime'])}"
                    f" / {c2} {g2} {clock(s2['startTime'])}-{clock(s2['endTime'])}"
                )
    if not clashes:
        print("אין התנגשויות" if he else "No clashes")
    if exams:
        print(f"\n# {'מועדי בחינות' if he else 'Exam dates'}")
        dates = {}
        for day, code, line in sorted(exams, key=lambda x: (x[0] == "", x[0], x[1])):
            if day:
                dates.setdefault(day, set()).add(code)
            print(f"- {code} · {line}")
        for day, codes in sorted(dates.items()):
            if len(codes) > 1:
                print(("! באותו יום: " if he else "! Same day: ") + f"{day} " + ", ".join(sorted(codes)))
    # The catalog's own planner notice.
    print("\n" + (
        "מערכת תכנון השעות היא כלי לתכנון בלבד. הוספת קורסים למערכת אינה מהווה רישום לקורסים, "
        "אינה שומרת מקום ואינה מקנה עדיפות בשיבוץ. הרישום בפועל יתבצע במערכת הרישום בלבד."
        if he else
        "Planning only: this is not course registration, does not reserve a place and gives no "
        "priority. Registration happens only in the registration system."
    ))


# ── Command line ────────────────────────────────────────────────────────


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--year", type=int, help="catalog year, e.g. 2027 for תשפ\"ז (default: the current one)")
    common.add_argument("--lang", choices=["he", "en"], default="he", help="language for names (default he)")
    common.add_argument("--json", action="store_true", help="print the raw API response")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    def command(name, func, text):
        p = sub.add_parser(name, parents=[common], help=text, description=text)
        p.set_defaults(func=func)
        return p

    command("years", cmd_years, "catalog years and which is current")
    command("faculties", cmd_faculties, "faculty and school codes")
    command("departments", cmd_departments, "departments of a faculty").add_argument("faculty", help="faculty code, e.g. 012")
    p = command("course", cmd_course, "a course: credits, semester, groups; --sessions adds times and rooms")
    p.add_argument("code")
    p.add_argument("--sessions", action="store_true", help="include days, times, rooms and lecturers")
    command("syllabus", cmd_syllabus, "a course's published syllabus").add_argument("code")
    command("exams", cmd_exams, "grade components and exam dates").add_argument("code")
    command("prereqs", cmd_prereqs, "prerequisites, alternative courses and what requires this course").add_argument("code")

    p = command("search", cmd_search, "search courses by name and filters")
    p.add_argument("text", nargs="?", help="words from the course name, in Hebrew or English")
    p.add_argument("--faculty", action="append", help="faculty code (repeatable)")
    p.add_argument("--department", action="append", help="department code (repeatable)")
    p.add_argument("--semester", action="append", choices=list(SEMESTERS), help="course period (repeatable)")
    p.add_argument("--day", action="append", choices=list(DAY_INPUT), help="teaching day (repeatable)")
    p.add_argument("--language", action="append", help="he, en, ar or a language code (repeatable)")
    p.add_argument("--min-credits", type=float)
    p.add_argument("--max-credits", type=float)
    p.add_argument("--teacher", help="part of a lecturer's name")
    p.add_argument("--include-untaught", action="store_true", help="also courses not taught this year")
    p.add_argument("--limit", type=int, default=40, help="lines to print (default 40)")

    start = {"type": int, "dest": "start_year", "help": "the year the student began the program (default: the catalog year)"}
    p = command("programs", cmd_programs, "find study programs and specializations by name")
    p.add_argument("name")
    p.add_argument("--start-year", **start)
    p = command("program", cmd_program, "degree requirements of a program (e.g. 521-3010) or specialization")
    p.add_argument("code")
    p.add_argument("--start-year", **start)
    p.add_argument("--level", help="learning program code for a specialization, e.g. 004 (from `programs`)")
    p = command("programs-with", cmd_programs_with, "programs whose requirements list a course")
    p.add_argument("code")
    p.add_argument("--start-year", **start)
    p = command("cornerstone", cmd_cornerstone, "cornerstone (אבני פינה) courses")
    p.add_argument("--start-year", **start)
    p.add_argument("--semester", action="append", choices=list(SEMESTERS), help="only courses of this period (repeatable)")
    p.add_argument("--day", action="append", choices=list(DAY_INPUT), help="only courses meeting on this day (repeatable)")
    p = command("timetable", cmd_timetable, "weekly sessions, clashes and exam dates for several courses")
    p.add_argument("courses", nargs="+", metavar="CODE[:GROUP,GROUP]", help="e.g. 67101:1-01,2-02 80131")
    p.add_argument("--semester", choices=list(SESSION_PERIODS), default="a")

    a = parser.parse_args(argv)
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if a.command not in ("years", "faculties") and a.year is None:
            a.year = current_year()
        if getattr(a, "start_year", "unset") is None:
            a.start_year = a.year
        a.func(a)
    except Failure as e:
        print(f"shnaton: {e}", file=sys.stderr)
        return 1
    except BrokenPipeError:  # output piped into `head` and the like
        sys.stderr.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
