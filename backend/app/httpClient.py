from aiohttp import ClientSession

class httpClientSession():
    def __init__(self, baseUrl: str, apiAuth: str, apiKey: str):
        self._session = ClientSession(
            base_url = baseUrl,
            headers={
                apiAuth : apiKey
            }
        )

#Здесь есть зазор на дальнейшее наследование класса конкретного апи клиента 
# #на основании данного класса клиента
