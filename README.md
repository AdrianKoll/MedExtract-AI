# MedExtract

Aplicação Django para receber texto, imagens e áudio relacionados a prescrições e organizar os campos identificados em uma ficha estruturada. O projeto usa SQLite no desenvolvimento local e PostgreSQL no ambiente Docker, com uma separação simples entre entrada HTTP, OCR, transcrição e regra de extração.

> O resultado é apenas uma pré-organização técnica do conteúdo recebido. Não substitui a conferência de um profissional de saúde e não deve ser usado para decidir tratamento ou alterar uma prescrição.

## Funcionalidades

- entrada manual de texto;
- leitura de imagens por OCR local;
- transcrição local de arquivos de áudio;
- identificação de medicamento, concentração, quantidade, posologia e duração;
- persistência do histórico em SQLite local ou PostgreSQL no Docker;
- formulário protegido por CSRF;
- validação de extensão e tamanho de uploads;
- testes automatizados e pipeline de integração contínua.

## Provedores externos opcionais

O projeto possui adaptadores externos configuráveis, sem acoplar a view a um fornecedor específico:

- **OCR de imagem:** OCR.space via `OCR_SPACE_API_KEY`. A documentação do serviço informa uma chave gratuita, limite de arquivo de 1 MB e limite de requisições por IP no plano gratuito.
- **Transcrição de áudio:** Hugging Face Inference via `HF_TOKEN`, usando um endpoint de speech-to-text configurável em `HF_AUDIO_API_URL`.

Quando a variável do provedor não está configurada, o sistema usa o processamento local já existente. Se o provedor falhar, também há fallback local. As chaves são lidas somente do ambiente e não devem ser colocadas no código ou no README.

## Tecnologias

- Python 3.11+
- Django 5+
- SQLite para desenvolvimento
- Pillow e Tesseract para OCR local
- faster-whisper para transcrição local opcional
- GitHub Actions para checks automatizados

O OCR e a transcrição dependem de ferramentas/modelos locais. Não há chave de API ou serviço pago obrigatório no fluxo padrão. A instalação do mecanismo de transcrição pode exigir download de um modelo e mais memória do que a execução somente com texto.

Para demonstrar as integrações externas, preencha o `.env`:

```env
OCR_SPACE_API_KEY=sua-chave-gratuita
HF_TOKEN=seu-token-com-permissao-de-inferencia
```

O OCR.space documenta o endpoint `https://api.ocr.space/parse/image`. A documentação do Hugging Face descreve a autenticação por token e o uso de provedores de inferência. Verifique os limites e termos atuais de cada serviço antes de enviar dados reais. Prescrições contêm dados sensíveis; use somente imagens e áudios de teste em serviços externos, com autorização adequada.

## Estrutura

```text
MedExtract/
├── extractor/
│   ├── api.py
│   ├── migrations/
│   ├── models.py
│   ├── ocr.py
│   ├── services.py
│   ├── transcription.py
│   ├── validators.py
│   ├── views.py
│   └── tests.py
├── medextract/settings.py
├── templates/extractor/dashboard.html
├── static/extractor/app.css
├── .env.example
├── manage.py
└── pyproject.toml
```

## Segurança e API para integrações

O front-end público funciona como uma vitrine: visitantes podem testar uma extração, mas o resultado não é salvo sem autenticação. Usuários cadastrados podem salvar e apagar somente os próprios registros. O histórico é filtrado pelo proprietário no servidor, e não apenas pela interface.

A API versionada exige um token Bearer. Para obter um token em uma conta de demonstração, envie as credenciais por HTTPS:

```bash
curl -X POST https://seu-dominio.example/api/v1/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"seu-usuario","password":"sua-senha"}'
```

Use o token retornado para criar e consultar prescrições de texto:

```bash
curl -X POST https://seu-dominio.example/api/v1/prescriptions/ \
  -H "Authorization: Bearer medx_seu_token" \
  -H 'Content-Type: application/json' \
  -d '{"source_text":"Amoxicilina 500 mg, tomar por 7 dias."}'

curl https://seu-dominio.example/api/v1/prescriptions/ \
  -H "Authorization: Bearer medx_seu_token"
```

