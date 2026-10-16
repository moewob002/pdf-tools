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
        <h2 class="text-2xl font-bold text-gray-900">Split PDF</h2>
        <p class="text-sm text-gray-500">Select pages to extract into separate files</p>
      </div>
    </div>

    <div class="space-y-6">
      <div v-if="!resultBlob" class="bg-white rounded-xl shadow-sm border p-6">
        <FileUpload
          ref="splitUpload"
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
          <div class="mt-4 flex items-center gap-4">
            <input
              v-model="pageRanges"
              type="text"
              placeholder='Pages: "1-3,5,7-9"'
              class="border rounded-lg px-3 py-2 text-sm flex-1 font-mono"
            />
            <DownloadButton
              :loading="loading"
              :disabled="files.length === 0 || !pageRanges"
              @click="splitPdf"
            >
              Split
            </DownloadButton>
          </div>
        </div>
        <div v-else-if="previewLoading" class="mt-4">
          <ProcessingSpinner message="Generating page previews..." submessage="This may take a moment for large PDFs" />
        </div>
      </div>

      <ResultCard
        v-if="resultBlob"
        title="Split Complete"
        :subtitle="`${pagesSelected} page(s) extracted`"
        filename="split_pages.zip"
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
import { loadThumbnails } from "../api/thumbnails";
import { getErrorMessage } from "../utils/errors";
import { rangesFromPages } from "../utils/pages";
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
const splitUpload = ref(null);
const pageGrid = ref(null);
const resultBlob = ref(null);
const pagesSelected = ref(0);

async function onFileChange(f) {
  files.value = f;
  pageRanges.value = "";
  thumbnails.value = [];
  error.value = "";
  if (f.length > 0) {
    previewLoading.value = true;
    try {
      thumbnails.value = await loadThumbnails(f[0]);
    } catch (e) {
      error.value = await getErrorMessage(e, "Failed to load preview");
    } finally {
      previewLoading.value = false;
    }
  }
}

function onSelectionChange(selected) {
  pageRanges.value = selected.length === 0 ? "" : rangesFromPages(selected);
  pagesSelected.value = selected.length;
}

async function splitPdf() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    form.append("pages", pageRanges.value);
    const res = await api.post("/edit/split", form, { responseType: "blob" });
    resultBlob.value = res.data;
  } catch (e) {
    error.value = await getErrorMessage(e, "Split failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  files.value = [];
  thumbnails.value = [];
  pageRanges.value = "";
  pagesSelected.value = 0;
  error.value = "";
  if (splitUpload.value) splitUpload.value.clear();
}
</script>
