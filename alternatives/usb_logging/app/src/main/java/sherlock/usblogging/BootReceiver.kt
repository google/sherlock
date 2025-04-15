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
import android.util.Log
import boot.BootLog.BootEvent
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.text.SimpleDateFormat
import java.time.Instant
import java.util.Locale

class BootReceiver : BroadcastReceiver() {

  override fun onReceive(context: Context, intent: Intent) {
    if (intent.action == Intent.ACTION_BOOT_COMPLETED) {

      val logsDir = File(context.filesDir, LOGS_DIRNAME)
      if (!logsDir.exists()) {
        if (!logsDir.mkdirs()) {
          Log.e(TAG, "Cannot create: $LOGS_DIRNAME")
        }
      }

      try {
        val timestamp = Instant.now().toEpochMilli()
        appendTimestampToAsciiFile(context, timestamp)
        appendTimestampToProtoFile(context, timestamp)
      } catch (e: Exception) {
        Log.e(TAG, "Error writing boot event to file: ${e.message}")
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

  private fun appendTimestampToAsciiFile(context: Context, timestamp: Long) {
    Log.d(TAG, "appendTimestampToAsciiFile()  -  ${timestamp}")

    val logsDir = getOrCreateLogsDirectory(context) ?: return

    try {
      val timestampStr =
        SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(timestamp)
      val file = File(logsDir, BOOT_EVENTS_ASCII_FILENAME)

      file.appendText("Boot at $timestampStr\n")
    } catch (e: Exception) {
      Log.e(TAG, "Error writing BOOT event to file: ${e.message}")
    }
  }

  private fun appendTimestampToProtoFile(context: Context, timestamp: Long) {
    Log.d(TAG, "appendTimestampToProtoFile()  -  ${timestamp}")

    val logsDir = getOrCreateLogsDirectory(context) ?: return

    try {
      val file = File(logsDir, BOOT_EVENTS_PROTO_FILENAME)
      val bootEvent = BootEvent.newBuilder().setTimestamp(timestamp).build()
      file.appendBytes(
        bootEvent.toByteArray().let { byteArray ->
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
      Log.e(TAG, "Error writing BOOT event to file: ${e.message}")
    }
  }

  private companion object {
    const val TAG = "BootReceiver"
    const val LOGS_DIRNAME = "Logs"
    const val BOOT_EVENTS_ASCII_FILENAME = "boot_events.txt"
    const val BOOT_EVENTS_PROTO_FILENAME = "boot_events.pb"
    const val PROTO_SIZE_PREFIX_BYTES = 4
  }
}
