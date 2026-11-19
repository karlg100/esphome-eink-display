// Frame persistence across deep sleep for the Inkplate driver.
// Addition to ESPHome's inkplate component (esphome-eink-display).
//
// The 1-bit frame (1200x825 = 123,750 bytes on an Inkplate 10) is PackBits
// run-length encoded - a mostly white info screen shrinks to a few KB - and
// kept as a blob in the NVS partition, which already has wear leveling.
// It is written once per deep sleep (on_shutdown), never during normal drawing.

#include "inkplate.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

#include <cinttypes>
#include <cstring>
#include <nvs.h>

namespace esphome::inkplate {

static const char *const TAG = "inkplate.frame";
static const char *const NVS_NAMESPACE = "inkplate_fb";
static const char *const NVS_KEY = "frame";
static const uint32_t FRAME_MAGIC = 0x31424650;  // "PFB1"

struct FrameHeader {
  uint32_t magic;
  uint16_t width;
  uint16_t height;
  uint32_t raw_len;
  uint32_t hash;
};

static uint32_t fnv1a(const uint8_t *data, size_t len) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < len; i++) {
    h ^= data[i];
    h *= 16777619UL;
  }
  return h;
}

// PackBits: header n >= 0 -> n+1 literal bytes follow; -127..-1 -> next byte repeated 1-n times
static size_t packbits_encode(const uint8_t *in, size_t n, uint8_t *out) {
  size_t i = 0, o = 0;
  while (i < n) {
    size_t run = 1;
    while (i + run < n && run < 128 && in[i + run] == in[i])
      run++;
    if (run >= 3) {
      out[o++] = static_cast<uint8_t>(257 - run);
      out[o++] = in[i];
      i += run;
      continue;
    }
    size_t start = i, lit = 0;
    while (i < n && lit < 128) {
      if (i + 2 < n && in[i] == in[i + 1] && in[i] == in[i + 2])
        break;
      i++;
      lit++;
    }
    out[o++] = static_cast<uint8_t>(lit - 1);
    memcpy(out + o, in + start, lit);
    o += lit;
  }
  return o;
}

static size_t packbits_decode(const uint8_t *in, size_t n, uint8_t *out, size_t cap) {
  size_t i = 0, o = 0;
  while (i < n) {
    int8_t h = static_cast<int8_t>(in[i++]);
    if (h >= 0) {
      size_t c = static_cast<size_t>(h) + 1;
      if (i + c > n || o + c > cap)
        return 0;
      memcpy(out + o, in + i, c);
      i += c;
      o += c;
    } else if (h != -128) {
      size_t c = static_cast<size_t>(1 - h);
      if (i >= n || o + c > cap)
        return 0;
      memset(out + o, in[i++], c);
      o += c;
    }
  }
  return o;
}

void Inkplate::on_shutdown() {
  if (this->frame_valid_) {
    this->save_frame();
  } else {
    // whatever is on the panel now is not what buffer_ holds: make sure the
    // next wake does not trust an older saved frame
    this->forget_frame();
  }
}

bool Inkplate::save_frame() {
  if (this->greyscale_ || this->buffer_ == nullptr)
    return false;
  uint32_t start = millis();
  size_t raw_len = this->get_buffer_length_();
  RAMAllocator<uint8_t> allocator;
  size_t cap = sizeof(FrameHeader) + raw_len + raw_len / 128 + 16;
  uint8_t *blob = allocator.allocate(cap);
  if (blob == nullptr) {
    ESP_LOGW(TAG, "No memory to save the frame");
    return false;
  }
  FrameHeader hdr{FRAME_MAGIC, static_cast<uint16_t>(this->get_width_internal()),
                  static_cast<uint16_t>(this->get_height_internal()), static_cast<uint32_t>(raw_len),
                  fnv1a(this->buffer_, raw_len)};
  memcpy(blob, &hdr, sizeof(hdr));
  size_t len = sizeof(hdr) + packbits_encode(this->buffer_, raw_len, blob + sizeof(hdr));

  bool ok = false;
  nvs_handle_t handle;
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle);
  if (err == ESP_OK) {
    err = nvs_set_blob(handle, NVS_KEY, blob, len);
    if (err == ESP_OK)
      err = nvs_commit(handle);
    nvs_close(handle);
    ok = err == ESP_OK;
  }
  allocator.deallocate(blob, cap);
  if (ok) {
    ESP_LOGI(TAG, "Saved frame: %zu bytes (from %zu) in %" PRIu32 "ms", len, raw_len, millis() - start);
  } else {
    ESP_LOGW(TAG, "Saving the frame failed: %s", esp_err_to_name(err));
  }
  return ok;
}

bool Inkplate::restore_frame() {
  this->frame_restored_ = false;
  if (this->greyscale_ || this->buffer_ == nullptr)
    return false;
  uint32_t start = millis();
  nvs_handle_t handle;
  if (nvs_open(NVS_NAMESPACE, NVS_READONLY, &handle) != ESP_OK) {
    ESP_LOGI(TAG, "No saved frame");
    return false;
  }
  size_t len = 0;
  esp_err_t err = nvs_get_blob(handle, NVS_KEY, nullptr, &len);
  if (err != ESP_OK || len <= sizeof(FrameHeader)) {
    nvs_close(handle);
    ESP_LOGI(TAG, "No saved frame");
    return false;
  }
  RAMAllocator<uint8_t> allocator;
  uint8_t *blob = allocator.allocate(len);
  if (blob == nullptr) {
    nvs_close(handle);
    return false;
  }
  err = nvs_get_blob(handle, NVS_KEY, blob, &len);
  nvs_close(handle);

  bool ok = false;
  size_t raw_len = this->get_buffer_length_();
  FrameHeader hdr;
  memcpy(&hdr, blob, sizeof(hdr));
  if (err == ESP_OK && hdr.magic == FRAME_MAGIC && hdr.raw_len == raw_len &&
      hdr.width == this->get_width_internal() && hdr.height == this->get_height_internal()) {
    size_t got = packbits_decode(blob + sizeof(hdr), len - sizeof(hdr), this->buffer_, raw_len);
    ok = got == raw_len && fnv1a(this->buffer_, raw_len) == hdr.hash;
  }
  allocator.deallocate(blob, len);

  if (!ok) {
    memset(this->buffer_, 0, raw_len);
    ESP_LOGW(TAG, "Saved frame is not usable, the next draw will be a full refresh");
    return false;
  }
  if (this->partial_buffer_ != nullptr)
    memcpy(this->partial_buffer_, this->buffer_, raw_len);
  this->block_partial_ = false;
  this->frame_valid_ = true;
  this->frame_restored_ = true;
  ESP_LOGI(TAG, "Restored frame (%zu bytes) in %" PRIu32 "ms", len, millis() - start);
  return true;
}

void Inkplate::forget_frame() {
  nvs_handle_t handle;
  if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle) != ESP_OK)
    return;
  if (nvs_erase_key(handle, NVS_KEY) == ESP_OK)
    nvs_commit(handle);
  nvs_close(handle);
}

}  // namespace esphome::inkplate
