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

## 6. Resultados Esperados por Herramienta

### 6.1 SonarCloud (SAST)

**Quality Gate: FAILED** — 6 issues de tipo Blocker:

| Hallazgo | Línea | Regla |
|----------|-------|-------|
| Hardcoded API_KEY (`sk-prod-...`) | ~24 | S6418 |
| XSS Reflejado en `/search` | ~72 | S5131 |
| XSS en `/hash` (echo de input) | ~165 | S5131 |
| SQL Injection en `/login` | ~101 | S3649 |
| Command Injection en `/ping` | ~136 | S4721 |
| Path Traversal en `/file` | ~152 | S4797 |

**No detectados por SonarCloud:**
- `SECRET_KEY` y `DB_PASS` (no coinciden con patrones de API keys)
- Uso de MD5 (CWE-327)
- Control de acceso roto (CWE-284)

### 6.2 Trivy (SCA + Container Scan)

**Security Gate: FAILED** — Múltiples CVEs CRITICAL y HIGH.

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

### 6.3 OWASP ZAP (DAST)

**Security Gate: FAILED** — 5 alertas HIGH:

| Alerta | Riesgo | URL |
|--------|--------|-----|
| Cross-Site Scripting (Reflected) | HIGH | `/search?q=` |
| DOM-Based XSS | HIGH | `/search?q=` |
| SQL Injection | HIGH | `/login` |
| Remote OS Command Injection | HIGH | `/ping?host=` |
| Path Traversal | HIGH | `/file?name=` |

Además: 5 Medium, 5 Low, 3 Informational.

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
| Criptografía insegura (MD5) | 327 | ❌ | ❌ | ❌ |
| Dependencias vulnerables | — | ❌ | ✅ | ❌ |
| Imagen base EOL | — | ❌ | ✅ | ❌ |

### Brechas Principales

1. **Detección incompleta de secretos:** SonarCloud detectó `API_KEY` pero no `SECRET_KEY` ni `DB_PASS`.
   - **Recomendación:** Agregar Gitleaks o TruffleHog al pipeline.

2. **Sin reglas de criptografía:** Ninguna herramienta detectó el uso de MD5.
   - **Recomendación:** Agregar Semgrep o Bandit con reglas de crypto.

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
