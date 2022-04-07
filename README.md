# Switchbot-Plug-InfluxDB
Connects to SwitchBot Plugs over BLE to poll power consumption data and import it into InfluxDB.

## Setup

0. Setup bluetooth (install BlueZ and enable the drivers for your receiver. This varies greatly machine-to-machine)

1. Install Requirements with pip: `pip install -r requirements.txt`

2. Configure `.env` based on `.env.example` for your InfluxDB config

3. Configure `config.json` with your specific plug BLE MAC addresses and give them a name

This script will scan your plugs basically as fast as it can -- if you have a small number of plugs, you may want to add a delay.

### Docker Setup
Bluetooth on docker is finicky. The easiest setup is:
1. Ensure Bluetooth is stopped on the host machine, to allow for Docker to utilize it (bluetoothd shouldn't be running).
2. Build the Docker image as regular (`docker build -t switchbot .`)
3. Start the Docker image with privileges to manage Bluetooth (`docker run --rm --privileged --net=host -d switchbot`)

## Results

Imports a point into InfluxDB with the following data:

```json
{
    "fields": {
        "uptime": 100,    // today's uptime in minutes
        "voltage": 120.3, // voltage in V
        "current": 600,   // current in A
        "wattage": 10,    // watts in W
    },
    "tags": {
        "plug": "my-plug" // configured plug name in config.json
    }
}
```

## Troubleshooting
### Characteristic Cache
Sometimes the characteristic cache of a device will get corrupted and need to be reset. This can be seen in logs with repeated failures of:
```
Characteristic with UUID CBA20003-224D-11E6-9FB8-0002A5D5C51B could not be found!
```
See [here](https://bleak.readthedocs.io/en/latest/troubleshooting.html#id2) for more info
