<template>
  <div>
    <ProcessingSpinner v-if="loading" message="Loading page previews…" />

    <div v-else-if="pages.length > 0" class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm text-muted">
          Drag pages (or use the arrow buttons) to reorder. Select a page to preview it.
          <span aria-hidden="true">·</span>
          <strong class="text-fg">{{ pages.length }} page{{ pages.length !== 1 ? 's' : '' }} total</strong>
        </p>
        <button type="button" class="btn-secondary px-3 py-1.5 text-xs" @click="$emit('addMore')">
          + Add more PDFs
        </button>
      </div>

      <ul v-if="uniqueFileCount > 1" class="flex flex-wrap gap-x-4 gap-y-1.5" aria-label="Source files">
        <li
          v-for="entry in sourceFiles"
          :key="entry.index"
          class="flex items-center gap-1.5 text-xs text-muted"
        >
          <span
            class="h-3 w-3 shrink-0 rounded-full"
            :style="{ backgroundColor: colorFor(entry.index) }"
            aria-hidden="true"
          ></span>
          {{ entry.name }}
        </li>
      </ul>

      <p class="sr-only" aria-live="polite">{{ announcement }}</p>

      <ul
        ref="gridEl"
        class="flex flex-wrap gap-3"
        @pointerdown="onPointerDown"
      >
        <li
          v-for="(page, index) in pages"
          :key="page.id"
          :data-index="index"
          class="hover-reveal-group relative w-[104px] flex-shrink-0 touch-none"
          :class="{
            'z-50': dragState.active && dragState.fromIndex === index,
          }"
          :style="getItemStyle(index)"
        >
          <div
            class="h-[136px] w-[104px] cursor-grab select-none overflow-hidden rounded-xl border-2 bg-white transition-shadow hover:shadow-md active:cursor-grabbing"
            :class="dragState.active && dragState.fromIndex === index ? 'rotate-2 shadow-2xl' : ''"
            :style="{ borderColor: colorFor(page.file_index) }"
          >
            <img
              v-if="page.thumbnail"
              :src="'data:image/jpeg;base64,' + page.thumbnail"
              :alt="`${page.source_name}, page ${page.page_num}`"
              class="h-[104px] w-full bg-white object-contain"
            />
            <div v-else class="flex h-[104px] w-full items-center justify-center bg-surface-2 text-xs text-muted">
              Page {{ page.page_num }}
            </div>
            <div class="flex h-[32px] items-center justify-center border-t border-line bg-surface text-xs font-semibold text-fg">
              {{ index + 1 }}
            </div>
          </div>

          <div
            class="pointer-events-none absolute left-1 top-1 max-w-[84px] truncate rounded px-1 py-0.5 text-[10px] font-semibold text-white"
            :style="{ backgroundColor: colorFor(page.file_index) }"
          >
            {{ page.source_name }} · p{{ page.page_num }}
          </div>

          <button
            type="button"
            class="hover-reveal absolute right-1 top-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-danger text-surface shadow"
            :aria-label="`Remove page ${page.page_num} of ${page.source_name}`"
            @click.stop="removePage(index)"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="hover-reveal absolute inset-x-1 bottom-9 flex justify-between">
            <button
              type="button"
              class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-surface text-fg shadow ring-1 ring-line-strong disabled:invisible"
              :disabled="index === 0"
              :aria-label="`Move page ${index + 1} earlier`"
              @click.stop="move(index, -1)"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              type="button"
              class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-surface text-fg shadow ring-1 ring-line-strong disabled:invisible"
              :disabled="index === pages.length - 1"
              :aria-label="`Move page ${index + 1} later`"
              @click.stop="move(index, 1)"
            >
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <button
            type="button"
            class="sr-only focus:not-sr-only focus:absolute focus:inset-x-1 focus:top-9 focus:rounded focus:bg-surface focus:px-1 focus:text-xs focus:text-fg"
            @click.stop="previewPage = page"
          >
            Preview page {{ index + 1 }}
          </button>
        </li>
      </ul>

      <Teleport to="body">
        <div
          v-if="dragState.active"
          class="pointer-events-none fixed z-[9999]"
          :style="ghostStyle"
          aria-hidden="true"
        >
          <div class="h-[136px] w-[104px] rotate-3 overflow-hidden rounded-xl border-2 bg-white opacity-90 shadow-2xl" :style="{ borderColor: colorFor(pages[dragState.fromIndex]?.file_index) }">
            <img
              v-if="pages[dragState.fromIndex]?.thumbnail"
              :src="'data:image/jpeg;base64,' + pages[dragState.fromIndex].thumbnail"
              alt=""
              class="h-[104px] w-full bg-white object-contain"
            />
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
import { ref, computed, watch } from "vue";
import ImageModal from "./ImageModal.vue";
import ProcessingSpinner from "./ProcessingSpinner.vue";

// Source-file colours. Each keeps >= 4.5:1 with the white label text drawn on it,
// and the file name is always shown too, so colour is never the only cue.
const FILE_COLORS = [
  "#2353F0",
  "#7134E6",
  "#B93A26",
  "#0B6E86",
  "#BE185D",
  "#167A3E",
  "#9A5A00",
  "#4338CA",
];
const colorFor = (fileIndex) => FILE_COLORS[(fileIndex ?? 0) % FILE_COLORS.length];

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "addMore"]);

const pages = ref([...props.modelValue]);
const gridEl = ref(null);
const previewPage = ref(null);
const announcement = ref("");

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
    } else if (!started) {
      previewPage.value = pages.value[index];
    }
  }

  document.addEventListener("pointermove", onMove);
  document.addEventListener("pointerup", onUp);
}

function removePage(index) {
  const [removed] = pages.value.splice(index, 1);
  emit("update:modelValue", [...pages.value]);
  announcement.value = `Removed page ${removed.page_num} of ${removed.source_name}.`;
}

function move(index, delta) {
  const to = index + delta;
  if (to < 0 || to >= pages.value.length) return;
  const [moved] = pages.value.splice(index, 1);
  pages.value.splice(to, 0, moved);
  emit("update:modelValue", [...pages.value]);
  announcement.value = `Moved to position ${to + 1} of ${pages.value.length}.`;
}
</script>
