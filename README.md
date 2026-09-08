# Photo Booth

Een kleine lokale photobooth-webapp die via Flask draait en een GoPro HERO12 Black via USB-C gebruikt als primaire camera.

## Laptop development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open vervolgens:

```text
http://localhost:8000
```

Op macOS en Windows gebruikt de development-configuratie automatisch de lokale
laptopwebcam als er geen andere camera beschikbaar is. Op Linux staat deze
fallback standaard uit: daar gebruikt de app alleen een V4L2-device, zoals de
GoPro via USB-C.

## Controleer beschikbare video-apparaten op Linux

Voor een GoPro over USB-C is Linux vaak zichtbaar als een V4L2-video apparaat, bijvoorbeeld `/dev/video0`, `/dev/video1`, etc.

```bash
ls /dev/video*
```

Of:

```bash
v4l2-ctl --list-devices
```

Als de GoPro in USB Connected staat, is hij meestal direct als video source beschikbaar.

## Camera selectie

In `config.py` kun je de camera instellen:

```python
CAMERA_DEVICE = "auto"
```

Je kunt de lokale webcamfallback ook expliciet instellen met een environment
variable:

```bash
ALLOW_LOCAL_WEBCAM_FALLBACK=1 python3 app.py
```

Gebruik op de Linux photobooth-pc juist:

```bash
ALLOW_LOCAL_WEBCAM_FALLBACK=0 python3 app.py
```

Of handmatig:

```python
CAMERA_DEVICE = 0
```

of:

```python
CAMERA_DEVICE = "/dev/video0"
```

De camera detectie probeert automatisch de juiste V4L2-device te vinden. De app gebruikt geen verzonnen GoPro API; het werkt met OpenCV + standaard Linux video-devices.

## Test mode

In `config.py` staat standaard:

```python
TEST_MODE = True
```

Wanneer test mode actief is, wordt de printer niet gebruikt. De uiteindelijke stripafbeelding wordt opgeslagen in:

```text
output/
```

Voorbeeld:

```text
output/photobooth_2026-09-07_123456.jpg
```

## Production Ubuntu photobooth

Op de Ubuntu photobooth-pc:

1. Python installeren
2. dependencies installeren
3. GoPro via USB-C aansluiten
4. controleren of Linux de GoPro als video device ziet
5. `TEST_MODE = False` zetten in `config.py`
6. CUPS en printer controleren
7. Flask app starten
8. Chromium in kiosk-mode openen naar `http://localhost:8000`

## DNP printer

De productieprinter is:

```text
DNP-DSRX1
```

De printopdracht gebruikt de CUPS-parameters:

```text
PageSize=w288h432-div2
ColorModel=CMYK
StpImageType=Photo
Resolution=300dpi
StpLaminate=Glossy
```

## Kiosk

Voor een fullscreen Chromium kiosk:

```bash
chromium --kiosk --disable-infobars --noerrdialogs --incognito http://localhost:8000
```

## Systemd example

Maak `/etc/systemd/system/photobooth.service`:

```ini
[Unit]
Description=Photobooth
After=network.target

[Service]
WorkingDirectory=/path/to/photobooth
ExecStart=/path/to/photobooth/venv/bin/python /path/to/photobooth/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Gebruik daarna:

```bash
sudo systemctl daemon-reload
sudo systemctl enable photobooth
sudo systemctl start photobooth
```

## Flow

1. Live camera blijft zichtbaar
2. Gebruiker tikt op het scherm
3. Countdown 3, 2, 1
5. Drie foto’s worden gemaakt
6. Eén PhotoCard met de drie foto’s wordt gegenereerd
7. In test mode wordt de output in `output/` opgeslagen
8. Wanneer `TEST_MODE = False` wordt de PhotoCard naar de printer gestuurd
8. App keert terug naar de live camera

## Foutafhandeling

Als geen camera gevonden wordt, toont de app een duidelijke melding:

```text
Camera niet gevonden.
Controleer of de GoPro via USB is aangesloten en USB Connected toont.
```

## Config

Belangrijkste instellingen staan in `config.py`:

```python
TEST_MODE = True
CAMERA_DEVICE = "auto"
PRINTER_NAME = "DNP-DSRX1"
PRIMARY_BLUE = "#02559F"
STRIP_TITLE_TOP = "60 Jaar"
STRIP_TITLE_BOTTOM = "FOS 207"
```
