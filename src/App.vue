<script setup lang="ts">
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

const jsonFilePath = ref("");
const jsonFileName = ref("");
const jsonOutput = ref("");
const jsonLoading = ref(false);
const jsonError = ref("");

const credentialsStatus = ref("");
const credentialsStatusType = ref<"info" | "success" | "warning" | "">("");

const authStatus = ref("Loading...");
const authLoading = ref(false);
const isAuthenticated = ref(false);

onMounted(async () => {
  try {
    await new Promise(resolve => setTimeout(resolve, 800));
    await checkAuthStatus();
  } catch (e) {
    console.error("Auth check error:", e);
  }
});

async function checkAuthStatus() {
  try {
    const result = await invoke("check_auth_status");
    const response = JSON.parse(String(result));
    
    if (response.status === "authenticated") {
      isAuthenticated.value = true;
      authStatus.value = "✓ Authenticated with Google";
    } else if (response.status === "expired") {
      isAuthenticated.value = false;
      authStatus.value = "⚠ Token expired, please re-authenticate";
    } else {
      isAuthenticated.value = false;
      authStatus.value = response.has_credentials 
        ? "Ready to authenticate" 
        : "Please save credentials first";
    }
  } catch (e) {
    console.error("Auth check error:", e);
    authStatus.value = "Ready to start";
  }
}

async function openJsonFile() {
  try {
    jsonError.value = "";
    const file = await open({
      filters: [
        {
          name: "JSON",
          extensions: ["json"],
        },
      ],
    });

    if (!file) return;

    jsonFilePath.value = file as string;
    jsonFileName.value = (file as string).split(/[\\/]/).pop() || "";
    
    await processJson();
  } catch (e) {
    jsonError.value = `Failed to open file dialog: ${String(e)}`;
  }
}

async function processJson() {
  if (!jsonFilePath.value) {
    jsonError.value = "No file selected";
    return;
  }

  jsonLoading.value = true;
  jsonError.value = "";
  jsonOutput.value = "";
  credentialsStatus.value = "";

  try {
    const result = await invoke("validate_credentials_file", { filePath: jsonFilePath.value });
    jsonOutput.value = String(result);
  } catch (e) {
    jsonError.value = String(e);
  } finally {
    jsonLoading.value = false;
  }
}

async function saveCredentials() {
  if (!jsonFilePath.value) {
    jsonError.value = "No file selected";
    return;
  }

  try {
    credentialsStatus.value = "";
    jsonError.value = "";
    
    const result = await invoke("save_credentials", { filePath: jsonFilePath.value });
    const response = JSON.parse(String(result));
    
    if (response.status === "saved") {
      credentialsStatus.value = response.message;
      credentialsStatusType.value = "success";
      await checkAuthStatus();
    } else if (response.status === "updated") {
      credentialsStatus.value = response.message;
      credentialsStatusType.value = "warning";
      await checkAuthStatus();
    } else if (response.status === "already_saved") {
      credentialsStatus.value = "✓ " + response.message;
      credentialsStatusType.value = "info";
    } else if (response.status === "error") {
      jsonError.value = response.message;
    }
  } catch (e) {
    jsonError.value = `Failed to save credentials: ${String(e)}`;
  }
}

async function authenticateGoogle() {
  authLoading.value = true;
  jsonError.value = "";
  credentialsStatus.value = "";
  
  try {
    const result = await invoke("authenticate_google");
    const response = JSON.parse(String(result));
    
    if (response.status === "success") {
      credentialsStatus.value = response.message;
      credentialsStatusType.value = "success";
      await checkAuthStatus();
    } else {
      jsonError.value = response.message;
    }
  } catch (e) {
    jsonError.value = `Authentication failed: ${String(e)}`;
  } finally {
    authLoading.value = false;
  }
}
</script>

