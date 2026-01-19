from API.damia_client import DamiaClient
from analytics.normalize_contracts import normalize_contracts_format1

client = DamiaClient(api_key="4bc605c8ceb52ecf5cd4bdac80f0859f38ab0165")

raw = client.get_contracts(
    inn="7803046541",
    fz="44",
    role=0,
    from_date="2024-01-01",
    to_date="2024-12-31",
    format=1
)

records = normalize_contracts_format1(raw)

print("Всего строк:", len(records))
print("Первая строка:", records[0])

