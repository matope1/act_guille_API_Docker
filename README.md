## API de administracion de profesores con almacenamiento en BBDD

### API con FastAPI en python en Base de datos PostGresSQL

- (GET) Ver porfesores
- (GET) Ver profesores de una asignatura
- (POST) Añadir profesor
- (Delete) Eliminar profesor


### Levantar docker compose despues de Clonar repo
```bash
cd act_guille_API_Docker
```

```bash
docker compose up -d
```


### Acceder al contenedor postgres y ver la informacion 
```
docker exec -it db psql -U postgres
```
```
\c guille_db
```
```
select * from profesores;
```
```
\q #Salir de postgres
```
