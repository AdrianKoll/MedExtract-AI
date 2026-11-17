# Versão de teste e deploy

## O que foi revisado

Esta versão mantém o processamento local de OCR e transcrição e inclui comentários em português nos pontos principais do código. Também foram aplicados ajustes de robustez:

- imagens agora são verificadas pelo Pillow antes de serem encaminhadas ao Tesseract;
- o formulário preserva o tipo de entrada escolhido quando ocorre um erro;
- o Gunicorn aceita a porta informada pela variável `PORT`;
- a API e os fluxos de autenticação ficaram documentados com comentários de intenção;
- os checks Django, os testes automatizados e a verificação de migrações foram executados com sucesso.

## Teste local sem Docker

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python manage.py migrate
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

## Teste com Docker

```bash
cp .env.example .env
# Troque DJANGO_SECRET_KEY e POSTGRES_PASSWORD antes de usar um ambiente público.
docker compose up --build
```

O endpoint de saúde é `GET /healthz/`.

## Plataformas Pages

Este repositório é um backend Django com Gunicorn, banco PostgreSQL, Tesseract e FFmpeg. Plataformas do tipo **Pages** que aceitam somente arquivos estáticos não executam o Django, não rodam migrações e não fornecem o processo Gunicorn. Portanto, esta aplicação não deve ser publicada diretamente como um site estático em uma plataforma Pages.

Para testar a aplicação completa, use um serviço que aceite container Docker ou runtime Python e configure:

- comando de inicialização equivalente ao `Dockerfile`;
- `PORT` fornecida pelo provedor;
- `DJANGO_SECRET_KEY` longa e aleatória;
- `DJANGO_DEBUG=false`;
- `DJANGO_ALLOWED_HOSTS` com o domínio do serviço;
- `DATABASE_URL` apontando para PostgreSQL persistente;
- armazenamento persistente para `/app/media` e `/app/backups` quando esses recursos forem necessários.

Se o objetivo for usar uma plataforma Pages, é necessário separar o frontend estático do backend Django e configurar um endpoint externo para a API. Não há uma conversão automática segura deste repositório para somente frontend, porque OCR, transcrição, autenticação, banco e uploads dependem do servidor.

## Validações executadas

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```
