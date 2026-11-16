<script setup lang="ts">
import { ref, watch } from "vue";

import { initials } from "./types";

const props = defineProps<{ name: string; image?: string | null; large?: boolean }>();

// Fall back to initials if the photo is missing or fails to load (e.g. a deleted
// file, or a private file the viewer is no longer permitted to read).
const failed = ref(false);
watch(
	() => props.image,
	() => {
		failed.value = false;
	},
);
</script>

<template>
	<span class="employee-avatar" :class="{ large }">
		<img
			v-if="image && !failed"
			:src="image"
			:alt="`Photo of ${name}`"
			loading="lazy"
			@error="failed = true"
		/>
		<template v-else>{{ initials(name) }}</template>
	</span>
</template>
