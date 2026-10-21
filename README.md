[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.md)
[![pl](https://img.shields.io/badge/lang-pl-yellow.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.pl.md)

# hacs_nexo – Unofficial Home Assistant Integration for Nexwell/Nexo System

**Simple, unofficial integration for exposing devices managed by the Nexwell/Nexo system via the Multimedia Card.**

## Supported Features


This integration currently supports:

- **Lights and LEDs** – On/Off and brightness for dimmable resources
- **Dimmers and lighting groups** – Brightness, including LED groups
- **Switches and output groups** – On/Off
- **Binary Sensors** – On/Off  
- **Analog Sensors**
- **Blinds** – Open / Close / Stop / Set Position
- **Temperature**
- **Thermostats**  
- **Gates**  
- **Alarm Partitions**
- **Local weather station** – Temperature, wind and light observations
- **External commands** – Buttons for Nexo automations

### External command buttons

Commands announced by the bridge are added automatically, including commands
received after startup. To add command names manually, open the Nexo integration's
**Configure** dialog and enter comma separated names under **External commands**.
Saving options reloads that integration entry. Each button targets its own bridge
and uses the current connection after reconnecting.

### Local weather

Weather observations come from the multimedia card's `set_weather` messages.
The weather entity becomes available when the station reports observations.
Temperature is reported in °C and wind speed in m/s, with unit conversion handled
by Home Assistant. No external forecast service is required.


## Installation

To install the integration:

1. **Copy the `nexo` folder** into your Home Assistant `custom_components` directory.

   ![Folder structure](img/folder_structure.jpg)

2. **Restart Home Assistant.**
3. Go to **Settings → Add Integration → nexo**.

   ![Add integration](img/add_integration.jpg)

4. **Enter the IP address** of your Nexwell Multimedia Card.

   ![Configuration wizard](img/config_wizard.jpg)
   
5. **You're all set! Enjoy your integration.**

   ![Enjoy](img/enjoy.jpg)

    
## License

This project is licensed under the [Apache 2.0 License](https://github.com/lzelazny/hacs_nexo/blob/main/LICENSE).

