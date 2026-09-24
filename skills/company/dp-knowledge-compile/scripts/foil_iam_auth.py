#!/usr/bin/env python3
"""Acquire a short-lived Foil IAM token from runtime environment variables."""

from __future__ import annotations

import base64
import binascii
import errno
import hashlib
import ipaddress
import json
import os
import secrets
import socket
import stat
import ssl
import time
from pathlib import Path
from typing import Any, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

try:
    import truststore
except ImportError:  # Optional dependency.
    truststore = None


class IamConfigurationError(ValueError):
    pass


class IamAuthenticationError(RuntimeError):
    pass


class IamTransportError(RuntimeError):
    pass


class LoginCredentials(NamedTuple):
    username: str
    password: str
    enterprise_code: str


class IamToken(NamedTuple):
    authorization: str
    expires_in: int


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# IAM 登录域名不再写死：优先 FOIL_IAM_ORIGIN，其次从 FOIL_BASE_URL 的 host 推导，
# 最后才回退到共享生产登录域名。这样 skill 不感知测试/正式环境，地址完全由运行环境注入。
_PUBLIC_KEY_PATH = "/deepexi-console-iam/sso/public-key"
_TOKEN_PATH = "/deepexi-console-iam/oauth/token"


def resolve_iam_origin(base_url: str | None = None) -> str:
    explicit = os.environ.get("FOIL_IAM_ORIGIN", "").strip()
    if explicit:
        return explicit.rstrip("/")
    if base_url:
        parsed = urlsplit(base_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    raise IamConfigurationError("FOIL_IAM_ORIGIN is missing and cannot be derived from FOIL_BASE_URL")
_CLIENT_CODE = "414dddb1453f4e27bb046bd158227f1b"
_CLIENT_CODE_HEADER = "X-CLIENT-CODE-HEADER"
_MAX_IAM_RESPONSE_BYTES = 65_536
_RSA_CHUNK_CHARACTERS = 60
_RSA_ENCRYPTION_OID = bytes.fromhex("06092a864886f70d010101")
_ACCOUNT_ENV_NAME = "DEEPWORKS_AGENT_FOIL_ACCOUNT"
_PASSWORD_ENV_NAME = "DEEPWORKS_AGENT_FOIL_PASSWORD"
_ACCOUNT_TEST_ENV_NAME = "DEEPWORKS_AGENT_FOIL_ACCOUNT_TEST"
_PASSWORD_TEST_ENV_NAME = "DEEPWORKS_AGENT_FOIL_PASSWORD_TEST"
_FOIL_TARGET_ENV_NAME = "FOIL_KNOWLEDGE_CENTER_TARGET"
_FALLBACK_ENV_NAME = "DEEPWORKS_AGENT_FOIL_AUTH_FALLBACK"
_LOCAL_AUTH_JSON_FALLBACK = "local_auth_json"
_MAX_AUTH_FILE_BYTES = 16_384
_TOKEN_CACHE_ENV_NAME = "DEEPWORKS_FOIL_TOKEN_CACHE"
_TOKEN_CACHE_MAX_BYTES = 8_192
_TOKEN_SKEW_SECONDS = 90
_DEFAULT_TOKEN_EXPIRES_IN = 3_600


def _runtime_env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _normalize_target(value: str | None) -> str | None:
    if value is None:
        return None
    target = value.strip().lower()
    if target in {"test", "production"}:
        return target
    raise IamConfigurationError(f"{_FOIL_TARGET_ENV_NAME} must be test or production")


def resolve_knowledge_center_target(base_url: str | None = None) -> str:
    explicit = _normalize_target(_runtime_env(_FOIL_TARGET_ENV_NAME) or None)
    if explicit is not None:
        return explicit
    has_prod = bool(_runtime_env(_ACCOUNT_ENV_NAME) or _runtime_env(_PASSWORD_ENV_NAME))
    has_test = bool(_runtime_env(_ACCOUNT_TEST_ENV_NAME) or _runtime_env(_PASSWORD_TEST_ENV_NAME))
    if has_prod and not has_test:
        return "production"
    if has_test and not has_prod:
        return "test"
    candidate = (base_url or "").strip().lower()
    if candidate:
        raise IamConfigurationError(f"{_FOIL_TARGET_ENV_NAME} must be set explicitly when {base_url} is used")
    return "test"


def _credential_env_names(target: str) -> tuple[str, str]:
    if target == "test":
        return _ACCOUNT_TEST_ENV_NAME, _PASSWORD_TEST_ENV_NAME
    if target == "production":
        return _ACCOUNT_ENV_NAME, _PASSWORD_ENV_NAME
    raise IamConfigurationError(f"unsupported knowledge center target: {target}")


def default_local_auth_file() -> Path:
    return Path.home() / ".deepworks" / ".knowledge" / "auth.json"


def system_ssl_context() -> ssl.SSLContext:
    if truststore is not None:
        try:
            return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except Exception as error:  # noqa: BLE001
            raise IamTransportError("Foil system trust store is unavailable") from error
    return ssl.create_default_context()


def _iam_ssl_context() -> ssl.SSLContext:
    return system_ssl_context()


def _clean_credential(value: str | None, label: str, maximum: int) -> str:
    if value is None or value == "" or len(value) > maximum:
        raise IamConfigurationError(f"{label} is missing or invalid in runtime environment variables")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise IamConfigurationError(f"{label} contains unsupported control characters")
    return value


def resolve_login_credentials_from_environment(target: str | None = None) -> LoginCredentials | None:
    resolved_target = resolve_knowledge_center_target() if target is None else _normalize_target(target)
    account_env, password_env = _credential_env_names(resolved_target)
    account = _runtime_env(account_env)
    password = _runtime_env(password_env)
    if not account and not password:
        return None
    if account.count("@") != 1:
        raise IamConfigurationError(f"{account_env} must use username@enterprise-code")
    username, enterprise_code = account.split("@", 1)
    if not password:
        raise IamConfigurationError(f"{password_env} is missing or invalid")
    return LoginCredentials(
        _clean_credential(username, "Foil login username", 256),
        _clean_credential(password, "Foil login password", 1024),
        _clean_credential(enterprise_code, "Foil enterprise code", 128),
    )


def _validate_auth_file_metadata(descriptor: int) -> None:
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        raise IamConfigurationError("Foil local auth.json must be a regular file")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise IamConfigurationError("Foil local auth.json must be owned by the current user")
    if os.name != "nt" and stat.S_IMODE(metadata.st_mode) & 0o077:
        raise IamConfigurationError("Foil local auth.json must have permissions 0600 or stricter")
    if metadata.st_size > _MAX_AUTH_FILE_BYTES:
        raise IamConfigurationError("Foil local auth.json exceeds the size limit")


def _read_auth_file(path: Path) -> dict[str, Any] | None:
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.EMLINK}:
            raise IamConfigurationError("Foil local auth.json must not be a symbolic link") from error
        raise IamConfigurationError("Foil local auth.json is unavailable") from error
    try:
        _validate_auth_file_metadata(descriptor)
        with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
            descriptor = -1
            try:
                document = json.load(stream)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise IamConfigurationError("Foil local auth.json is not valid JSON") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if not isinstance(document, dict):
        raise IamConfigurationError("Foil local auth.json must contain an object")
    return document


