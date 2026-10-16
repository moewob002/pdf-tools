<template>
  <div class="mx-auto max-w-4xl">
    <PageHeader
      :title="tool.title"
      :description="tool.desc"
      :category="tool.category"
      :icon="tool.icon"
      :back="{ path: '/edit', label: 'Edit tools' }"
    />

    <div v-if="!resultBlob" class="space-y-5">
      <ToolStep :number="1" title="Upload a PDF">
        <FileUpload
          ref="splitUpload"
          :file-status="fileStatus"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="onFileChange"
        />
      </ToolStep>

      <ToolStep :number="2" title="Choose pages to extract" hint="Select page tiles or type ranges. Each page becomes its own PDF.">
        <ProcessingSpinner v-if="previewLoading" message="Generating page previews…" submessage="This may take a moment for large PDFs" />
        <PageGrid
          v-else-if="thumbnails.length > 0"
          ref="pageGrid"
          :pages="thumbnails"
          intent="keep"
          @update:selected="onSelectionChange"
        />
        <p v-else class="rounded-xl border border-dashed border-line-strong px-4 py-6 text-center text-sm text-muted">
          Page previews appear here after you upload a PDF.
        </p>

        <div class="mt-4">
          <label for="split-ranges" class="field-label">Pages to extract</label>
          <input
            id="split-ranges"
            v-model="pageRanges"
            type="text"
            inputmode="numeric"
            placeholder="e.g. 1-3,5,7-9"
            class="field font-mono"
            :disabled="files.length === 0"
          />
        </div>
      </ToolStep>

      <ToolStep :number="3" title="Split and download">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Splitting…"
            :disabled="files.length === 0 || !pageRanges"
            @click="splitPdf"
          >
            Split PDF
          </DownloadButton>
          <p v-if="files.length === 0" class="text-sm text-muted">Upload a PDF to continue.</p>
          <p v-else-if="!pageRanges" class="text-sm text-muted">Choose at least one page.</p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob"
      title="Split complete"
      :subtitle="`${pagesSelected} page(s) extracted`"
      filename="split_pages.zip"
      :file-size="resultBlob.size"
      :blob="resultBlob"
      :show-reset="true"
      @reset="reset"
    />

    <AlertMessage v-if="error" class="mt-5">{{ error }}</AlertMessage>
  </div>
</template>

<script setup>
import { ref, defineAsyncComponent } from "vue";
import api from "../api";
import { loadThumbnails } from "../api/thumbnails";
import { getErrorMessage } from "../utils/errors";
import { previewStatus } from "../utils/previewStatus";
import { rangesFromPages } from "../utils/pages";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ProcessingSpinner from "../components/ProcessingSpinner.vue";
import ResultCard from "../components/ResultCard.vue";
import AlertMessage from "../components/AlertMessage.vue";
import PageHeader from "../components/PageHeader.vue";
import ToolStep from "../components/ToolStep.vue";
import { toolById } from "../tools";

const PageGrid = defineAsyncComponent(() =>
  import("../components/PageGrid.vue")
);

const tool = toolById("split");
const files = ref([]);
const thumbnails = ref([]);
const pageRanges = ref("");
const previewLoading = ref(false);
const loading = ref(false);
const error = ref("");
const previewFailed = ref(false);
const fileStatus = () =>
  previewStatus({ loading: previewLoading.value, failed: previewFailed.value, pageCount: thumbnails.value.length });
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
    previewFailed.value = false;
    try {
      thumbnails.value = await loadThumbnails(f[0]);
    } catch (e) {
      previewFailed.value = true;
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
