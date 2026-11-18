<script setup lang="ts">
import { ExternalLink, X } from "@lucide/vue";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

/** Full-size view of a single image. Esc, the close button or a backdrop click dismiss it. */
const props = defineProps<{ src: string; alt: string; caption?: string }>();
const emit = defineEmits<{ close: [] }>();

const closeButton = ref<HTMLButtonElement>();
const failed = ref(false);
const opener = typeof document !== "undefined" ? (document.activeElement as HTMLElement | null) : null;

function onKey(event: KeyboardEvent) {
  if (event.key === "Escape") { event.stopPropagation(); emit("close"); }
}
onMounted(async () => { document.addEventListener("keydown", onKey, true); await nextTick(); closeButton.value?.focus(); });
// Return focus to whatever opened the preview.
onBeforeUnmount(() => { document.removeEventListener("keydown", onKey, true); opener?.focus?.(); });
</script>

<template>
  <Teleport to="body">
    <div class="image-lightbox" role="dialog" aria-modal="true" :aria-label="caption || alt" @click.self="emit('close')">
      <figure>
        <img v-if="!failed" :src="props.src" :alt="alt" @error="failed = true" />
        <p v-else class="image-lightbox-error" role="alert">This image could not be loaded.</p>
        <figcaption>
          <span>{{ caption }}</span>
          <a :href="props.src" target="_blank" rel="noopener">Open original <ExternalLink :size="14" /></a>
          <button ref="closeButton" type="button" class="icon-button" aria-label="Close image preview" title="Close" @click="emit('close')"><X :size="20" /></button>
        </figcaption>
      </figure>
    </div>
  </Teleport>
</template>

<style scoped>
.image-lightbox { align-items: center; background: rgb(8 14 11 / 86%); display: flex; inset: 0; justify-content: center; padding: 16px; position: fixed; z-index: 1000; }
figure { display: flex; flex-direction: column; gap: 10px; margin: 0; max-height: 100%; max-width: min(960px, 100%); }
img { background: #0f1a15; max-height: calc(100vh - 96px); max-width: 100%; object-fit: contain; }
figcaption { align-items: center; color: #fff; display: flex; font-size: .85rem; gap: 12px; }
figcaption span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
figcaption a { align-items: center; color: #fff; display: inline-flex; gap: 4px; }
figcaption .icon-button { color: #fff; }
.image-lightbox-error { background: #fff; color: var(--text, #1d2a23); margin: 0; padding: 24px; }
</style>
