import requests
from bs4 import BeautifulSoup
import datetime
import warnings


class BasicGradeResponse:
    def __init__(self, type: str, calification: str):
        self.calification: str = calification
        self.type = type

        self.passed: bool = calification == "APTO"

    def __repr__(self) -> str:
        return f"Type: {self.type}\nCalification: {self.calification}"


class TheoryGradeResponse(BasicGradeResponse):
    def __init__(self, type: str, calification: str, num_errors: int):
        super().__init__(type, calification)

        self.num_errors: int = num_errors

    def __repr__(self) -> str:
        lines = [super().__repr__()]
        lines.append(f"Errors: {self.num_errors}")
        return "\n".join(lines)


class CirculationGradeResponse(BasicGradeResponse):
    def __init__(
        self, type: str, calification: str, num_errors: int, errors: dict = {}
    ):
        super().__init__(type, calification)

        self.num_errors: int = num_errors
        self.errors: dict = errors

    def __repr__(self) -> str:
        lines = [super().__repr__()]
        lines.append(f"{self.num_errors} Errors:")
        for err_type, errors in self.errors:
            lines.append(f"\t- {err_type}: {', '.join(errors)}")
        return "\n".join(lines)


class ClosedCircuitGradeResponse(BasicGradeResponse):
    def __init__(
        self, type: str, calification: str, num_errors: int, maneuvers: dict = {}
    ):
        super().__init__(type, calification)

        self.maneuvers: dict = maneuvers

    def __repr__(self) -> str:
        lines = [super().__repr__()]

        lines.append("Errors:")
        lines.append("| Maniobra | Eliminatorias | Deficientes | Leves |")
        lines.append("|------------------------------------------------|")
        fmt = "| {:^8} | {:^13} | {:^11} | {:^5} |"
        for name, errors in self.maneuvers.items():
            lines.append(fmt.format(*([name] + list(errors.values()))))

        return "\n".join(lines)


class DGTGradeChecker:
    def __init__(self):
        self.url = "https://sedeclave.dgt.gob.es/WEB_NOTP_CONSULTA/consultaNota.faces"
        self.session = requests.Session()

    def _get_view_state(self) -> str:
        response = self.session.get(self.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find("input", {"name": "javax.faces.ViewState"})["value"]

    def _submit_form(self, payload: dict) -> BeautifulSoup:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self.session.post(self.url, data=payload, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    def fetch_grade(
        self, dni: str, exam_date: datetime, licenseClass: str, birth_date: datetime
    ) -> BasicGradeResponse:
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
        error_messages = soup.find_all("li", class_="msgError")
        if not error_messages:
            calificacion = soup.find(
                id="formularioResultadoNotas:j_id38:0:j_id70"
            ).get_text(strip=True)

            tipo_examen = soup.find(
                id="formularioResultadoNotas:j_id38:0:j_id54"
            ).get_text(strip=True)

            if tipo_examen == "CIRCULACIÓN":
                errors = {}
                num_errors = 0
                for tipo in ("eliminatoria", "deficiente", "leve"):
                    type_errors_text = soup.find(
                        "td", headers=f"faltasCometidas {tipo}"
                    ).get_text(strip=True)

                    if (
                        type_errors_text == "Detalle no disponible"
                        or type_errors_text == "0"
                    ):
                        type_errors = []
                    else:
                        type_errors = type_errors_text.split(" - ")
                        num_errors += len(type_errors)

                    # We want the key to be in plural
                    errors[tipo + "s"] = type_errors

                return CirculationGradeResponse(
                    type=tipo_examen,
                    calification=calificacion,
                    num_errors=num_errors,
                    errors=errors,
                )
            elif tipo_examen == "DESTREZA EN CIRCUITO CERRADO":
                tabla = soup.find(id="formularioResultadoNotas:j_id38:0:tablaRegistros")
                maneuvers = {}
                num_errors = 0
                for maniobra in tabla.find_all("tbody"):
                    maneuver_name = maniobra.find(
                        "td", headers="faltasCometidas maniobra"
                    ).get_text(strip=True)
                    maneuvers[maneuver_name] = {}
                    for tipo in ("eliminatoria", "deficiente", "leve"):
                        num_errors_text = maniobra.find(
                            "td", headers=f"faltasCometidas {tipo}"
                        ).get_text(strip=True)

                        maneuvers[maneuver_name][tipo + "s"] = int(num_errors_text)
                return ClosedCircuitGradeResponse(
                    type=tipo_examen,
                    calification=calificacion,
                    num_errors=num_errors,
                    maneuvers=maneuvers,
                )
            elif "TEÓRICO" in tipo_examen:
                num_errors = int(
                    soup.find(id="formularioResultadoNotas:j_id38:0:j_id78").text
                )
                return TheoryGradeResponse(
                    type=tipo_examen,
                    calification=calificacion,
                    num_errors=num_errors,
                )
            else:
                warnings.warn(f"Unknown exam type: {tipo_examen}")
                return BasicGradeResponse(type=tipo_examen, calification=calificacion)
        else:
            # Extract the text from the errors and join with newlines
            error_messages_text = "\n".join(
                li.get_text(strip=True) for li in error_messages
            )

            raise ValueError(error_messages_text)
