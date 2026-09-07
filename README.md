# MedExtract AI — versão local em Django

Esta versão representa o backend original do projeto: Django, uma view para receber a entrada, um serviço Python para organizar os campos e SQLite para persistência local. A página HTML em `templates/extractor/dashboard.html` é apenas uma tela de validação do fluxo.

## Executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. O fluxo de validação usa POST para a view Django e registra os resultados na tabela `extractor_prescription` do SQLite.

O arquivo `templates/extractor/dashboard.html` é a tela HTML simples usada para validar as entradas. A regra de extração está em `extractor/services.py`, separada da view.

Esta versão não usa OpenAI, Azure ou outra API externa. Imagens usam Tesseract OCR local e áudios usam Whisper local via `faster-whisper`; o primeiro download do modelo pode ser grande. Ela é uma base local de validação e não substitui a conferência profissional de uma prescrição.
