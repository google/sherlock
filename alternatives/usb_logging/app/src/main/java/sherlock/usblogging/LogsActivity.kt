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

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileInputStream
import java.io.IOException

class LogsActivity : ComponentActivity() {

  private lateinit var fileContentTextView: TextView

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_log_list)

    val displayBootContentButton: Button = findViewById(R.id.displayBootContentButton)
    val displayUsbDevicesContentButton: Button = findViewById(R.id.displayUsbDevicesContentButton)
    val clearLogsButton: Button = findViewById(R.id.deleteLogsButton)
    val shareLogsButton: Button = findViewById(R.id.shareEventsLogsbutton)
    fileContentTextView = findViewById(R.id.logContentTextView)

    displayBootContentButton.setOnClickListener {
      readTimestampsFromAsciiFile(BOOT_EVENTS_ASCII_FILENAME)
    }
    displayUsbDevicesContentButton.setOnClickListener {
      displayLogsContent(USB_DEVICES_EVENTS_ASCII_FILENAME)
    }
    clearLogsButton.setOnClickListener {
      deleteLogFiles()
      fileContentTextView.text = "Log files deleted"
    }
    shareLogsButton.setOnClickListener { shareLogFiles() }
  }

  private fun displayLogsContent(fileName: String) {
    val logsDir = File(filesDir, LOGS_DIRNAME)
    if (!logsDir.exists()) {
      if (!logsDir.mkdirs()) {
        Log.e(TAG, "Cannot create: $LOGS_DIRNAME")
        return
      }
    }

    val file = File(logsDir, fileName)
    if (file.exists()) {
      fileContentTextView.text = ""
      try {
        val fileInputStream = FileInputStream(file)
        val buffer = ByteArray(file.length().toInt())
        fileInputStream.read(buffer)
        fileInputStream.close()

        val fileContent = String(buffer)
        fileContentTextView.text = fileContent
      } catch (e: IOException) {
        Log.e(TAG, "Error reading file: ${e.message}")
        fileContentTextView.text = "Error reading file."
      }
    } else {
      fileContentTextView.text = "File not found."
      Log.e(TAG, "File not found: $fileName")
    }
  }

  private fun readTimestampsFromAsciiFile(fileName: String) {
    val logsDir = File(filesDir, LOGS_DIRNAME)
    if (!logsDir.exists()) {
      if (!logsDir.mkdirs()) {
        Log.e(TAG, "Cannot create: $LOGS_DIRNAME")
        return
      }
    }

    val file = File(logsDir, fileName)
    if (file.exists()) {
      fileContentTextView.text = ""
      try {
        val fileInputStream = FileInputStream(file)
        val buffer = ByteArray(file.length().toInt())
        fileInputStream.read(buffer)
        fileInputStream.close()

        val fileContent = String(buffer)
        fileContentTextView.text = fileContent
      } catch (e: IOException) {
        Log.e(TAG, "Error reading file: ${e.message}")
        fileContentTextView.text = "Error reading file."
      }
    } else {
      fileContentTextView.text = "File not found."
      Log.e(TAG, "File not found: $fileName")
    }
  }

  private fun deleteLogFiles() {
    val logsDir = File(filesDir, LOGS_DIRNAME)
    val logFiles =
      listOf(
        USB_DEVICES_EVENTS_ASCII_FILENAME,
        USB_DEVICES_EVENTS_FILENAME,
        BOOT_EVENTS_ASCII_FILENAME,
        BOOT_EVENTS_PROTO_FILENAME,
      )

    if (logsDir.exists() && logsDir.isDirectory) {
      val files = logsDir.listFiles()

      if (files != null) {
        Log.d(TAG, "Listing specific files:")
        for (fileName in logFiles) {
          val file = File(logsDir, fileName)
          if (file.exists()) {
            if (file.delete()) {
              Log.d(TAG, "Deleted file: ${file.name}")
            } else {
              Log.e(TAG, "Failed to delete file: ${file.name}")
            }
          } else {
            Log.d(TAG, "$fileName not found")
          }
        }
      } else {
        Log.e(TAG, "Error listing files: logsDir.listFiles() returned null")
      }
    } else {
      Log.e(TAG, "Private directory ($LOGS_DIRNAME) does not exist or is not a directory.")
    }
  }

  private fun shareLogFiles() {
    val logsDir = File(filesDir, LOGS_DIRNAME)
    if (logsDir.exists() && logsDir.isDirectory) {
      val bootEventsFile = File(logsDir, BOOT_EVENTS_PROTO_FILENAME)
      val usbEventsFile = File(logsDir, USB_DEVICES_EVENTS_FILENAME)
      try {
        val urisToShare = mutableListOf<Uri>()

        if (bootEventsFile.exists()) {
          val uriBootLogFile: Uri =
            FileProvider.getUriForFile(this, "sherlock.usblogging.fileprovider", bootEventsFile)
          urisToShare.add(uriBootLogFile)
        }
        if (usbEventsFile.exists()) {
          val uriUsbEventsLogFile: Uri =
            FileProvider.getUriForFile(this, "sherlock.usblogging.fileprovider", usbEventsFile)
          urisToShare.add(uriUsbEventsLogFile)
        }
        if (urisToShare.isNotEmpty()) {
          val shareIntent: Intent =
            if (urisToShare.size == 1) {
              Intent().apply {
                action = Intent.ACTION_SEND
                putExtra(Intent.EXTRA_STREAM, urisToShare[0])
                type = "application/octet-stream"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
              }
            } else {
              Intent().apply {
                action = Intent.ACTION_SEND_MULTIPLE
                putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(urisToShare))
                type = "application/octet-stream"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
              }
            }

          startActivity(Intent.createChooser(shareIntent, "Share Logs"))
        } else {
          Log.e(TAG, "No log files found to share.")
        }
      } catch (e: Exception) {
        Log.e(TAG, "Error getUriForFile(): ${e.message}")
      }
    } else {
      Log.e(TAG, "Private directory ($LOGS_DIRNAME) does not exist or is not a directory.")
    }
  }

  private companion object {
    const val TAG = "LogListActivity"
    const val LOGS_DIRNAME = "Logs"
    const val USB_DEVICES_EVENTS_ASCII_FILENAME = "usb_device_events.txt"
    const val USB_DEVICES_EVENTS_FILENAME = "usb_device_events.pb"
    const val BOOT_EVENTS_ASCII_FILENAME = "boot_events.txt"
    const val BOOT_EVENTS_PROTO_FILENAME = "boot_events.pb"
  }
}
