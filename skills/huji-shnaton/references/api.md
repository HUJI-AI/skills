# Shnaton API reference

Base URL: `https://shnaton.huji.ac.il/api`. Read-only JSON, no login or key.
These are the requests the catalogue website itself makes. Send `Accept:
application/json`. A response that is a web page instead of JSON means the
service is unavailable or wants a browser: stop and use the website.

`scripts/shnaton.py` wraps the useful ones. This file is for agents that
call the API directly, and for reading `--json` output.

## Conventions

- **Bilingual text** is an object `{"he": "...", "en": "..."}`. English is
  sometimes empty or in Hebrew; fall back to the other language.
- **Notes** (`remark`, `shnatonInfo`, syllabus fields) may contain HTML.
- **`year`** is the catalogue year, named by the calendar year in which the
  academic year ends: `2027` is 2026–27 (תשפ"ז).
- **`thresholdYear`** is the year the student began the programme. Programme
  requirements depend on it.
- **`activeYear`** is the catalogue year being viewed (same values as `year`).
- **Days** (`dayOfWeek`, search `daysOfWeek`): 0 = Sunday … 5 = Friday.
- **Times** (`startTime`, `endTime` of study sessions): milliseconds after
  midnight. 43200000 is 12:00; 49500000 is 13:45.
- **Course period** (`coursePeriod`, search `semesters`): 1 Semester A,
  2 Semester B, 3 Semester A or B, 4 Summer, 5 Yearly.
- **Group and session period** (`period`): 1 Semester A, 2 Semester B,
  3 Summer, 4 Semesters A + B. In a yearly group each session has its own
  period 1 or 2.
- **Group code** `"<type>-<nn>"`, for example `1-01`. The meeting type is in
  `studySessionTypeName` (Lesson, Exercise, Laboratory, Seminar …). The
  website's planner asks for a group of each meeting type, all in the same
  semester.
- **Course code** is a string in URLs, for example `67101`. **Programme
  (track) code** looks like `521-3010`. **Specialization code** is numeric,
  for example `3668`, together with a learning programme code.
- **Learning programme codes** (`/learning-programs`): `001` Bachelor's, `004`
  Master's, `002` Diploma, `003` Supplementary studies for Master's, `005`
  Ph.D., and more.

## Reference data

| Request | Returns |
|---|---|
| `GET /health` | `Healthy` (plain text) |
| `GET /reference-data/active-years` | `[{year, hebrewYear, current}]`; the current year has `current: true` |
| `GET /reference-data/threshold-years` | start years available for requirements |
| `GET /faculties` | `[{code, name}]`, for example `012` Computer Science & Engineering |
| `GET /faculties/{facultyCode}/departments?year=` | `[{id, code, name}]`; `facultyCode` is three digits |
| `GET /learning-programs` | `[{userCode, name, displayName}]` |
| `GET /reference-data/languages` | `[{code, name}]`: `0` Hebrew, `2` English, `1` Arabic … |
| `GET /reference-data/study-session-types` | meeting types `[{code, name}]` |

## Courses

| Request | Returns |
|---|---|
| `GET /courses/code/{code}?year=&include=` | a list with the course, or `[]`. `include=1` adds `groups`; `include=2` adds each group's `studySessions` |
| `GET /courses/search?name=&year=` | courses whose name matches, in Hebrew or English, without groups. Also lists courses not taught that year: keep `isLearning: 1`, which gives the same courses as the website's search |
| `POST /courses/search-advanced?include=1` | the website's search: courses matching a JSON query with filters (below) |
| `GET /syllabus?courseCode=&year=` | the syllabus; when none is published, `courseName` is empty |
| `GET /courses/code/{code}/grades?year=` | `{grades: [{name, groupName, weight}], lastPublishedAt}`; 404 when not published |
| `GET /assignments?year=&courseId=` | assessment items with exam `schedules`; `courseId` is the course's internal `id`, not its code |
| `GET /courses/code/{code}/requirements?year=` | prerequisites (below) |
| `GET /courses/code/{code}/replacements?year=` | `[{parsedReplacements, roadmapName}]`: alternative courses |
| `GET /courses/code/{code}/with-requirement?year=` | codes of courses that list this one as a prerequisite |
| `GET /courses/groups-with-sessions?year=&courseIds=1,2` | groups with sessions for several courses at once, keyed by internal `id` |

**Course fields:** `id`, `code`, `name`, `departmentName`, `facultyName`,
`academicPoints` (credit points, נ"ז), `coursePeriod`, `coursePeriodName`,
`courseStructureType` (Hebrew only), `totalHours`, `remark`, `groups`.

**Group fields:** `code`, `period`, `periodName`, `languageName`,
`studySessionTypeName`, `remark`, `studySessions`.

**Session fields:** `dayOfWeek`, `startTime`, `endTime`, `period`,
`isRecorded`, `isLiveBroadcast`, `calendarFrequency` (every N weeks, when not
weekly), `teachers` (`name`, `title`, university email),
`room` (`name`, `building.name`, `building.campus.name`) and
`studySessionSchedules` (the individual meeting dates). A session without a
day or time has no fixed meeting time.

**Exam schedules** (in `/assignments`): each item has `assignmentDefinition`
(`name`, `assignmentType`), `weight`, `period` and `schedules`, each with
`moed` (1 Moed A, 2 Moed B, 3 Moed C, 4 special term), `startTime` (a date;
`null` when not yet set), `period` and `rooms`. The website adds: "Exam
details appear in the personal information system".

### Course search body

```json
{
  "year": 2027,
  "q": "machine learning",
  "facultyCodes": ["012"],
  "departmentCodes": ["521"],
  "semesters": [1, 3, 5],
  "daysOfWeek": [0],
  "languageCodes": ["2"],
  "creditPointsMin": 2,
  "creditPointsMax": 4,
  "teacherQuery": "lecturer name",
  "includeUntaught": true
}
```

Only `year` is required; leave out what you don't filter on. `q` matches
course names in Hebrew or English, not course numbers. Results include
groups without sessions. Without any filter the response is the entire
catalogue (thousands of courses, over 10 MB): always filter.

### Prerequisites

`positiveRequirements` and `negativeRequirements` are **JSON strings** (parse
them a second time), or empty. Each is a tree of nodes:

- `{"type": "COURSE", "courseCode": 67109, "courseName": {...}, "minGrade": 60}`
  (`minGrade` is optional)
- `{"type": "AND", "children": [...]}`: all of the children
- `{"type": "OR", "children": [...]}`: one of the children

The website labels them: positive, "Only permitted for those who have
fulfilled this condition"; negative after a positive one, "Provided that this
condition has not been fulfilled"; negative alone, "Only permitted for those
who have not fulfilled this condition". `additionalRequirements: true` means
"There are additional prerequisites at the department and/or track level that
are not detailed here."

## Programmes and requirements

| Request | Returns |
|---|---|
| `GET /yearly-roadmaps/search?name=&year={startYear}` | programmes whose name matches (two letters or more) |
| `GET /yearly-roadmaps/{programCode}/thresholds?activeYear=&thresholdYear=` | the programme's requirements |
| `GET /yearly-roadmaps/{programCode}/combinations?year={startYear}` | programmes it can be combined with (dual majors) |
| `GET /yearly-roadmaps/{programCode}/specializations?year=` | linked specialisations |
| `GET /yearly-roadmaps/search-by-course?courseCode=&thresholdYear=` | `[{roadmap, studyYears}]`: programmes whose requirements list the course |
| `GET /specializations/search?name=&year={startYear}` | specialisations, once per learning programme |
| `GET /specializations/{code}/thresholds?activeYear=&thresholdYear=&learningProgramCode=` | a specialisation's requirements |
| `GET /specializations/search-by-course?courseCode=&thresholdYear=` | `[{specialization, studyYears}]` |
| `GET /departments/334/thresholds?activeYear=&thresholdYear=` | cornerstone (אבני פינה) course lists, as the website's cornerstone page reads them; courses include groups and weekly times, without rooms or lecturers |

Adding `include=1` or `include=2` to a programme or specialisation thresholds
request adds groups or sessions to every listed course and makes the response
several times larger; leave it out unless you need times.

**Programme fields:** `roadmapCode`, `roadmap.name`, `learningProgramDisplayName`
(First degree …), `diplomaDegreeTypeName` (B.Sc …), `scopeName`
(Single-major, Dual-major …), `departmentName`, `facultyName`, `thresholds`,
and `academicInfo`:

- `minNaz`: minimum credit points for the programme.
- `studiesScopeSections`: `[{description, units}]`, for example "Total in
  the degree" 134, "Compulsory in the teaching program" 82, "years for the
  degree" 3.
- `shnatonInfo`: general rules as text (English courses, supplementary
  studies, cornerstone requirements …).

**Threshold (requirement block) fields:** `subChapter` (Mandatory, Required
elective, Elective, Additional courses …), `isMandatory`,
`fromToAcademicYear` (years of study it applies to, for example `[2, 3]`),
`displayAcademicYear`, `minNaz` and `maxNaz` (credit points from this block),
`maxCourseCount`, `hebrewNote` and `englishNote` (rules such as which
semester to take a course in or "at most one course from this list"),
`notIncludeInShnaton` (not shown on the website; skip it) and `courses`.

## Links to the website

- Course: `https://shnaton.huji.ac.il/course/{code}/year/{year}`
- Syllabus: `https://shnaton.huji.ac.il/course/{code}/syllabus/year/{year}`
- Programme: `https://shnaton.huji.ac.il/roadmap/{programCode}/year/{year}`
- Specialization: `https://shnaton.huji.ac.il/specialization/{code}/year/{year}`
- Cornerstone courses: `https://shnaton.huji.ac.il/cornerstone-courses`
- Schedule planner: `https://shnaton.huji.ac.il/schedule-plan`
- Catalogs 2000–2019: `https://www.huji.ac.il/shnatonOrbit/`

Do not send other POST requests the website makes (feedback, usage
statistics, Excel export): they are not lookups.
