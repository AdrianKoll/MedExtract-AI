# MedExtract

Aplicação web desenvolvida com Django para organizar informações de prescrições a partir de texto, imagens e arquivos de áudio. O sistema transforma a entrada em uma ficha estruturada com medicamento, concentração, quantidade, posologia, duração e observações.

> O resultado é uma organização preliminar das informações. A conferência por um profissional de saúde continua sendo obrigatória. O sistema não deve ser usado para decidir tratamentos ou alterar prescrições.

## Visão geral

O processamento de documentos é local. Imagens são tratadas com Pillow e Tesseract dentro do ambiente da aplicação, sem envio automático para serviços externos. A execução recomendada utiliza Docker para manter versões e dependências reproduzíveis.

## Funcionalidades

- cadastro, login e logout;
- entrada manual de texto;
- leitura local de imagens por Tesseract OCR;
- transcrição local opcional de arquivos de áudio;
- extração estruturada dos principais campos da prescrição;
- histórico individual por usuário;
- API versionada com autenticação Bearer;
- tokens com expiração e revogação;
- validação de uploads e limites de tamanho;
- proteção contra excesso de tentativas de login;
- auditoria de operações relevantes;
- limpeza de dados conforme política de retenção;
- backups e endpoint de verificação de disponibilidade;
- testes automatizados e integração contínua.

## Tecnologias

- Python 3.11+
- Django 5+
- PostgreSQL no ambiente Docker
- SQLite para desenvolvimento local sem Docker
- Pillow e Tesseract OCR com idioma português
- faster-whisper para transcrição local opcional
- Gunicorn
- Docker e Docker Compose
- GitHub Actions

## Execução recomendada com Docker

O contêiner instala Python, Django, Tesseract, o idioma português e FFmpeg. Para iniciar:

```bash
git clone https://github.com/AdrianKoll/MedExtract-AI.git
cd MedExtract-AI
cp .env.example .env
```

Edite `.env` e defina uma chave longa para `DJANGO_SECRET_KEY` e uma senha forte para `POSTGRES_PASSWORD`. Depois execute:

```bash
docker compose up --build
```

A aplicação ficará disponível em <http://127.0.0.1:8000/>.

Para consultar os logs ou encerrar o ambiente:

```bash
docker compose logs -f web
docker compose down
```

As migrações são executadas pelo entrypoint do contêiner antes da inicialização do servidor.

## Execução sem Docker

O SQLite pode ser usado para desenvolvimento, estudo e testes rápidos. Esse caminho ainda exige a instalação das dependências Python, mas não requer PostgreSQL ou Docker.

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Abra <http://127.0.0.1:8000/> no navegador.

Para usar OCR fora do Docker, o Tesseract precisa estar instalado no sistema e disponível no `PATH`, incluindo o pacote de idioma português. A transcrição local é opcional e exige o mecanismo configurado em `extractor/transcription.py`.

## API

A API exige um token Bearer. Solicite um token com as credenciais de um usuário cadastrado:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"seu-usuario","password":"sua-senha"}'
```

Crie uma extração de texto:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prescriptions/ \
  -H 'Authorization: Bearer medx_seu_token' \
  -H 'Content-Type: application/json' \
  -d '{"source_text":"Amoxicilina 500 mg, tomar uma cápsula por 7 dias."}'
```

Consulte o histórico:

```bash
curl http://127.0.0.1:8000/api/v1/prescriptions/ \
  -H 'Authorization: Bearer medx_seu_token'
```

Revogue o token atual:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/token/revoke/ \
  -H 'Authorization: Bearer medx_seu_token'
```

O endpoint de disponibilidade é `GET /healthz/`.

## Segurança e operação

A aplicação possui HTTPS configurável, cookies seguros, proteção CSRF, headers de segurança, isolamento por proprietário, rate limit, proteção contra tentativas repetidas de login, expiração e revogação de tokens, validação de uploads e auditoria.

Em produção, configure `DJANGO_ENV=production`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, hosts autorizados, HTTPS e PostgreSQL. Nunca versionar `.env`, `db.sqlite3`, arquivos de mídia ou backups.

Os comandos de manutenção são:

```bash
python manage.py cleanup_data
python manage.py backup_database
python manage.py monitor_health
```

## Testes

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

O workflow de integração contínua executa as verificações e os testes em alterações enviadas à branch `main`.

## Estrutura

```text
extractor/
├── api.py
├── forms.py
├── health.py
├── management/commands/
├── migrations/
├── models.py
├── ocr.py
├── security.py
├── services.py
├── tests.py
├── tests_security.py
├── transcription.py
├── urls.py
├── validators.py
└── views.py
medextract/
├── settings.py
├── urls.py
└── wsgi.py
```

## Uso

Este projeto é apresentado para fins de estudo e demonstração técnica. Antes de processar dados reais, faça a revisão de privacidade, segurança, requisitos regulatórios e responsabilidades envolvidas.
