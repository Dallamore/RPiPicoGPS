# Refactored Pico GPS logger with NMEA checksum validation (MicroPython)
from machine import Pin, UART, I2C, SPI
from micropython import const
from ssd1306 import SSD1306_I2C
import sdcard, os, time, machine

# ----- Configuration -----
I2C_SDA = 20
I2C_SCL = 21
OLED_WIDTH = 128
OLED_HEIGHT = 64

UART_ID = 1
UART_BAUD = 9600
UART_TX = 4
UART_RX = 5

SD_CS = 14
SPI_ID = 1
SPI_SCK = 10
SPI_MOSI = 11
SPI_MISO = 12
SPI_BAUD = 1_000_000

STEP_TIME = const(2)        # seconds to wait for a fix in get_gps
LED_PIN = 25

# If True, sentences without a checksum are rejected.
REQUIRE_CHECKSUM = True

# ----- Hardware init -----
i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
led = Pin(LED_PIN, Pin.OUT)
gps_uart = UART(UART_ID, baudrate=UART_BAUD, tx=Pin(UART_TX), rx=Pin(UART_RX))

# ----- Helpers -----
def safe_decode(raw):
    if not raw:
        return ""
    if isinstance(raw, bytes):
        try:
            return raw.decode('ascii', 'ignore').strip()
        except Exception:
            return ""
    return str(raw).strip()

def nmea_checksum_valid(line):
    """
    Validate NMEA sentence checksum.
    Returns True if valid, False otherwise.
    Accepts lines like:
      $GPGGA,....*47
    Ignores trailing CR/LF and whitespace.
    """
    if not line:
        return False
    # strip whitespace and CR/LF
    line = line.strip()
    if not line.startswith('$'):
        return False
    # find asterisk
    if '*' in line:
        try:
            star_idx = line.rfind('*')
            payload = line[1:star_idx]  # between $ and *
            checksum_str = line[star_idx+1:]
            # checksum may be followed by other chars (rare); take first two hex digits
            checksum_str = checksum_str[:2]
            # compute XOR of payload bytes
            cs = 0
            for ch in payload:
                cs ^= ord(ch)
            # compare hex (uppercase)
            expected = "{:02X}".format(cs)
            return expected == checksum_str.upper()
        except Exception:
            return False
    else:
        # no checksum present
        return not REQUIRE_CHECKSUM

