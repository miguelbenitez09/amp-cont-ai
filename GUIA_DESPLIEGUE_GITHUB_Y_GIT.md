# GUÍA MAESTRA DE DESPLIEGUE EN GITHUB Y TUTORIAL PRÁCTICO DE GIT
## Ecosistema Industrial Panamá PortOps-AI v1.0
**Firma Oficial:** `Desarrollado v1.0 Miguel Benítez`  
**Autor Principal:** Miguel Benítez (`mbeni`)  
**Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria (Sección 7)  

---

## 1. SEGURIDAD DE CREDENCIALES: ¿ME DEBES PASAR TU API KEY O TOKEN?

> [!CAUTION]
> **NUNCA compartas tus contraseñas, Personal Access Tokens (PAT) ni API Keys en el chat de ningún asistente de IA ni en commits públicos de Git.**  
> La seguridad de tu cuenta de GitHub debe permanecer bajo tu custodia exclusiva.

### ¿Cómo se gestionan las credenciales de forma 100% segura?
1. **No necesitas darme tu API Key:** Tu entorno local de Windows ya cuenta con **Git Credential Manager (GCM)** instalado por defecto con Git.
2. Al ejecutar el comando `git push -u origin main` por primera vez, Windows desplegará automáticamente una ventana emergente del navegador para autenticarte con un solo clic en tu cuenta de GitHub de manera encriptada.
3. Si prefieres utilizar un **Personal Access Token (PAT)**:
   - Ve a [GitHub Token Settings](https://github.com/settings/tokens).
   - Genera un token clásico o *fine-grained* con permiso exclusivo `repo`.
   - Cuando la terminal te pida `Password for 'https://github.com':`, pega tu PAT (Windows lo almacenará en el Administrador de Credenciales cifrado y nunca viajará en texto plano).

---

## 2. FUNDAMENTOS TEÓRICOS DE GIT: ¿CÓMO FUNCIONA POR DENTRO?

Git no es un sistema de archivos que almacena diferencias (*diffs*) entre archivos, sino un **sistema de archivos direccionable por contenido criptográfico** estructurado como un **Grafo Acíclico Dirigido (DAG)**.

### 2.1 Los Tres Árboles y Zonas de Vida de Git
1. **Working Directory (Directorio de Trabajo):**  
   Los archivos físicos que ves en tu disco duro (`C:\Users\mbeni\Downloads\amp-cont-ai`). Aquí editas código y ejecutas análisis.
2. **Staging Area / Index (Área de Preparación):**  
   Un archivo binario (`.git/index`) que actúa como borrador del próximo commit. Cuando ejecutas `git add`, Git calcula el hash SHA-1/SHA-256 del contenido de cada archivo, almacena los datos en el directorio de objetos (`.git/objects`) como objetos tipo `blob`, y registra la ruta y permisos en el *Index*.
3. **Repository (Historial Inmutable de Commits):**  
   Cuando ejecutas `git commit`, Git toma el snapshot exacto del *Index*, crea un objeto de tipo `tree` (que representa la estructura de carpetas) y un objeto de tipo `commit` que apunta a ese árbol, al autor, fecha y al hash del commit padre.

### 2.2 Anatomía de un Commit y el Grafo DAG
Cada commit es inmutable: si cambias un solo byte de un archivo, su hash cambia completamente. Las ramas (*branches*) en Git no son carpetas pesadas; son simplemente **punteros móviles de 41 bytes** que apuntan al hash del último commit del grafo.

```text
(Commit A: Initial) <-- (Commit B: Medallion Pipeline) <-- (Commit C: Multi-Algorithm & Simulation)
                                                                      ^
                                                                      |
                                                                  [main] <-- HEAD
```

---

## 3. PASO A PASO: COMANDOS PARA PUBLICAR EN TU GITHUB REAL

### Paso 1: Crear el Repositorio Vacío en GitHub
1. Abre tu navegador e ingresa a: **https://github.com/new**
2. **Repository name:** `amp-cont-ai` (o `panama-portops-ai`)
3. **Description:** `Panamá PortOps-AI: Ecosistema MLOps, Benchmarking Multi-Algoritmo y Motor de Simulación Estocástica para Logística Portuaria (AMP 2015-2026). Desarrollado v1.0 Miguel Benítez.`
4. **Visibilidad:** Público (para cumplir con la misión de datos abiertos y la licencia GPL-3.0).
5. **IMPORTANTE:** **NO** marques las casillas de *"Add a README file"*, *"Add .gitignore"* ni *"Choose a license"*, ya que nuestro repositorio local ya tiene todos estos archivos meticulosamente configurados.
6. Haz clic en **Create repository**.

---

### Paso 2: Ejecutar los Comandos en tu Terminal (PowerShell)

Abre PowerShell en `C:\Users\mbeni\Downloads\amp-cont-ai` y ejecuta los siguientes comandos paso a paso:

#### 1. Verificar el Estado del Repositorio y Reglas de Ignorado
```powershell
git status
```
*¿Qué hace?* Compara los archivos en tu disco con el índice. Verás que gracias al archivo `.gitignore` que diseñamos, **ningún dataset (`.csv`, `.parquet`) ni modelo binario (`.joblib`, `.db`) será subido**, protegiendo tu ancho de banda y la higiene del repositorio.

#### 2. Agregar los Archivos al Staging Area
```powershell
git add .
```
*¿Qué hace?* Lee el archivo `.gitignore`, toma todos los archivos de código fuente, configuraciones, documentación doctoral, pruebas y scripts, calcula sus hashes criptográficos y los prepara en el *Index*.

#### 3. Crear el Primer Commit Maestro
```powershell
git commit -m "feat(core): initial release panama-portops-ai v1.0 - MLOps, multi-algorithm benchmark and stochastic simulation"
```
*¿Qué hace?* Crea el objeto *commit* inmutable en tu base de datos local de Git con la firma de autoría de Miguel Benítez.

#### 4. Asegurar la Rama Principal como `main`
```powershell
git branch -M main
```
*¿Qué hace?* Renombra la rama activa al estándar internacional moderno `main`.

#### 5. Vincular tu Repositorio Remoto de GitHub
*(Reemplaza `<tu-usuario>` por tu usuario real de GitHub, por ejemplo `mbeni`)*:
```powershell
git remote add origin https://github.com/miguelbenitez09/amp-cont-ai.git
```
*¿Qué hace?* Crea un alias llamado `origin` en tu configuración local (`.git/config`) que apunta a la URL remota de GitHub.

#### 6. Subir el Código a GitHub
```powershell
git push -u origin main
```
*¿Qué hace?*
- Empaqueta los objetos de Git y los transmite de forma comprimida al servidor de GitHub.
- El parámetro `-u` (*upstream*) vincula permanentemente tu rama local `main` con `origin/main`. En el futuro, solo necesitarás escribir `git push` o `git pull`.
- En este punto, Git Credential Manager abrirá una pequeña ventana de Windows para autenticarte de forma segura en GitHub sin exponer claves.

---

## 4. CÓMO INSPECCIONAR Y COMPRENDER LOS LOGS DE GIT

Para visualizar el historial de commits y verificar la estructura del grafo:

```powershell
# Registro compacto con hashes cortos y referencias de ramas:
git log --oneline --graph --decorate --all

# Registro detallado con estadísticas de líneas modificadas y autor:
git log --stat -n 5

# Ver el contenido exacto del último commit:
git show HEAD
```

---

## 5. PROTECCIÓN CONTRA WORKFLOWS PELIGROSOS EN GITHUB ACTIONS

Hemos creado el archivo `.github/workflows/ci.yml` configurado con los estándares más estrictos de ciberseguridad recomendados por la Linux Foundation y la OpenSSF:

1. **Principio de Mínimo Privilegio:**
   ```yaml
   permissions:
     contents: read
   ```
   El flujo de integración continua no posee permisos de escritura en el repositorio, previniendo que scripts maliciosos alteren ramas o publiquen código sin control.
2. **Aislamiento Criptográfico de Credenciales:**
   ```yaml
   uses: actions/checkout@v4
   with:
     persist-credentials: false
   ```
   Garantiza que el token temporal de GitHub no permanezca en la máquina virtual tras descargar el código.
3. **Prohibición de `pull_request_target`:**  
   Se utiliza el evento seguro `pull_request` ordinario, el cual se ejecuta en un sandbox sin acceso a secretos ni variables de entorno sensibles.
4. **Reproducibilidad Garantizada:**  
   El CI valida la semilla estocástica determinista (`seed=42`) y ejecuta la suite de 25 pruebas unitarias e integración en Ubuntu y Python 3.12.

---

## 6. SCRIPT AUTOMATIZADO DE UN SOLO PASO (`scripts/deploy_github.ps1`)

Para mayor comodidad, se incluye un script en PowerShell que automatiza las comprobaciones de higiene y te guía en el push:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_github.ps1
```

**Firma Oficial del Proyecto:**  
`Desarrollado v1.0 Miguel Benítez`  
República de Panamá, 2026.
