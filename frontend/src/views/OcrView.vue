<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-900 mb-2">OCR - Extract Text</h2>
    <p class="text-sm text-gray-500 mb-6">
      Extract text from scanned PDFs. Choose between viewing the text or generating a new PDF with selectable text.
    </p>

    <div class="space-y-8">
      <div class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div>
            <h3 class="font-semibold text-gray-800">Upload Scanned PDF</h3>
            <p class="text-xs text-gray-500">Select a PDF with scanned text to process</p>
          </div>
        </div>

        <FileUpload
          ref="ocrUpload"
          accept=".pdf"
          accept-text="PDF files (scanned documents)"
          @update:files="onOcrFileChange"
        />

        <div v-if="ocrThumbnails.length > 0" class="mt-4">
          <p class="text-xs text-gray-500 mb-3">
            Preview — {{ ocrThumbnails.length }} page{{ ocrThumbnails.length !== 1 ? 's' : '' }}
          </p>
          <div class="flex gap-2 overflow-x-auto pb-2">
            <div
              v-for="page in ocrThumbnails"
              :key="page.page"
              class="flex-shrink-0 relative group/thumb cursor-pointer"
              @click="openPreview(page)"
            >
              <img
                :src="'data:image/jpeg;base64,' + page.image"
                :alt="'Page ' + page.page"
                class="h-28 rounded border"
              />
              <div class="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-[10px] text-center py-0.5 rounded-b">
                Page {{ page.page }}
              </div>
              <div class="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover/thumb:opacity-100 transition-opacity rounded">
                <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex items-center gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Language</label>
            <select
              v-model="language"
              class="border rounded-lg px-3 py-2 text-sm"
            >
              <option value="eng">English</option>
              <option value="ind">Indonesian</option>
              <option value="jpn">Japanese</option>
              <option value="kor">Korean</option>
              <option value="chi_sim">Chinese (Simplified)</option>
              <option value="deu">German</option>
              <option value="fra">French</option>
              <option value="spa">Spanish</option>
            </select>
          </div>

          <div class="flex-1"></div>

          <DownloadButton
            :loading="extractLoading"
            :disabled="ocrFiles.length === 0"
            @click="extractText"
          >
            Extract Text
          </DownloadButton>

          <DownloadButton
            :loading="makeSelectableLoading"
            :disabled="ocrFiles.length === 0"
            @click="makeSelectable"
          >
            Make Text Selectable
          </DownloadButton>
        </div>
      </div>

      <ResultCard
        v-if="selectableBlob"
        title="Selectable PDF Ready"
        :subtitle="`Text extracted using ${selectableBackend} and overlaid on original`"
        :filename="`selectable_${ocrFiles[0]?.name || 'output.pdf'}`"
        :file-size="selectableBlob.size"
        :blob="selectableBlob"
        :show-reset="true"
        @reset="resetSelectable"
      />

      <div v-if="result" class="bg-white rounded-xl shadow-sm border p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
            <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-gray-800">Extracted Text</h3>
            <p class="text-xs text-gray-500">
              {{ result.total_pages }} pages processed using {{ result.backend }}
            </p>
          </div>
          <button
            class="px-3 py-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors"
            @click="copyText"
          >
            {{ copied ? "Copied!" : "Copy All" }}
          </button>
        </div>
        <div class="max-h-96 overflow-y-auto space-y-4">
          <div
            v-for="page in result.pages"
            :key="page.page"
            class="border-b pb-4 last:border-0 last:pb-0"
          >
            <div class="text-xs font-medium text-gray-400 mb-2">Page {{ page.page }}</div>
            <pre class="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">{{ page.text || "(no text found)" }}</pre>
          </div>
        </div>
      </div>

      <div v-if="error" class="bg-red-50 text-red-700 rounded-lg p-4 text-sm">
        {{ error }}
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
import { ref, computed, defineAsyncComponent } from "vue";
import api from "../api";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";

const ImageModal = defineAsyncComponent(() =>
  import("../components/ImageModal.vue")
);

const ocrFiles = ref([]);
const ocrThumbnails = ref([]);
const language = ref("eng");
const extractLoading = ref(false);
const makeSelectableLoading = ref(false);
const error = ref("");
const result = ref(null);
const copied = ref(false);
const ocrUpload = ref(null);

const selectableBlob = ref(null);
const selectableBackend = ref("");

const previewPage = ref(null);
const previewSrc = computed(() => {
  if (!previewPage.value) return "";
  return "data:image/jpeg;base64," + previewPage.value.image;
});
const previewTitle = computed(() => {
  if (!previewPage.value) return "";
  return `Page ${previewPage.value.page}`;
});

function openPreview(page) {
  previewPage.value = page;
}

async function onOcrFileChange(files) {
  ocrFiles.value = files;
  ocrThumbnails.value = [];
  result.value = null;
  selectableBlob.value = null;
  if (files.length > 0) {
    try {
      const form = new FormData();
      form.append("file", files[0]);
      form.append("dpi", "100");
      const res = await api.post("/edit/thumbnails", form);
      ocrThumbnails.value = res.data.pages;
    } catch (_) {}
  }
}

async function extractText() {
  extractLoading.value = true;
  error.value = "";
  result.value = null;
  try {
    const form = new FormData();
    form.append("file", ocrFiles.value[0]);
    form.append("language", language.value);
    const res = await api.post("/ocr/extract-text", form);
    result.value = res.data;
  } catch (e) {
    error.value = e.response?.data?.detail || "OCR failed";
  } finally {
    extractLoading.value = false;
  }
}

async function makeSelectable() {
  makeSelectableLoading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", ocrFiles.value[0]);
    form.append("language", language.value);
    const res = await api.post("/ocr/make-selectable", form, {
      responseType: "blob",
    });
    selectableBlob.value = res.data;
    selectableBackend.value = res.headers["x-ocr-backend"] || "tesseract";
  } catch (e) {
    error.value = e.response?.data?.detail || "Processing failed";
  } finally {
    makeSelectableLoading.value = false;
  }
}

async function copyText() {
  if (!result.value) return;
  await navigator.clipboard.writeText(result.value.full_text);
  copied.value = true;
  setTimeout(() => (copied.value = false), 2000);
}

function resetSelectable() {
  selectableBlob.value = null;
  selectableBackend.value = "";
}
</script>
