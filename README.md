# Azure Biblioteca

Proyecto completo para una biblioteca con frontend Vue 3 + Vite, backend FastAPI, SQLite, Docker, Docker Compose, Terraform para Azure Container Instances y GitHub Actions.

## Estructura

- `backend/`: API FastAPI con SQLAlchemy y SQLite.
- `frontend/`: app Vue 3 + Vite servida con Nginx en Docker.
- `infra/`: Terraform para Azure Resource Group, ACR, Storage Share y Azure Container Instances.
- `.github/workflows/`: pipeline de validacion, build, push y despliegue.
- `docker-compose.yml`: ejecucion local.

## Ejecucion local

```bash
docker compose up --build
```

Servicios:

- Frontend: http://localhost:8080
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

La base SQLite se guarda en el volumen Docker `backend_data`.

Para reconstruir despues de cambios en el frontend:

```bash
docker compose build frontend
docker compose up -d
```

## Funcionalidad

- Dashboard con metricas.
- CRUD de libros.
- CRUD de usuarios.
- CRUD de prestamos.
- Metricas: total de libros, libros disponibles, libros prestados, usuarios registrados y prestamos activos.

## Flujo de prestamos

La disponibilidad de libros se administra automaticamente desde los prestamos:

1. Al crear un libro, queda disponible.
2. Al crear un prestamo activo, el libro queda como prestado.
3. Mientras el prestamo siga activo, ese libro no aparece como opcion para nuevos prestamos.
4. Al editar el prestamo y marcarlo como devuelto, el libro vuelve a quedar disponible.

No es necesario editar el libro para cambiar su estado de disponibilidad.

## Interfaz

El frontend incluye:

- Tarjetas de metricas para total de libros, disponibles, prestados, usuarios y prestamos activos.
- Secciones separadas para libros, usuarios y prestamos.
- Formularios de alta/edicion.
- Tablas con badges de estado.
- Estados vacios cuando aun no hay registros.

## Despliegue en Azure con Terraform

Recursos por defecto:

- Resource group: `rg-azure-biblioteca-dev`
- Container registry: `acrazurebibliotecadev`
- Container instance: `aci-azure-biblioteca-dev`
- Imagenes: `azure-biblioteca-backend` y `azure-biblioteca-frontend`

Terraform administra el resource group, ACR, storage share y container instance. Para el primer despliegue manual, usa este flujo en dos fases.

Primero crea el resource group y ACR con Terraform:

```bash
az login
cd infra
terraform init
terraform apply -target=azurerm_resource_group.main -target=azurerm_container_registry.main
```

Luego construye y sube las imagenes:

```bash
cd ..
az acr login --name acrazurebibliotecadev

ACR_LOGIN_SERVER=$(az acr show --name acrazurebibliotecadev --query loginServer -o tsv)
docker build -t $ACR_LOGIN_SERVER/azure-biblioteca-backend:latest backend
docker build -t $ACR_LOGIN_SERVER/azure-biblioteca-frontend:latest frontend
docker push $ACR_LOGIN_SERVER/azure-biblioteca-backend:latest
docker push $ACR_LOGIN_SERVER/azure-biblioteca-frontend:latest
```

Finalmente despliega Azure Container Instances:

```bash
cd infra
terraform apply
```

Terraform imprimira la URL publica del frontend y del backend.

Si ya creaste recursos manualmente en Azure con los mismos nombres, importalos al estado de Terraform antes de aplicar o elimina esos recursos manuales para evitar conflictos.

## GitHub Actions

El workflow ejecuta validacion en cada `push` y `pull_request`. El despliegue a Azure queda como ejecucion manual desde `workflow_dispatch`, porque requiere credenciales de Azure.

Para habilitar despliegue automatico desde GitHub Actions, configura el secreto `AZURE_CREDENTIALS` en el repositorio con un service principal:

```bash
az ad sp create-for-rbac \
  --name sp-azure-biblioteca-dev \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID> \
  --sdk-auth
```

El workflow valida backend, frontend y Terraform. En `main` construye y sube imagenes a `acrazurebibliotecadev`, y despliega ACI con la etiqueta del commit.

Si tu tenant no permite crear service principals y aparece `Insufficient privileges to complete the operation`, usa el despliegue manual con `az login` desde WSL. Ese metodo funciona con tu usuario interactivo y no necesita `AZURE_CREDENTIALS`.

## Validacion local recomendada

```bash
docker compose config
docker compose up --build
curl http://localhost:8000/health
```

Prueba funcional:

1. Crear un libro.
2. Crear un usuario.
3. Crear un prestamo.
4. Confirmar que el libro queda como prestado.
5. Editar el prestamo y marcarlo como devuelto.
6. Confirmar que el libro vuelve a disponible.

## Notas para WSL en Windows

Si usas Docker Desktop en Windows, activa la integracion con tu distro WSL en `Settings > Resources > WSL Integration`. Despues reinicia la terminal WSL y valida:

```bash
docker --version
docker compose version
```

Terraform y Azure CLI pueden instalarse dentro de WSL para ejecutar los comandos de infraestructura desde la misma carpeta del proyecto.
