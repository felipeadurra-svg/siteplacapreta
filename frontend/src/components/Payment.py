import mercadopago

sdk = mercadopago.SDK("APP_USR-8540820157639220-031816-b9cd7ef61039410acb9bfff199a3b48c-3275856453")

def gerar_preferencia_laudo():
    preference_data = {
        "items": [
            {
                "title": "Relatório Técnico - Veículo Antigo",
                "quantity": 1,
                "unit_price": 100.00, # Valor de exemplo
                "currency_id": "BRL"
            }
        ],
        "back_urls": {
            "success": "https://meucarroantigo.com/sucesso",
            "failure": "https://meucarroantigo.com/erro",
            "pending": "https://meucarroantigo.com/pendente"
        },
        "auto_return": "approved",
    }
    
    result = sdk.preference().create(preference_data)
    return result["response"]["id"] # Retorna o ID para o Frontend