<template>
  <div class="mx-auto max-w-4xl">
    <PageHeader
      :title="tool.title"
      :description="tool.desc"
      :category="tool.category"
      :icon="tool.icon"
      :back="{ path: '/', label: 'all tools' }"
    />

    <div class="space-y-5">
      <ToolStep :number="1" title="Upload a scanned PDF">
        <FileUpload
          ref="ocrUpload"
          :file-status="fileStatus"
          accept=".pdf"
          accept-text="PDF files (scanned documents)"
          @update:files="onOcrFileChange"
        />

        <div v-if="ocrThumbnails.length > 0" class="mt-4">
          <p class="mb-2 text-sm text-muted">
            {{ ocrThumbnails.length }} page{{ ocrThumbnails.length !== 1 ? 's' : '' }}
          </p>
          <ul class="flex gap-2 overflow-x-auto pb-2">
            <li v-for="page in ocrThumbnails" :key="page.page" class="flex-shrink-0">
              <button
                type="button"
                class="relative block overflow-hidden rounded-lg border border-line bg-white transition hover:shadow-md"
                :aria-label="`Preview page ${page.page}`"
                @click="openPreview(page)"
              >
                <img :src="'data:image/jpeg;base64,' + page.image" alt="" class="h-28" />
                <span class="absolute inset-x-0 bottom-0 bg-black/70 py-0.5 text-center text-[10px] font-semibold text-white">
                  Page {{ page.page }}
                </span>
              </button>
            </li>
          </ul>
        </div>
      </ToolStep>

      <ToolStep :number="2" title="Choose the document language">
        <div class="max-w-xs">
          <label for="ocr-language" class="field-label">Language</label>
          <select id="ocr-language" v-model="language" class="field">
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
      </ToolStep>

      <ToolStep :number="3" title="Run OCR" hint="Extract the text to copy, or download a PDF with selectable, searchable text.">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="extractLoading"
            loading-text="Reading text…"
            :disabled="ocrFiles.length === 0 || makeSelectableLoading"
            @click="extractText"
          >
            Extract text
          </DownloadButton>
          <DownloadButton
            variant="secondary"
            :loading="makeSelectableLoading"
            loading-text="Building PDF…"
            :disabled="ocrFiles.length === 0 || extractLoading"
            @click="makeSelectable"
          >
            Make text selectable
          </DownloadButton>
          <p v-if="ocrFiles.length === 0" class="text-sm text-muted">Upload a PDF to continue.</p>
        </div>
      </ToolStep>

      <ResultCard
        v-if="selectableBlob"
        title="Searchable PDF ready"
        :subtitle="`Text recognised with ${selectableBackend} and placed over the original pages`"
        :filename="`selectable_${ocrFiles[0]?.name || 'output.pdf'}`"
        :file-size="selectableBlob.size"
        :blob="selectableBlob"
        :show-reset="true"
        @reset="resetSelectable"
      />

      <section v-if="result" class="card p-5 sm:p-6" aria-labelledby="ocr-text-title">
        <div class="mb-4 flex flex-wrap items-center gap-3">
          <span class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-success/10 text-success">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </span>
          <div class="min-w-0 flex-1" role="status">
            <h2 id="ocr-text-title" class="text-lg font-bold text-fg">Extracted text</h2>
            <p class="text-sm text-muted">{{ result.total_pages }} page(s) processed with {{ result.backend }}</p>
          </div>
          <button type="button" class="btn-secondary px-3 py-2" @click="copyText">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="copied ? 'M5 13l4 4L19 7' : 'M8 16H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2m-6 12h8a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2z'" />
            </svg>
            <span aria-live="polite">{{ copied ? "Copied" : "Copy all" }}</span>
          </button>
        </div>
        <div class="max-h-96 space-y-4 overflow-y-auto rounded-xl border border-line bg-surface-2/60 p-4" tabindex="0" aria-label="Extracted text">
          <div v-for="page in result.pages" :key="page.page" class="border-b border-line pb-4 last:border-0 last:pb-0">
            <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Page {{ page.page }}</div>
            <pre class="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-fg">{{ page.text || "(no text found)" }}</pre>
          </div>
        </div>
      </section>

      <AlertMessage v-if="error">{{ error }}</AlertMessage>
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
import { loadThumbnails } from "../api/thumbnails";
import { getErrorMessage } from "../utils/errors";
import { previewStatus } from "../utils/previewStatus";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";
import AlertMessage from "../components/AlertMessage.vue";
import PageHeader from "../components/PageHeader.vue";
import ToolStep from "../components/ToolStep.vue";
import { toolById } from "../tools";

const ImageModal = defineAsyncComponent(() =>
  import("../components/ImageModal.vue")
);

const tool = toolById("ocr");
const ocrFiles = ref([]);
const ocrThumbnails = ref([]);
const language = ref("eng");
const extractLoading = ref(false);
const makeSelectableLoading = ref(false);
const error = ref("");
const previewFailed = ref(false);
const fileStatus = () =>
  previewStatus({ loading: previewLoading.value, failed: previewFailed.value, pageCount: ocrThumbnails.value.length });
const previewLoading = ref(false);
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
  error.value = "";
  if (files.length > 0) {
    previewLoading.value = true;
    previewFailed.value = false;
    try {
      ocrThumbnails.value = await loadThumbnails(files[0]);
    } catch (e) {
      previewFailed.value = true;
      error.value = await getErrorMessage(e, "Failed to load preview");
    } finally {
      previewLoading.value = false;
    }
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
    error.value = await getErrorMessage(e, "OCR failed");
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
    error.value = await getErrorMessage(e, "Processing failed");
  } finally {
    makeSelectableLoading.value = false;
  }
}

async function copyText() {
  if (!result.value) return;
  try {
    await navigator.clipboard.writeText(result.value.full_text);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    error.value = "Copying failed. Select the text and copy it manually.";
  }
}

function resetSelectable() {
  selectableBlob.value = null;
  selectableBackend.value = "";
}
</script>
