import argparse
from datetime import datetime
import json
from .check_grade import DGTGradeChecker


def main():
    parser = argparse.ArgumentParser(
        description="Check the grade of a DGT test you did. Uses https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/resultadoConsultaNota.faces"
    )
    parser.add_argument("DNI", type=str, help="Your DNI (NIF/NIE)")
    parser.add_argument(
        "exam_date",
        type=str,
        help="The date when you took the exam, in DD/MM/YYYY format",
    )
    parser.add_argument(
        "license_class",
        type=str,
        help="The type of driving license the test was for, e.g. B",
    )
    parser.add_argument(
        "birth_date", type=str, help="Your birth date, in DD/MM/YYYY format"
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Print the output in JSON format",
    )

    args = parser.parse_args()

    try:
        exam_date = datetime.strptime(args.exam_date, "%d/%m/%Y")
        birth_date = datetime.strptime(args.birth_date, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Error: The dates format should be DD/MM/YYYY.")

    dgt_grade_checker = DGTGradeChecker()
    grade = dgt_grade_checker.fetch_grade(
        args.DNI, exam_date, args.license_class, birth_date
    )

    if args.json:
        print(json.dumps(grade.__dict__, ensure_ascii=False))
    else:
        print(grade)


if __name__ == "__main__":
    main()
