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
        <h2 class="text-2xl font-bold text-gray-900">Delete Pages</h2>
        <p class="text-sm text-gray-500">Select pages to remove from the PDF</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="deleteUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="onFileChange"
        />
        <div v-if="thumbnails.length > 0" class="mt-4">
          <PageGrid
            ref="pageGrid"
            :pages="thumbnails"
            :loading="previewLoading"
            @update:selected="onSelectionChange"
          />
          <p class="mt-2 text-xs text-gray-500">
            Selected pages will be <span class="text-red-600 font-medium">removed</span>
          </p>
          <div class="mt-3 flex items-center gap-4">
            <input
              v-model="pageRanges"
              type="text"
              placeholder='Pages to remove: "2,4,6-8"'
              class="border rounded-lg px-3 py-2 text-sm flex-1 font-mono"
            />
            <DownloadButton
              :loading="loading"
              :disabled="files.length === 0 || !pageRanges"
              @click="deletePages"
            >
              Delete Pages
            </DownloadButton>
          </div>
        </div>
        <div v-else-if="previewLoading" class="mt-4">
          <ProcessingSpinner message="Generating page previews..." submessage="This may take a moment for large PDFs" />
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="Pages Deleted"
        :subtitle="`Removed ${pagesDeleted} page(s) from PDF`"
        filename="remaining_pages.pdf"
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

const PageGrid = defineAsyncComponent(() =>
  import("../components/PageGrid.vue")
);

const files = ref([]);
const thumbnails = ref([]);
const pageRanges = ref("");
const previewLoading = ref(false);
const loading = ref(false);
const error = ref("");
const deleteUpload = ref(null);
const pageGrid = ref(null);
const resultBlob = ref(null);
const pagesDeleted = ref(0);

async function loadThumbnails(file) {
  const form = new FormData();
  form.append("file", file);
  form.append("dpi", "100");
  const res = await api.post("/edit/thumbnails", form);
  return res.data.pages;
}

function rangesFromPages(pages) {
  if (pages.length === 0) return "";
  const sorted = [...pages].sort((a, b) => a - b);
  const ranges = [];
  let start = sorted[0];
  let end = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === end + 1) {
      end = sorted[i];
    } else {
      ranges.push(start === end ? `${start}` : `${start}-${end}`);
      start = sorted[i];
      end = sorted[i];
    }
  }
  ranges.push(start === end ? `${start}` : `${start}-${end}`);
  return ranges.join(",");
}

async function onFileChange(f) {
  files.value = f;
  pageRanges.value = "";
  thumbnails.value = [];
  if (f.length > 0) {
    previewLoading.value = true;
    try {
      thumbnails.value = await loadThumbnails(f[0]);
    } catch (e) {
      error.value = "Failed to load preview";
    } finally {
      previewLoading.value = false;
    }
  }
}

function onSelectionChange(selected) {
  pageRanges.value = selected.length === 0 ? "" : rangesFromPages(selected);
  pagesDeleted.value = selected.length;
}

async function deletePages() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    form.append("pages", pageRanges.value);
    const res = await api.post("/edit/delete-pages", form, { responseType: "blob" });
    resultBlob.value = res.data;
  } catch (e) {
    error.value = e.response?.data?.detail || "Delete failed";
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  files.value = [];
  thumbnails.value = [];
  pageRanges.value = "";
  pagesDeleted.value = 0;
  error.value = "";
  if (deleteUpload.value) deleteUpload.value.clear();
}
</script>
