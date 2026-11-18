"""HTTP API shared by the network client and Swagger UI."""
import logging
from contextlib import asynccontextmanager
from datetime import date
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path as PathParameter, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from config import ROLE_ADMIN, ROLE_OPERATOR, ROLES_LIST
from database.connection import get_session, init_db
from database.models import User
from services import department_service as departments
from services import report_service as reports
from services import teacher_service as teachers
from services import workload_service as workload
from services.auth_service import session_key, user_info, verify_credentials

LOG = logging.getLogger("uvicorn.error")
SESSION_SECONDS = 3600
AUTH = HTTPBearer(auto_error=False)
EXPORT_TYPES = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "pdf": "application/pdf"}


class ApiProblem(BaseModel):
    detail: str


AUTH_ERRORS = {401: {"model": ApiProblem, "description": "Требуется действующая сессия"}}
VALIDATION_ERRORS = {422: {"model": ApiProblem, "description": "Некорректные поля запроса"}}
WRITE_ERRORS = {**VALIDATION_ERRORS,
                403: {"model": ApiProblem, "description": "Недостаточно прав"},
                409: {"model": ApiProblem, "description": "Операция отклонена по правилам учета"}}


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Credentials(Input):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256, json_schema_extra={"format": "password"})
    model_config = ConfigDict(extra="forbid")


class Identity(BaseModel):
    id: int
    username: str
    role_id: int
    role_name: str


class LoginResult(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = SESSION_SECONDS
    user: Identity


class Change(BaseModel):
    message: str
    id: int | None = None


class Department(BaseModel):
    id: int
    name: str


class Discipline(Department):
    code: str
    department_id: int


class TeacherInput(Input):
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str = Field(default="", max_length=100)
    department_id: int = Field(gt=0, strict=True)
    qualification: str = Field(default="", max_length=100)
    experience: int = Field(default=0, ge=0, le=70)
    phone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=100)
    status: Literal["работает", "в отпуске", "уволен"] = "работает"
    birth_date: date | None = None
    allow_similar: bool = False


class TeacherRow(BaseModel):
    id: int
    full_name: str
    department_id: int
    department: str
    experience: int
    status: str
    hours: int


class TeacherCard(TeacherRow):
    last_name: str
    first_name: str
    middle_name: str
    birth_date: date | None
    phone: str | None
    email: str | None
    qualification: str | None


class PoolInput(Input):
    academic_year: str = Field(pattern=r"^\d{4}-\d{4}$")
    semester: int = Field(ge=1, le=2, strict=True)
    group_name: str = Field(min_length=1, max_length=100)
    discipline_id: int = Field(gt=0, strict=True)
    hours_lecture: int = Field(ge=0, le=1000000, strict=True)
    hours_practice: int = Field(ge=0, le=1000000, strict=True)
    weeks: int = Field(default=18, ge=1, le=52, strict=True)


class PoolRow(BaseModel):
    id: int
    academic_year: str
    semester: int
    group_name: str
    discipline_id: int
    discipline: str
    hours_lecture: int
    hours_practice: int
    weeks: int
    available_lecture: int
    available_practice: int


class AssignmentInput(Input):
    teacher_id: int = Field(gt=0, strict=True)
    pool_id: int = Field(gt=0, strict=True)
    hours_lecture: int = Field(ge=0, le=1000000, strict=True)
    hours_practice: int = Field(ge=0, le=1000000, strict=True)


class AssignmentRow(BaseModel):
    id: int
    teacher_id: int
    teacher: str
    pool_id: int | None
    academic_year: str
    semester: int
    group_name: str
    discipline: str
    hours_lecture: int
    hours_practice: int
    total_hours: int
    hours_per_week: float


class Period(BaseModel):
    academic_year: str | None = None
    semester: Literal["0", "1", "2"] | None = None
    department_id: int | None = Field(default=None, gt=0)

    def filters(self):
        return dict(academic_year=self.academic_year,
                    semester=int(self.semester) if self.semester is not None else None,
                    department_id=self.department_id)


class ReportFilters(Period):
    teacher_id: int | None = Field(default=None, gt=0)

    def filters(self):
        return {**super().filters(), "teacher_id": self.teacher_id}


@asynccontextmanager
async def lifespan(app):
    init_db()
    app.state.sessions = {}
    app.state.session_lock = Lock()
    yield


app = FastAPI(title="Учет преподавателей и учебной нагрузки", version="1.0.0", lifespan=lifespan)
public = APIRouter(prefix="/api/v1")
protected = APIRouter(prefix="/api/v1", responses=AUTH_ERRORS)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    fields = [".".join(map(str, issue["loc"])) for issue in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "Проверьте поля: " + ", ".join(fields)})


