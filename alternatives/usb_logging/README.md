# USB Logging for Android

`USBLogging` application provides a straightforward way to monitor devices
connected to your Android phone's USB port (Host mode). It is designed to work
across various Android versions. While Android 14+ offers advanced system
tracing solutions with `Perfetto`, which can provide detailed USB information as
part of broader diagnostics, `USBLogging` serves as a simpler, dedicated
alternative focused specifically on recording connected USB peripherals.

## Features

* **Detects Connected Devices:** Automatically records USB devices when they
are plugged into and unplugged from the phone's USB port
* **Displays Device Information:** Shows basic details for each detected device,
such as:
    * Device Id
    * Product Id
    * Vendor Id
    * Device Class
    * Device Subclass
    * Device Protocol
    * Device Name
    * Manufacturer Name
    * Product Name
* **Records Last Boot Time:** Detects and stores the timestamp of the last time
the device has booted. (Note: This requires the app to have been installed
*before* the relevant boot occurred, as it relies on receiving the system's
boot completion signal).
* **Exports Logs:** Allows exporting the recorded USB connection, disconnection,
and device information events to a file. The log files are generated using the
**Protocol Buffers (Protobuf)** message format, enabling structured data
logging.
* **Clear Logs:** Provides a simple one-button option to delete the existing log
files, offering a quick way to clear previous records.

## Building from Source

If you want to build the project yourself:

1.  **Clone:** Clone this repository
2.  **Open:** Open the cloned directory (`sherlock/alternatives/usb_logging`) in
    Android Studio (latest stable version recommended).
3.  **Sync:** Let Gradle sync the project dependencies.
4.  **Build:** Use `Build -> Make Project` or `Build -> Build Bundle(s) / APK(s) -> Build APK(s)`.
5.  **Run:** Run the app on a connected device or emulator using `Run -> Run 'app'`.

