from __future__ import annotations

import requests


class ProviderError(RuntimeError):
    """Erro controlado de um provedor externo de processamento."""


def post_file(url: str, *, headers=None, files=None, data=None, timeout=(10, 60)) -> requests.Response:
    try:
        response = requests.post(
            url,
            headers=headers or {},
            files=files,
            data=data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        raise ProviderError('O serviço externo não respondeu corretamente.') from exc
