<script setup>
import { storeUser } from "@vueda/stores/storeUser.js";
import { computed } from "vue";

const userStore = storeUser();
const displayName = computed(() => userStore.user?.name || userStore.user?.email || "there");
</script>

<template>
    <div style="padding: 2rem">
        <h1>Welcome, {{ displayName }}</h1>
        <p>Widget Warehouse management console.</p>
        <nav>
            <ul>
                <li>
                    <RouterLink to="/catalog/widget/list/">Widgets</RouterLink>
                </li>
                <li>
                    <RouterLink to="/catalog/widget-category/list/">Categories</RouterLink>
                </li>
                <li>
                    <RouterLink to="/catalog/widget-variant/list/">Variants</RouterLink>
                </li>
            </ul>
        </nav>
    </div>
</template>
