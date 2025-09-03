[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.md)
[![pl](https://img.shields.io/badge/lang-pl-yellow.svg)](https://github.com/lzelazny/hacs_nexo/blob/main/README.pl.md)

# hacs_nexo – Unofficial Home Assistant Integration for Nexwell/Nexo System

**Simple, unofficial integration for exposing devices managed by the Nexwell/Nexo system via the Multimedia Card.**

## Supported Features

This integration currently supports:

- **Lights** – On/Off  
- **Switches** – On/Off  
- **Binary Sensors** – On/Off  
- **Analog Sensors**
- **Blinds** – Open / Close / Stop / Set Position
- **Temperature**
- **Thermostats**  
- **Gates**  
- **Alarm Partitions**
- **Dimmers** - On/Off / Brightness
- **LED** - On/Off / Brightness
- **Dimmers, LED Groups** - On/Off / Brightness
- **Switches Groups**  - On/Off
- **Blinds Groups** – Open / Close / Stop / Set Position 
- **Weather station** - Temperature, Wind, Weather pictogram, Wind direction, Light direction, Forecast from Open-Meteo
- **Ext commands**


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


## Ext commands - how to

If you use command-triggered automation in Nexo, you can use these commands in HA in three ways (example command "gateway"):

1. Service

   **Developer tools → Actions:** > action: **nexo.send_ext_command** > cmd **gateway**

2. Entity Button

   **Add to dashboard** > by entity > entity **gateway** > **Continue
   **Add to dashboard** > by card > **Button** > entity **gateway** > Interactions > Perform action > action: **nexo.send_ext_command** > cmd **gateway** > **Save**

   After clicking it sends {"type":"ext_command","cmd":"gateway"}.

   In order for the entity with the command to be displayed, the list of commands must be manually entered in configuration.yaml at the root level (just like automation: etc.): #unfortunately, I cannot download them automatically - TO DO

```
nexo:
  ext_commands:
    - gateway
    - door
    - any_command
```

3. Automation in YAML

```
alias: Open the gate at 7:00
trigger:
  - platform: time
    at: "07:00:00"
action:
  - service: nexo.send_ext_command
    data:
      cmd: brama
```

    
## License

This project is licensed under the [Apache 2.0 License](https://github.com/lzelazny/hacs_nexo/blob/main/LICENSE).

