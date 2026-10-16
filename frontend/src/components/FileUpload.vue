<template>
  <div>
    <input
      :id="inputId"
      ref="fileInput"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="sr-only"
      tabindex="-1"
      aria-hidden="true"
      @change="handleFileSelect"
    />

    <div
      v-if="files.length === 0"
      class="relative rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors"
      :class="isDragging ? 'border-primary-text bg-primary/10' : 'border-line-strong bg-surface-2/60 hover:border-primary-text'"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave="onDragLeave"
      @drop.prevent="handleDrop"
    >
      <span class="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl text-on-primary shadow-md" style="background-image: var(--gradient-brand)">
        <svg class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 0 1-.9-7.9A5 5 0 1 1 15.9 6H16a5 5 0 0 1 1 9.9M15 13l-3-3m0 0-3 3m3-3v12" />
        </svg>
      </span>
      <p class="text-base font-semibold text-fg">
        {{ isDragging ? "Drop to add" : `Drag & drop ${multiple ? "files" : "a file"} here` }}
      </p>
      <p class="mt-1 text-sm text-muted">or</p>
      <button type="button" class="btn-primary mt-3" @click="openPicker">
        Browse {{ multiple ? "files" : "for a file" }}
      </button>
      <p class="mt-4 text-xs text-muted">{{ acceptText }} · up to {{ maxSizeMB }}MB each</p>
    </div>

    <div v-else class="space-y-3">
      <ul class="space-y-2" aria-label="Selected files">
        <li
          v-for="(file, i) in files"
          :key="fileKey(file)"
          class="flex items-center gap-3 rounded-xl border border-line bg-surface-2/60 px-3 py-2.5"
        >
          <span class="tool-chip h-10 w-10 tool-convert">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5.6a1 1 0 0 1 .7.3l5.4 5.4a1 1 0 0 1 .3.7V19a2 2 0 0 1-2 2z" />
            </svg>
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-fg" :title="file.name">{{ file.name }}</div>
            <div class="text-xs text-muted">{{ formatSize(file.size) }}</div>
          </div>
          <FileStatus :status="statusOf(file)" />
          <button
            type="button"
            class="btn-icon shrink-0 hover:text-danger"
            :aria-label="`Remove ${file.name}`"
            @click="removeFile(i)"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </li>
      </ul>

      <div
        class="flex flex-wrap items-center gap-2"
        @dragover.prevent
        @drop.prevent="handleDrop"
      >
        <button type="button" class="btn-secondary px-3 py-2" @click="openPicker">
          {{ multiple ? "+ Add more files" : "Replace file" }}
        </button>
        <button type="button" class="btn-ghost px-3 py-2" @click="clear">
          {{ multiple ? "Clear all" : "Remove" }}
        </button>
      </div>
    </div>

    <ul v-if="rejected.length" class="mt-3 space-y-1" role="alert">
      <li v-for="(item, i) in rejected" :key="i" class="flex items-start gap-2 text-sm text-danger">
        <svg class="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
        <span><strong>{{ item.file.name }}</strong> was not added: {{ item.reason }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, useId } from "vue";
import { partitionFiles } from "../utils/files";
import { formatSize } from "../utils/format";
import FileStatus from "./FileStatus.vue";

const props = defineProps({
  accept: { type: String, default: ".pdf" },
  acceptText: { type: String, default: "PDF files" },
  multiple: { type: Boolean, default: false },
  maxSizeMB: { type: Number, default: 50 },
  // Optional per-file status: (file) => { state: "ready" | "loading" | "error", label }
  fileStatus: { type: Function, default: null },
});

const emit = defineEmits(["update:files"]);

const inputId = useId();
const files = ref([]);
const rejected = ref([]);
const isDragging = ref(false);
const fileInput = ref(null);

const keys = new WeakMap();
let nextKey = 0;
function fileKey(file) {
  if (!keys.has(file)) keys.set(file, nextKey++);
  return keys.get(file);
}

function statusOf(file) {
  return props.fileStatus ? props.fileStatus(file) : { state: "ready", label: "Ready" };
}

function openPicker() {
  fileInput.value?.click();
}

function onDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) isDragging.value = false;
}

function handleDrop(e) {
  isDragging.value = false;
  addFiles(Array.from(e.dataTransfer?.files || []));
}

function handleFileSelect(e) {
  addFiles(Array.from(e.target.files));
  e.target.value = "";
}

function addFiles(newFiles) {
  const { accepted: filtered, rejected: skipped } = partitionFiles(newFiles, {
    accept: props.accept,
    maxBytes: props.maxSizeMB * 1024 * 1024,
  });
  rejected.value = skipped;
  if (filtered.length === 0) return;

  if (props.multiple) {
    files.value = [...files.value, ...filtered];
  } else {
    files.value = filtered.slice(0, 1);
  }
  emit("update:files", files.value);
}

function removeFile(index) {
  files.value.splice(index, 1);
  emit("update:files", files.value);
}

function clear() {
  files.value = [];
  rejected.value = [];
  emit("update:files", []);
}

defineExpose({ clear, openPicker });
</script>
