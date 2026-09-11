# MedExtract

Aplicação Django para receber texto, imagens e áudio relacionados a prescrições e organizar os campos identificados em uma ficha estruturada. O projeto mantém o processamento local, SQLite para desenvolvimento e uma separação simples entre entrada HTTP, OCR, transcrição e regra de extração.

> O resultado é apenas uma pré-organização técnica do conteúdo recebido. Não substitui a conferência de um profissional de saúde e não deve ser usado para decidir tratamento ou alterar uma prescrição.

## Funcionalidades

- entrada manual de texto;
- leitura de imagens por OCR local;
- transcrição local de arquivos de áudio;
- identificação de medicamento, concentração, quantidade, posologia e duração;
- persistência do histórico em SQLite;
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
└── requirements.txt
```

## Execução local — Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>.

## Execução local — Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Para OCR de imagens, o Tesseract precisa estar instalado no sistema e disponível no `PATH`. O processamento de áudio usa o modelo configurado em `extractor/transcription.py`; a primeira execução pode baixar arquivos grandes.

## Configuração

Nunca envie `.env`, `db.sqlite3` ou arquivos em `media/` para o GitHub. Em produção, defina `DJANGO_ENV=production`, `DJANGO_SECRET_KEY` forte, `DJANGO_DEBUG=false` e `DJANGO_ALLOWED_HOSTS` com os domínios autorizados. O projeto recusa iniciar em produção sem uma chave configurada.

## Testes

```bash
python manage.py check
python manage.py test
```

O workflow em `.github/workflows/ci.yml` executa configuração, migrações e testes em pushes e pull requests na branch `main`, com permissão de conteúdo somente leitura.

## Status

Projeto de portfólio em evolução, com foco em processamento local, organização de dados e validação de um fluxo Django. Antes de qualquer uso real, é necessário revisar privacidade, retenção, controle de acesso, criptografia, observabilidade e validação clínica.
