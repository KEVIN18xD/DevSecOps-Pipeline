# Lab: Integración de Tubería DevSecOps Completa (SAST / SCA / DAST con Puertas de Seguridad)

**Curso:** Seguridad en Aplicaciones  
**Basado en:** [AdhamMarzouk/DevSecOps-Pipeline](https://github.com/AdhamMarzouk/DevSecOps-Pipeline)  
**Fecha:** Noviembre 2026

---

## 1. Resumen Ejecutivo

Este laboratorio implementa una **tubería CI/CD automatizada** con GitHub Actions que integra tres capas de análisis de seguridad:

| Etapa | Herramienta | Tipo de Análisis | Puerta de Seguridad |
|-------|-------------|-------------------|----------------------|
| SAST  | SonarCloud  | Análisis estático de código fuente | Quality Gate (falla en issues Blocker) |
| SCA + Container Scan | Trivy | Dependencias vulnerables + imagen base | Falla en CVEs CRITICAL o HIGH |
| DAST  | OWASP ZAP   | Escaneo dinámico de la app en ejecución | Falla en alertas de riesgo HIGH |

La aplicación objetivo es una **API FastAPI intencionalmente vulnerable** con 7 clases de vulnerabilidades plantadas.

---

## 2. Objetivos del Laboratorio

1. Construir una tubería CI/CD con **puertas de seguridad** (security gates) que bloqueen despliegues inseguros.
2. Integrar análisis **SAST** (SonarCloud) para detectar vulnerabilidades en código fuente.
3. Integrar análisis **SCA** (Trivy) para detectar dependencias con CVEs conocidos y vulnerabilidades en la imagen base del contenedor.
4. Integrar análisis **DAST** (OWASP ZAP) para detectar vulnerabilidades explotables en tiempo de ejecución.
5. Generar artefactos de evidencia (reportes SARIF y HTML).
6. Analizar las brechas de cobertura entre herramientas.

---

## 3. Arquitectura de la Tubería

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Push a main / Dispatch                        │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │     BUILD      │
              │  Docker build  │
              │  + save image  │
              └───────┬────────┘
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
   ┌───────────────┐    ┌────────────────────┐
   │  SAST          │    │  SCA / Container    │
   │  SonarCloud    │    │  Trivy              │
   │  Quality Gate  │    │  CRITICAL + HIGH    │
   └───────┬───────┘    └────────┬───────────┘
           │                     │
           └──────────┬──────────┘
                      ▼
              ┌────────────────┐
              │     DAST       │
              │   OWASP ZAP    │
              │  Full Scan     │
              │  fail on HIGH  │
              └────────────────┘
```

**Flujo:**
1. **Build** — Construye la imagen Docker y la comparte como artefacto.
2. **SAST + SCA** — Se ejecutan **en paralelo** después del build.
3. **DAST** — Se ejecuta al final; levanta la aplicación y la escanea.

> Nota: ZAP usa `if: always()`, por lo que se ejecuta incluso si SAST o Trivy fallan, para obtener cobertura completa.

---

## 4. Aplicación Objetivo — Vulnerabilidades Plantadas

La aplicación (`app/main.py`) es una API FastAPI con las siguientes vulnerabilidades intencionales:

| # | Ruta | Vulnerabilidad | CWE | Detectada por |
|---|------|----------------|-----|---------------|
| 1 | (constantes) | Credenciales hardcodeadas | CWE-798 | SAST (SonarCloud) |
| 2 | `GET /search?q=` | XSS Reflejado | CWE-79 | DAST (ZAP) |
| 3 | `POST /login` | Inyección SQL | CWE-89 | SAST + DAST |
| 4 | `GET /admin` | Control de acceso roto | CWE-284 | **Ninguna herramienta** |
| 5 | `GET /ping?host=` | Inyección de comandos OS | CWE-78 | SAST + DAST |
| 6 | `GET /file?name=` | Path Traversal | CWE-22 | SAST + DAST |
| 7 | `POST /hash` | Criptografía insegura (MD5) | CWE-327 | **Ninguna herramienta** |

### Dependencias Vulnerables (SCA)

| Paquete | Versión | CVE | Severidad |
|---------|---------|-----|-----------|
| pyyaml | 5.3.1 | CVE-2020-14343 | CRITICAL |
| Pillow | 9.0.0 | CVE-2022-22817 | CRITICAL |
| Pillow | 9.0.0 | CVE-2023-50447 | CRITICAL |

### Imagen Base Vulnerable

- `python:3.8-slim` — End-of-Life desde octubre 2024, contiene múltiples CVEs en paquetes del sistema operativo.

---

## 5. Configuración del Pipeline

### 5.1 Requisitos Previos

1. **Cuenta de GitHub** con un repositorio.
2. **Cuenta de SonarCloud** (gratuita para repos públicos):
   - Crear un proyecto y obtener un `SONAR_TOKEN`.
   - Actualizar `sonar-project.properties` con tu `sonar.projectKey` y `sonar.organization`.
3. **GitHub Secret:** Agregar `SONAR_TOKEN` en Settings → Secrets → Actions.
4. **Docker** (ya incluido en los runners de GitHub Actions).

### 5.2 Estructura del Proyecto

```
Lab DevSecOps Pipeline/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          ← Tubería CI/CD completa
├── app/
│   ├── Dockerfile             ← Imagen base vulnerable (python:3.8-slim)
│   ├── main.py                ← Aplicación FastAPI vulnerable
│   ├── requirements.txt       ← Dependencias con CVEs conocidos
│   └── files/
│       └── readme.txt         ← Archivo de prueba para /file endpoint
├── sonar-project.properties   ← Configuración de SonarCloud
├── .gitignore
└── README.md                  ← Este documento
```

### 5.3 Ejecución

```bash
# 1. Crear repositorio en GitHub y subir el código
git remote add origin https://github.com/TU_USUARIO/DevSecOps-Pipeline.git
git branch -M main
git push -u origin main

# 2. El pipeline se ejecuta automáticamente al hacer push a main
# 3. También se puede ejecutar manualmente desde Actions → CI/CD Pipeline → Run workflow
```

---

## 6. Resultados Reales del Pipeline (Run #45079044967)

**Pipeline ejecutado:** 22 de noviembre de 2026  
**Repositorio:** [KEVIN18xD/DevSecOps-Pipeline](https://github.com/KEVIN18xD/DevSecOps-Pipeline)  
**Resultado global:** Las 3 puertas de seguridad **FALLARON** correctamente.

| Etapa | Estado | Tiempo | Exit Code |
|-------|--------|--------|-----------|
| Build | ✅ Exitoso | 26s | 0 |
| SonarCloud (SAST) | ❌ FAILED | 7s | 1 |
| Trivy (SCA) | ❌ FAILED | 33s | 1 |
| OWASP ZAP (DAST) | ❌ FAILED | 3m 9s | 2 |

### 6.1 SonarCloud (SAST) — 17 Vulnerabilidades Detectadas

**Calificación de Seguridad: E (la peor)**

#### Issues BLOCKER (8 issues — bloquean el Quality Gate):

| Archivo | Línea | Regla | Descripción |
|---------|-------|-------|-------------|
| main.py | 22 | S6418 | **Hardcoded API_KEY** (`sk-prod-...`) detectado |
| main.py | 63 | S5131 | **Reflected XSS** via HTTP request en `search()` |
| main.py | 95 | S5131 | **Reflected XSS** via HTML form en `login()` |
| main.py | 121 | S2076 | **Command Injection** via HTTP request en `ping()` |
| main.py | 128 | S5131 | **Reflected XSS** via HTTP request en `ping()` |
| main.py | 141 | S2083 | **Path Traversal** via HTTP request en `read_file()` |
| main.py | 145 | S5131 | **Reflected XSS** via HTTP request en `read_file()` |
| main.py | 169 | S5131 | **Reflected XSS** via HTML form en `hash_text()` |

#### Issues CRITICAL (2 issues):

| Archivo | Línea | Regla | Descripción |
|---------|-------|-------|-------------|
| Dockerfile | 13 | S6470 | `COPY .` puede incluir datos sensibles |
| main.py | 168 | S4790 | Uso de **hashing inseguro** (MD5) |

#### Issues MAJOR (6 issues):

| Archivo | Línea | Regla | Descripción |
|---------|-------|-------|-------------|
| ci-cd.yml | 9 | S8233 | Permisos write a nivel de workflow (debería ser por job) |
| ci-cd.yml | 47 | S7637 | Dependencia sin SHA hash completo (supply chain risk) |
| ci-cd.yml | 69 | S7637 | Dependencia sin SHA hash completo |
| ci-cd.yml | 118 | S7637 | Dependencia sin SHA hash completo |
| Dockerfile | 10 | S8541 | pip install sin `--only-binary :all:` |
| Dockerfile | 10 | S8544 | Dependencias sin lock de versiones resueltas |

#### Issue MINOR (1 issue):

| Archivo | Línea | Regla | Descripción |
|---------|-------|-------|-------------|
| Dockerfile | 4 | S6471 | Imagen ejecuta como **root** por defecto |

**No detectados por SonarCloud:**
- `SECRET_KEY` y `DB_PASS` (no coinciden con patrones de API keys conocidos)
- Control de acceso roto en `/admin` (CWE-284)

**Dato notable:** SonarCloud SÍ detectó el uso de MD5 (S4790, línea 168) como CRITICAL — una mejora respecto a versiones anteriores.

### 6.2 Trivy (SCA + Container Scan)

**Security Gate: FAILED** — `exit-code: 1` activado por CVEs CRITICAL/HIGH.

Los resultados se suben en formato SARIF a la pestaña **Security** del repositorio en GitHub. Las vulnerabilidades incluyen:

**Dependencias Python:**
| Paquete | CVE | Severidad |
|---------|-----|-----------|
| Pillow 9.0.0 | CVE-2022-22817 | CRITICAL |
| Pillow 9.0.0 | CVE-2023-50447 | CRITICAL |
| Pillow 9.0.0 | CVE-2023-44271 | HIGH |
| pyyaml 5.3.1 | CVE-2020-14343 | CRITICAL |
| setuptools | CVE-2022-40897 | HIGH |

**Paquetes del sistema operativo (python:3.8-slim):**
- Múltiples CVEs en libsqlite3, gpgv, libexpat1, libpam, ncurses, perl-base, etc.
- **SonarCloud también detectó 63 dependency risks (calificación D).**

### 6.3 OWASP ZAP (DAST) — 13 Alertas

**Security Gate: FAILED** — ZAP reportó alertas de seguridad.  
**Resultado:** FAIL-NEW: 0 | WARN-NEW: 13 | PASS: 130

#### Alertas de vulnerabilidades activas:

| Alerta | Instancias | Riesgo |
|--------|------------|--------|
| **Cross Site Scripting (Reflected)** | 4 | HIGH |
| **Cross Site Scripting (DOM Based)** | 5 | HIGH |
| **SQL Injection** | 2 | HIGH |
| **Remote OS Command Injection** | 1 | HIGH |
| **Path Traversal** | 1 | HIGH |
| **Source Code Disclosure - File Inclusion** | 2 | MEDIUM |

#### Alertas de configuración:

| Alerta | Instancias | Riesgo |
|--------|------------|--------|
| Missing Anti-clickjacking Header | 10 | MEDIUM |
| X-Content-Type-Options Header Missing | 10 | MEDIUM |
| Content Security Policy (CSP) Header Not Set | 10 | MEDIUM |
| Permissions Policy Header Not Set | 10 | LOW |
| HTTP Only Site | 1 | LOW |
| Absence of Anti-CSRF Tokens | 2 | MEDIUM |
| Cross-Origin-Resource-Policy Header Missing | 12 | LOW |

**Reporte completo:** Disponible como artefacto `zap-report` en GitHub Actions.

---

## 7. Análisis de Brechas (Gap Analysis)

### Matriz de Detección

| Vulnerabilidad | CWE | SonarCloud | Trivy | ZAP |
|----------------|-----|------------|-------|-----|
| Credenciales hardcodeadas | 798 | ✅ (parcial) | ❌ | ❌ |
| XSS Reflejado | 79 | ✅ | ❌ | ✅ |
| Inyección SQL | 89 | ✅ | ❌ | ✅ |
| Control de acceso roto | 284 | ❌ | ❌ | ❌ |
| Inyección de comandos | 78 | ✅ | ❌ | ✅ |
| Path Traversal | 22 | ✅ | ❌ | ✅ |
| Criptografía insegura (MD5) | 327 | ✅ (CRITICAL) | ❌ | ❌ |
| Dependencias vulnerables | — | ❌ | ✅ | ❌ |
| Imagen base EOL | — | ❌ | ✅ | ❌ |

### Brechas Principales

1. **Detección incompleta de secretos:** SonarCloud detectó `API_KEY` pero no `SECRET_KEY` ni `DB_PASS`.
   - **Recomendación:** Agregar Gitleaks o TruffleHog al pipeline.

2. **Criptografía detectada parcialmente:** SonarCloud detectó MD5 como CRITICAL (S4790), pero solo ZAP o herramientas adicionales pueden verificar su impacto en contexto.
   - **Recomendación:** Agregar Semgrep o Bandit con reglas específicas de crypto para cobertura completa.

3. **Control de acceso no detectado:** ZAP no puede detectar autorización rota sin un contexto de autenticación.
   - **Recomendación:** Configurar ZAP con escaneo autenticado y scripts de autorización.

4. **Sin solapamiento total:** SAST y DAST confirman mutuamente la explotabilidad de XSS, SQLi, command injection y path traversal — esto demuestra el valor de combinar ambas técnicas.

---

## 8. Plan de Remediación

| Vulnerabilidad | Remediación |
|----------------|-------------|
| SQL Injection | Consultas parametrizadas: `cursor.execute("SELECT ... WHERE username=?", (username,))` |
| XSS Reflejado | Escapar HTML: usar `html.escape()` o plantillas con auto-escape (Jinja2) |
| Command Injection | No usar `shell=True`; usar `subprocess.run(["ping", "-c", "1", host])` con allowlist |
| Path Traversal | Resolver y validar rutas: `os.path.realpath()` + verificar prefijo contra directorio base |
| Credenciales hardcodeadas | Usar `os.getenv()` + GitHub Secrets |
| MD5 inseguro | Usar `bcrypt` o `argon2` para hashing de contraseñas |
| Imagen base EOL | Actualizar a `python:3.12-slim` |
| pyyaml vulnerable | Actualizar a `pyyaml>=6.0.1` |
| Pillow vulnerable | Actualizar a `Pillow>=10.3.0` |

---

## 9. Herramientas Adicionales Recomendadas

| Herramienta | Propósito | Fase |
|-------------|-----------|------|
| **Gitleaks** | Detección de secretos en el historial de git | Pre-commit / CI |
| **Bandit** | SAST específico para Python (crypto, injection, etc.) | CI |
| **Semgrep** | SAST con reglas personalizables | CI |
| **Snyk** | SCA con fix automático y monitoreo continuo | CI |
| **OWASP Dependency-Check** | SCA alternativo basado en NVD | CI |

---

## 10. Conclusiones

1. **Ninguna herramienta individual cubre todas las vulnerabilidades.** La combinación SAST + SCA + DAST es necesaria para una cobertura razonable.
2. **Las puertas de seguridad automatizadas** (security gates) previenen que código vulnerable llegue a producción sin intervención manual.
3. **SAST y DAST se complementan:** SAST encuentra vulnerabilidades en código que DAST no puede alcanzar (credenciales), y DAST confirma la explotabilidad real de las que SAST detecta como patrones.
4. **Existen brechas:** control de acceso roto y criptografía débil requieren herramientas o configuraciones adicionales.
5. **DevSecOps no ralentiza el desarrollo:** el pipeline completo se ejecuta en minutos y proporciona retroalimentación inmediata a los desarrolladores.

---

## Apéndice: Cómo Configurar SonarCloud

1. Ir a [sonarcloud.io](https://sonarcloud.io) e iniciar sesión con GitHub.
2. Importar el repositorio.
3. Copiar el **Project Key** y la **Organization** al archivo `sonar-project.properties`.
4. Generar un token en My Account → Security → Generate Token.
5. Agregar el token como secreto `SONAR_TOKEN` en GitHub (Settings → Secrets and variables → Actions).
