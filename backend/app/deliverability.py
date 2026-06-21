"""DNS-based deliverability checks for the configured sender domain.

Performs direct DNS resolution (no third-party DNS-over-HTTPS API) to stay
consistent with this project's no-cloud-dependency stance: the container
already resolves the SMTP server's own hostname to send mail, so this
introduces no new network trust boundary.

Every check returns a plain dict with at least a ``status`` of
``'pass'``, ``'warn'``, or ``'fail'`` and a human-readable ``message``.
Exceptions are caught here and translated to a fixed message -- callers in
routes.py never see a raw DNS exception, consistent with this app's rule
that client-facing responses never contain ``str(exc)``.
"""
import dns.exception
import dns.resolver


def _resolve_txt(name: str, timeout: float = 5.0) -> list[str]:
    """Return decoded TXT record strings for `name`, or [] if absent."""
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    try:
        answers = resolver.resolve(name, 'TXT')
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    return [b''.join(rdata.strings).decode('utf-8', errors='replace') for rdata in answers]


def _dns_error_result(exc: Exception) -> dict:
    if isinstance(exc, dns.exception.Timeout):
        return {'status': 'fail', 'message': 'DNS query timed out.'}
    if isinstance(exc, dns.resolver.NoNameservers):
        return {'status': 'fail', 'message': 'No DNS resolver reachable from the server.'}
    return {'status': 'fail', 'message': 'DNS lookup failed.'}


def check_spf(domain: str) -> dict:
    try:
        records = [t for t in _resolve_txt(domain) if t.lower().startswith('v=spf1')]
    except (dns.exception.Timeout, dns.resolver.NoNameservers) as e:
        return _dns_error_result(e)
    if not records:
        return {'status': 'fail', 'message': f'No SPF record (v=spf1) found on {domain}.', 'record': None}
    if len(records) > 1:
        return {
            'status': 'fail',
            'message': (
                f'Found {len(records)} separate SPF records on {domain}. This is '
                'invalid -- a domain must have exactly one SPF TXT record, otherwise '
                'SPF evaluation fails (PermError) and mail is often spam-filtered or '
                'rejected. Merge them into one record using multiple "include:" mechanisms.'
            ),
            'records': records,
        }
    return {'status': 'pass', 'message': 'SPF record found.', 'record': records[0]}


def check_dmarc(domain: str) -> dict:
    name = f'_dmarc.{domain}'
    try:
        records = [t for t in _resolve_txt(name) if t.lower().startswith('v=dmarc1')]
    except (dns.exception.Timeout, dns.resolver.NoNameservers) as e:
        return _dns_error_result(e)
    if not records:
        return {'status': 'fail', 'message': f'No DMARC record found at {name}.', 'record': None}

    record = records[0]
    policy = None
    for part in record.split(';'):
        part = part.strip()
        if part.lower().startswith('p='):
            policy = part.split('=', 1)[1].strip().lower()
            break

    explanation = {
        'none': 'Policy "none": failures are reported but mail is still delivered. '
                'Monitoring only -- offers no actual protection yet.',
        'quarantine': 'Policy "quarantine": mail failing DMARC is likely sent to spam/junk by receivers.',
        'reject': 'Policy "reject": mail failing DMARC is rejected outright. Strongest protection.',
    }.get(policy, f'Unrecognized or missing policy value ("{policy}").')
    status = 'pass' if policy in ('quarantine', 'reject') else 'warn' if policy == 'none' else 'fail'
    return {'status': status, 'message': explanation, 'record': record, 'policy': policy}


def check_dkim(domain: str, selector: str) -> dict:
    name = f'{selector}._domainkey.{domain}'
    try:
        records = [t for t in _resolve_txt(name) if 'v=dkim1' in t.lower()]
    except (dns.exception.Timeout, dns.resolver.NoNameservers) as e:
        return _dns_error_result(e)
    if not records:
        return {
            'status': 'fail',
            'message': (
                f'No DKIM record found at {name}. Check that the selector '
                f'("{selector}") matches exactly what your SMTP provider gave you.'
            ),
            'record': None,
        }
    return {'status': 'pass', 'message': 'DKIM record found.', 'record': records[0]}
