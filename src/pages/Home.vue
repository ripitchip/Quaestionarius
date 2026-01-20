<script setup lang="ts">
import { ref, computed } from "vue";
import { open } from "@tauri-apps/plugin-dialog";
import { readFile } from "@tauri-apps/plugin-fs";
import { Trash2, UploadCloud, Users, Mail, Hash } from "lucide-vue-next";
import Papa from "papaparse";

interface Participant {
  Name: string;
  LastName: string;
  Email: string;
  Group: string;
  id?: string;
}

const csvData = ref<Participant[]>([]);
const fileName = ref("");

// Groups flat list into a Record<GroupName, Participant[]>
const groupedParticipants = computed(() => {
  return csvData.value.reduce((acc, person) => {
    const groupName = person.Group || "Unassigned";
    if (!acc[groupName]) acc[groupName] = [];
    acc[groupName].push(person);
    return acc;
  }, {} as Record<string, Participant[]>);
});

async function handleFileImport() {
  try {
    const selected = await open({
      multiple: false,
      filters: [{ name: "CSV", extensions: ["csv"] }],
    });

    if (!selected || Array.isArray(selected)) return;

    fileName.value = selected.split(/[\\/]/).pop() || "";
    const contents = await readFile(selected);
    const decoder = new TextDecoder("utf-8");
    const csvText = decoder.decode(contents);
    
    parseCsvData(csvText);
  } catch (error) {
    console.error("Import failed:", error);
  }
}

function parseCsvData(content: string) {
  Papa.parse(content, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      csvData.value = results.data.map((row: any) => ({
        Name: row.Name || "Unknown",
        LastName: row.LastName || "",
        Email: "demo@foobarbaz.fr", // Strict override for safety
        Group: row.Group || "General",
        id: row.id || Math.floor(Math.random() * 1000).toString()
      }));
    },
  });
}

function resetData() {
  csvData.value = [];
  fileName.value = "";
}
</script>

<template>
  <div class="page-container">
    <header class="page-header">
      <div class="header-text">
        <h1>Dashboard</h1>
        <div v-if="csvData.length > 0" class="meta-row">
          <span class="pill-badge"><Users :size="12" /> {{ csvData.length }} Entries</span>
          <span class="pill-badge">👥 {{ Object.keys(groupedParticipants).length }} Teams</span>
        </div>
      </div>
      
      <div v-if="csvData.length > 0" class="active-file-tag">
        <span class="filename-text">{{ fileName }}</span>
        <button class="btn-clear-red" @click="resetData">
          <Trash2 :size="12" />
        </button>
      </div>
    </header>

    <div v-if="csvData.length === 0" class="upload-hero-container" @click="handleFileImport">
      <div class="hero-inner">
        <div class="icon-blob">
          <UploadCloud :size="32" />
        </div>
        <h2>Import Participant CSV</h2>
        <p>Required: Name, LastName, Group, id</p>
        <div class="demo-warning">
          Emails automatically set to demo@foobarbaz.fr
        </div>
      </div>
    </div>

    <div v-else class="carousel-viewport">
      <div v-for="(members, groupName) in groupedParticipants" :key="groupName" class="group-card">
        <div class="card-head">
          <h3 class="group-label">{{ groupName }}</h3>
          <span class="count-tag">{{ members.length }}</span>
        </div>
        
        <div class="member-scroller">
          <div v-for="person in members" :key="person.id" class="member-tile">
            <div class="avatar-box">
              {{ person.Name[0] }}{{ person.LastName[0] }}
            </div>
            <div class="text-stack">
              <span class="full-name">{{ person.Name }} {{ person.LastName }}</span>
              <span class="email-sub"><Mail :size="10" /> {{ person.Email }}</span>
            </div>
            <span class="id-dim">#{{ person.id }}</span>
          </div>
        </div>
      </div>
    </div>

    <footer class="page-footer">
      <p><Hash :size="12" /> Environment: Local File Parsing Mode</p>
    </footer>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1.25rem;
  overflow: hidden; /* Prevent vertical scroll on the whole page */
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

