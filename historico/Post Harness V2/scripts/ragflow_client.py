"""Small retrieval-only RAGFlow HTTP adapter; no generation, no third-party SDK."""
import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener


class RetrievalError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the RAGFlow credential to another endpoint.
        return None


class RAGFlowClient:
    def __init__(self, base_url, api_key, dataset_ids, *, timeout=30, page_size=5,
                 similarity_threshold=0.2, allow_insecure_http=False):
        parts = urlsplit(base_url)
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
            raise RetrievalError('La URL de RAGFlow debe ser HTTP(S), sin credenciales, query ni fragmento.')
        if parts.scheme == 'http' and parts.hostname not in ('127.0.0.1', 'localhost', '::1') and not allow_insecure_http:
            raise RetrievalError('Usar HTTPS para RAGFlow remoto o habilitar explícitamente allow_insecure_http en una red de prueba.')
        if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in '\r\n'):
            raise RetrievalError('Falta una API key válida en la variable de entorno configurada.')
        if not isinstance(dataset_ids, list) or not dataset_ids or not all(isinstance(i, str) and i.strip() for i in dataset_ids):
            raise RetrievalError('Definir dataset_ids explícitos; no se busca en todo el conocimiento disponible.')
        if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 30:
            raise RetrievalError('page_size debe estar entre 1 y 30.')
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 120:
            raise RetrievalError('timeout debe estar entre 0 y 120 segundos.')
        if not isinstance(similarity_threshold, (int, float)) or not math.isfinite(similarity_threshold) or not 0 <= similarity_threshold <= 1:
            raise RetrievalError('similarity_threshold debe estar entre 0 y 1.')
        self.base_url = base_url.rstrip('/')
        self.key = api_key
        self.datasets = sorted(set(dataset_ids))
        self.timeout = timeout
        self.page_size = page_size
        self.threshold = similarity_threshold
        self.opener = build_opener(NoRedirect())

    def retrieve(self, question):
        payload = {'question': question, 'dataset_ids': self.datasets,
                   'page': 1, 'page_size': self.page_size,
                   'similarity_threshold': self.threshold, 'highlight': False,
                   'keyword': False, 'use_kg': False, 'toc_enhance': False,
                   'include_knowledge_compilation': False}
        request = Request(self.base_url + '/api/v1/retrieval',
                          data=json.dumps(payload).encode(),
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + self.key})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
        except HTTPError as error:
            raise RetrievalError(f'RAGFlow respondió HTTP {error.code}; revisar disponibilidad, autenticación y permisos.') from None
        except (URLError, TimeoutError, OSError):
            raise RetrievalError('No se pudo completar la consulta a RAGFlow dentro del tiempo configurado.') from None
        if len(raw) > 8 * 1024 * 1024:
            raise RetrievalError('La respuesta de RAGFlow superó 8 MiB; reducir page_size.')
        try:
            response = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise RetrievalError('RAGFlow devolvió una respuesta JSON inválida.') from None
        if not isinstance(response, dict) or response.get('code') != 0 or not isinstance(response.get('data'), dict):
            raise RetrievalError('RAGFlow informó un error de aplicación; revisar la configuración sin continuar con contexto vacío.')
        data = response['data']
        chunks = data.get('chunks')
        total = data.get('total')
        if not isinstance(chunks, list) or not isinstance(total, int) or total < len(chunks):
            raise RetrievalError('La respuesta no respeta el contrato de retrieval esperado.')
        return chunks, total
