<script setup lang="ts">
import { ref, watch } from "vue";

import ImageLightbox from "@/components/ImageLightbox.vue";

import { initials } from "./types";

const props = defineProps<{ name: string; image?: string | null; large?: boolean; expandable?: boolean }>();

// Fall back to initials if the photo is missing or fails to load (e.g. a deleted
// file, or a private file the viewer is no longer permitted to read).
const failed = ref(false);
const expanded = ref(false);
watch(
	() => props.image,
	() => {
		failed.value = false;
		expanded.value = false;
	},
);
</script>

<template>
	<button
		v-if="expandable && image && !failed"
		type="button"
		class="employee-avatar employee-avatar-button"
		:class="{ large }"
		:title="`View full-size photo of ${name}`"
		:aria-label="`View full-size photo of ${name}`"
		@click="expanded = true"
	>
		<img :src="image" :alt="`Photo of ${name}`" loading="lazy" @error="failed = true" />
	</button>
	<span v-else class="employee-avatar" :class="{ large }">
		<img
			v-if="image && !failed"
			:src="image"
			:alt="`Photo of ${name}`"
			loading="lazy"
			@error="failed = true"
		/>
		<template v-else>{{ initials(name) }}</template>
	</span>
	<ImageLightbox
		v-if="expanded && image"
		:src="image"
		:alt="`Photo of ${name}`"
		:caption="name"
		@close="expanded = false"
	/>
</template>

<style scoped>
.employee-avatar-button {
	border: 0;
	cursor: zoom-in;
	padding: 0;
}
.employee-avatar-button:focus-visible {
	outline: 3px solid var(--gold);
	outline-offset: 2px;
}
</style>
