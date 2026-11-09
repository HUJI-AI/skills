---
name: huji-shnaton
description: >-
  Look up Hebrew University (HUJI) courses and degree requirements in the
  official course catalogue, the Shnaton (shnaton.huji.ac.il), through its
  public read-only API. Covers finding courses by name, faculty, department,
  semester, day, language or lecturer; a course's credit points, groups,
  weekly times, rooms and lecturers; its syllabus, grade components and exam
  dates; prerequisites and alternative courses; a study programme's
  requirements for the year the student began; cornerstone (Avnei Pina)
  courses; planning a weekly timetable without clashes; and semester dates
  from the academic calendar. Use whenever a HUJI student asks about courses,
  course numbers, the Shnaton, prerequisites, exam dates (moed A/B), degree or
  track requirements, credit points (נ"ז), semester dates, or building a
  semester schedule.
metadata:
  title: "השנתון: קורסים, דרישות ומערכת שעות"
  summary: חיפוש קורסים בשנתון האוניברסיטה העברית, שעות ומועדי בחינות, דרישות קדם ודרישות התואר לפי שנת תחילת הלימודים, ובדיקת התנגשויות במערכת השעות.
  title_en: "The Shnaton: courses, requirements and timetables"
  summary_en: Search the Hebrew University course catalogue for courses, class times and exam dates, prerequisites and degree requirements by start year, and check a timetable for clashes.
  pillar: students
---
# The HUJI course catalogue (Shnaton)

The Shnaton at <https://shnaton.huji.ac.il> is the Hebrew University's course
catalogue. Its website reads a public, read-only JSON API at
`https://shnaton.huji.ac.il/api`; no login or key is needed. Use it to
answer students' questions about courses, requirements and schedules from
the catalogue itself rather than from memory.

## Before you answer

- **The catalogue is information, not registration.** Registration, the
  student's own grades and status, and personal exam details are in the
  university's personal systems, which this skill cannot see. Never ask for
  passwords, ID numbers or codes.
- **Cite what you used.** Name the catalogue year and give the website link for
  each course or programme you relied on (see **Links**). Information in the
  catalogue can change, and the website may mark a newly opened year as
  provisional.
- **Report, don't guess.** If a field is empty, say it is not published. Quote
  notes that set rules ("at most one course from this list", "take it in
  Semester A") instead of paraphrasing them away. When the catalogue says there
  are further department or track requirements, say so, and refer the
  student to the department or to Student Administration
  (<https://studentsadmin.huji.ac.il/>).
- **Go easy on the service.** Ask for what the question needs: a course by
  number, or a filtered search. Never fetch the whole catalogue or loop over
  every course; an unfiltered search returns thousands of courses. Reuse
  what you already fetched in the conversation.
- **If the API fails** (an error, or a web page instead of JSON), stop and
  send the student to the website. Do not try to get around a block.
- **Only read.** Use GET requests and the course search. Never send the
  website's other POST requests (feedback, usage statistics, export).
- **People's details.** Sessions list lecturers' names and university email
  addresses. Use them only to answer the student's own question, such as who
  teaches their group; don't compile lists of people or addresses.

## Key ideas

- **Catalogue year** (`year`) is named by the calendar year in which the
  academic year ends: 2027 is 2026–27 (תשפ"ז). Use the current year unless the
  student says otherwise; the active-years request shows it. The API covers
  2020 onwards; catalogues from 2000–2019 are at
  <https://www.huji.ac.il/shnatonOrbit/>.
- **Start year** (`thresholdYear`, "שנת תחילת לימודים במסלול"): programme
  requirements depend on the year the student began the programme, and differ
  between years. **Ask for it** before answering about degree requirements.
- **Codes.** Courses have numbers such as `40109`. Programmes (tracks) have
  codes such as `821-7878`. Specialisations have numeric codes such as `3668`
  plus a learning programme (`001` Bachelor's, `004` Master's …). Faculties
  have three-digit codes (`007`), departments their own codes (`821`). Search
  matches names, not numbers: look a known number up directly.
- **Semesters.** A course runs in Semester A, Semester B, either, summer, or
  all year. A course has **groups** for each kind of meeting: `1-01` is
  lecture group 1, `2-03` exercise group 3, and so on. The website's planner
  asks for a group of each meeting type, all in the same semester.
- **Language.** Names and notes come in Hebrew and English; English is
  sometimes missing. Answer in the student's language and always include
  course numbers.

## Reaching the catalogue

Use the first of these that works. Never ask a student to install software
for this skill.

1. **The helper script**, when you can run code: `scripts/shnaton.py` needs
   only Python 3.8 or later. In Claude chats (claude.ai and the Claude
   apps) a skill's scripts run in Claude's own sandbox, so the student
   installs nothing. When you run on the student's own computer (for
   example in Claude Code), Python may be missing (often on Windows); then
   use direct requests.
2. **Direct requests**: the GET links below return JSON that a web-fetch tool
   or any HTTP client can read. If your fetch tool summarises pages, ask it
   for the raw values (`dayOfWeek`, `startTime`, `endTime`, codes) and
   convert them yourself.
3. **If neither can reach shnaton.huji.ac.il**, tell the student why, in
   their language, and offer a way forward:
    - The sandbox has no internet access (a network or name-resolution
      error): in Claude, network access for code execution is set under
      Settings → Capabilities; on an organisation plan, its owner sets it.
    - Your fetch tool opens only links that appear in the conversation: give
      the student the exact API link and ask them to paste it back.
    - Otherwise, the student can look the course up on the website (see
      **Links**).

### Direct requests

Base: `https://shnaton.huji.ac.il/api`. Replace `{year}` with the catalogue
year and `{start}` with the year the student began the programme.

| To get | GET |
|---|---|
| the current catalogue year | `/reference-data/active-years` (the item with `"current": true`) |
| a course, with groups and weekly times | `/courses/code/{code}?year={year}&include=2` |
| courses by name, Hebrew or English | `/courses/search?name={words}&year={year}`; keep only `"isLearning": 1`, the courses taught that year |
| the syllabus | `/syllabus?courseCode={code}&year={year}` |
| grade components | `/courses/code/{code}/grades?year={year}` |
| exam dates | `/assignments?year={year}&courseId={id}`, with the course's `id` field, not its number |
| prerequisites | `/courses/code/{code}/requirements?year={year}` |
| alternative courses | `/courses/code/{code}/replacements?year={year}` |
| programmes by name | `/yearly-roadmaps/search?name={words}&year={start}` |
| a programme's requirements | `/yearly-roadmaps/{programCode}/thresholds?activeYear={year}&thresholdYear={start}` |
| cornerstone courses, with weekly times | `/departments/334/thresholds?activeYear={year}&thresholdYear={start}` |

Reading the JSON:

- `dayOfWeek`: 0 is Sunday, 5 is Friday. `startTime` and `endTime` are
  milliseconds after midnight: 43200000 is 12:00, 49500000 is 13:45. A
  session without them has no fixed time.
- A session's `period`: 1 Semester A, 2 Semester B, 3 summer.
- `positiveRequirements` and `negativeRequirements` are JSON text inside the
  JSON. They are trees of `COURSE` nodes under `AND` (all of) and `OR` (one
  of), sometimes with a `minGrade`. Positive: required before the course.
  Negative: the course is not open to those who completed it.
  `additionalRequirements: true`: the department or track has further
  prerequisites not listed.
- Exam `schedules`: `moed` 1 is Moed A, 2 Moed B, 3 Moed C, 4 a special term;
  `startTime` `null` means the date is not set yet.
- Programme requirements come in blocks (`thresholds`): `subChapter`
  (Mandatory, Elective …), `fromToAcademicYear` (years of study), `minNaz` and
  `maxNaz` (credit points), rules in `hebrewNote` or `englishNote`, and
  `courses`. Skip blocks with `notIncludeInShnaton: true`. Totals are in
  `academicInfo.studiesScopeSections`; general rules in
  `academicInfo.shnatonInfo`. A programme's requirements run to over 100,000
  characters: if your tool cuts the page short, read the rest before
  answering.

More endpoints, fields and the filtered course search (a POST request) are
in [references/api.md](references/api.md).

### The helper script

Run it from the skill folder: `python3 scripts/shnaton.py <command> [options]`.

| Command | What it gives |
|---|---|
| `years` | catalogue years; which one is current |
| `faculties` / `departments 001` | faculty and department codes |
| `course 40109 [--sessions]` | credit points, semester, groups; with `--sessions`, days, times, rooms and lecturers |
| `syllabus 40109` | the published syllabus |
| `exams 40109` | grade components and exam dates |
| `prereqs 67504` | prerequisites, alternative courses, and what requires this course |
| `search "words" [filters]` | courses by name and filters (below) |
| `programs "גאוגרפיה" --start-year 2026` | programmes and specialisations whose name matches |
| `program 821-7878 --start-year 2026` | a programme's requirements; for a specialisation, `program 3668 --level 004` |
| `programs-with 40109 --start-year 2026` | programmes whose requirements list the course |
| `cornerstone [--semester a] [--day mon]` | cornerstone (אבני פינה) courses by area, with weekly times |
| `timetable 40107 40109:1-01 40130 --semester a` | sessions of several courses, clashes between chosen groups, and exam dates |

Every command takes `--year` (catalogue year), `--lang he|en` and `--json`
(the raw API response). Search filters: `--faculty`, `--department`,
`--semester a|b|a-or-b|summer|yearly`, `--day sun..fri`,
`--language he|en|ar`, `--min-credits`, `--max-credits`, `--teacher`,
`--include-untaught`, `--limit`. Repeat a filter for several values.

## Common requests

**"Tell me about course 40109."** Get the course with its weekly times, then
the syllabus, grade components, exam dates or prerequisites as the question
needs (`course --sessions`, `syllabus`, `exams`, `prereqs`). Give credit
points, semester, meeting times, how the grade is made up, and the link.

**"Find me a course …"** Turn the request into words from the course name
and, with the script, filters: faculty or department, semester, day,
language, credit points, lecturer. When the student plans Semester A,
include `--semester a --semester a-or-b --semester yearly`, and likewise for
B. With direct requests, search by name and check the semester and times in
the results. Show the best matches with numbers, credit points and semester,
and offer to narrow down.

**"Can I take this course?"** Get the prerequisites. Explain the tree: "all
of" and "one of", any minimum grade, and courses that exclude it. Mention
alternative courses. Whether the student meets the conditions is for them,
and the department, to confirm.

**"What do I need for my degree?"** Ask for the programme and start year. Find
the programme code by name, then get its requirements (`programs`, `program`).
Summarise the total credit points, the scope table, each year's mandatory
courses, and each elective list with its minimum and maximum. Keep the
notes' rules. For a dual major, each major has its own programme. If the
student lists the courses they have completed, compare them with each
requirement block and say what is still missing, noting that the official
status is with the department and in their personal records.

**"Build my timetable."** Ask for the courses and the semester. With the
script, run `timetable` with the course numbers: it marks with `*` the groups
chosen or the only group of a meeting type, and lists the choices still open.
Pick one group per meeting type with the student, run it again with
`course:group,group`, and resolve clashes. Without the script, get each
course with its times and compare the chosen groups' sessions yourself: a
clash is the same day with overlapping times in the same semester. Point out
exam dates that fall on the same day or close together. Remind the student
that this is planning, not registration. The website also has a schedule
planner: <https://shnaton.huji.ac.il/schedule-plan>.

**"Which cornerstone courses are there on Monday?"** One request lists them
by area with their weekly times (`cornerstone --semester a --day mon`). For
rooms and lecturers, get the courses the student likes. The programme's own
cornerstone requirement is in its scope table and general information.

**"Which programmes include this course?"** `programs-with`, or
`/yearly-roadmaps/search-by-course?courseCode={code}&thresholdYear={start}`.

**"When does the semester start?"** The academic calendar is not in the
Shnaton. The Academic Administration publishes it as pages a web-fetch tool
can read:

- Hebrew: <https://academic-secretary.huji.ac.il/%D7%9C%D7%95%D7%97-%D7%A9%D7%A0%D7%94-%D7%90%D7%A7%D7%93%D7%9E%D7%99>
- English: <https://en.academic-secretary.huji.ac.il/academic-calendars>

The page holds several academic years, one per tab, and may open on an
earlier year: use the section headed with the year in question. It gives
the first and last day of each semester, holidays and breaks without classes
or exams, and days when classes end early. A separate document,
linked from the Hebrew page, sets special arrangements on other holidays and
fasts. The meeting dates in the Shnaton already leave out the days without
classes; the calendar explains the gaps.

## Links

- Course: `https://shnaton.huji.ac.il/course/{code}/year/{year}`
- Syllabus: `https://shnaton.huji.ac.il/course/{code}/syllabus/year/{year}`
- Programme: `https://shnaton.huji.ac.il/roadmap/{programCode}/year/{year}`
- Cornerstone courses: <https://shnaton.huji.ac.il/cornerstone-courses>
- Academic calendar: [Hebrew](https://academic-secretary.huji.ac.il/%D7%9C%D7%95%D7%97-%D7%A9%D7%A0%D7%94-%D7%90%D7%A7%D7%93%D7%9E%D7%99), [English](https://en.academic-secretary.huji.ac.il/academic-calendars)
- Questions about the catalogue: Student Administration,
  <https://studentsadmin.huji.ac.il/contactHuji>
