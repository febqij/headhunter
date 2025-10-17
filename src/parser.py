class HHParser:
    def __init__(self, base_url, params):
        self.base_url = base_url
        self.params = params  # area, per_page, etc.
        self.session = requests.Session()  # переиспользование соединения
    
    def fetch_vacancies(self, page=0):
        """Получает страницу вакансий с обработкой ошибок"""
        try:
            response = self.session.get(url, params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Обработка 429 (rate limit), 500, 503
        except requests.exceptions.ConnectionError:
            # Обработка сетевых ошибок
        except requests.exceptions.Timeout:
            # Обработка таймаутов
    
    def parse_all_pages(self):
        """Итерация по всем страницам с учетом лимитов API"""
        # Учет ограничения 2000 вакансий
        # Добавление time.sleep(0.2) между запросами