h1 { font-size: 1.35rem; font-weight: 800; margin: 0; }
.meta-row { display: flex; gap: 8px; margin-top: 4px; }
.pill-badge { 
  font-size: 0.7rem; background: #f1f5f9; padding: 2px 8px; 
  border-radius: 6px; color: #475569; display: flex; align-items: center; gap: 4px;
  font-weight: 600;
}

.active-file-tag {
  display: flex; align-items: center; gap: 8px; background: white;
  padding: 4px 4px 4px 12px; border-radius: 8px; border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.filename-text { font-size: 0.75rem; font-weight: 700; color: #64748b; }
.btn-clear-red { 
  background: #fee2e2; border: none; color: #ef4444; 
  cursor: pointer; border-radius: 6px; padding: 6px; display: flex; 
}

/* --- The Carousel [Horizontal Scroller] --- */
.carousel-viewport {
  display: flex;
  gap: 1.25rem;
  overflow-x: auto;
  padding: 5px 0 20px 0; /* Space for scrollbar */
  scroll-snap-type: x mandatory;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

/* Webkit Scrollbar Styling */
.carousel-viewport::-webkit-scrollbar { height: 8px; }
.carousel-viewport::-webkit-scrollbar-track { background: #f8fafc; border-radius: 10px; }
.carousel-viewport::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.carousel-viewport::-webkit-scrollbar-thumb:hover { background: #6366f1; }

.group-card {
  flex: 0 0 280px; /* Essential: keeps cards from shrinking */
  scroll-snap-align: start;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  height: 380px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.card-head {
  padding: 14px;
  border-bottom: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
  background: #f8fafc; border-radius: 14px 14px 0 0;
}
.group-label { font-size: 0.85rem; font-weight: 800; color: #1e293b; margin: 0; }
.count-tag { background: #6366f1; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 6px; font-weight: 700; }

.member-scroller {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.member-tile {
  display: flex; align-items: center; gap: 10px;
  padding: 8px; border-radius: 10px; margin-bottom: 6px;
  transition: background 0.2s;
}
.member-tile:hover { background: #f8fafc; }

.avatar-box {
  width: 30px; height: 30px; background: white; border: 1.5px solid #f1f5f9;
  border-radius: 8px; display: flex; align-items: center;
  justify-content: center; font-size: 0.7rem; font-weight: 800; color: #6366f1;
}

.text-stack { display: flex; flex-direction: column; flex: 1; }
.full-name { font-size: 0.8rem; font-weight: 700; color: #334155; }
.email-sub { font-size: 0.65rem; color: #94a3b8; display: flex; align-items: center; gap: 3px; }
.id-dim { font-size: 0.6rem; font-family: monospace; color: #cbd5e1; }

/* --- Upload State --- */
.upload-hero-container {
  flex: 1; max-height: 250px; border: 2px dashed #cbd5e1;
  border-radius: 16px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; cursor: pointer;
  background: #f8fafc; margin: auto 0;
}
.upload-hero-container:hover { border-color: #6366f1; background: #f5f7ff; }
.icon-blob { width: 64px; height: 64px; background: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; color: #6366f1; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.demo-warning { margin-top: 1rem; font-size: 0.7rem; color: #3b82f6; background: #eff6ff; padding: 4px 10px; border-radius: 20px; font-weight: 600; }

.page-footer {
  margin-top: auto; padding-top: 1rem;
  font-size: 0.7rem; color: #94a3b8;
  border-top: 1px solid #f1f5f9;
  display: flex; align-items: center;
}

@media (prefers-color-scheme: dark) {
  .group-card, .active-file-tag, .upload-hero-container { background: #1a1a26; border-color: #2d2d3d; }
  .card-head { background: #232335; border-bottom-color: #2d2d3d; }
  .member-tile:hover { background: #2d2d3d; }
  .full-name { color: #e2e8f0; }
  .pill-badge { background: #252538; color: #94a3b8; }
  .avatar-box { background: #1a1a26; border-color: #2d2d3d; }
}
</style>