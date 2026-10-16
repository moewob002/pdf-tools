<template>
  <div>
    <ProcessingSpinner v-if="loading" message="Loading pages…" />

    <div v-else-if="pages.length > 0" class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm text-muted" aria-live="polite">
          <strong class="text-fg">{{ selected.size }}</strong> of {{ pages.length }} pages selected
        </p>
        <div class="flex gap-1">
          <button type="button" class="btn-ghost px-3 py-1.5 text-xs" @click="selectAll">Select all</button>
          <button type="button" class="btn-ghost px-3 py-1.5 text-xs" @click="clearSelection">Clear</button>
        </div>
      </div>

      <ul class="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
        <li v-for="page in pages" :key="page.page" class="relative">
          <button
            type="button"
            class="group block w-full overflow-hidden rounded-xl border-2 bg-white text-left transition"
            :class="selected.has(page.page)
              ? `${selectedBorder} shadow-md`
              : 'border-line hover:border-line-strong'"
            :aria-pressed="selected.has(page.page) ? 'true' : 'false'"
            :aria-label="`Page ${page.page}`"
            @click="togglePage(page.page)"
          >
            <img :src="'data:image/jpeg;base64,' + page.image" alt="" class="w-full" />
            <span
              class="absolute left-1.5 top-1.5 inline-flex h-6 min-w-[1.5rem] items-center justify-center gap-0.5 rounded-full px-1.5 text-xs font-bold"
              :class="selected.has(page.page) ? selectedBadge : 'bg-surface text-fg ring-1 ring-line-strong'"
              aria-hidden="true"
            >
              <svg v-if="selected.has(page.page)" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" :d="selectedIcon" />
              </svg>
              {{ page.page }}
            </span>
          </button>
          <button
            type="button"
            class="absolute bottom-1.5 right-1.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-surface text-fg shadow ring-1 ring-line-strong transition hover:text-primary-text"
            :aria-label="`View page ${page.page} full size`"
            @click="openPreview(page)"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0zM10 7v6m-3-3h6" />
            </svg>
          </button>
        </li>
      </ul>
    </div>

    <ImageModal
      :show="!!previewPage"
      :src="previewSrc"
      :title="previewTitle"
      @close="previewPage = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import ImageModal from "./ImageModal.vue";
import ProcessingSpinner from "./ProcessingSpinner.vue";

const props = defineProps({
  pages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  // "keep" marks selected pages with a check; "remove" marks them for deletion.
  intent: { type: String, default: "keep" },
});

const emit = defineEmits(["update:selected"]);

const selected = ref(new Set());
const previewPage = ref(null);

const selectedBorder = computed(() => (props.intent === "remove" ? "border-danger" : "border-primary-text"));
const selectedBadge = computed(() => (props.intent === "remove" ? "bg-danger text-surface" : "text-on-primary bg-primary"));
const selectedIcon = computed(() => (props.intent === "remove" ? "M6 18 18 6M6 6l12 12" : "M5 13l4 4L19 7"));

const previewSrc = computed(() => {
  if (!previewPage.value) return "";
  return "data:image/jpeg;base64," + previewPage.value.image;
});

const previewTitle = computed(() => {
  if (!previewPage.value) return "";
  return `Page ${previewPage.value.page}`;
});

function togglePage(pageNum) {
  if (selected.value.has(pageNum)) {
    selected.value.delete(pageNum);
  } else {
    selected.value.add(pageNum);
  }
  emitSelection();
}

function selectAll() {
  props.pages.forEach((p) => selected.value.add(p.page));
  emitSelection();
}

function clearSelection() {
  selected.value.clear();
  emitSelection();
}

function emitSelection() {
  emit("update:selected", Array.from(selected.value).sort((a, b) => a - b));
}

function openPreview(page) {
  previewPage.value = page;
}

watch(
  () => props.pages,
  () => {
    selected.value.clear();
    emitSelection();
  }
);

function setSelected(pages) {
  selected.value = new Set(pages);
}

defineExpose({ setSelected, clearSelection, selectAll });
</script>
