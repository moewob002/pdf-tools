<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Convert PDF</h2>
    <p class="text-sm text-gray-500 mb-6">Choose a conversion.</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <router-link
        to="/convert/pdf-to-image"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-blue-300 transition-all"
      >
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">PDF to Images</h3>
        <p class="text-sm text-gray-500 mt-1">Extract each page as an image file</p>
      </router-link>

      <router-link
        to="/convert/image-to-pdf"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-green-300 transition-all"
      >
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">Images to PDF</h3>
        <p class="text-sm text-gray-500 mt-1">Combine multiple images into a single PDF</p>
      </router-link>

      <router-link
        to="/convert/pdf-to-word"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-purple-300 transition-all"
      >
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">PDF to Word</h3>
        <p class="text-sm text-gray-500 mt-1">Convert PDF to an editable Word document</p>
      </router-link>
    </div>
  </div>
</template>