def convert_to_degree(raw):
    try:
        rawf = float(raw)
    except Exception:
        return ""
    deg_part = int(rawf // 100)
    min_part = rawf - (deg_part * 100)
    deg = deg_part + min_part / 60.0
    return "{:.6f}".format(deg)

def mount_sd():
    """Attempt to mount SD; return True on success, False otherwise."""
    try:
        cs = machine.Pin(SD_CS, machine.Pin.OUT)
        spi = machine.SPI(SPI_ID,
                          baudrate=SPI_BAUD,
                          polarity=0,
                          phase=0,
                          sck=machine.Pin(SPI_SCK),
                          mosi=machine.Pin(SPI_MOSI),
                          miso=machine.Pin(SPI_MISO))
        sd = sdcard.SDCard(spi, cs)
        os.mount(sd, '/sd')
        print("SD mounted at /sd")
        return True
    except Exception as e:
        print("SD mount failed:", e)
        return False

def complete_files():
    """Close and rename any incomplete GPX files on the SD card."""
    try:
        for entry in os.ilistdir("/sd"):
            name, typ = entry[0], entry[1]
            if typ == 0x8000 and name.startswith("incomplete_") and name.endswith(".gpx"):
                path = "/sd/" + name
                try:
                    with open(path, "a") as f:
                        f.write("    </trkseg>\r\n  </trk>\r\n</gpx>")
                    new_name = name[len("incomplete_"):]
                    os.rename(path, "/sd/" + new_name)
                    print(name, "->", new_name)
                except Exception as e:
                    print("Failed to complete", name, e)
    except Exception as e:
        print("Complete files error:", e)
    time.sleep(1)

def create_gpx_header(gps_date, gps_time, time_ns):
    header = (
        '<?xml version="1.0" encoding="UTF-8"?>\r\n'
        '<gpx creator="Dallamore PicoGPS" version="1.1"\r\n'
        '  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/11.xsd"\r\n'
        '  xmlns:ns3="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"\r\n'
        '  xmlns="http://www.topografix.com/GPX/1/1"\r\n'
        '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns2="http://www.garmin.com/xmlschemas/GpxExtensions/v3">\r\n'
        '  <metadata>\r\n'
        '    <link href="connect.garmin.com">\r\n'
        '    <text>Dallamore PicoGPS</text>\r\n'
        '    </link>\r\n'
        '    <time>{}T{}.000Z</time>\r\n'
        '  </metadata>\r\n'
        '  <trk>\r\n'
        '    <name>{}T{}</name>\r\n'
        '    <type>walking</type>\r\n'
        '    <trkseg>\r\n'
    ).format(gps_date, gps_time, gps_date, gps_time, gps_date, gps_time)
    return header

def append_trackpoint(path, lat, lon, ele, gps_date, gps_time):
    tp = (
        '      <trkpt lat="{lat}" lon="{lon}">\r\n'
        '        <ele>{ele}</ele>\r\n'
        '        <time>{date}T{time}.000Z</time>\r\n'
        '      </trkpt>\r\n'
    ).format(lat=lat, lon=lon, ele=ele, date=gps_date, time=gps_time)
    try:
        with open(path, "a") as f:
            f.write(tp)
            f.flush()
        print("Written to", path)
        return True
    except Exception as e:
        print("Write failed:", e)
        return False

# ----- GPS parsing -----
def get_gps(uart, timeout_seconds=STEP_TIME):
    """
    Read NMEA lines until a valid GPGGA fix is found or timeout.
    Returns a dict with keys:
      { 'gps_date','gps_time','gps_time_ns','lat','lon','alt','sats' }
    or None on timeout/no valid fix.
    """
    deadline = time.time() + timeout_seconds
    gps_date = ""
    while time.time() < deadline:
        raw = uart.readline()
        if not raw:
            time.sleep(0.05)
            continue
        line = safe_decode(raw)
        if not line:
            continue
        # Validate checksum first
        if not nmea_checksum_valid(line):
            # invalid checksum; skip
            # print("Bad checksum:", line)
            continue
        parts = line.split(',')
        # GPRMC -> date field (index 9)
        if parts and parts[0].startswith("$GPRMC") and len(parts) > 9:
            date_field = parts[9]
            if date_field and len(date_field) >= 6:
                gps_date = "20{}-{}-{}".format(date_field[4:6], date_field[2:4], date_field[0:2])
        # GPGGA -> time, lat, lon, fix, sats, alt
        if parts and parts[0].startswith("$GPGGA"):
            if len(parts) >= 10:
                time_field = parts[1]
                lat_field = parts[2]
                lat_dir = parts[3] if len(parts) > 3 else ""
                lon_field = parts[4] if len(parts) > 4 else ""
                lon_dir = parts[5] if len(parts) > 5 else ""
                fix_field = parts[6] if len(parts) > 6 else ""
                sats_field = parts[7] if len(parts) > 7 else ""
                alt_field = parts[9] if len(parts) > 9 else ""
                if fix_field and fix_field != '0' and lat_field and lon_field:
                    lat = convert_to_degree(lat_field)
                    if lat_dir == 'S':
                        lat = "-" + lat
                    lon = convert_to_degree(lon_field)
                    if lon_dir == 'W':
                        lon = "-" + lon
                    gps_time = ""
                    gps_time_ns = ""
                    if len(time_field) >= 6:
                        gps_time = "{}:{}:{}".format(time_field[0:2], time_field[2:4], time_field[4:6])
                        gps_time_ns = time_field[0:6]
                    return {
                        'gps_date': gps_date,
                        'gps_time': gps_time,
                        'gps_time_ns': gps_time_ns,
                        'lat': lat,
                        'lon': lon,
                        'alt': alt_field,
                        'sats': sats_field
                    }
    # timeout
    return None

# ----- Display helpers -----
def show_message(line1="", line2="", line3="", line4=""):
    oled.fill(0)
    oled.text(line1, 0, 0)
    oled.text(line2, 0, 10)
    oled.text(line3, 0, 20)
    oled.text(line4, 0, 30)
    oled.show()

# ----- Main (local state only) -----
# Replace the main loop body with this version (only the loop part shown)
def main():
    sd_ready = mount_sd()
    show_message("Completing files", "")
    if sd_ready:
        complete_files()
    show_message("----------------------","Waiting for GPS", "----------------------")
    print("Starting main loop")

    file_path = ""          # current GPX file path
    gpstime_prev = ""       # previous GPS time string
    fix_count = 0

    # NEW: track last successful fix time and whether we've shown the warning
    last_fix_time = 0.0
    NO_GPS_THRESHOLD = 5.0   # seconds of no-fix before showing "No GPS data"
    no_gps_shown = False

    while True:
        led.off()
        if not sd_ready:
            show_message("No SD Card", "Restart required")
            print("No SD Card")
            time.sleep(2)
            sd_ready = mount_sd()
            continue

        parsed = get_gps(gps_uart, timeout_seconds=STEP_TIME)
        if parsed:
            # Unpack parsed data
            gps_date = parsed.get('gps_date', "")
            gps_time = parsed.get('gps_time', "")
            gps_time_ns = parsed.get('gps_time_ns', "")
            lat = parsed.get('lat', "")
            lon = parsed.get('lon', "")
            alt = parsed.get('alt', "")
            sats = parsed.get('sats', "")

            # Console
            print("----------------------")
            print('TimeStamp="{} {}" Lat="{}" Lon="{}" Alt="{}"'.format(
                gps_date or "----", gps_time or "----", lat or "----", lon or "----", alt or "----"))

            # OLED
            show_message("Time: " + (gps_time or "----"),
                         "Lat: " + (lat or "----"),
                         "Lng: " + (lon or "----"),
                         "Sats: " + (sats or "0"))

            # Save to SD
            led.on()
            if gps_date and len(gps_date) > 4:
                if not file_path:
                    file_path = "/sd/incomplete_{}{}.gpx".format(gps_date, gps_time_ns or "")
                    header = create_gpx_header(gps_date, gps_time, gps_time_ns)
                    try:
                        with open(file_path, "a") as f:
                            f.write(header)
                        print("New file:", file_path)
                    except Exception as e:
                        print("Failed to create file:", e)
                if file_path:
                    append_trackpoint(file_path, lat, lon, alt, gps_date, gps_time)

            # update previous time and counters
            print("{}  &  {}".format(gps_time or "", gpstime_prev or ""))
            gpstime_prev = gps_time
            fix_count = min(fix_count + 1, 9999)

            # update last_fix_time and clear any "no gps" warning
            last_fix_time = time.time()
            no_gps_shown = False

        else:
            # No valid fix within timeout
            now = time.time()
            # Only show the warning after a sustained gap
            if (now - last_fix_time) > NO_GPS_THRESHOLD:
                if not no_gps_shown:
                    print("----------------------")
                    print("No GPS data is found.")
                    oled.text("No GPS data.", 0, 40)
                    oled.show()
                    no_gps_shown = True
            # small delay before next attempt
            time.sleep(0.2)

# Run main
if __name__ == "__main__":
    main()
