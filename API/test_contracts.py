from damia_client import DamiaClient

API_KEY = "Твой ключ"

client = DamiaClient(api_key=API_KEY)

data = client.get_contracts(
    inn="7803046541",
    fz="44",
    role=0,
    from_date="2024-01-01",
    to_date="2024-12-31",
    format=1
)

print(data)
