<script setup>
import {
    faAngleLeft,
    faBoxesStacked,
    faCodeBranch,
    faCog,
    faHandshake,
    faLayerGroup,
    faMoon,
    faRightFromBracket,
    faRightToBracket,
    faSun,
    faTag,
    faWarehouse,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Sidebar from "@vueda/navigation/sidebar/Sidebar.vue";
import SidebarContent from "@vueda/navigation/sidebar/SidebarContent.vue";
import SidebarFooter from "@vueda/navigation/sidebar/SidebarFooter.vue";
import SidebarHeader from "@vueda/navigation/sidebar/SidebarHeader.vue";
import SidebarMenu from "@vueda/navigation/sidebar/SidebarMenu.vue";
import SidebarMenuButton from "@vueda/navigation/sidebar/SidebarMenuButton.vue";
import SidebarMenuItem from "@vueda/navigation/sidebar/SidebarMenuItem.vue";
import SidebarRail from "@vueda/navigation/sidebar/SidebarRail.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import { storeUser } from "@vueda/stores/storeUser.js";
import { useSidebar } from "@vueda/use/useSidebar.js";
import { computedAsync } from "@vueuse/core";
import { computed, unref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import NavButton from "@/nav/NavButton.vue";
import NavLogo from "@/nav/NavLogo.vue";

const darkModeStore = storeDarkMode();
const userStore = storeUser();
const router = useRouter();
const { state: sidebarState, toggleSidebar, isMobile, openMobile } = useSidebar();

async function handleSignOut() {
    try {
        await userStore.logout();
    } catch {
        return;
    }
    router.push({ name: "landing" });
}
const isExpanded = computed(() => (isMobile.value ? openMobile.value : sidebarState.value === "expanded"));

const models = [
    { title: "Inventory Records", model: "inventoryrecord", icon: faBoxesStacked },
    { title: "Promotions", model: "promotion", icon: faTag },
    { title: "Suppliers", model: "supplier", icon: faHandshake },
    { title: "Warehouses", model: "warehouse", icon: faWarehouse },
    { title: "Widgets", model: "widget", icon: faCog },
    { title: "Widget Categories", model: "widgetcategory", icon: faLayerGroup },
    { title: "Widget Variants", model: "widgetvariant", icon: faCodeBranch },
].map(({ icon = null, ...m }) => ({
    ...m,
    icon,
    to: computedAsync(() => getCRUDForTo({ app: "catalog", model: m.model, view: "list" })),
}));
</script>

<template>
    <Sidebar collapsible="icon">
        <SidebarHeader :theme-override="{ SidebarHeader: { root: { class: { 'p-2': false } } } }">
            <NavButton
                variant="ghost"
                :show-tooltip="!isExpanded"
                data-sidebar="trigger"
                data-slot="sidebar-trigger"
                @click="toggleSidebar"
            >
                <template #default>
                    <FontAwesomeIcon
                        :icon="faAngleLeft"
                        fixed-width
                        :class="['transition-transform duration-200', isExpanded ? 'rotate-0' : 'rotate-180']"
                    />
                    <span v-if="isExpanded">Collapse</span>
                </template>
                <template #tooltip>
                    <p>Expand</p>
                </template>
            </NavButton>
            <NavLogo class="pl-2 pt-2 whitespace-nowrap" :animated="true" />
        </SidebarHeader>
        <SidebarContent>
            <SidebarMenu>
                <SidebarMenuItem v-for="model in models" :key="model.title">
                    <SidebarMenuButton v-if="unref(model.to)" as-child :tooltip="model.title">
                        <RouterLink :to="unref(model.to)">
                            <FontAwesomeIcon v-if="model.icon" :icon="model.icon" />
                            <span>{{ model.title }}</span>
                        </RouterLink>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarContent>
        <SidebarFooter>
            <RouterLink v-if="!userStore.loggedIn" v-slot="{ href, navigate }" to="/sign-in/" custom>
                <NavButton :show-tooltip="!isExpanded" as="a" :href="href" @click="navigate">
                    <template #default>
                        <FontAwesomeIcon :icon="faRightToBracket" fixed-width />
                        <span v-if="isExpanded">Sign In</span>
                    </template>
                    <template #tooltip>
                        <p>Sign In</p>
                    </template>
                </NavButton>
            </RouterLink>
            <NavButton v-else :show-tooltip="!isExpanded" @click="handleSignOut">
                <template #default>
                    <FontAwesomeIcon :icon="faRightFromBracket" fixed-width />
                    <span v-if="isExpanded">Sign Out</span>
                </template>
                <template #tooltip>
                    <p>Sign Out</p>
                </template>
            </NavButton>
            <NavButton variant="secondary" :show-tooltip="!isExpanded" @click="darkModeStore.toggle()">
                <template #default>
                    <FontAwesomeIcon v-if="darkModeStore.isDark" :icon="faSun" fixed-width />
                    <FontAwesomeIcon v-else :icon="faMoon" fixed-width />
                    <span v-if="isExpanded" class="overflow-hidden whitespace-nowrap">
                        Switch to {{ darkModeStore.isDark ? "light" : "dark" }} mode
                    </span>
                </template>
                <template #tooltip>
                    <p>Switch to {{ darkModeStore.isDark ? "light" : "dark" }} mode</p>
                </template>
            </NavButton>
        </SidebarFooter>
        <SidebarRail />
    </Sidebar>
</template>
