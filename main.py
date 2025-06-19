from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import List
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,  Session
import logging 
import os

# env
app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")
#DATABASE_URL = "sqlite:///./profesores.db"
VALID_ASIGNATURES = ["programacion", "docker", "ia", "devops"]



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



logging.basicConfig(

    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)




engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base  = declarative_base()


# sql
class profesoresDB(Base):
    __tablename__ = "profesores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)
    asignature = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)



class profes(BaseModel):
    name: str
    asignature: str

    # Profesor debera tener una asignatura validada
    @field_validator("asignature")
    def asig_listada(cls, profe):
        list_func = ["programacion", "docker", "ia", "devops"]
        if profe not in list_func:
            logger.warning(f"El profesor no tiene una asignatura valida {VALID_ASIGNATURES}")
            raise HTTPException(status_code=422, detail=f"ERROR: El profesor debera tener la asignatura de, Opciones: {VALID_ASIGNATURES}")
        return profe





# Función para manejar los errores ValueError
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# http logger
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    
    return response


@app.get("/")
def test_Conex():
    logger.info(f"--CONEXION EXITOSA--")
    return {"message" : "Ha podido acceder a la plantilla de profesores"}


@app.get("/profesores", response_model=list[profes])
def all_profe(db: Session = Depends(get_db)):
    logger.info(f"Solicitud enviada para MOSTRAR TODOS los profesores")

    exist_profesor = db.query(profesoresDB).all()
    if not exist_profesor:

        raise HTTPException(status_code=404, detail="No hay profesores registrados")
    logger.info("Se estan mostrando todos los profesores EXITOSAMENTE")
    return exist_profesor


# Mostrar profesores por asignatura
@app.get("/profesor/asignatura/{asignature}", response_model=List[profes])
def asig_profe(asignature: str, 
                          db: Session = Depends(get_db) # Session db
                          ):

    exist_profe = db.query(profesoresDB).filter(profesoresDB.asignature == asignature).all()
    logger.info(f"Recibida petición para mostrar profesores que tienen la asignatura de {asignature}")
    # Mensaje al cliente 404, y logg para el servidor si no existe la asignatura
    if asignature not in VALID_ASIGNATURES:

        logger.warning(f"Asignatura no encontrada: {asignature}, Opciones: {', '.join(VALID_ASIGNATURES)}")
        raise HTTPException(status_code=400, detail= f"La asignatura '{asignature}' no es válida. Opciones: {', '.join(VALID_ASIGNATURES)}"
        )

    if not exist_profe:
        logger.warning(f"No se encontraron profesores con asignatura: {asignature}")
        raise HTTPException(status_code=404, detail=f"No se encontraron profesores con la asignatura: {asignature}")
    logger.info("--Se han mostrado los profesores EXITOSAMENTE--")
    return exist_profe


# Añadir profesor
@app.post("/profesor/nuevo")
def new_profe(name: profes, 
              db: Session = Depends(get_db)
              ):
    

    # Si el profesor ya existe con el mismo nombre, no se podra añadir
    existe = db.query(profesoresDB).filter(profesoresDB.name == name.name).first()
    if existe:
        logger.warning(f"Intento de registrar profesor duplicado: {name.name}")
        raise HTTPException(status_code=400, detail="El profesor ya está registrado, prueba con otro nombre")

    # añadir datos a bd
    profe_db = profesoresDB(
        name=name.name,
        asignature=name.asignature
)
    
    db.add(profe_db)
    db.commit()
    db.refresh(profe_db)
    db.close()

    logger.info(f"--El profesor {name} se ha REGISTRADO CORRECTAMENTE--")    
    return {
        "status":"Success",
        "msg": "profesor registrado correctamente",
        "profesor": {
            "name": name.name
        }
    }


@app.delete("/profesor/despido/{name}")
def delete_profe(name: str,
                db: Session = Depends(get_db)
                    ):

    profe = db.query(profesoresDB).filter(profesoresDB.name == name).first()

    # Mensaje de error si el profesor no existe
    if not profe:
        logger.warning(f"No se encontro profesor: {name}")
        raise HTTPException(status_code=404, detail="profesor no encontrado")
    
    db.delete(profe)
    db.commit()
    logger.info(f"Eliminado el profesor: {name}")
    return {"status": "Success",
            "mensaje": f"profesor {name} eliminado exitosamente"}
