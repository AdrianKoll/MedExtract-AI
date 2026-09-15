# Segurança e operação do MedExtract

## Controles implementados

O projeto força configurações de HTTPS por ambiente (`DJANGO_SECURE_SSL_REDIRECT`, cookies `Secure`, HSTS e `SECURE_PROXY_SSL_HEADER`) e inclui headers seguros, `HttpOnly`, `SameSite`, CSRF e `X-Frame-Options: DENY`. Em produção, defina `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, redirecionamento HTTPS e HSTS somente depois de confirmar que todo o domínio está servido por HTTPS.

O cadastro usa os validadores de senha do Django, com comprimento mínimo de 12 caracteres. O login web e a emissão de tokens API têm proteção contra brute force por IP e usuário. O rate limit básico é aplicado por IP e caminho para a API. Para ambientes com múltiplos workers, substitua o cache local por Redis ou outro backend compartilhado.

Cada token API é armazenado somente como hash, tem nome, data de expiração, último uso e revogação. É possível emitir múltiplos tokens por usuário e revogar o token corrente em `POST /api/v1/token/revoke/`. Tokens expirados ou revogados não autenticam. O endpoint de integração suporta múltiplas integrações independentes por usuário, sem expor o segredo na resposta; os segredos são protegidos com assinatura do Django e devem ser mantidos no ambiente de produção com uma `DJANGO_SECRET_KEY` protegida.

Prescrições persistidas são sempre filtradas por `owner` no servidor. Demos não autenticadas não recebem proprietário e são removidas automaticamente pelo comando `cleanup_data`. Uploads possuem limite de 10 MB, extensões permitidas, MIME permitido e limites globais de request. O texto da API possui limite de 20.000 caracteres.

Todas as operações relevantes geram `AuditEvent`, com usuário quando disponível, IP, ação, resultado e metadados mínimos. Não registre texto bruto da prescrição, tokens ou segredos nos logs. O comando de retenção remove demos antigas, prescrições além da retenção formal, eventos de auditoria antigos e tokens expirados.

## Política de retenção padrão

| Dado | Retenção padrão | Configuração |
| --- | ---: | --- |
| Demonstrações sem usuário | 24 horas | `DEMO_RETENTION_HOURS` |
| Prescrições de usuários | 730 dias | `PRESCRIPTION_RETENTION_DAYS` |
| Auditoria | 365 dias | `AUDIT_RETENTION_DAYS` |
| Tokens expirados | Limpeza no próximo ciclo | `cleanup_data` |
| Backups | 14 arquivos | `BACKUP_KEEP` |

A organização responsável deve validar esses prazos com o encarregado de proteção de dados, necessidade operacional, contratos com processadores e legislação aplicável antes de usar dados reais.

## Operação

Execute periodicamente:

```bash
python manage.py cleanup_data
python manage.py backup_database
python manage.py monitor_health
```

`/healthz/` retorna `200` quando o banco responde e `503` caso contrário. `monitor_health` verifica o banco e o diretório de mídia e envia um JSON para `ALERT_WEBHOOK_URL` quando configurado. O backup usa `pg_dump` para PostgreSQL e cópia do arquivo para SQLite; os arquivos devem ser enviados para armazenamento externo criptografado, com controle de acesso e teste de restauração. O Compose cria o volume `backup_data`, mas volume local não é uma estratégia suficiente contra perda do host.

Para automatizar, use um scheduler confiável do ambiente de hospedagem. Exemplo de cron no host:

```cron
0 2 * * * cd /srv/medextract && docker compose exec -T web python manage.py backup_database
15 2 * * * cd /srv/medextract && docker compose exec -T web python manage.py cleanup_data
*/5 * * * * cd /srv/medextract && docker compose exec -T web python manage.py monitor_health
```

## Revisão jurídica e de privacidade necessária

Antes de produção, faça revisão por profissional qualificado sobre LGPD, base legal, transparência, direitos dos titulares, contratos com provedores de OCR/transcrição, transferência internacional, subcontratantes, incidente de segurança, controlador/operador, prazo de retenção e descarte seguro. O produto é uma ferramenta de pré-organização e não substitui validação de profissional de saúde; essa mensagem deve permanecer visível no produto e nos termos de uso.

Não envie dados reais a OCR, transcrição ou outros provedores sem autorização, base legal e avaliação contratual. Prefira processamento local e mantenha cada integração desativada por padrão até sua configuração explícita.

## Testes de segurança recomendados

A suíte existente valida autenticação Bearer, isolamento entre usuários, exclusão limitada ao proprietário, upload inválido, OCR/transcrição e fluxo de demonstração. Antes de publicar, acrescente ao pipeline: `python manage.py check --deploy`, varredura de dependências (`pip-audit`), SAST (`bandit`), testes de CSRF, brute force, expiração/revogação de tokens, rate limit em múltiplos workers, IDOR em todos os endpoints, validação MIME por conteúdo, upload poliglota, restauração de backup e teste de alertas. Faça também pentest independente e revisão jurídica; estes não podem ser substituídos por testes automatizados.
