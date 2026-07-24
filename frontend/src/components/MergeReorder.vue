<template>
  <div>
    <div v-if="loading" class="text-center py-8">
      <svg class="animate-spin h-8 w-8 text-indigo-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <p class="mt-2 text-sm text-gray-500">Loading page previews...</p>
    </div>

    <div v-else-if="pages.length > 0" class="space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-sm text-gray-600">
          Drag to reorder pages, click &times; to remove
          <span class="text-gray-400">·</span>
          {{ pages.length }} page{{ pages.length !== 1 ? 's' : '' }} total
        </p>
        <button
          class="text-xs text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 px-2 py-1 rounded transition-colors"
          @click="$emit('addMore')"
        >
          + Add more PDFs
        </button>
      </div>

      <div v-if="uniqueFileCount > 1" class="flex flex-wrap gap-2 mb-2">
        <div
          v-for="entry in sourceFiles"
          :key="entry.index"
          class="flex items-center gap-1.5 text-[11px] text-gray-600"
        >
          <span
            class="w-3 h-3 rounded-full flex-shrink-0"
            :style="{ backgroundColor: FILE_COLORS[entry.index % FILE_COLORS.length] }"
          ></span>
          {{ entry.name }}
        </div>
      </div>

      <div
        ref="gridEl"
        class="flex flex-wrap gap-2"
        @pointerdown="onPointerDown"
      >
        <div
          v-for="(page, index) in pages"
          :key="page.id"
          :data-index="index"
          class="relative group/card w-[100px] flex-shrink-0 touch-none"
          :class="{
            'z-50': dragState.active && dragState.fromIndex === index,
          }"
          :style="getItemStyle(index)"
        >
          <div
            class="w-[100px] h-[130px] rounded-lg border-2 overflow-hidden bg-white hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing select-none"
            :class="dragState.active && dragState.fromIndex === index ? 'shadow-2xl rotate-2' : ''"
            :style="{
              borderColor: FILE_COLORS[page.file_index % FILE_COLORS.length] + '80',
            }"
          >
            <img
              v-if="page.thumbnail"
              :src="'data:image/jpeg;base64,' + page.thumbnail"
              :alt="`Page ${page.page_num}`"
              class="w-full h-[100px] object-contain bg-gray-50"
            />
            <div v-else class="w-full h-[100px] flex items-center justify-center text-gray-400 text-xs bg-gray-50">
              Page {{ page.page_num }}
            </div>
            <div
              class="h-[30px] flex items-center justify-center border-t"
              :style="{ backgroundColor: FILE_COLORS[page.file_index % FILE_COLORS.length] + '15' }"
            >
              <span class="text-[10px] text-gray-600 truncate px-1">{{ page.page_num }}</span>
            </div>
          </div>

          <div
            class="absolute top-1 left-1 text-white text-[9px] px-1 py-0.5 rounded truncate max-w-[80px] pointer-events-none"
            :style="{ backgroundColor: FILE_COLORS[page.file_index % FILE_COLORS.length] + 'cc' }"
          >
            {{ page.source_name }}
          </div>

          <button
            class="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center text-xs hover:bg-red-600 transition-colors opacity-0 group-hover/card:opacity-100"
            @click.stop="removePage(index)"
          >
            &times;
          </button>
        </div>
      </div>

      <Teleport to="body">
        <div
          v-if="dragState.active"
          class="fixed pointer-events-none z-[9999]"
          :style="ghostStyle"
        >
          <div class="w-[100px] h-[130px] rounded-lg border-2 shadow-2xl opacity-80 bg-white overflow-hidden rotate-3">
            <img
              v-if="pages[dragState.fromIndex]?.thumbnail"
              :src="'data:image/jpeg;base64,' + pages[dragState.fromIndex].thumbnail"
              class="w-full h-[100px] object-contain bg-gray-50"
            />
            <div
              class="h-[30px] flex items-center justify-center border-t"
              :style="{ backgroundColor: FILE_COLORS[pages[dragState.fromIndex]?.file_index % FILE_COLORS.length] + '15' }"
            >
              <span class="text-[10px] text-gray-600 truncate px-1">{{ pages[dragState.fromIndex]?.page_num }}</span>
            </div>
          </div>
        </div>
      </Teleport>
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
import { ref, computed, watch, nextTick } from "vue";
import ImageModal from "./ImageModal.vue";

