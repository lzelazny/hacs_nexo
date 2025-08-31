[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.md)
[![pl](https://img.shields.io/badge/lang-pl-yellow.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.pl.md)

# hacs_nexo – Nieoficjalna integracja Nexwell/Nexo dla Home Assistant

**Nieoficjalna integracja umożliwiająca udostępnienie urządzeń zarządzanych przez system Nexwell/Nexo za pośrednictwem Karty Multimedialnej.**

## Obsługiwane zasoby:

- **Oświetlenie** – Włącz / Wyłącz  
- **Przełączniki** – Włącz / Wyłącz  
- **Czujniki binarne** – Włącz / Wyłącz  
- **Czujniki analogowe**  
- **Rolety** – Otwórz / Zamknij / Zatrzymaj / Ustaw pozycję  
- **Temperatura**  
- **Termostaty**  
- **Bramy**  
- **Strefy alarmowe**  
- **Ściemniacze** - Włącz / Wyłącz / Ustaw jasność
- **LED**  - Włącz / Wyłącz / Ustaw jasność
- **Grupy Ściemniaczy, LEDów**  - Włącz / Wyłącz / Ustaw jasność
- **Grupy Przełączników**  - Włącz / Wyłącz
- **Stacja pogodowa** - Temperatura, Wiatr, Piktogram pogody, Kierunek wiatru, Kierunek światła, Prognoza z Open-Meteo

## TO DO:
- **Grupy Rolet** – Otwórz / Zamknij / Zatrzymaj / Ustaw pozycję 

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
