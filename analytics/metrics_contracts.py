from typing import Any, Dict, List
Record = Dict[str, Any]

def to_float(x: Any) -> float:
    if x is None:
        return 0.0

    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if not s:
        return 0.0

    s = s.replace(' ', '').replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0

def to_int(x: Any) -> int:
    if x is None:
        return 0
    if isinstance(x, int):
        return x
    s = str(x).strip().replace(' ', '').replace(',', '.')
    if not s:
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def is_total(r: Record) -> bool:
    return r.get('record_type') == 'total'


def is_counterparty(r: Record) -> bool:
    return r.get('record_type') == 'counterparty'


def filter_records(
        records: List[Record],
        *,
        subject_inn: str | None = None,
        years: List[int] | None = None,
        statuses: List[str] | None = None,
        role: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None) -> List[Record]:

    out: List[Record] = []
    s_years = set(years) if years is not None else None
    s_statuses = set(statuses) if statuses is not None else None
    for r in records:
        if subject_inn is not None and r.get('subject_inn') != subject_inn:
            continue

        if s_years is not None and r.get('year') not in s_years:
            continue

        if s_statuses is not None and r.get('status') not in s_statuses:
            continue

        amt = to_float(r.get('amount'))
        if min_amount is not None and amt < min_amount:
            continue

        if max_amount is not None and amt > max_amount:
            continue

        if role is not None and r.get('record_type') == 'counterparty':
            if r.get('counterparty_role') != role:
                continue

        out.append(r)

    return out


def pick_main_currency(currencies: list[str]) -> str | None:
    if not currencies:
        return None
    if 'RUB' in currencies:
        return 'RUB'
    return currencies[0]


def summary_totals(records: List[Record]) -> Dict[str, Any]:
    by_currency: Dict[str, Dict[str, float | int]] = {}

    for r in records:
        if r.get('record_type') != 'total':
            continue

        cur = r.get('currency') or 'UNKNOWN'
        if cur not in by_currency:
            by_currency[cur] = {'amount': 0.0, 'count': 0}

        by_currency[cur]['amount'] += to_float(r.get('amount'))
        by_currency[cur]['count'] += to_int(r.get('count'))

    currencies = sorted(by_currency.keys())
    return {'by_currency': by_currency, 'currencies': currencies}

def by_year(records: List[Record], currency: str) -> List[Record]:
    agg: Dict[int, Dict[str, Any]] = {}

    for r in records:
        if r.get('record_type') != 'total':
            continue
        if (r.get('currency') or 'UNKNOWN') != currency:
            continue

        year = r.get('year')
        if year is None:
            continue

        if year not in agg:
            agg[year] = {'year': year, 'currency': currency, 'amount': 0.0, 'count': 0}

        agg[year]['amount'] += to_float(r.get('amount'))
        agg[year]['count'] += to_int(r.get('count'))

    return sorted(agg.values(), key=lambda x: x['year'])


def by_status(records: List[Record], currency: str) -> List[Record]:
    agg: Dict[str, Dict[str, Any]] = {}

    for r in records:
        if r.get('record_type') != 'total':
            continue
        if (r.get('currency') or 'UNKNOWN') != currency:
            continue

        status = r.get('status') or 'UNKNOWN'

        if status not in agg:
            agg[status] = {'status': status, 'currency': currency, 'amount': 0.0, 'count': 0}

        agg[status]['amount'] += to_float(r.get('amount'))
        agg[status]['count'] += to_int(r.get('count'))

    return sorted(agg.values(), key=lambda x: x['amount'], reverse=True)


def year_status(records: List[Record], currency: str) -> List[Record]:
    agg: Dict[tuple[int, str], Dict[str, Any]] = {}

    for r in records:
        if r.get('record_type') != 'total':
            continue
        if (r.get('currency') or 'UNKNOWN') != currency:
            continue

        year = r.get('year')
        if year is None:
            continue

        status = r.get('status') or 'UNKNOWN'
        key = (year, status)

        if key not in agg:
            agg[key] = {'year': year, 'status': status, 'currency': currency, 'amount': 0.0, 'count': 0}

        agg[key]['amount'] += to_float(r.get('amount'))
        agg[key]['count'] += to_int(r.get('count'))

    return sorted(agg.values(), key=lambda x: (x['year'], x['status']))


