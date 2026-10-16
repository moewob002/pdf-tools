<template>
  <section class="card overflow-hidden" :aria-labelledby="titleId">
    <div class="h-1.5" style="background-image: var(--gradient-brand)" aria-hidden="true"></div>
    <div class="p-5 sm:p-6">
      <div class="flex flex-wrap items-start gap-3">
        <span class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-success/10 text-success">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
        </span>
        <div class="min-w-0 flex-1" role="status">
          <h2 :id="titleId" ref="heading" tabindex="-1" class="text-lg font-bold text-fg focus:outline-none">
            {{ title }}
          </h2>
          <p v-if="subtitle" class="text-sm text-muted">{{ subtitle }}</p>
        </div>
        <button v-if="showReset" type="button" class="btn-ghost px-3 py-2" @click="$emit('reset')">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.6m15.4 2A8 8 0 0 0 4.6 9m0 0H9m11 11v-5h-.6m0 0a8 8 0 0 1-15.4-2m15.4 2H15" />
          </svg>
          Process another
        </button>
      </div>

      <div v-if="$slots.default" class="mt-5">
        <slot />
      </div>

      <div v-if="filename" class="mt-5 flex flex-col gap-3 rounded-xl border border-line bg-surface-2/60 p-4 sm:flex-row sm:items-center">
        <div class="flex min-w-0 flex-1 items-center gap-3">
          <span class="tool-chip h-10 w-10 tool-convert">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.6a1 1 0 0 1 .7.3l5.4 5.4a1 1 0 0 1 .3.7V19a2 2 0 0 1-2 2z" />
            </svg>
          </span>
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold text-fg" :title="filename">{{ filename }}</div>
            <div v-if="fileSize" class="text-xs text-muted">{{ formatSize(fileSize) }}</div>
          </div>
        </div>
        <button type="button" class="btn-primary px-5 py-3 text-base" @click="download">
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1m-4-4-4 4m0 0-4-4m4 4V4" />
          </svg>
          Download
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, useId } from "vue";
import { formatSize } from "../utils/format";

const props = defineProps({
  title: { type: String, default: "Done" },
  subtitle: { type: String, default: "" },
  filename: { type: String, default: "" },
  fileSize: { type: Number, default: 0 },
  blob: { type: Blob, default: null },
  showReset: { type: Boolean, default: false },
});

defineEmits(["reset"]);

const titleId = useId();
const heading = ref(null);

// Move focus to the result so keyboard and screen-reader users land on the download.
onMounted(() => heading.value?.focus());

function download() {
  if (!props.blob) return;
  const url = URL.createObjectURL(props.blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = props.filename;
  a.click();
  URL.revokeObjectURL(url);
}
</script>
