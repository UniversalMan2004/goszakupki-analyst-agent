from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


def normalize_contracts_format1(raw: Dict[str, Any]) -> List[Dict[str, Any]]:

    records: List[Dict[str, Any]] = []

    if not isinstance(raw, dict):
        raise ValueError("raw должен быть dict (JSON-объект верхнего уровня)")

    for subject_inn, years_block in raw.items():
        if not isinstance(years_block, dict):
            continue

        for year_str, statuses_block in years_block.items():
            if not isinstance(statuses_block, dict):
                continue

            year = _safe_int(year_str)

            for status, payload in statuses_block.items():
                if not isinstance(payload, dict):
                    continue

                totals = payload.get("Цена", [])
                if isinstance(totals, list):
                    for t in totals:
                        if not isinstance(t, dict):
                            continue
                        records.append({
                            "record_type": "total",
                            "subject_inn": str(subject_inn),
                            "year": year,
                            "status": str(status),

                            "currency": t.get("ВалютаКод"),
                            "currency_name": t.get("ВалютаНаим"),
                            "amount": t.get("Сумма"),
                            "count": t.get("Количество"),
                            "counterparty_role": None,
                            "counterparty_inn": None,
                            "counterparty_ogrn": None,
                            "counterparty_name_full": None,
                            "counterparty_name_short": None,
                            "counterparty_address": None,
                            "counterparty_head_fio": None,
                            "counterparty_head_innfl": None,
                            "counterparty_phone": None,
                            "counterparty_email": None,
                            "reg_numbers": [],
                        })

                if "Заказчики" in payload:
                    _extend_counterparties(
                        out=records,
                        subject_inn=str(subject_inn),
                        year=year,
                        status=str(status),
                        role_name="customer",
                        items=payload.get("Заказчики"),
                    )

                if "Поставщики" in payload:
                    _extend_counterparties(
                        out=records,
                        subject_inn=str(subject_inn),
                        year=year,
                        status=str(status),
                        role_name="supplier",
                        items=payload.get("Поставщики"),
                    )

    return records


def _extend_counterparties(
    out: List[Dict[str, Any]],
    subject_inn: str,
    year: Optional[int],
    status: str,
    role_name: str,
    items: Any,
) -> None:
    if not isinstance(items, list):
        return

    for cp in items:
        if not isinstance(cp, dict):
            continue

        price_obj = cp.get("Цена", {})
        currency_rows = _parse_currency_price_object(price_obj)

        reg_numbers = cp.get("РегНомера", [])
        if not isinstance(reg_numbers, list):
            reg_numbers = []

        if not currency_rows:
            currency_rows = [(None, None, None)]

        for currency, amount, count in currency_rows:
            out.append({
                "record_type": "counterparty",
                "subject_inn": subject_inn,
                "year": year,
                "status": status,

                "currency": currency,
                "currency_name": None,
                "amount": amount,
                "count": count,

                "counterparty_role": role_name,
                "counterparty_inn": cp.get("ИНН"),
                "counterparty_ogrn": cp.get("ОГРН"),
                "counterparty_name_full": cp.get("НаимПолн"),
                "counterparty_name_short": cp.get("НаимСокр"),
                "counterparty_address": cp.get("АдресПолн"),
                "counterparty_head_fio": cp.get("РукФИО"),
                "counterparty_head_innfl": cp.get("РукИННФЛ"),

                "counterparty_phone": cp.get("Телефон"),
                "counterparty_email": cp.get("Email"),

                "reg_numbers": reg_numbers,
            })


def _parse_currency_price_object(price_obj: Any) -> List[Tuple[Optional[str], Any, Any]]:

    rows: List[Tuple[Optional[str], Any, Any]] = []

    if not isinstance(price_obj, dict):
        return rows

    for currency, v in price_obj.items():
        if isinstance(v, dict):
            rows.append((currency, v.get("Сумма"), v.get("Количество")))
        else:
            rows.append((currency, None, None))

    return rows


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value))
    except Exception:
        return None
