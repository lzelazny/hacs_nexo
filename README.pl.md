[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.md)
[![pl](https://img.shields.io/badge/lang-pl-yellow.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.pl.md)

# hacs_nexo – Nieoficjalna integracja Nexwell/Nexo dla Home Assistant

**Nieoficjalna integracja umożliwiająca udostępnienie urządzeń zarządzanych przez system Nexwell/Nexo za pośrednictwem Karty Multimedialnej.**

## Obsługiwane zasoby:

- **Oświetlenie i LED** – Włącz / Wyłącz oraz jasność zasobów ściemnianych
- **Ściemniacze i grupy oświetlenia** – Regulacja jasności, także grup LED
- **Przełączniki i grupy wyjść** – Włącz / Wyłącz
- **Czujniki binarne** – Włącz / Wyłącz  
- **Czujniki analogowe**  
- **Rolety** – Otwórz / Zamknij / Zatrzymaj / Ustaw pozycję  
- **Temperatura**  
- **Termostaty**  
- **Bramy**  
- **Strefy alarmowe**  
- **Lokalna stacja pogodowa** – Temperatura, wiatr i pomiary światła
- **Komendy zewnętrzne** – Przyciski uruchamiające automatykę Nexo

### Przyciski komend

Komendy zgłaszane przez mostek są dodawane automatycznie, również po uruchomieniu
integracji. Aby podać nazwy ręcznie, otwórz **Konfiguruj** w integracji Nexo i wpisz
nazwy oddzielone przecinkami w polu **External commands**. Zapis opcji przeładowuje
dany wpis integracji. Przyciski korzystają z aktualnego połączenia swojego mostka.

### Pogoda lokalna

Dane pochodzą z komunikatów `set_weather` Karty Multimedialnej. Encja pogody staje
się dostępna po otrzymaniu pomiarów. Temperatura jest przekazywana w °C, a prędkość
wiatru w m/s; Home Assistant przelicza jednostki zgodnie z ustawieniami.
Zewnętrzna usługa prognozy nie jest wymagana.

## Instalacja

Aby zainstalować integrację:

1. **Skopiuj folder `nexo`** do katalogu `custom_components` w Home Assistant.

   ![Struktura folderów](img/folder_structure.jpg)

2. **Zrestartuj Home Assistant.**  
3. Przejdź do **Ustawienia → Dodaj integrację → nexo**.

   ![Dodaj integrację](img/add_integration.jpg)

4. **Wprowadź adres IP** Karty Multimedialnej Nexwell.

   ![Kreator konfiguracji](img/config_wizard.jpg)

5. **Gotowe! Ciesz się integracją.**

   ![Ciesz się](img/enjoy.jpg)

## Licencja

Projekt jest objęty licencją [Apache 2.0 License](https://github.com/lzelazny/hacs_nexo/blob/main/LICENSE).
