<template>
  <div class="mx-auto max-w-5xl">
    <PageHeader
      title="Convert"
      :description="CATEGORIES.convert.desc"
      category="convert"
      :icon="CATEGORIES.convert.icon"
      :back="{ path: '/', label: 'all tools' }"
    />
    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <ToolCard v-for="tool in toolsIn('convert')" :key="tool.id" :tool="tool" />
    </div>
  </div>
</template>

<script setup>
import PageHeader from "../components/PageHeader.vue";
import ToolCard from "../components/ToolCard.vue";
import { CATEGORIES, toolsIn } from "../tools";
</script>
