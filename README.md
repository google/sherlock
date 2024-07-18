# Sherlock

Sherlock is a tool that will help you to investigate and find potential attack by using [Perfetto](https://perfetto.dev/) traces, for Android devices (non userdebug).

You can use it in different ways:
   * run automatically Perfetto in the background and use normally the device
   * fetch the Perfetto traces later or live, and analyse the results

## Requirements

In order to generate the traces, you will need few requirements:
  * Python 3.X
  * enable Developer Mode on your phone
  * a Chrome version >= 124.0.6367.54


You will need to provide a command line for chrome by creating and editing the file '/data/local/tmp/chrome-command-line'
```sh
chrome --js-flags=--perfetto_code_logger --disable-fre --no-default-browser-check --no-first-run
```

Moreover in Chrome you will need few extra steps, via chrome://flags, and enable the following options:
  * 'Enable Perfetto system tracing'
  * 'Enable command line on non-rooted devices'


We are prodiving a binary version of the configuration as the v8 support is not fully supported in the configuration.

Download the protobuf release for your operating system and architecture from https://github.com/protocolbuffers/protobuf/releases
Extract this into a directory, e.g. protoc.  You should have a bin directory containing the protoc executable, along with an include directory
Check-out a copy of the Android source code, or more-easily, download the perfetto_config.proto file from here, for example on a Linux system:

```sh
wget -O- "https://android.googlesource.com/platform/external/perfetto/+/refs/heads/main/protos/perfetto/config/perfetto_config.proto?format=TEXT" | base64 -d > data/perfetto_config.proto
```

And you can generate yourself a version by using this command line:
```sh
protoc --encode=perfetto.protos.TraceConfig -I. data/perfetto_config.proto < data/log_sherlock.yaml > data/log_sherlock.bin
```

## Installation

```sh
git clone 
cd sherlock
pip3 install -e .
```

## Usage