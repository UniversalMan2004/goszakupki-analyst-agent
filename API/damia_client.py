
import requests
from typing import Dict, Any
import datetime as dt


class DamiaAPIError(Exception):
    pass


class DamiaClient:
    base_url = "https://api.damia.ru/zakupki"


    def __init__(self, api_key: str, timeout: int=30):
        self.api_key = api_key
        self.timeout = timeout


    def _get(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f'{self.base_url}/{method}'
        params['key'] = self.api_key
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = requests.get(url=url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise DamiaAPIError(f"Ошибка сети: {e}") from e

        if response.status_code != 200:
            raise DamiaAPIError(f"HTTP {response.status_code}: {response.text}")

        if not response.text.strip():
            raise DamiaAPIError('Пустой ответ от API')

        try:
            data = response.json()
        except ValueError:
            raise DamiaAPIError(f'Ответ не является JSON файлом: {response.text}')

        return data


    def get_contracts(self, inn: str, fz: str='44', role: int=0, from_date: str | None = None, to_date: str | None = None, format: int=1):
        self._validate_inn(inn)
        self._validate_fz(fz)

        if role not in {0, 1}:
            raise DamiaAPIError('Параметр роль должен принимать одно из двух значений 0 или 1')

        self._validate_date("from_date", from_date)
        self._validate_date("to_date", to_date)

        return self._get(method='contracts', params={'inn': inn, 'fz': fz, 'role': role,'from_date': from_date, 'to_date': to_date, 'format': format})


    def get_zakupka(self, regn: str, actual: int=0):
        if not regn.strip():
            raise DamiaAPIError('Номер извещения о закупке в ЕИС госзакупок обязателен для получения информации')

        if actual not in {0, 1}:
            raise DamiaAPIError('Параметр role должен принимать одно из значений 0 или 1')

        return self._get(method='zakupka', params={'regn': regn, 'actual': actual})


    def get_contract(self, regn: str):
        if not regn.strip():
            raise DamiaAPIError('Необходимо подать реестровый номер контракта (по 44-ФЗ) или идентификатор договора (по 223-ФЗ)')

        return self._get(method='contract', params={'regn': regn})


    def get_zakupki(self, inn: str, fz: str='44', role: int=0, from_date: str | None = None, to_date: str | None = None, format: int=1):
        self._validate_inn(inn)
        self._validate_fz(fz)

        if role not in {0, 1}:
            raise DamiaAPIError('Параметр роль должен принимать одно из двух значений 0 или 1')

        self._validate_date("from_date", from_date)
        self._validate_date("to_date", to_date)

        return self._get(method='zakupki', params={'inn': inn, 'fz': fz, 'role': role,'from_date': from_date, 'to_date': to_date, 'format': format})


    def get_zsearch(self, q: str, region: str | None = None, okpd: str | None = None, cust_inn: str | None = None,
                    status: str | None = None, min_price: int | None = None, max_price: int | None = None, smp: int=2,
                    from_date: str | None = None, to_date: str | None = None,
                    placing: str='1,2,3,4,5,99', etp: str='1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,99', fz: int | None = None, page: int=1):

        if not q or not q.strip():
            raise DamiaAPIError('Обязательно укажите список ключевых слов и словосочетаний, разделенных запятыми')

        if region is not None and not region.strip():
            raise DamiaAPIError('Обязательно укажите код региона поставки в соответствии кодами субъектов РФ')

        if okpd is not None and not okpd.strip():
            raise DamiaAPIError('Обязательно укажите ОКПД поставляемой продукции (в соответствии с кодификатором ОКПД2). Для закупок по ФЗ-223 возможно указание ОКДП')

        if status is not None and status not in {'1', '2', '3', '4'}:
            raise DamiaAPIError('Этап закупки должен принимать одно из следующих значений: 1, 2, 3, 4')

        if cust_inn is not None:
            self._validate_inn(cust_inn)

        if min_price is not None and max_price is not None and min_price > max_price:
            raise DamiaAPIError("min_price не может быть больше max_price")

        if fz is not None and fz not in {44, 223, 615}:
            raise DamiaAPIError('ФЗ, по которому могут быть заключены контракты: 44, 223 или 615 по ПП РФ')

        if page < 1:
            raise DamiaAPIError("page должен быть >= 1")

        self._validate_date("from_date", from_date)
        self._validate_date("to_date", to_date)

        # возможно стоит выбрать значение по умолчанию для placing и etp как все кода, указанные в документации
        return  self._get(method='zsearch', params={'q': q, 'region': region, 'okpd': okpd, 'status': status, 'cust_inn': cust_inn,
                                                    'min_price': min_price, 'max_price': max_price, 'smp': smp, 'from_date': from_date,
                                                    'to_date': to_date, 'placing': placing, 'etp': etp, 'fz': fz, 'page': page})

    def get_customer(self, req: str):
        self._validate_req(req)

        return self._get(method='customer', params={'req': req})


    def get_eruz(self, req: str):
        self._validate_req(req)

        return self._get(method='eruz', params={'req': req})


    def get_zfas(self, inn: str, page: int=1):
        self._validate_inn(inn)

        return self._get(method='zfas', params={'inn': inn, 'page': page})


    def get_rnp(self, inn: str):
        self._validate_inn(inn)

        return self._get(method='rnp', params={'inn': inn})


    def get_sro(self, req: str):
        self._validate_req(req)

        return self._get(method='sro', params={'req': req})


    # def get_zmon(self, ): - данный метод необходим для мониторинга закупок с помощью рассылок на электронную почту, для агента скорее всего не нужен

    @staticmethod
    def _validate_date(name: str, value: str | None):
        if value is None:
            return
        try:
            dt.date.fromisoformat(value)  # строго YYYY-MM-DD
        except ValueError:
            raise DamiaAPIError(f"{name} должен быть в формате YYYY-MM-DD")


    @staticmethod
    def _validate_inn(inn: str):
        if not inn or not inn.strip():
            raise DamiaAPIError('ИНН - обязательный параметр')


    @staticmethod
    def _validate_fz(fz: str):
        if fz not in {'44', '223', '615'}:
            raise DamiaAPIError('ФЗ, по которому могут быть заключены контракты: 44, 223 или 615 по ПП РФ')


    @staticmethod
    def _validate_req(req: str):
        if not req or not req.strip():
            raise DamiaAPIError('Обязательный параметр ИНН или ОГРН заказчика')