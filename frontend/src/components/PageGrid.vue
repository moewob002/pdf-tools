<template>
  <div>
    <div
      v-if="loading"
      class="text-center py-8"
    >
      <svg
        class="animate-spin h-8 w-8 text-indigo-600 mx-auto"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <p class="mt-2 text-sm text-gray-500">Loading pages...</p>
    </div>

    <div
      v-else-if="pages.length > 0"
      class="space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="text-sm text-gray-600">
          {{ selected.size }} of {{ pages.length }} pages selected
        </span>
        <div class="space-x-2">
          <button
            class="text-xs text-indigo-600 hover:text-indigo-800"
            @click="selectAll"
          >
            Select all
          </button>
          <button
            class="text-xs text-gray-500 hover:text-gray-700"
            @click="clearSelection"
          >
            Clear
          </button>
        </div>
      </div>

      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
        <div
          v-for="page in pages"
          :key="page.page"
          class="relative group"
        >
          <div
            class="border-2 rounded-lg overflow-hidden transition-all cursor-pointer"
            :class="[
              selected.has(page.page)
                ? 'border-indigo-500 ring-2 ring-indigo-200'
                : 'border-gray-200 hover:border-gray-400',
            ]"
            @click="togglePage(page.page)"
          >
            <img
              :src="'data:image/jpeg;base64,' + page.image"
              :alt="'Page ' + page.page"
              class="w-full"
            />
            <div
              class="absolute top-1 right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium transition-colors"
              :class="[
                selected.has(page.page)
                  ? 'bg-indigo-500 text-white'
                  : 'bg-white/80 text-gray-600 group-hover:bg-white',
              ]"
            >
              {{ page.page }}
            </div>
            <div
              v-if="selected.has(page.page)"
              class="absolute inset-0 bg-indigo-500/10 pointer-events-none"
            />
          </div>
          <button
            class="absolute bottom-1 left-1 w-6 h-6 rounded-full bg-white/90 text-gray-500 hover:text-indigo-600 hover:bg-white flex items-center justify-center shadow opacity-0 group-hover:opacity-100 transition-opacity"
            title="View full size"
            @click.stop="openPreview(page)"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
        </div>
      </div>
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

const props = defineProps({
  pages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["update:selected"]);

const selected = ref(new Set());
const previewPage = ref(null);

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