<template>
  <main class="container">
    <h1>🔐 Quaestionarius</h1>
    <p class="subtitle">Google Forms Authentication Manager</p>

    <div class="auth-status" :class="{ authenticated: isAuthenticated }">
      {{ authStatus }}
    </div>

    <section class="card">
      <h2>Step 1: Upload Credentials</h2>
      <div class="button-group">
        <button @click="openJsonFile" :disabled="jsonLoading" class="btn-primary">
          📁 Select credentials.json
        </button>
        <span v-if="jsonFileName" class="file-name">{{ jsonFileName }}</span>
      </div>

      <div v-if="jsonFileName" class="button-group" style="margin-top: 15px;">
        <button 
          @click="saveCredentials" 
          :disabled="jsonLoading || credentialsStatusType === 'info'" 
          class="btn-success"
        >
          💾 Save Credentials
        </button>
      </div>

      <div v-if="credentialsStatus" :class="['status-message', credentialsStatusType]">
        {{ credentialsStatus }}
      </div>

      <div v-if="jsonError" class="error">
        <strong>Error:</strong> {{ jsonError }}
      </div>
    </section>

    <section class="card">
      <h2>Step 2: Authenticate with Google</h2>
      <button 
        @click="authenticateGoogle" 
        :disabled="authLoading || isAuthenticated" 
        class="btn-google"
      >
        <span v-if="authLoading">⏳ Authenticating...</span>
        <span v-else-if="isAuthenticated">✓ Already Authenticated</span>
        <span v-else>🔗 Connect to Google Account</span>
      </button>
      <p class="help-text">
        This will open a browser window for Google authentication
      </p>
    </section>
  </main>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 5px;
  font-size: 2.5em;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-top: 0;
  margin-bottom: 30px;
}

.auth-status {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  background-color: #fff3cd;
  color: #856404;
  font-weight: 500;
  margin-bottom: 30px;
}

.auth-status.authenticated {
  background-color: #d4edda;
  color: #155724;
}

.card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.3em;
}

.button-group {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.8em 1.5em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.25s;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #646cff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #535bf2;
}

.btn-success {
  background-color: #4caf50;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #45a049;
}

.btn-google {
  background-color: #4285f4;
  color: white;
  width: 100%;
  font-size: 1.1em;
}

.btn-google:hover:not(:disabled) {
  background-color: #357ae8;
}

.file-name {
  color: #646cff;
  font-weight: 500;
  font-size: 0.95em;
}

.help-text {
  margin-top: 10px;
  font-size: 0.9em;
  color: #666;
  font-style: italic;
}

.status-message {
  padding: 12px;
  border-radius: 8px;
  margin-top: 15px;
  font-weight: 500;
}

.status-message.success {
  color: #155724;
  background-color: #d4edda;
}

.status-message.info {
  color: #004085;
  background-color: #cce5ff;
}

.status-message.warning {
  color: #856404;
  background-color: #fff3cd;
}

.error {
  color: #721c24;
  background-color: #f8d7da;
  padding: 12px;
  border-radius: 8px;
  margin-top: 15px;
}

@media (prefers-color-scheme: dark) {
  .container {
    color: #f6f6f6;
  }

  .subtitle {
    color: #aaa;
  }

  .card {
    background-color: #1e1e1e;
    color: #f6f6f6;
  }

  .card h2 {
    color: #f6f6f6;
  }

  .auth-status {
    background-color: #3a2f00;
    color: #fff9c4;
  }

  .auth-status.authenticated {
    background-color: #1b5e20;
    color: #a5d6a7;
  }

  .status-message.success {
    color: #a5d6a7;
    background-color: #1b5e20;
  }

  .status-message.info {
    color: #90caf9;
    background-color: #0d47a1;
  }

  .status-message.warning {
    color: #fff9c4;
    background-color: #f57f17;
  }

  .error {
    background-color: #5a1a1a;
    color: #f8d7da;
  }
}
</style>

<style>
:root {
  font-family: Inter, Avenir, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;

  color: #0f0f0f;
  background-color: #f6f6f6;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  min-height: 100vh;
}

@media (prefers-color-scheme: dark) {
  :root {
    color: #f6f6f6;
    background-color: #2f2f2f;
  }
}
</style>