def top_counterparties(
    records: List[Record],
    role: str,
    currency: str,
    top_n: int = 10,
) -> List[Record]:

    agg: Dict[str, Dict[str, Any]] = {}

    for r in records:
        if r.get('record_type') != 'counterparty':
            continue
        if r.get('counterparty_role') != role:
            continue
        if (r.get('currency') or 'UNKNOWN') != currency:
            continue

        inn = r.get('counterparty_inn') or 'UNKNOWN_INN'
        if inn not in agg:
            agg[inn] = {
                'counterparty_role': role,
                'currency': currency,
                'counterparty_inn': r.get('counterparty_inn'),
                'counterparty_name_full': r.get('counterparty_name_full'),
                'amount': 0.0,
                'count': 0,
                'rows_used': 0,
                'reg_numbers': set(),
            }

        agg[inn]['amount'] += to_float(r.get('amount'))
        agg[inn]['count'] += to_int(r.get('count'))
        agg[inn]['rows_used'] += 1

        for reg in (r.get('reg_numbers') or []):
            if reg:
                agg[inn]['reg_numbers'].add(reg)

    out: List[Record] = []
    for v in agg.values():
        v['reg_numbers'] = sorted(v['reg_numbers'])
        out.append(v)

    out.sort(key=lambda x: x['amount'], reverse=True)
    return out[:max(0, top_n)]


def reg_numbers_sample(
    records: List[Record],
    role: str | None = None,
    limit: int = 20,
) -> List[str]:

    seen: set[str] = set()
    out: List[str] = []

    for r in records:
        if r.get('record_type') != 'counterparty':
            continue

        if role is not None and r.get('counterparty_role') != role:
            continue

        reg_numbers = r.get('reg_numbers') or []
        if not isinstance(reg_numbers, list):
            reg_numbers = []

        for reg in reg_numbers:
            if not reg:
                continue
            if reg in seen:
                continue

            seen.add(reg)
            out.append(reg)

            if len(out) >= limit:
                return out

    return out


def compute_contracts_metrics(
    records: List[Record],
    filters: Dict[str, Any] | None = None,
    top_n: int = 10,
    reg_limit: int = 20,
) -> Dict[str, Any]:
    filters = filters or {}

    filtered = filter_records(
        records,
        subject_inn=filters.get('subject_inn'),
        years=filters.get('years'),
        statuses=filters.get('statuses'),
        role=filters.get('role'),
        min_amount=filters.get('min_amount'),
        max_amount=filters.get('max_amount')
    )

    summary = summary_totals(filtered)
    currencies: list[str] = summary['currencies']
    main_currency = pick_main_currency(currencies)

    result: dict[str, Any] = {
        'filters': filters,
        'summary': summary,
        'main_currency': main_currency,
        'by_year': [],
        'by_status': [],
        'year_status': [],
        'top_customers': [],
        'top_suppliers': [],
        'reg_numbers': {
            'all': reg_numbers_sample(filtered, role=None, limit=reg_limit),
            'customers': reg_numbers_sample(filtered, role='customer', limit=reg_limit),
            'suppliers': reg_numbers_sample(filtered, role='supplier', limit=reg_limit),
        },
        'rows': {
            'input': len(records),
            'after_filter': len(filtered),
            'total_rows': sum(1 for r in filtered if r.get('record_type') == 'total'),
            'counterparty_rows': sum(1 for r in filtered if r.get('record_type') == 'counterparty'),
        },
    }
    if main_currency is None:
        return result
    result['by_year'] = by_year(filtered, main_currency)
    result['by_status'] = by_status(filtered, main_currency)
    result['year_status'] = year_status(filtered, main_currency)

    result['top_customers'] = top_counterparties(
        filtered, role='customer', currency=main_currency, top_n=top_n
    )
    result['top_suppliers'] = top_counterparties(
        filtered, role='supplier', currency=main_currency, top_n=top_n
    )

    return result



