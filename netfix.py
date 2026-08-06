"""SSL workaround for this machine's AVG Antivirus TLS interception.

AVG's Web/Mail Shield intercepts HTTPS with its own self-signed root cert.
Python 3.13's ssl module enables VERIFY_X509_STRICT by default, which rejects
that cert (its Basic Constraints extension isn't marked critical, an RFC 5280
violation) even once it's added to the trust store. literature.py already
works around this for plain urllib calls (Semantic Scholar); this module does
the equivalent for requests-based libraries (astroquery), which build their
own SSLContext internally and don't honor REQUESTS_CA_BUNDLE alone for the
strict-flag part of the problem.

Harmless on a machine without AVG installed -- falls back to a normal
requests session in that case.
"""
from __future__ import annotations

import ssl
from pathlib import Path

import certifi
from requests.adapters import HTTPAdapter

_AVG_INTERCEPT_CERT = Path(r"C:\ProgramData\AVG\Antivirus\wscert.pem")


def _relaxed_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    if _AVG_INTERCEPT_CERT.exists():
        try:
            ctx.load_verify_locations(cafile=str(_AVG_INTERCEPT_CERT))
        except ssl.SSLError:
            pass
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


class RelaxedSSLAdapter(HTTPAdapter):
    """requests HTTPAdapter using an SSLContext with the strict X.509 check
    relaxed and the AVG intercept cert trusted, while still verifying every
    other certificate normally (via certifi's bundle)."""

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = _relaxed_ssl_context()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = _relaxed_ssl_context()
        return super().proxy_manager_for(*args, **kwargs)


def patch_session(session) -> None:
    """Mount the relaxed adapter onto an existing requests.Session in place."""
    session.mount("https://", RelaxedSSLAdapter())


def patch_alma(alma_class) -> None:
    """Patch every requests.Session astroquery's Alma class touches -- the
    main query session plus the lazily-created datalink/tap/sia sub-clients,
    which each carry their own pyvo session."""
    patch_session(alma_class._session)
    for attr in ("_datalink", "_tap", "_sia"):
        obj = getattr(alma_class, attr, None)
        sess = getattr(obj, "_session", None)
        if sess is not None:
            patch_session(sess)

    # datalink/tap/sia are lazily constructed on first access (see
    # astroquery.alma.core.AlmaClass.datalink/tap/sia @property), each
    # wrapping a *new* requests.Session -- patch those too, once created.
    orig_datalink_getter = type(alma_class).datalink.fget
    orig_tap_getter = type(alma_class).tap.fget
    orig_sia_getter = type(alma_class).sia.fget

    def _patched_datalink(self):
        obj = orig_datalink_getter(self)
        if getattr(obj, "_session", None) is not None:
            patch_session(obj._session)
        return obj

    def _patched_tap(self):
        obj = orig_tap_getter(self)
        if getattr(obj, "_session", None) is not None:
            patch_session(obj._session)
        return obj

    def _patched_sia(self):
        obj = orig_sia_getter(self)
        if getattr(obj, "_session", None) is not None:
            patch_session(obj._session)
        return obj

    type(alma_class).datalink = property(_patched_datalink)
    type(alma_class).tap = property(_patched_tap)
    type(alma_class).sia = property(_patched_sia)