def resolve_login_credentials_from_local_auth_json(path: Path | None = None) -> LoginCredentials | None:
    auth_path = path or default_local_auth_file()
    document = _read_auth_file(auth_path)
    if document is None:
        return None
    allowed = {"version", "account", "password"}
    if set(document) - allowed or document.get("version") != 1:
        raise IamConfigurationError("Foil local auth.json must use version 1 and only account/password fields")
    account = document.get("account")
    password = document.get("password")
    if not isinstance(account, str) or account.count("@") != 1:
        raise IamConfigurationError("Foil local auth.json account must use username@enterprise-code")
    username, enterprise_code = account.split("@", 1)
    return LoginCredentials(
        _clean_credential(username, "Foil login username", 256),
        _clean_credential(password, "Foil login password", 1024),
        _clean_credential(enterprise_code, "Foil enterprise code", 128),
    )


def resolve_login_credentials(target: str | None = None) -> tuple[LoginCredentials | None, str | None]:
    environment_credentials = resolve_login_credentials_from_environment(target)
    if environment_credentials is not None:
        return environment_credentials, "runtime_environment"
    fallback = _runtime_env(_FALLBACK_ENV_NAME)
    if not fallback:
        return None, None
    if fallback != _LOCAL_AUTH_JSON_FALLBACK:
        raise IamConfigurationError(f"{_FALLBACK_ENV_NAME} must be {_LOCAL_AUTH_JSON_FALLBACK}")
    local_credentials = resolve_login_credentials_from_local_auth_json()
    if local_credentials is not None:
        return local_credentials, "local_auth_json"
    return None, "local_auth_json"


