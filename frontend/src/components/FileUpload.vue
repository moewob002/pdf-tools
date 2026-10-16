<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center transition-all relative"
    :class="[
      isDragging ? 'border-indigo-500 bg-indigo-50 scale-[1.01]' : 'border-gray-300 hover:border-indigo-400',
      files.length > 0 ? 'border-solid bg-gray-50' : '',
    ]"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="hidden"
      @change="handleFileSelect"
    />

    <div v-if="files.length === 0" class="space-y-4">
      <div class="text-gray-400">
        <svg
          class="mx-auto h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>
      <div class="text-sm text-gray-600">
        <button
          type="button"
          class="cursor-pointer text-indigo-600 hover:text-indigo-500 font-medium underline-offset-2 hover:underline"
          @click="fileInput?.click()"
        >
          Click to upload
        </button>
        or drag and drop
      </div>
      <p class="text-xs text-gray-500">
        {{ acceptText }} (max {{ maxSizeMB }}MB)
      </p>
    </div>

    <div
      v-else
      class="space-y-3"
    >
      <div
        v-for="(file, i) in files"
        :key="i"
        class="flex items-center bg-white border rounded-lg px-4 py-3 text-sm shadow-sm"
      >
        <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center mr-3">
          <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-medium text-gray-800 truncate">{{ file.name }}</div>
          <div class="text-xs text-gray-500">{{ formatSize(file.size) }}</div>
        </div>
        <button
          class="ml-3 w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
          :aria-label="`Remove ${file.name}`"
          @click="removeFile(i)"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex items-center gap-3">
        <button
          class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          @click="fileInput?.click()"
        >
          {{ multiple ? "+ Add more files" : "Replace file" }}
        </button>
        <button
          class="text-xs text-gray-500 hover:text-gray-700"
          @click="clear"
        >
          Clear all
        </button>
      </div>
    </div>

    <ul v-if="rejected.length" class="mt-3 space-y-1 text-left" role="alert">
      <li v-for="(item, i) in rejected" :key="i" class="text-xs text-red-700">
        {{ item.file.name }} was not added: {{ item.reason }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { partitionFiles } from "../utils/files";
import { formatSize } from "../utils/format";

const props = defineProps({
  accept: { type: String, default: ".pdf" },
  acceptText: { type: String, default: "PDF files" },
  multiple: { type: Boolean, default: false },
  maxSizeMB: { type: Number, default: 50 },
});

const emit = defineEmits(["update:files"]);

const files = ref([]);
const rejected = ref([]);
const isDragging = ref(false);
const fileInput = ref(null);

function handleDrop(e) {
  isDragging.value = false;
  const dropped = Array.from(e.dataTransfer.files);
  addFiles(dropped);
}

function handleFileSelect(e) {
  const selected = Array.from(e.target.files);
  addFiles(selected);
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

defineExpose({ clear });
</script>
