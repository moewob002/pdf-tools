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
      <ToolStep :number="1" title="Upload images" hint="Pages follow the order of this list.">
        <FileUpload
          ref="fileUpload"
          accept="image/png,image/jpeg,image/tiff,image/bmp"
          accept-text="PNG, JPG, TIFF or BMP images"
          :multiple="true"
          @update:files="(f) => (files = f)"
        />
      </ToolStep>

      <ToolStep :number="2" title="Create the PDF">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Creating PDF…"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to PDF
          </DownloadButton>
          <p class="text-sm text-muted">
            <template v-if="files.length === 0">Upload at least one image.</template>
            <template v-else>{{ files.length }} image{{ files.length !== 1 ? "s" : "" }} will be combined.</template>
          </p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob"
      title="PDF ready"
      :subtitle="`${imageCount} image(s) combined into one PDF`"
      filename="converted.pdf"
      :file-size="resultBlob.size"
      :blob="resultBlob"
      :show-reset="true"
      @reset="reset"
    />

    <AlertMessage v-if="error" class="mt-5">{{ error }}</AlertMessage>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "../api";
import { getErrorMessage } from "../utils/errors";
import FileUpload from "../components/FileUpload.vue";
import DownloadButton from "../components/DownloadButton.vue";
import ResultCard from "../components/ResultCard.vue";
import AlertMessage from "../components/AlertMessage.vue";
import PageHeader from "../components/PageHeader.vue";
import ToolStep from "../components/ToolStep.vue";
import { toolById } from "../tools";

const tool = toolById("image-to-pdf");
const files = ref([]);
const loading = ref(false);
const error = ref("");
const fileUpload = ref(null);
const resultBlob = ref(null);
const imageCount = ref(0);

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    files.value.forEach((f) => form.append("files", f));
    const res = await api.post("/convert/image-to-pdf", form, { responseType: "blob" });
    resultBlob.value = res.data;
    imageCount.value = files.value.length;
  } catch (e) {
    error.value = await getErrorMessage(e, "Conversion failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  imageCount.value = 0;
  files.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