def _read_der_length(document: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(document):
        raise IamTransportError("Foil public key is invalid")
    first = document[offset]
    if first < 128:
        return first, offset + 1
    count = first & 0x7F
    if count == 0 or count > 4 or offset + 1 + count > len(document):
        raise IamTransportError("Foil public key is invalid")
    length = int.from_bytes(document[offset + 1 : offset + 1 + count], "big")
    if length < 128:
        raise IamTransportError("Foil public key is invalid")
    return length, offset + 1 + count


def _read_der_value(document: bytes, offset: int, tag: int) -> tuple[bytes, int]:
    if offset >= len(document) or document[offset] != tag:
        raise IamTransportError("Foil public key is invalid")
    length, value_offset = _read_der_length(document, offset + 1)
    end = value_offset + length
    if end > len(document):
        raise IamTransportError("Foil public key is invalid")
    return document[value_offset:end], end


def _parse_rsa_public_key(public_key: str) -> tuple[int, int, int]:
    try:
        document = base64.b64decode(public_key, validate=True)
    except (ValueError, binascii.Error) as error:
        raise IamTransportError("Foil public key is invalid") from error
    subject_public_key_info, end = _read_der_value(document, 0, 0x30)
    if end != len(document):
        raise IamTransportError("Foil public key is invalid")
    algorithm, offset = _read_der_value(subject_public_key_info, 0, 0x30)
    if _RSA_ENCRYPTION_OID not in algorithm:
        raise IamTransportError("Foil public key algorithm is unsupported")
    bit_string, offset = _read_der_value(subject_public_key_info, offset, 0x03)
    if offset != len(subject_public_key_info) or not bit_string or bit_string[0] != 0:
        raise IamTransportError("Foil public key is invalid")
    rsa_document, rsa_end = _read_der_value(bit_string[1:], 0, 0x30)
    if rsa_end != len(bit_string) - 1:
        raise IamTransportError("Foil public key is invalid")
    modulus_bytes, rsa_offset = _read_der_value(rsa_document, 0, 0x02)
    exponent_bytes, rsa_offset = _read_der_value(rsa_document, rsa_offset, 0x02)
    if rsa_offset != len(rsa_document):
        raise IamTransportError("Foil public key is invalid")
    modulus = int.from_bytes(modulus_bytes, "big")
    exponent = int.from_bytes(exponent_bytes, "big")
    key_bytes = (modulus.bit_length() + 7) // 8
    if key_bytes < 128 or key_bytes > 512 or exponent < 3 or exponent % 2 == 0:
        raise IamTransportError("Foil public key parameters are unsupported")
    return modulus, exponent, key_bytes


def _nonzero_random_bytes(length: int) -> bytes:
    output = bytearray()
    while len(output) < length:
        output.extend(value for value in secrets.token_bytes(length - len(output)) if value)
    return bytes(output[:length])


def _rsa_encrypt_chunks(value: str, public_key: str) -> list[str]:
    modulus, exponent, key_bytes = _parse_rsa_public_key(public_key)
    encrypted: list[str] = []
    for offset in range(0, len(value), _RSA_CHUNK_CHARACTERS):
        message = value[offset : offset + _RSA_CHUNK_CHARACTERS].encode("utf-8")
        padding_length = key_bytes - len(message) - 3
        if padding_length < 8:
            raise IamConfigurationError("Foil login fields are too long")
        encoded = b"\x00\x02" + _nonzero_random_bytes(padding_length) + b"\x00" + message
        cipher = pow(int.from_bytes(encoded, "big"), exponent, modulus)
        encrypted.append(base64.b64encode(cipher.to_bytes(key_bytes, "big")).decode("ascii"))
    return encrypted


def _read_json_response(response: Any) -> dict[str, Any]:
    content_length = response.headers.get("Content-Length") if response.headers else None
    if content_length is not None:
        try:
            if int(content_length) > _MAX_IAM_RESPONSE_BYTES:
                raise IamTransportError("Foil response exceeds the size limit")
        except ValueError:
            raise IamTransportError("Foil response content length is invalid") from None
    raw = response.read(_MAX_IAM_RESPONSE_BYTES + 1)
    if len(raw) > _MAX_IAM_RESPONSE_BYTES:
        raise IamTransportError("Foil response exceeds the size limit")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IamTransportError("Foil response is not valid JSON") from error
    if not isinstance(document, dict):
        raise IamTransportError("Foil response envelope is invalid")
    return document


def _open_json(opener: Any, request: Request, timeout: float) -> dict[str, Any]:
    try:
        with opener.open(request, timeout=timeout) as response:
            if 300 <= response.status < 400:
                raise IamTransportError("Foil redirects are forbidden")
            return _read_json_response(response)
    except HTTPError as error:
        try:
            if error.code in {400, 401, 403}:
                raise IamAuthenticationError("Foil login was rejected; update the configured account and password")
            if 300 <= error.code < 400:
                raise IamTransportError("Foil redirects are forbidden") from None
            raise IamTransportError(f"Foil request failed with status {error.code}") from None
        finally:
            error.close()
    except (URLError, TimeoutError) as error:
        raise IamTransportError("Foil request failed") from error


def _remaining_timeout(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise IamTransportError("Foil login exceeded the request deadline")
    return remaining


def _validate_iam_origin(origin: str) -> None:
    parsed = urlsplit(origin)
    if parsed.scheme != "https" or not parsed.hostname or parsed.port not in {None, 443}:
        raise IamConfigurationError(f"approved IAM origin is invalid: {origin}")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise IamTransportError("approved IAM host cannot be resolved") from error
    if not addresses:
        raise IamTransportError("approved IAM host did not resolve")
    for address in {item[4][0] for item in addresses}:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError as error:
            raise IamTransportError("approved IAM host resolved to an invalid address") from error
        if not parsed_address.is_global:
            raise IamTransportError("approved IAM host resolved outside the public network")


def _successful_payload(document: dict[str, Any], label: str) -> Any:
    code = str(document.get("code"))
    if code != "0" or "payload" not in document:
        if code in {"400", "401", "403"}:
            raise IamAuthenticationError(f"Foil {label} was rejected")
        raise IamTransportError(f"Foil {label} was unsuccessful")
    return document["payload"]


def _normalize_authorization(token: Any) -> str:
    if not isinstance(token, str):
        raise IamTransportError("Foil login response does not contain an access token")
    value = token.strip()
    if value.startswith("Bearer "):
        value = value[7:]
    if not value or any(character.isspace() for character in value) or value.startswith("Bearer "):
        raise IamTransportError("Foil login response contains an invalid access token")
    if len(value) > 32_768:
        raise IamTransportError("Foil login response contains an oversized access token")
    return f"Bearer {value}"


def _token_expires_in(payload: dict[str, Any]) -> int:
    raw = payload.get("expires_in")
    if raw is None:
        raw = payload.get("expiresIn")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = _DEFAULT_TOKEN_EXPIRES_IN
    if value <= _TOKEN_SKEW_SECONDS:
        return _DEFAULT_TOKEN_EXPIRES_IN
    return value


def account_fingerprint(credentials: LoginCredentials) -> str:
    blob = f"{credentials.username}\0{credentials.enterprise_code}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def default_token_cache_file() -> Path:
    override = _runtime_env(_TOKEN_CACHE_ENV_NAME)
    if override:
        return Path(override)
    return Path.home() / ".deepworks" / ".knowledge" / "foil-iam-token.json"


def _restrict_private_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _read_token_cache(fingerprint: str) -> str | None:
    path = default_token_cache_file()
    try:
        if not path.is_file() or path.stat().st_size > _TOKEN_CACHE_MAX_BYTES:
            return None
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    if document.get("account_fp") != fingerprint:
        return None
    expires_at = document.get("expires_at")
    if not isinstance(expires_at, (int, float)):
        return None
    if float(expires_at) - _TOKEN_SKEW_SECONDS <= time.time():
        return None
    try:
        return _normalize_authorization(document.get("authorization"))
    except IamTransportError:
        return None


def _write_token_cache(fingerprint: str, authorization: str, expires_in: int) -> None:
    path = default_token_cache_file()
    document = {
        "account_fp": fingerprint,
        "authorization": authorization,
        "expires_at": time.time() + max(int(expires_in), _TOKEN_SKEW_SECONDS + 1),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        _restrict_private_file(path)
    except OSError:
        pass


def _acquire_token(
    credentials: LoginCredentials,
    timeout_seconds: float,
    *,
    base_url: str | None = None,
    origin: str | None = None,
) -> IamToken:
    if timeout_seconds <= 0:
        raise IamConfigurationError("Foil timeout must be positive")
    credentials = LoginCredentials(
        _clean_credential(credentials.username, "Foil login username", 256),
        _clean_credential(credentials.password, "Foil login password", 1024),
        _clean_credential(credentials.enterprise_code, "Foil enterprise code", 128),
    )
    resolved_origin = origin or resolve_iam_origin(base_url)
    _validate_iam_origin(resolved_origin)
    opener = build_opener(
        ProxyHandler({}),
        HTTPSHandler(context=_iam_ssl_context()),
        _NoRedirect(),
    )
    deadline = time.monotonic() + timeout_seconds
    common_headers = {"Accept": "application/json", _CLIENT_CODE_HEADER: _CLIENT_CODE}
    public_key_request = Request(
        resolved_origin + _PUBLIC_KEY_PATH,
        headers=common_headers,
        method="GET",
    )
    public_key = _successful_payload(
        _open_json(opener, public_key_request, _remaining_timeout(deadline)),
        "public-key request",
    )
    if not isinstance(public_key, str):
        raise IamTransportError("Foil public-key response is invalid")

    serialized = "&".join(
        (
            "grant_type=deepexi",
            "scope=all",
            f"username={credentials.username}",
            f"password={credentials.password}",
            f"enterpriseCode={credentials.enterprise_code}",
        )
    )
    encrypted = _rsa_encrypt_chunks(serialized, public_key)
    token_request = Request(
        resolved_origin + _TOKEN_PATH,
        data=json.dumps(encrypted, separators=(",", ":")).encode("utf-8"),
        headers={**common_headers, "Content-Type": "application/json"},
        method="POST",
    )
    payload = _successful_payload(
        _open_json(opener, token_request, _remaining_timeout(deadline)),
        "login",
    )
    if not isinstance(payload, dict):
        raise IamTransportError("Foil login response payload is invalid")
    return IamToken(
        _normalize_authorization(payload.get("access_token")),
        _token_expires_in(payload),
    )


def authenticate(credentials: LoginCredentials, timeout_seconds: float) -> str:
    return _acquire_token(credentials, timeout_seconds).authorization


def authenticate_from_runtime_environment(
    timeout_seconds: float,
    *,
    force: bool = False,
    base_url: str | None = None,
    target: str | None = None,
) -> str:
    resolved_target = _normalize_target(target) if target is not None else resolve_knowledge_center_target(base_url)
    credentials, _source = resolve_login_credentials(resolved_target)
    if credentials is None:
        raise IamConfigurationError(
            "Foil runtime credentials are not configured; set "
            f"{_credential_env_names(resolved_target)[0]} and {_credential_env_names(resolved_target)[1]}, "
            f"or set {_FALLBACK_ENV_NAME}={_LOCAL_AUTH_JSON_FALLBACK} for local auth.json fallback"
        )
    fingerprint = account_fingerprint(credentials)
    if not force:
        cached = _read_token_cache(fingerprint)
        if cached:
            return cached
    token = _acquire_token(credentials, timeout_seconds, base_url=base_url)
    try:
        _write_token_cache(fingerprint, token.authorization, token.expires_in)
    except OSError:
        pass
    return token.authorization
