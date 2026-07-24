<template>
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center gap-3 mb-6">
      <router-link
        to="/edit"
        class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Merge PDFs</h2>
        <p class="text-sm text-gray-500">Combine pages from multiple PDFs, drag to reorder</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="mergeUpload"
          accept=".pdf"
          accept-text="PDF files"
          :multiple="true"
          @update:files="onFilesChange"
        />

        <div v-if="previewLoading" class="mt-4">
          <ProcessingSpinner message="Loading page previews..." submessage="Extracting thumbnails from each PDF" />
        </div>

        <div v-if="mergePages.length > 0 && !previewLoading" class="mt-4">
          <MergeReorder
            v-model="mergePages"
            :loading="false"
            @addMore="triggerAddMore"
          />
          <div class="mt-4 flex items-center gap-4">
            <DownloadButton
              :loading="loading"
              :disabled="mergePages.length < 2"
              @click="mergePdfs"
            >
              Merge {{ mergePages.length }} Pages
            </DownloadButton>
            <span class="text-xs text-gray-500">from {{ fileCount }} file{{ fileCount !== 1 ? 's' : '' }}</span>
          </div>
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="Merge Complete"
        :subtitle="`${resultPageCount} pages merged from ${fileCount} file${fileCount !== 1 ? 's' : ''}`"
        filename="merged.pdf"
        :file-size="resultBlob.size"
        :blob="resultBlob"
        :show-reset="true"
        @reset="reset"
      />

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineAsyncComponent } from "vue";
import api from "../api";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ProcessingSpinner from "../components/ProcessingSpinner.vue";
import ResultCard from "../components/ResultCard.vue";

const MergeReorder = defineAsyncComponent(() =>
  import("../components/MergeReorder.vue")
);

const mergePages = ref([]);
const previewLoading = ref(false);
const loading = ref(false);
const error = ref("");
const mergeUpload = ref(null);
const resultBlob = ref(null);
const fileCount = ref(0);
const resultPageCount = ref(0);

let nextFileIdx = 0;
let fileMap = {};

async function loadThumbnails(file) {
  const form = new FormData();
  form.append("file", file);
  form.append("dpi", "100");
  const res = await api.post("/edit/thumbnails", form);
  return res.data.pages;
}

async function onFilesChange(files) {
  previewLoading.value = true;
  error.value = "";

  if (files.length === 0) {
    mergePages.value = [];
    fileCount.value = 0;
    nextFileIdx = 0;
    fileMap = {};
    previewLoading.value = false;
    return;
  }

  const existingNames = new Set(mergePages.value.map((p) => p.source_name));
  const newPages = [...mergePages.value];

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (existingNames.has(file.name)) continue;

    const fileIdx = nextFileIdx++;
    fileMap[fileIdx] = file;
    existingNames.add(file.name);

    try {
      const pages = await loadThumbnails(file);
      for (const page of pages) {
        newPages.push({
          id: `${file.name}-${page.page}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          file_index: fileIdx,
          page_num: page.page,
          source_name: file.name,
          thumbnail: page.image,
        });
      }
    } catch (_) {
      newPages.push({
        id: `${file.name}-p1-${Date.now()}`,
        file_index: fileIdx,
        page_num: 1,
        source_name: file.name,
        thumbnail: null,
      });
    }
  }

  mergePages.value = newPages;
  fileCount.value = Object.keys(fileMap).length;
  previewLoading.value = false;
}

function triggerAddMore() {
  if (mergeUpload.value?.$el) {
    const input = mergeUpload.value.$el.querySelector('input[type="file"]');
    if (input) input.click();
  }
}

async function mergePdfs() {
  loading.value = true;
  error.value = "";
  try {
    const pageOrder = mergePages.value.map((p) => ({
      file_index: p.file_index,
      page: p.page_num,
    }));

    const form = new FormData();
    const sortedFileIndices = [...new Set(mergePages.value.map((p) => p.file_index))].sort((a, b) => a - b);
    for (const idx of sortedFileIndices) {
      if (fileMap[idx]) {
        form.append("files", fileMap[idx]);
      }
    }

    const originalToNewMap = {};
    sortedFileIndices.forEach((origIdx, newIdx) => {
      originalToNewMap[origIdx] = newIdx;
    });

    const remappedOrder = pageOrder.map((item) => ({
      file_index: originalToNewMap[item.file_index],
      page: item.page,
    }));

    form.append("page_order", JSON.stringify(remappedOrder));

    const res = await api.post("/edit/merge-custom", form, { responseType: "blob" });
    resultBlob.value = res.data;
    resultPageCount.value = mergePages.value.length;
  } catch (e) {
    error.value = e.response?.data?.detail || "Merge failed";
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  mergePages.value = [];
  fileCount.value = 0;
  resultPageCount.value = 0;
  nextFileIdx = 0;
  fileMap = {};
  error.value = "";
  if (mergeUpload.value) mergeUpload.value.clear();
}
</script>