def active_session(request: Request, auth: Annotated[HTTPAuthorizationCredentials | None, Depends(AUTH)]):
    token = auth.credentials if auth else ""
    with request.app.state.session_lock:
        record = request.app.state.sessions.get(token)
        if record and record[1] <= monotonic():
            request.app.state.sessions.pop(token, None)
            record = None
    if record:
        with get_session() as session:
            user = session.get(User, record[0])
            if user and session_key(user) == record[2] and user.role and user.role.name in ROLES_LIST:
                return Identity(**user_info(user))
        with request.app.state.session_lock:
            request.app.state.sessions.pop(token, None)
    raise HTTPException(401, "Войдите в систему повторно.", headers={"WWW-Authenticate": "Bearer"})


Current = Annotated[Identity, Depends(active_session)]
Identifier = Annotated[int, PathParameter(gt=0)]


def editor(user: Current):
    if user.role_name not in (ROLE_ADMIN, ROLE_OPERATOR):
        raise HTTPException(403, "Роль разрешает просмотр и экспорт.")
    return user


Editor = Annotated[Identity, Depends(editor)]


def change(user, resource, result, entity_id=None):
    ok, message, *saved_id = result
    if not ok:
        raise HTTPException(409, message)
    identifier = saved_id[0] if saved_id else entity_id
    LOG.info("change user_id=%d resource=%s id=%s", user.id, resource, identifier)
    return Change(message=message, id=identifier)


@public.get("/health")
def health():
    return {"status": "ok"}


@public.post("/auth/login", responses={**AUTH_ERRORS, **VALIDATION_ERRORS})
def login(data: Credentials, request: Request) -> LoginResult:
    credentials = verify_credentials(data.username, data.password)
    if credentials is None or credentials[0]["role_name"] not in ROLES_LIST:
        raise HTTPException(401, "Неверное имя пользователя или пароль.")
    info, key = credentials
    token = token_urlsafe(32)
    with request.app.state.session_lock:
        now = monotonic()
        sessions = request.app.state.sessions
        for key in [key for key, value in sessions.items() if value[1] <= now]:
            del sessions[key]
        sessions[token] = (info["id"], now + SESSION_SECONDS, key)
    return LoginResult(access_token=token, user=Identity(**info))


@protected.delete("/auth/session", status_code=204)
def logout(request: Request, user: Current, auth: Annotated[HTTPAuthorizationCredentials, Depends(AUTH)]):
    with request.app.state.session_lock:
        request.app.state.sessions.pop(auth.credentials, None)
    return Response(status_code=204)


@protected.get("/departments")
def list_departments(user: Current) -> list[Department]:
    return [Department(id=row.id, name=row.name) for row in departments.get_departments()]


@protected.get("/disciplines")
def list_disciplines(user: Current) -> list[Discipline]:
    return [Discipline(id=row.id, name=row.name, code=row.code, department_id=row.department_id)
            for row in departments.get_disciplines()]


@protected.get("/years")
def list_years(user: Current) -> list[str]:
    return workload.get_academic_years()


@protected.get("/teachers", responses=VALIDATION_ERRORS)
def list_teachers(user: Current, search: str | None = None,
                  department_id: Annotated[int | None, Query(gt=0)] = None,
                  academic_year: str | None = None, rate: Literal["below", "equal", "above"] | None = None,
                  sort: Literal["full_name", "experience", "department", "total_hours"] = "full_name",
                  descending: bool = False) -> list[TeacherRow]:
    rows = teachers.get_teachers(search, department_id, academic_year=academic_year, rate_filter=rate,
                                 sort_by=sort, descending=descending)
    return [TeacherRow(id=row.id, full_name=row.full_name, department_id=row.department_id,
                       department=row.department.name if row.department else "",
                       experience=row.experience or 0, status=row.status or "работает",
                       hours=row.period_hours) for row in rows]


@protected.post("/teachers", status_code=201, responses=WRITE_ERRORS)
def create_teacher(data: TeacherInput, user: Editor) -> Change:
    return change(user, "teacher.create",
                  teachers.add_teacher(data.model_dump(exclude={"allow_similar"}), data.allow_similar))


@protected.get("/teachers/{teacher_id}", responses={
    **VALIDATION_ERRORS, 404: {"model": ApiProblem, "description": "Карточка не найдена"},
})
def get_teacher(teacher_id: Identifier, user: Current) -> TeacherCard:
    row = teachers.get_teacher_by_id(teacher_id)
    if row is None:
        raise HTTPException(404, "Преподаватель не найден.")
    return TeacherCard(id=row.id, full_name=row.full_name, department_id=row.department_id,
                       department=row.department.name if row.department else "",
                       experience=row.experience or 0, status=row.status or "работает", hours=row.total_hours,
                       last_name=row.last_name, first_name=row.first_name, middle_name=row.middle_name,
                       birth_date=row.birth_date, phone=row.phone, email=row.email, qualification=row.qualification)


