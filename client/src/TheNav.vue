<script setup>
import Sidebar from "@vueda/navigation/sidebar/Sidebar.vue";
import SidebarContent from "@vueda/navigation/sidebar/SidebarContent.vue";
import SidebarFooter from "@vueda/navigation/sidebar/SidebarFooter.vue";
import SidebarHeader from "@vueda/navigation/sidebar/SidebarHeader.vue";
import SidebarRail from "@vueda/navigation/sidebar/SidebarRail.vue";
</script>

<template>
    <Sidebar>
        <SidebarHeader>
            <h1 class="">
                <span class="inline-block text-xl font-bold text-[#0077f7] first-letter:text-2xl">Widget</span>
                <span class="inline-block text-xl italic text-[#0077f7] first-letter:text-2xl">Warehouse</span>
                <span class="inline-block">.com</span>
            </h1>
        </SidebarHeader>
        <SidebarContent> </SidebarContent>
        <SidebarFooter> </SidebarFooter>
        <SidebarRail />
    </Sidebar>
</template>
