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
      <ToolStep :number="1" title="Upload a PDF" hint="Text is extracted; pages without text are added as images.">
        <FileUpload
          ref="fileUpload"
          accept=".pdf"
          accept-text="PDF files"
          @update:files="(f) => (files = f)"
        />
      </ToolStep>

      <ToolStep :number="2" title="Convert and download">
        <div class="flex flex-wrap items-center gap-3">
          <DownloadButton
            :loading="loading"
            loading-text="Converting…"
            :disabled="files.length === 0"
            @click="convert"
          >
            Convert to DOCX
          </DownloadButton>
          <p v-if="files.length === 0" class="text-sm text-muted">Upload a PDF to continue.</p>
        </div>
      </ToolStep>
    </div>

    <ResultCard
      v-if="resultBlob"
      title="Word document ready"
      subtitle="Editable DOCX document"
      :filename="`${originalName}.docx`"
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

const tool = toolById("pdf-to-word");
const files = ref([]);
const loading = ref(false);
const error = ref("");
const fileUpload = ref(null);
const resultBlob = ref(null);
const originalName = ref("converted");

async function convert() {
  loading.value = true;
  error.value = "";
  try {
    const form = new FormData();
    form.append("file", files.value[0]);
    originalName.value = files.value[0].name.replace(/\.pdf$/i, "");
    const res = await api.post("/convert/pdf-to-word", form, { responseType: "blob" });
    resultBlob.value = res.data;
  } catch (e) {
    error.value = await getErrorMessage(e, "Conversion failed");
  } finally {
    loading.value = false;
  }
}

function reset() {
  resultBlob.value = null;
  originalName.value = "converted";
  files.value = [];
  error.value = "";
  if (fileUpload.value) fileUpload.value.clear();
}
</script>
