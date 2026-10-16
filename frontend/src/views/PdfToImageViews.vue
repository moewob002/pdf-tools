<template>
  <div class="mx-auto max-w-4xl">
    <PageHeader
      :title="tool.title"
      :description="tool.desc"
      :category="tool.category"
      :icon="tool.icon"
      :back="{ path: '/convert', label: 'Convert tools' }"
    />

    <div v-if="!resultBlob" class="space-y-5">
      <ToolStep :number="1" title="Upload a PDF">
        <FileUpload
          ref="fileUpload"
          :file-status="fileStatus"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="onFileChange"
        />
        <div v-if="preview.length > 0" class="mt-4">
          <p class="mb-2 text-sm text-muted">{{ preview.length }} page{{ preview.length !== 1 ? "s" : "" }} will be converted</p>
          <ul class="flex gap-2 overflow-x-auto pb-2">
            <li v-for="page in preview.slice(0, 8)" :key="page.page" class="flex-shrink-0">
              <button
                type="button"
                class="relative block overflow-hidden rounded-lg border border-line bg-white transition hover:shadow-md"
                :aria-label="`Preview page ${page.page}`"
                @click="openPreview(page, `Page ${page.page}`)"
              >
                <img :src="'data:image/jpeg;base64,' + page.image" alt="" class="h-24" />
                <span class="absolute inset-x-0 bottom-0 bg-black/70 py-0.5 text-center text-[10px] font-semibold text-white">{{ page.page }}</span>
              </button>
            </li>
            <li
              v-if="preview.length > 8"
              class="flex h-24 w-16 flex-shrink-0 items-center justify-center rounded-lg border border-line bg-surface-2 text-xs text-muted"
            >
              +{{ preview.length - 8 }} more
            </li>
          </ul>
        </div>
      </ToolStep>

      <ToolStep :number="2" title="Choose format and resolution">
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label for="img-format" class="field-label">Image format</label>
            <select id="img-format" v-model="imgFormat" class="field">
              <option value="png">PNG (lossless)</option>
              <option value="jpg">JPG (smaller)</option>
              <option value="tiff">TIFF (print)</option>
            </select>
          </div>
          <div>
            <label for="img-dpi" class="field-label">Resolution</label>
            <select id="img-dpi" v-model="dpi" class="field">
              <option :value="150">150 DPI (screen)</option>
              <option :value="200">200 DPI (balanced)</option>
              <option :value="300">300 DPI (print)</option>
            </select>
          </div>
        </div>
      </ToolStep>

      <ToolStep :number="3" title="Convert and download">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Converting…"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to images
          </DownloadButton>
          <p v-if="files.length === 0" class="text-sm text-muted">Upload a PDF to continue.</p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob"
      title="Images ready"
      :subtitle="`${pageCount} page(s) saved as ${imgFormat.toUpperCase()} in a ZIP file`"
      filename="images.zip"
      :file-size="resultBlob.size"
      :blob="resultBlob"
      :show-reset="true"
      @reset="reset"
    />

    <AlertMessage v-if="error" class="mt-5">{{ error }}</AlertMessage>

    <ImageModal
      :show="!!previewData"
      :src="previewSrc"
      :title="previewTitle"
      @close="previewData = null"
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

const tool = toolById("pdf-to-image");
const files = ref([]);
const preview = ref([]);
const imgFormat = ref("png");
const dpi = ref(200);
const loading = ref(false);
const error = ref("");
const previewFailed = ref(false);
const fileStatus = () =>
  previewStatus({ loading: previewLoading.value, failed: previewFailed.value, pageCount: preview.value.length });
const previewLoading = ref(false);
const fileUpload = ref(null);
const resultBlob = ref(null);
const pageCount = ref(0);

const previewData = ref(null);
const previewTitle = ref("");
const previewSrc = computed(() => {
  if (!previewData.value) return "";
  return "data:image/jpeg;base64," + previewData.value.image;
});

function openPreview(page, title) {
  previewData.value = page;
  previewTitle.value = title;
}

async function onFileChange(f) {
  files.value = f;
  preview.value = [];
  error.value = "";
  if (f.length > 0) {
    previewLoading.value = true;
    previewFailed.value = false;
    try {
      preview.value = await loadThumbnails(f[0], 72);
    } catch (e) {
      previewFailed.value = true;
      error.value = await getErrorMessage(e, "Failed to load preview");
    } finally {
      previewLoading.value = false;
    }
  }
}

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    form.append("format", imgFormat.value);
    form.append("dpi", dpi.value);
    const res = await api.post("/convert/pdf-to-image", form, { responseType: "blob" });
    resultBlob.value = res.data;
    pageCount.value = preview.value.length || 0;
  } catch (e) {
    error.value = await getErrorMessage(e, "Conversion failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  pageCount.value = 0;
  files.value = [];
  preview.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
