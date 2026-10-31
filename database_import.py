\
"""Import the supplied Excel workbooks into PostgreSQL.

Run from the project root after creating the schema:
    python database_import.py

This imports local copies of Applications.xlsx, Mentor.xlsx, Interviews.xlsx,
and Users.xlsx from the data/ directory. A populated database is protected by
default; --replace is required for an intentional full reload.
"""
from __future__ import annotations

import sys
import argparse
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from core.database import Database, DatabaseError, _load_env_file
from core.data_store import DataError, ensure_extended_schema

DATA_DIR = ROOT / "data"


def clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def date_value(value):
    value = clean(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def read_sheet(filename, sheet=None):
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing workbook: {path}")
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[sheet] if sheet else wb.worksheets[0]
        iterator = ws.iter_rows(values_only=True)
        headers = [str(x).strip() if x is not None else "" for x in next(iterator)]
        return [dict(zip(headers, row)) for row in iterator if any(x is not None for x in row)]
    finally:
        wb.close()


def getval(row, *names):
    for name in names:
        if name in row:
            return clean(row[name])
    return None


def main(replace_existing=False):
    _load_env_file()
    ensure_extended_schema()
    database = Database()
    apps = read_sheet("Applications.xlsx", "Applications")
    mentors = read_sheet("Mentor.xlsx", "Mentor")
    interviews = read_sheet("Interviews.xlsx", "Interviews")
    users = read_sheet("Users.xlsx", "Users")

    if not apps:
        print("Warning: Applications.xlsx contains no data rows.")

    with database.connection() as conn:
        with conn.cursor() as cur:
            # Never wipe a populated database accidentally. Use --replace only when a full reload is intentional.
            cur.execute('''SELECT (SELECT COUNT(*) FROM \"Applications\") + (SELECT COUNT(*) FROM \"Mentors\") + (SELECT COUNT(*) FROM \"ProjectTracking\") + (SELECT COUNT(*) FROM \"Trainees\") + (SELECT COUNT(*) FROM \"Users\")''')
            existing_count = cur.fetchone()[0]
            if existing_count and not replace_existing:
                raise RuntimeError('Database already contains records. Import cancelled to protect your data. If you intentionally want to replace all records with the Excel snapshot, rerun with --replace after backing up PostgreSQL.')
            if replace_existing:
                cur.execute('TRUNCATE TABLE "ProjectTracking", "Mentors", "Applications", "Trainees", "Users", "VITHistory" RESTART IDENTITY CASCADE')

            trainee_by_email = {}
            trainee_by_name = {}

            def add_trainee(name, email=None, phone=None, postal=None, state=None):
                name = str(name or "Unknown trainee").strip()
                email = str(email).strip() if email else None
                if email:
                    cur.execute(
                        '''INSERT INTO "Trainees" ("FullName","EmailAddress","PhoneNumber","PostalCode","StateOfResidence")
                           VALUES (%s,%s,%s,%s,%s)
                           ON CONFLICT ("EmailAddress") DO UPDATE SET
                             "FullName"=COALESCE(EXCLUDED."FullName","Trainees"."FullName"),
                             "PhoneNumber"=COALESCE(EXCLUDED."PhoneNumber","Trainees"."PhoneNumber"),
                             "PostalCode"=COALESCE(EXCLUDED."PostalCode","Trainees"."PostalCode"),
                             "StateOfResidence"=COALESCE(EXCLUDED."StateOfResidence","Trainees"."StateOfResidence")
                           RETURNING "TraineeID"''',
                        (name, email, phone, postal, state))
                else:
                    key = name.casefold()
                    if key in trainee_by_name:
                        return trainee_by_name[key]
                    cur.execute(
                        '''INSERT INTO "Trainees" ("FullName","PhoneNumber","PostalCode","StateOfResidence")
                           VALUES (%s,%s,%s,%s) RETURNING "TraineeID"''',
                        (name, phone, postal, state))
                trainee_id = cur.fetchone()[0]
                trainee_by_name[name.casefold()] = trainee_id
                if email:
                    trainee_by_email[email.casefold()] = trainee_id
                return trainee_id

            for row in apps:
                trainee_id = add_trainee(
                    getval(row, "Full Name"), getval(row, "Email"),
                    getval(row, "Phone"), getval(row, "Postal Code"), getval(row, "Province"))
                cur.execute(
                    '''INSERT INTO "Applications" (
                        "TraineeID","Timestamp","CurrentStatus","WillJoinITPHTraining",
                        "FinancialStatus","AttendingLanguageCourse","EnglishLevel","DutchLevel",
                        "UnderPressure","CompletedBootcamp","AttendedOnlineITCourse","ITExperience",
                        "IncludedInProject","WillingnessToWork","MotivationForJoining","ApplicationTerm",
                        "ReasonsForApplyingToVIT","MentorMeeting","GreenCheck","InternalTracking1","InternalTracking2","InternalTracking3","ProcessingStatus"
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (trainee_id, date_value(getval(row, "Timestamp")),
                     getval(row, "Current Status"), getval(row, "Desired Training"),
                     getval(row, "Financial Situation"), getval(row, "Currently in a Language Course"),
                     getval(row, "English Level"), getval(row, "Dutch Level"),
                     getval(row, "Municipal Pressure Regarding Work"),
                     getval(row, "Completed Another IT Bootcamp"),
                     getval(row, "Followed an Online IT Course"),
                     getval(row, "Prior IT Work Experience"),
                     getval(row, "Currently Involved in Another Project"),
                     getval(row, "Desired IT Department(s)"),
                     getval(row, "Motivation") or getval(row, "Reasons for Applying to VIT"),
                     getval(row, "Application Period"), getval(row, "Reasons for Applying to VIT"),
                     getval(row, "Mentor Meeting"), getval(row, "Green Check"),
                     getval(row, "Internal Tracking 1"), getval(row, "Internal Tracking 2"),
                     getval(row, "Internal Tracking 3"), getval(row, "Processing Status")))

            for row in mentors:
                name = getval(row, "Candidate Name")
                trainee_id = trainee_by_name.get(str(name or "").casefold())
                if trainee_id is None and name:
                    trainee_id = add_trainee(name)
                cur.execute(
                    '''INSERT INTO "Mentors" (
                        "MeetingDate","MentorFullName","TraineeID","HasRelevantKnowledge",
                        "EligibleForVITProject","Thoughts","AvailabilityStatus","Comments","VITGroup","SecondaryScore"
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (date_value(getval(row, "Date")), getval(row, "Mentor Name"), trainee_id,
                     getval(row, "Score"), getval(row, "Recommendation"),
                     getval(row, "Notes"), getval(row, "Alternative Recommendation"),
                     getval(row, "Notes"), getval(row, "VIT Group"), getval(row, "Secondary Score")))

            for row in interviews:
                name = getval(row, "Full Name")
                trainee_id = trainee_by_name.get(str(name or "").casefold())
                if trainee_id is None and name:
                    trainee_id = add_trainee(name)
                if trainee_id is not None:
                    cur.execute(
                        '''INSERT INTO "ProjectTracking" ("TraineeID","ProjectSubmissionDate","ProjectReviewDate")
                           VALUES (%s,%s,%s)''',
                        (trainee_id, date_value(getval(row, "Project Sent Date")),
                         date_value(getval(row, "Project Received Date"))))

            cur.execute('SELECT COUNT(*) FROM "VITHistory"')
            if cur.fetchone()[0] == 0:
                try:
                    history = read_sheet("Mentor.xlsx", "VIT History")
                except KeyError:
                    history = []
                for row in history:
                    if getval(row, "Candidate Name"):
                        cur.execute('INSERT INTO "VITHistory" ("VITGroup","CandidateName","Email") VALUES (%s,%s,%s)',
                                    (getval(row, "VIT Group"), getval(row, "Candidate Name"), getval(row, "Email")))

            for row in users:
                username = getval(row, "Username")
                password = getval(row, "Password")
                role = str(getval(row, "Role") or "user").strip().lower()
                if username and password is not None:
                    cur.execute(
                        '''INSERT INTO "Users" ("Username","Password","Role") VALUES (%s,%s,%s)
                           ON CONFLICT ("Username") DO UPDATE SET
                           "Password"=EXCLUDED."Password", "Role"=EXCLUDED."Role"''',
                        (str(username), str(password), "admin" if role == "admin" else "user"))

    print(f"Import complete: {len(apps)} application rows, {len(mentors)} mentor rows, "
          f"{len(interviews)} project-tracking rows, {len(users)} user rows processed.")
    print("Review README_DATABASE.md for the source-to-database mapping notes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Excel data into PostgreSQL safely.")
    parser.add_argument("--replace", action="store_true", help="replace all existing imported records (destructive; back up first)")
    args = parser.parse_args()
    try:
        main(replace_existing=args.replace)
    except (DatabaseError, DataError, FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        print(f"Import failed: {exc}")
        raise SystemExit(1)
