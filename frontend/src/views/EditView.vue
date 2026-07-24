<template>
  <div class="max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Edit PDF</h2>
    <p class="text-sm text-gray-500 mb-6">Choose an editing operation.</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <router-link
        to="/edit/split"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-blue-300 transition-all"
      >
        <div class="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">Split PDF</h3>
        <p class="text-sm text-gray-500 mt-1">Extract specific pages into separate files</p>
      </router-link>

      <router-link
        to="/edit/merge"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-green-300 transition-all"
      >
        <div class="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">Merge PDFs</h3>
        <p class="text-sm text-gray-500 mt-1">Combine multiple PDFs into one file</p>
      </router-link>

      <router-link
        to="/edit/delete"
        class="group bg-white rounded-xl shadow-sm border p-6 hover:shadow-md hover:border-red-300 transition-all"
      >
        <div class="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 group-hover:text-red-600 transition-colors">Delete Pages</h3>
        <p class="text-sm text-gray-500 mt-1">Remove unwanted pages from a PDF</p>
      </router-link>
    </div>
  </div>
</template>