const FILE_COLORS = [
  "#6366f1",
  "#f59e0b",
  "#10b981",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
];

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "addMore"]);

const pages = ref([...props.modelValue]);
const gridEl = ref(null);
const previewPage = ref(null);

const dragState = ref({
  active: false,
  fromIndex: null,
  overIndex: null,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
});

watch(
  () => props.modelValue,
  (newVal) => {
    pages.value = [...newVal];
  },
  { deep: true }
);

const uniqueFileCount = computed(() => {
  const indices = new Set(pages.value.map((p) => p.file_index));
  return indices.size;
});

const sourceFiles = computed(() => {
  const seen = new Map();
  for (const p of pages.value) {
    if (!seen.has(p.file_index)) {
      seen.set(p.file_index, { index: p.file_index, name: p.source_name });
    }
  }
  return Array.from(seen.values());
});

const previewSrc = computed(() => {
  if (!previewPage.value || !previewPage.value.thumbnail) return "";
  return "data:image/jpeg;base64," + previewPage.value.thumbnail;
});

const previewTitle = computed(() => {
  if (!previewPage.value) return "";
  return `${previewPage.value.source_name} — Page ${previewPage.value.page_num}`;
});

const ghostStyle = computed(() => ({
  left: dragState.value.currentX - 50 + "px",
  top: dragState.value.currentY - 65 + "px",
}));

function getItemStyle(index) {
  if (!dragState.value.active) return {};
  if (dragState.value.fromIndex === index) {
    return { opacity: "0.3" };
  }
  if (dragState.value.overIndex === index) {
    return { transform: "scale(1.05)", transition: "transform 0.15s ease" };
  }
  return {};
}

function getIndexFromPoint(x, y) {
  if (!gridEl.value) return null;
  const cards = gridEl.value.querySelectorAll("[data-index]");
  for (const card of cards) {
    const rect = card.getBoundingClientRect();
    if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
      return parseInt(card.dataset.index, 10);
    }
  }
  return null;
}

function onPointerDown(e) {
  if (e.button !== 0) return;
  const card = e.target.closest("[data-index]");
  if (!card) return;
  if (e.target.closest("button")) return;

  const index = parseInt(card.dataset.index, 10);
  if (isNaN(index)) return;

  const startX = e.clientX;
  const startY = e.clientY;
  let started = false;

  function onMove(ev) {
    const dx = ev.clientX - startX;
    const dy = ev.clientY - startY;

    if (!started && (Math.abs(dx) > 5 || Math.abs(dy) > 5)) {
      started = true;
      dragState.value = {
        active: true,
        fromIndex: index,
        overIndex: index,
        startX,
        startY,
        currentX: ev.clientX,
        currentY: ev.clientY,
      };
    }

    if (started) {
      dragState.value.currentX = ev.clientX;
      dragState.value.currentY = ev.clientY;
      const overIdx = getIndexFromPoint(ev.clientX, ev.clientY);
      if (overIdx !== null && overIdx !== dragState.value.overIndex) {
        dragState.value.overIndex = overIdx;
      }
    }
  }

  function onUp() {
    document.removeEventListener("pointermove", onMove);
    document.removeEventListener("pointerup", onUp);

    if (started && dragState.value.active) {
      const from = dragState.value.fromIndex;
      const to = dragState.value.overIndex ?? dragState.value.fromIndex;
      if (from !== null && to !== null && from !== to) {
        const moved = pages.value.splice(from, 1)[0];
        pages.value.splice(to, 0, moved);
        emit("update:modelValue", [...pages.value]);
      }
      dragState.value = {
        active: false,
        fromIndex: null,
        overIndex: null,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,
      };
    }
  }

  document.addEventListener("pointermove", onMove);
  document.addEventListener("pointerup", onUp);
}

function removePage(index) {
  pages.value.splice(index, 1);
  emit("update:modelValue", [...pages.value]);
}
</script>
