# dgt_grades

Consult the grades of your official DGT (Dirección General de Tráfico) exams
**in the terminal!!**.

It does this by scraping
https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/resultadoConsultaNota.faces

> Migrated from
> [GitHub Gists](https://gist.github.com/peprolinbot/abc08b61aff39e8ee7f069b24325e174)

## 📝 Exam support

We support the following exam types:

- TEORICO COMÚN
- TEORICO ESPECÍFICO A2
- All other theory exams (probably, not tested)
- CIRCULACIÓN B
- DESTREZA EN CIRCUITO CERRADO A2

If you find an exam that is not supported, you will receive a warning and basic
info. Please create an issue and/or PR.

## ⚙️ Running

You can easily run this if you have [Nix installed](https://nixos.org/download)
with:

```bash
nix run github:peprolinbot/dgt_grades -- 12345678A 28/02/2026 B 13/01/2000
```

If you don't want to use nix, you can install the python package and run with:
```bash
pip install git+https://github.com/peprolinbot/dgt_grades
dgt-grade-check 12345678A 28/02/2026 B 13/01/2000
```

Use the flag `-h` to see the avaliable options:
```
usage: dgt-grade-check [-h] [-j] DNI exam_date license_class birth_date

Check the grade of a DGT test you did. Uses
https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/resultadoConsultaNota.faces

positional arguments:
  DNI            Your DNI (NIF/NIE)
  exam_date      The date when you took the exam, in DD/MM/YYYY format
  license_class  The type of driving license the test was for, e.g. B
  birth_date     Your birth date, in DD/MM/YYYY format

options:
  -h, --help     show this help message and exit
  -j, --json     Print the output in JSON format
```

## ❤️ Credits
Originally based on: [this](https://github.com/josericardopenase/drivingschool-metrics-backend/blob/e1a8627e49d0ec946c27d8cb9cf900b7dbc65239/administrative_management/infrastructure/grade_checkers/dgt_theory_grade_checker.py) by [@josericardopenase](https://github.com/josericardopenase) 
