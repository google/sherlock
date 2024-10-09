# Sherlock: Automated Perfetto Traces Capture and Analysis for Android

Sherlock is a command-line tool designed to simplify the process of capturing and analyzing Perfetto traces on Android devices. This information can be helpful to understand if your device has behaved in an unusual manner, which could indicate that an attempt has been made to exploit it. Sherlock is intended to be used by individuals to monitor their own device, who are able to interpret the data obtained or pass it to a suitably-qualified person. It does not necessarily produce an absolute determination.

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).

Sherlock offers two primary modes of operation:

**1. Device Manager Mode:**

* Automatically detects and monitors connected Android devices.
* Captures Perfetto traces based on a specified configuration file.
* Handles trace collection and storage.

**2. Traces Analysis Mode:**

* Performs various types of analysis on collected trace files. The system can be
  extended by adding/implementing additional analysis modules.

## Installation

```bash
# Clone the repository
git clone [URL]

# Navigate to the project directory
cd sherlock

# Install dependencies (replace with your preferred method)
pip install -r requirements.txt
```

### Configuring Chrome

To use Chrome's Perfetto support, it is necessary to provide some configuration
options. Ensure that Developer Mode is enabled on your Android device, and then
you will need to provide a command-line parameter to Chrome. This is done by creating a file `/data/local/tmp/chrome-command-line` on your Android device with the following contents:
```
chrome --js-flags=--perfetto_code_logger
```
Note that on a non-rooted device, it is necessary to turn on an additional setting so Chrome will process these flags. In Chrome on the Android device, go to chrome://flags and search for enable-command-line-on-non-rooted-devices. You need to enable this setting.

Then restart Chrome completely, and check whether the command-line flags have been processed by browsing to chrome://version and looking to see if they are present in the `Command Line` section.

## Usage

Sherlock provides two subcommands: `device-manager` and `trace-analysis`.

### Device Manager Mode

This mode allows you to automatically detect and start monitoring on connected Android devices, capturing Perfetto traces based on a configuration file.

#### Arguments
* `-c`, `--perfetto-config-file`: **[Required]** Path to the Perfetto configuration file. This file defines the categories and buffers to be traced. See the Perfetto documentation for more information on creating configuration files.
* `--traces-directory`: **[Required]** Directory to store captured trace files. Sherlock will create this directory if it doesn't exist.
* `--operation`: **[Required]** Specifies how connected devices should be handled. Available options:
  * `TERMINATE_COLLECT`: Terminate any `perfetto` tracing session and collect the trace files.
  * `TERMINATE_COLLECT_RESTART`: Terminate any `perfetto` tracing session and collect the trace files and launch a new `perfetto` tracing session.
* `-v`, `--verbose`: **[Optional]** Enable verbose logging to see detailed debugging information.

```bash
python sherlock.py device-manager --perfetto-config-file <perfetto_config_file> --traces-directory <traces_directory> --operation <operation_mode> [-v]
```

#### Generating configuration
To generate a binary protobuf, review the full instructions [here](https://perfetto.dev/docs/concepts/config#pbtx-vs-binary-format), and follow these steps:
1. Download the protobuf release for your operating system and architecture from https://github.com/protocolbuffers/protobuf/releases
2. Extract this into a directory, e.g. `protoc`. You should have a bin directory containing the protoc executable, along with an `include` directory
3. Check-out a copy of the Android source code, or more-easily, download the perfetto_config.proto file from here, for example on a Linux system:
```commandline
$ wget -O- "https://android.googlesource.com/platform/external/perfetto/+/refs/heads/main/protos/perfetto/config/perfetto_config.proto?format=TEXT" | base64 -d > perfetto_config.proto
```
4. Run the following command to convert the text proto `log_chrome_url.textproto` file into the binary form in `log_chrome_url.bin`:
```commandline
$ ./protoc/bin/protoc --encode=perfetto.protos.TraceConfig -I. perfetto_config.proto < log_chrome_url.textproto > log_chrome_url.bin
```
The binary configuration file is then given to the sherlock tool (`--perfetto-config-file` option).

### Trace Analysis Mode

This mode allows you to perform various analyses on the captured trace files.

#### Arguments:
* `--traces-directory`: **[Required]** Directory containing the trace files to analyze.
* `--module`: **[Required]**  Type of analysis to perform. You can specify multiple modules. Available options:
  * `ANALYSIS_ALL`: Perform all available analyses.
  * `ANALYSIS_URL`: Extract all the URLs visited with Chrome.
* `-s`, `--serial`: **[Optional]** Serial number(s) of the device(s) to analyze. If not provided, Sherlock will analyze traces from all devices found in the `traces-directory`.
* `-v`, `--verbose`: **[Optional]** Enable verbose logging.

```bash
python sherlock.py trace-analysis --traces-directory <traces_directory> --module <analysis_module> [--serial <serial_number>] [-v]
```
