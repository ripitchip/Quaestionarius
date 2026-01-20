<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { MessageSquare, Calendar, Phone, Settings, LayoutGrid } from 'lucide-vue-next';
import logoUrl from '../assets/vue.svg'; // Merged the logo import here

const router = useRouter();
const route = useRoute();

const menuItems = [
  { path: '/', icon: LayoutGrid },
  { path: '/chat', icon: MessageSquare },
  { path: '/calendar', icon: Calendar },
  { path: '/phone', icon: Phone },
  { path: '/settings', icon: Settings },
];
</script>

<template>
  <nav class="sidebar">
    <div class="logo">
      <img :src="logoUrl" alt="Logo" width="32" height="32" />
    </div>
    <ul>
      <li v-for="item in menuItems" 
          :key="item.path"
          :class="{ active: route.path === item.path }"
          @click="router.push(item.path)">
        <component :is="item.icon" class="icon" :size="22" />
      </li>
    </ul>
  </nav>
</template>

<style scoped>
/* Your existing styles remain exactly the same */
.sidebar {
  width: 72px;
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0; /* Changed to 0 to ensure it hits the top */
}
.logo { 
  height: 72px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  margin-bottom: 20px; 
}
ul { list-style: none; padding: 0; margin: 0; width: 100%; }
li {
  height: 50px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s;
  margin-bottom: 10px;
  position: relative;
}
li:hover, li.active { color: white; background: rgba(255,255,255,0.05); }
li.active::before {
  content: '';
  position: absolute;
  left: 0;
  width: 4px;
  height: 20px;
  background: var(--accent);
  border-radius: 0 4px 4px 0;
}
.icon { transition: transform 0.2s; }
li:hover .icon { transform: scale(1.1); }
</style>