@protected.put("/teachers/{teacher_id}", responses=WRITE_ERRORS)
def update_teacher(teacher_id: Identifier, data: TeacherInput, user: Editor) -> Change:
    values = data.model_dump(exclude={"allow_similar"})
    return change(user, "teacher.update", teachers.update_teacher(teacher_id, values, data.allow_similar), teacher_id)


@protected.delete("/teachers/{teacher_id}", responses=WRITE_ERRORS)
def delete_teacher(teacher_id: Identifier, user: Editor) -> Change:
    return change(user, "teacher.delete", teachers.delete_teacher(teacher_id), teacher_id)


@protected.get("/pools", responses=VALIDATION_ERRORS)
def list_pools(user: Current, filters: Annotated[Period, Query()]) -> list[PoolRow]:
    return [PoolRow(id=row.id, academic_year=row.academic_year, semester=row.semester,
                    group_name=row.group_name, discipline_id=row.discipline_id, discipline=row.discipline.name,
                    hours_lecture=row.hours_lecture, hours_practice=row.hours_practice, weeks=row.weeks,
                    available_lecture=row.available_lecture, available_practice=row.available_practice)
            for row in workload.get_pools(**filters.filters())]


@protected.post("/pools", status_code=201, responses=WRITE_ERRORS)
def create_pool(data: PoolInput, user: Editor) -> Change:
    return change(user, "pool.create", workload.save_pool(**data.model_dump()))


@protected.put("/pools/{pool_id}", responses=WRITE_ERRORS)
def update_pool(pool_id: Identifier, data: PoolInput, user: Editor) -> Change:
    return change(user, "pool.update", workload.save_pool(pool_id=pool_id, **data.model_dump()))


@protected.delete("/pools/{pool_id}", responses=WRITE_ERRORS)
def delete_pool(pool_id: Identifier, user: Editor) -> Change:
    return change(user, "pool.delete", workload.delete_pool(pool_id), pool_id)


@protected.get("/assignments", responses=VALIDATION_ERRORS)
def list_assignments(user: Current, filters: Annotated[ReportFilters, Query()]) -> list[AssignmentRow]:
    return [AssignmentRow(id=row.id, teacher_id=row.teacher_id, teacher=row.teacher.full_name,
                          pool_id=row.pool_id, academic_year=row.academic_year, semester=row.semester,
                          group_name=row.pool.group_name if row.pool else "Не указана",
                          discipline=row.discipline.name, hours_lecture=row.hours_lecture,
                          hours_practice=row.hours_practice, total_hours=row.total_hours,
                          hours_per_week=row.hours_per_week)
            for row in workload.get_workloads(**filters.filters())]


@protected.post("/assignments", status_code=201, responses=WRITE_ERRORS)
def create_assignment(data: AssignmentInput, user: Editor) -> Change:
    return change(user, "assignment.create", workload.add_workload(None, discipline_id=None, **data.model_dump()))


@protected.put("/assignments/{assignment_id}", responses=WRITE_ERRORS)
def update_assignment(assignment_id: Identifier, data: AssignmentInput, user: Editor) -> Change:
    result = workload.update_workload(assignment_id, None, discipline_id=None, **data.model_dump())
    return change(user, "assignment.update", result, assignment_id)


@protected.delete("/assignments/{assignment_id}", responses=WRITE_ERRORS)
def delete_assignment(assignment_id: Identifier, user: Editor) -> Change:
    return change(user, "assignment.delete", workload.delete_workload(assignment_id), assignment_id)


@protected.get("/reports/workload/{format}", response_class=Response,
               responses={**VALIDATION_ERRORS,
                          200: {"content": {media: {"schema": {"type": "string", "format": "binary"}}
                                            for media in EXPORT_TYPES.values()}},
                          500: {"model": ApiProblem, "description": "Не удалось сформировать ведомость"}})
def download_report(format: Literal["xlsx", "pdf"], user: Current, filters: Annotated[ReportFilters, Query()]):
    export = {"xlsx": reports.export_workload_to_excel, "pdf": reports.export_workload_to_pdf}[format]
    with TemporaryDirectory(prefix="college-report-") as folder:
        file = Path(folder) / f"workload.{format}"
        ok, message = export(str(file), **filters.filters())
        if not ok:
            LOG.error("report export failed: %s", message)
            raise HTTPException(500, "Не удалось сформировать ведомость.")
        return Response(file.read_bytes(), media_type=EXPORT_TYPES[format],
                        headers={"Content-Disposition": f'attachment; filename="workload.{format}"'})


app.include_router(public)
app.include_router(protected)
