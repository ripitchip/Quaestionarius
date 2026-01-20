<template>
  <div class="app-container">
    <NavBar />
    <main class="main-content">
      <div class="content-inner">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import NavBar from './components/NavBar.vue';
</script>

<style scoped>
.app-container {
  display: flex;
  /* Use fixed viewport dimensions to ensure the sidebar stays pinned */
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden; /* This prevents the whole window from scrolling */
}

.main-content {
  flex: 1;
  height: 100%;
  background-color: #f8fafd;
  /* Scroll logic moves here so the NavBar stays fixed */
  overflow-y: auto; 
  display: flex;
  flex-direction: column;
}

.content-inner {
  padding: 40px 32px;
  width: 100%;
  max-width: 1200px; /* Optional: keeps content from getting too wide on large screens */
  margin: 0 auto;
}

/* Ensure no margins are leaking from the dark mode setup */
@media (prefers-color-scheme: dark) {
  .main-content {
    background-color: #121212;
  }
}
</style>