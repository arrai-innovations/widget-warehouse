<script setup>
import TheNav from "./TheNav.vue";
import Sonner from "@vueda/feedback/toast/Sonner.vue";
import SidebarInset from "@vueda/navigation/sidebar/SidebarInset.vue";
import SidebarProvider from "@vueda/navigation/sidebar/SidebarProvider.vue";
import SidebarTrigger from "@vueda/navigation/sidebar/SidebarTrigger.vue";
import { RouterView } from "vue-router";
</script>

<template>
    <SidebarProvider>
        <TheNav />
        <SidebarInset>
            <SidebarTrigger />
            <RouterView />
        </SidebarInset>
    </SidebarProvider>
    <Sonner />
</template>
