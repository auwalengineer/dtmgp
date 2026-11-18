<script setup lang="ts">
import { Camera, RefreshCw, SwitchCamera } from "@lucide/vue";
import { onBeforeUnmount, onMounted, ref } from "vue";

/**
 * Live-camera photo capture. Deliberately has no file-picker fallback: staff
 * photos must be taken with the device camera, not chosen from a gallery.
 * (The server can't verify where image bytes came from — this is a UI rule.)
 * getUserMedia needs a secure context (HTTPS or localhost).
 */
const emit = defineEmits<{ captured: [file: File]; cancel: [] }>();

const MAX_WIDTH = 800;
const video = ref<HTMLVideoElement | null>(null);
const stream = ref<MediaStream | null>(null);
const facingMode = ref<"environment" | "user">("environment");
const canSwitch = ref(false);
const preview = ref("");
const captured = ref<File | null>(null);
const error = ref("");
const starting = ref(false);

function stop() {
  stream.value?.getTracks().forEach((track) => track.stop());
  stream.value = null;
}

async function start() {
  stop();
  error.value = "";
  if (!navigator.mediaDevices?.getUserMedia) {
    error.value = window.isSecureContext ? "This device or browser has no camera access." : "The camera needs a secure (HTTPS) connection.";
    return;
  }
  starting.value = true;
  try {
    stream.value = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: facingMode.value }, width: { ideal: 1280 } }, audio: false });
    if (video.value) { video.value.srcObject = stream.value; await video.value.play().catch(() => undefined); }
    const devices = await navigator.mediaDevices.enumerateDevices?.() ?? [];
    canSwitch.value = devices.filter((device) => device.kind === "videoinput").length > 1;
  } catch (reason) {
    const name = reason instanceof DOMException ? reason.name : "";
    error.value = name === "NotAllowedError" ? "Camera permission was denied. Allow camera access for this site and try again."
      : name === "NotFoundError" || name === "OverconstrainedError" ? "No camera was found on this device."
      : "Unable to start the camera.";
  } finally {
    starting.value = false;
  }
}

function switchCamera() {
  facingMode.value = facingMode.value === "environment" ? "user" : "environment";
  start();
}

function capture() {
  const source = video.value;
  if (!source || !source.videoWidth) return;
  const scale = Math.min(1, MAX_WIDTH / source.videoWidth);
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(source.videoWidth * scale);
  canvas.height = Math.round(source.videoHeight * scale);
  canvas.getContext("2d")?.drawImage(source, 0, 0, canvas.width, canvas.height);
  canvas.toBlob((blob) => {
    if (!blob) { error.value = "Could not capture the photo."; return; }
    captured.value = new File([blob], `employee-photo-${Date.now()}.jpg`, { type: "image/jpeg" });
    preview.value = URL.createObjectURL(blob);
    stop();
  }, "image/jpeg", 0.85);
}

function retake() {
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = "";
  captured.value = null;
  start();
}

function usePhoto() { if (captured.value) emit("captured", captured.value); }

onMounted(start);
onBeforeUnmount(() => { stop(); if (preview.value) URL.revokeObjectURL(preview.value); });
</script>

<template>
  <div class="camera-capture">
    <div class="camera-frame">
      <img v-if="preview" :src="preview" alt="Captured photo preview" />
      <video v-else ref="video" playsinline muted autoplay aria-label="Live camera preview" />
      <p v-if="starting && !preview" class="camera-status">Starting camera…</p>
    </div>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <div class="camera-actions">
      <button type="button" class="secondary-action" @click="emit('cancel')">Cancel</button>
      <template v-if="preview">
        <button type="button" class="secondary-action" @click="retake"><RefreshCw :size="15" /> Retake</button>
        <button type="button" class="primary-action" @click="usePhoto">Use photo</button>
      </template>
      <template v-else>
        <button v-if="canSwitch" type="button" class="secondary-action" :disabled="starting" @click="switchCamera"><SwitchCamera :size="15" /> Switch camera</button>
        <button v-if="!error" type="button" class="primary-action" :disabled="starting || !stream" @click="capture"><Camera :size="15" /> Capture</button>
        <button v-else type="button" class="primary-action" @click="start">Try again</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.camera-capture { display: flex; flex-direction: column; gap: 12px; }
.camera-frame { align-items: center; aspect-ratio: 4 / 3; background: #0f1a15; display: flex; justify-content: center; overflow: hidden; position: relative; width: 100%; }
.camera-frame video, .camera-frame img { height: 100%; object-fit: contain; width: 100%; }
.camera-status { color: #fff; font-size: .8rem; position: absolute; }
.camera-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.camera-actions button { align-items: center; display: inline-flex; gap: 6px; }
</style>