Cada token pertence a um usuário e é armazenado somente como hash no banco. Cada consulta, leitura e exclusão é limitada ao proprietário autenticado. Tokens devem ser tratados como senhas, usados exclusivamente sobre HTTPS e revogados por rotação ou exclusão da credencial quando houver suspeita de vazamento. A API de demonstração aceita texto; o front-end continua oferecendo os fluxos de upload para OCR e áudio.

## Execução recomendada com Docker

Docker encapsula Python, Django, Tesseract em português, FFmpeg, PostgreSQL e as dependências do projeto. Não é necessário criar `venv` nem instalar dependências Python no sistema host. O `pyproject.toml` é usado pelo Docker como manifesto de dependências e metadados do projeto.

```bash
cp .env.example .env
# edite .env e defina DJANGO_SECRET_KEY e POSTGRES_PASSWORD
docker compose up --build
```

Acesse <http://127.0.0.1:8000/>. O container web espera o PostgreSQL ficar saudável, executa as migrações e coleta os arquivos estáticos automaticamente. O PostgreSQL, a mídia e os estáticos ficam em volumes Docker persistentes.

Para parar e acompanhar os logs:

```bash
docker compose down
docker compose logs -f web
```

No Android, o ZIP pode ser extraído e enviado ao GitHub pelo aplicativo de Git. Para executar os containers, será necessário um computador ou servidor com Docker; o celular pode editar e versionar o projeto, mas não substitui um host Docker completo.

## Execução local — Windows PowerShell sem Docker

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>.

## Execução local — Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Para OCR de imagens, o Tesseract precisa estar instalado no sistema e disponível no `PATH`. O processamento de áudio usa o modelo configurado em `extractor/transcription.py`; a primeira execução pode baixar arquivos grandes.

## Configuração e publicação

Nunca envie `.env`, `db.sqlite3` ou arquivos em `media/` para o GitHub. Em produção, defina `DJANGO_ENV=production`, use uma `DJANGO_SECRET_KEY` longa e aleatória, mantenha `DJANGO_DEBUG=false`, configure `DJANGO_ALLOWED_HOSTS` com os domínios autorizados e use uma senha forte no PostgreSQL. Se a aplicação estiver atrás de HTTPS, ative `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE` e `DJANGO_CSRF_COOKIE_SECURE`; depois de confirmar que todo o domínio usa HTTPS, configure também `DJANGO_SECURE_HSTS_SECONDS` com uma política adequada. O Compose cria um serviço PostgreSQL separado e conecta o Django por `DATABASE_URL`; fora do Docker, o projeto continua usando SQLite quando `DATABASE_URL` não é definida.

Este repositório está pronto para publicação como código de portfólio e demonstração técnica. Para uso real com prescrições, ainda devem ser definidos política de retenção, auditoria, rate limiting, gestão operacional de tokens e requisitos legais aplicáveis. Prescrições são dados sensíveis; não envie dados reais a provedores externos sem consentimento, base legal e uma política de retenção definida. O sistema também não substitui revisão de um profissional de saúde.

## Testes

```bash
python manage.py check
python manage.py test
```

O workflow em `.github/workflows/ci.yml` executa configuração, migrações e testes em pushes e pull requests na branch `main`, com permissão de conteúdo somente leitura.

## Status

Projeto de portfólio em evolução, com foco em processamento local, organização de dados e validação de um fluxo Django. Antes de qualquer uso real, é necessário revisar privacidade, retenção, controle de acesso, criptografia, observabilidade e validação clínica.

## Segurança implementada

A versão atual inclui HTTPS configurável, cookies e headers seguros, cadastro e login com senha forte e proteção contra brute force, isolamento por usuário, rate limit básico, limites de upload, tokens API múltiplos com expiração e revogação, integrações independentes por usuário, auditoria, retenção formal, limpeza automática de dados de demonstração, backups, healthcheck e alertas opcionais. Consulte [`SECURITY.md`](SECURITY.md) para a política operacional, cron, revisão jurídica e plano de testes de segurança.

Para operação recorrente, execute `cleanup_data`, `backup_database` e `monitor_health` por um scheduler do ambiente. O endpoint `/healthz/` pode ser usado por um monitor externo.
