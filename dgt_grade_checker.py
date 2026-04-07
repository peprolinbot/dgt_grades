import requests
from bs4 import BeautifulSoup
import argparse
from datetime import datetime


class GradeResponse():
    def __init__(self, calification: str, num_errors: int, errors: dict = None):
        self.calification: str = calification
        self.num_errors: int = num_errors
        self.errors: dict = errors

        self.passed: bool = (calification == "APTO")

    def __repr__(self) -> str:
        return f"Calification: {self.calification} | {self.num_errors} Errors{f': {self.errors}' if not self.errors is None else ''}"


class DGTGradeChecker():
    def __init__(self):
        self.url = "https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/consultaNota.faces"
        self.session = requests.Session()

    def _get_view_state(self) -> str:
        response = self.session.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.find('input', {'name': 'javax.faces.ViewState'})['value']

    def _submit_form(self, payload: dict) -> BeautifulSoup:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self.session.post(self.url, data=payload, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    def fetch_grade(self, dni: str, exam_date: datetime, licenseClass: str, birth_date: datetime) -> GradeResponse:
        view_state = self._get_view_state()
        payload = {
            "formularioBusquedaNotas": "formularioBusquedaNotas",
            "formularioBusquedaNotas:nifnie": dni,
            "formularioBusquedaNotas:fechaExamen": exam_date.strftime("%d/%m/%Y"),
            "formularioBusquedaNotas:clasepermiso": licenseClass,
            "formularioBusquedaNotas:fechaNacimiento": birth_date.strftime("%d/%m/%Y"),
            "formularioBusquedaNotas:honeypot": "",
            "formularioBusquedaNotas:j_id51": "Buscar",
            "javax.faces.ViewState": view_state,
        }
        soup = self._submit_form(payload)

        # Find all <li> elements with the class 'msgError'
        error_messages = soup.find_all('li', class_='msgError')
        if not error_messages:
            calificacion = soup.find(
                id="formularioResultadoNotas:j_id38:0:j_id70").get_text(strip=True)

            tipo_examen = soup.find(
                id="formularioResultadoNotas:j_id38:0:j_id54").get_text(strip=True)

            if tipo_examen == "CIRCULACIÓN":
                errores = {}
                num_errores = 0
                for tipo in ("eliminatoria", "deficiente", "leve"):
                    errores_text = soup.find(
                        'td', headers=f"faltasCometidas {tipo}").get_text(strip=True)

                    if errores_text == "Detalle no disponible" or errores_text == "0":
                        errores_tipo = []
                    else:
                        errores_tipo = errores_text.split(" - ")
                        num_errores += len(errores_tipo)

                    # We want the key to be in plural
                    errores[tipo+"s"] = errores_tipo

            else:  # Idk which other types there are apart from CIRCULACIÓN and TEÓRICO COMÚN, so we default to TEÓRICO COMÚN
                num_errores = int(soup.find(
                    id="formularioResultadoNotas:j_id38:0:j_id78").text)
                errores = None

            return GradeResponse(calification=calificacion, num_errors=num_errores, errors=errores)
        else:
            # Extract the text from the errors and join with newlines
            error_messages_text = '\n'.join(li.get_text(strip=True)
                                            for li in error_messages)

            raise ValueError(error_messages_text)


def main():
    parser = argparse.ArgumentParser(
        description="Check the grade of a DGT test you did. Uses https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/resultadoConsultaNota.faces")
    parser.add_argument("DNI", type=str, help="Your DNI (NIF/NIE)")
    parser.add_argument("exam_date", type=str,
                        help="The date when you took the exam, in DD/MM/YYYY format")
    parser.add_argument("license_class", type=str,
                        help="The type of driving license the test was for, e.g. B")
    parser.add_argument("birth_date", type=str,
                        help="Your birth date, in DD/MM/YYYY format")

    args = parser.parse_args()

    try:
        exam_date = datetime.strptime(args.exam_date, "%d/%m/%Y")
        birth_date = datetime.strptime(args.birth_date, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Error: The dates format should be DD/MM/YYYY.")

    dgt_grade_checker = DGTGradeChecker()
    grade = dgt_grade_checker.fetch_grade(
        args.DNI, exam_date, args.license_class, birth_date)

    print(grade)


if __name__ == "__main__":
    main()
