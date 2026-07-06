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

## Demostracion con Terraform

Para demostrar el despliegue desde cero ante el profesor, puedes destruir los recursos y volverlos a crear. Esto elimina la instancia, el storage share y el ACR, por lo que tambien elimina la base SQLite guardada en Azure.

Destruir recursos:

```bash
cd /home/jahir/azure_biblioteca/infra
terraform destroy
```

Cuando Terraform pregunte, escribe `yes`.

Volver a desplegar desde cero:

```bash
cd /home/jahir/azure_biblioteca/infra
terraform apply -target=azurerm_resource_group.main -target=azurerm_container_registry.main
```

Despues construye y sube las imagenes:

```bash
cd /home/jahir/azure_biblioteca
az acr login --name acrazurebibliotecadev

docker build -t acrazurebibliotecadev.azurecr.io/azure-biblioteca-backend:latest backend
docker push acrazurebibliotecadev.azurecr.io/azure-biblioteca-backend:latest

docker build -t acrazurebibliotecadev.azurecr.io/azure-biblioteca-frontend:latest frontend
docker push acrazurebibliotecadev.azurecr.io/azure-biblioteca-frontend:latest
```

Finalmente crea Azure Container Instances:

```bash
cd /home/jahir/azure_biblioteca/infra
terraform apply
```

Para una demostracion mas rapida, no destruyas todo. Haz un cambio menor, reconstruye las imagenes, ejecuta `docker push` y luego:

```bash
cd /home/jahir/azure_biblioteca/infra
terraform apply
```

Terraform compara el estado declarado con Azure y solo aplica cambios necesarios.

## Demo desde otra computadora

La forma mas simple para una demostracion es usar esta misma laptop, porque ya tiene:

- Docker Desktop conectado a WSL.
- Azure CLI con `az login`.
- Terraform instalado en `~/.local/bin`.
- Estado local de Terraform en `infra/terraform.tfstate`.

Si usas otra computadora, tambien se puede, pero hay que preparar el entorno:

1. Instalar Git, Docker, Azure CLI y Terraform.
2. Clonar el repositorio:

```bash
git clone https://github.com/Jahir28/azure_biblioteca.git
cd azure_biblioteca
```

3. Iniciar sesion en Azure:

```bash
az login
az account set --subscription da09da24-1715-4fe3-b11d-636490598614
```

4. Ejecutar Docker Compose local si solo quieres probar la app:

```bash
docker compose up --build
```

5. Para administrar los recursos ya desplegados con Terraform desde otra computadora, hace falta el estado de Terraform. Este proyecto usa estado local, por lo que `infra/terraform.tfstate` no se sube a GitHub. Si no tienes ese archivo, Terraform no sabe que los recursos ya existen y puede intentar crearlos de nuevo.

Opciones:

- Usar la misma laptop para la demo de Terraform.
- Copiar de forma privada `infra/terraform.tfstate` a la otra computadora.
- Destruir los recursos desde la laptop original y recrearlos desde la nueva computadora.
- Configurar un backend remoto de Terraform en Azure Storage para compartir estado entre equipos.

Para este proyecto academico, lo mas practico es hacer la demo desde la laptop donde ya se hizo el despliegue.

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
