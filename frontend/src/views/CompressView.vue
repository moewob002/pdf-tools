<template>
  <div class="mx-auto max-w-4xl">
    <PageHeader
      :title="tool.title"
      :description="tool.desc"
      :category="tool.category"
      :icon="tool.icon"
      :back="{ path: '/', label: 'all tools' }"
    />

    <div v-if="!resultBlob" class="space-y-5">
      <ToolStep :number="1" title="Upload a PDF">
        <FileUpload
          ref="compressUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="(f) => (compressFiles = f)"
        />
      </ToolStep>

      <ToolStep :number="2" title="Choose a compression level">
        <fieldset>
          <legend class="sr-only">Compression level</legend>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label v-for="q in qualityOptions" :key="q.value" class="relative block cursor-pointer">
              <input v-model="quality" type="radio" name="quality" :value="q.value" class="peer sr-only" />
              <span class="flex h-full flex-col rounded-xl border-2 border-line bg-surface p-4 transition peer-checked:border-primary-text peer-checked:bg-primary/10 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus hover:border-line-strong">
                <span class="flex items-center justify-between gap-2">
                  <span class="font-semibold text-fg">{{ q.label }}</span>
                  <span
                    class="inline-flex h-5 w-5 items-center justify-center rounded-full border-2"
                    :class="quality === q.value ? 'border-transparent text-on-primary' : 'border-line-strong'"
                    :style="quality === q.value ? { backgroundImage: 'var(--gradient-brand)' } : null"
                    aria-hidden="true"
                  >
                    <svg v-if="quality === q.value" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3.5" d="M5 13l4 4L19 7" />
                    </svg>
                  </span>
                </span>
                <span class="mt-1 text-sm text-muted">{{ q.desc }}</span>
                <span v-if="q.warn" class="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-warning">
                  <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
                  </svg>
                  {{ q.warn }}
                </span>
              </span>
            </label>
          </div>
        </fieldset>
      </ToolStep>

      <ToolStep :number="3" title="Compress and download">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Compressing…"
            :disabled="compressFiles.length === 0"
            @click="compressPdf"
          >
            Compress PDF
          </DownloadButton>
          <p v-if="compressFiles.length === 0" class="text-sm text-muted">Upload a PDF to continue.</p>
        </div>
        <div v-if="loading" class="mt-4" role="status">
          <div class="h-2 w-full overflow-hidden rounded-full bg-surface-2">
            <div class="h-2 w-1/3 animate-[progress_1.2s_ease-in-out_infinite] rounded-full" style="background-image: var(--gradient-brand)"></div>
          </div>
          <p class="mt-2 text-sm text-muted">Recompressing images and removing unused data…</p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob && stats"
      title="Compression complete"
      :subtitle="`Engine: ${stats.engine === 'ghostscript' ? 'Ghostscript' : 'pikepdf'}`"
      :filename="`compressed_${compressFiles[0]?.name || 'output.pdf'}`"
      :file-size="resultBlob.size"
      :blob="resultBlob"
      :show-reset="true"
      @reset="reset"
    >
      <dl class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-xl bg-surface-2/70 p-4 text-center">
          <dt class="text-xs text-muted">Original</dt>
          <dd class="mt-1 text-lg font-bold text-fg">{{ formatSize(stats.original_size) }}</dd>
        </div>
        <div class="rounded-xl bg-surface-2/70 p-4 text-center">
          <dt class="text-xs text-muted">Compressed</dt>
          <dd class="mt-1 text-lg font-bold text-fg">{{ formatSize(stats.compressed_size) }}</dd>
        </div>
        <div class="rounded-xl p-4 text-center" :class="stats.reduction_percent > 0 ? 'bg-success/10' : 'bg-warning/10'">
          <dt class="text-xs text-muted">Change</dt>
          <dd class="mt-1 text-lg font-bold" :class="stats.reduction_percent > 0 ? 'text-success' : 'text-warning'">
            {{ stats.reduction_percent > 0 ? `−${stats.reduction_percent}%` : stats.reduction_percent < 0 ? `+${-stats.reduction_percent}% larger` : "No change" }}
          </dd>
        </div>
        <div v-if="stats.images_compressed > 0" class="rounded-xl bg-info/10 p-4 text-center">
          <dt class="text-xs text-muted">Images processed</dt>
          <dd class="mt-1 text-lg font-bold text-info">{{ stats.images_compressed }}/{{ stats.total_images }}</dd>
        </div>
      </dl>
    </ResultCard>

    <AlertMessage v-if="error" class="mt-5">{{ error }}</AlertMessage>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api";
import { getErrorMessage } from "../utils/errors";
import { formatSize } from "../utils/format";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";
import AlertMessage from "../components/AlertMessage.vue";
import PageHeader from "../components/PageHeader.vue";
import ToolStep from "../components/ToolStep.vue";
import { toolById } from "../tools";

const tool = toolById("compress");
const compressFiles = ref([]);
const quality = ref("medium");
const loading = ref(false);
const error = ref("");
const stats = ref(null);
const compressUpload = ref(null);
const resultBlob = ref(null);

const qualityOptions = [
  { value: "extreme", label: "Extreme", desc: "72 dpi, smallest file size", warn: "May reduce readability" },
  { value: "low", label: "Low", desc: "150 dpi, good balance" },
  { value: "medium", label: "Balanced", desc: "300 dpi, print quality" },
  { value: "high", label: "High Quality", desc: "300 dpi, no subsampling" },
];

async function compressPdf() {
  loading.value = true;
  error.value = "";
  stats.value = null;
  try {
    const form = new FormData();
    form.append("file", compressFiles.value[0]);
    form.append("quality", quality.value);
    const res = await api.post("/compress", form, { responseType: "blob" });
    resultBlob.value = res.data;
    stats.value = {
      original_size: parseInt(res.headers["x-original-size"]),
      compressed_size: parseInt(res.headers["x-compressed-size"]),
      reduction_percent: parseFloat(res.headers["x-reduction-percent"]),
      images_compressed: parseInt(res.headers["x-images-compressed"] || "0"),
      total_images: parseInt(res.headers["x-total-images"] || "0"),
      engine: res.headers["x-engine"] || "unknown",
    };
  } catch (e) {
    error.value = await getErrorMessage(e, "Compression failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  stats.value = null;
  compressFiles.value = [];
  error.value = "";
  if (compressUpload.value) compressUpload.value.clear();
}
</script>
