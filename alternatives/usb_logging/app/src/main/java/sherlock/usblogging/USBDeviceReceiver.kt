/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package sherlock.usblogging

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import android.util.Log
import com.google.protobuf.timestamp
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.text.SimpleDateFormat
import java.time.Instant
import java.util.Locale
import usb.UsbDeviceLog.USBDeviceEvent
import usb.UsbDeviceLog.USBDeviceInfo

class USBDeviceReceiver : BroadcastReceiver() {

  override fun onReceive(context: Context, intent: Intent) {
    val logsDir = File(context.filesDir, LOGS_DIRNAME)
    if (!logsDir.exists()) {
      if (!logsDir.mkdirs()) {
        Log.e(TAG, "Cannot create: $LOGS_DIRNAME")
      }
    }

    when (intent.action) {
      UsbManager.ACTION_USB_DEVICE_ATTACHED -> {
        // API >= 33 as intent.getParcelableExtra(UsbManager.EXTRA_DEVICE) is deprecated
        val device: UsbDevice? = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
        if (device != null) {
          val timestamp = Instant.now().toEpochMilli()
          writeUsbEventToAsciiFile(context, "Attached", device, timestamp)
          writeUsbEventToProtoFile(
            context,
            USBDeviceEvent.EventType.USB_DEVICE_ATTACHED,
            device,
            timestamp,
          )
        }
      }
      UsbManager.ACTION_USB_DEVICE_DETACHED -> {
        val device: UsbDevice? = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
        if (device != null) {
          val timestamp = Instant.now().toEpochMilli()
          writeUsbEventToAsciiFile(context, "Detached", device, timestamp)
          writeUsbEventToProtoFile(
            context,
            USBDeviceEvent.EventType.USB_DEVICE_DETACHED,
            device,
            timestamp,
          )
        }
      }
    }
  }

  private fun getOrCreateLogsDirectory(context: Context): File? {
    val logsDir = File(context.filesDir, LOGS_DIRNAME)

    if (!logsDir.exists()) {
      Log.d(TAG, "Logs directory does not exist. Attempting to create: ${logsDir.absolutePath}")
      if (!logsDir.mkdirs()) {
        Log.e(TAG, "Failed to create logs directory: ${logsDir.absolutePath}")
        return null
      }
      Log.d(TAG, "Logs directory created successfully: ${logsDir.absolutePath}")
    } else if (!logsDir.isDirectory) {
      Log.e(TAG, "Path exists but is not a directory: ${logsDir.absolutePath}")
      return null
    }

    return logsDir
  }

  private fun writeUsbEventToAsciiFile(
    context: Context,
    action: String,
    device: UsbDevice?,
    timestamp: Long,
  ) {
    Log.d(TAG, "writeUsbDetailsToAsciiFile()  -  ${action}  -  ${device}")

    val logsDir = getOrCreateLogsDirectory(context) ?: return

    try {
      val timestampStr =
        SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(timestamp)
      val file = File(logsDir, USB_DEVICES_EVENTS_ASCII_FILENAME)

      file.appendText("$timestampStr - USB Device $action:\n")

      if (device == null) { // Handle detached or permission denied
        file.appendText("  No USB device details available.\n")
      } else {
        file.appendText("  Device ID: ${device.deviceId}\n")
        file.appendText("  Product ID: ${device.productId}\n")
        file.appendText("  Vendor ID: ${device.vendorId}\n")
        file.appendText("  Class: ${device.deviceClass}\n")
        file.appendText("  Subclass: ${device.deviceSubclass}\n")
        file.appendText("  Protocol: ${device.deviceProtocol}\n")
        file.appendText("  Device Name: ${device.deviceName}\n")
        file.appendText("  Manufacturer Name: ${device.manufacturerName}\n")
        file.appendText("  Product Name: ${device.productName}\n")
        file.appendText("  --------------------\n")
      }
    } catch (e: Exception) {
      Log.e(TAG, "Error writing USB event to file: ${e.message}")
    }
  }

  private fun writeUsbEventToProtoFile(
    context: Context,
    event: USBDeviceEvent.EventType,
    device: UsbDevice?,
    timestamp: Long,
  ) {
    Log.d(TAG, "writeUsbDetailsToProtoFile()  -  ${event.toString()}  -  ${device}")

    val logsDir = getOrCreateLogsDirectory(context) ?: return

    try {
      val file = File(logsDir, USB_DEVICES_EVENTS_FILENAME)

      val usbEventBuilder = USBDeviceEvent.newBuilder()
      usbEventBuilder.setTimestamp(timestamp)
      usbEventBuilder.setEventType(event)

      val usbDeviceInfoBuilder = USBDeviceInfo.newBuilder()
      device?.let { device ->
        usbDeviceInfoBuilder.apply {
          setDeviceId(device.deviceId)
          setProductId(device.productId)
          setVendorId(device.vendorId)
          setDeviceClass(device.deviceClass)
          setDeviceSubclass(device.deviceSubclass)
          setDeviceProtocol(device.deviceProtocol)
          setDeviceName(device.deviceName)
          setManufacturerName(device.manufacturerName)
          setProductName(device.productName)
        }
      }
      usbEventBuilder.setUsbDeviceInfo(usbDeviceInfoBuilder.build())
      val usbEvent = usbEventBuilder.build()
      file.appendBytes(
        usbEvent.toByteArray().let { byteArray ->
          ByteBuffer.allocate(PROTO_SIZE_PREFIX_BYTES + byteArray.size)
            .apply {
              order(ByteOrder.LITTLE_ENDIAN)
              putInt(byteArray.size)
              put(byteArray)
            }
            .array()
        }
      )
    } catch (e: Exception) {
      Log.e(TAG, "Error writing USB event to file: ${e.message}")
    }
  }

  private companion object {
    const val TAG = "USBDeviceReceiver"
    const val LOGS_DIRNAME = "Logs"
    const val USB_DEVICES_EVENTS_ASCII_FILENAME = "usb_device_events.txt"
    const val USB_DEVICES_EVENTS_FILENAME = "usb_device_events.pb"
    const val PROTO_SIZE_PREFIX_BYTES = 4
  }
}
