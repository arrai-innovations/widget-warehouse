<script setup>
import {
    faBoxesStacked,
    faCloudMoon,
    faCodeBranch,
    faCog,
    faFileImport,
    faHandshake,
    faLayerGroup,
    faRightFromBracket,
    faRightToBracket,
    faSunBright,
    faTag,
    faWarehouse,
} from "@fortawesome/sharp-duotone-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Sidebar from "@vueda/navigation/sidebar/Sidebar.vue";
import SidebarContent from "@vueda/navigation/sidebar/SidebarContent.vue";
import SidebarFooter from "@vueda/navigation/sidebar/SidebarFooter.vue";
import SidebarGroup from "@vueda/navigation/sidebar/SidebarGroup.vue";
import SidebarGroupContent from "@vueda/navigation/sidebar/SidebarGroupContent.vue";
import SidebarGroupLabel from "@vueda/navigation/sidebar/SidebarGroupLabel.vue";
import SidebarHeader from "@vueda/navigation/sidebar/SidebarHeader.vue";
import SidebarMenu from "@vueda/navigation/sidebar/SidebarMenu.vue";
import SidebarMenuButton from "@vueda/navigation/sidebar/SidebarMenuButton.vue";
import SidebarMenuItem from "@vueda/navigation/sidebar/SidebarMenuItem.vue";
import SidebarMenuSkeleton from "@vueda/navigation/sidebar/SidebarMenuSkeleton.vue";
import SidebarRail from "@vueda/navigation/sidebar/SidebarRail.vue";
import SidebarUserBlock from "@vueda/navigation/sidebar/SidebarUserBlock.vue";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import { storeDarkMode } from "@vueda/stores/storeDarkMode.js";
import { storeModelInfo } from "@vueda/stores/storeModelInfo.js";
import { storeUser } from "@vueda/stores/storeUser.js";
import { computedAsync } from "@vueuse/core";
import { computed, unref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import NavLogo from "@/nav/NavLogo.vue";

const darkModeStore = storeDarkMode();
const modelInfoStore = storeModelInfo();
const userStore = storeUser();
const router = useRouter();
const route = useRoute();

async function handleSignOut() {
    try {
        await userStore.logout();
    } catch {
        return;
    }
    // VUEDA drops every permission-filtered cache itself when the principal changes,
    // including the change to an anonymous session, so nothing to clear here. Do not
    // use $reset: Pinia substitutes a new object for each nested container, which
    // detaches the toRef handles VUEDA composables hold into them.
    router.push({ name: "sign-in" });
}

// The signed-in user's own who-is response carries the name and the Django groups behind
// every permission decision on screen, so the footer block names the account actually in
// use rather than a fixed label. Groups are the demo roles: hyphenated slugs such as
// "inventory-supervisor", rendered here the way the sign-in panel lists them.
function humanizeRole(group) {
    const words = group.replace(/[-_]/g, " ").trim();
    return words.charAt(0).toUpperCase() + words.slice(1);
}

const userName = computed(() => userStore.loggedInUser?.name || userStore.loggedInUser?.email || "");

const userRole = computed(() => {
    const groups = userStore.loggedInUser?.groups ?? [];
    if (groups.length) {
        return groups.map(humanizeRole).join(", ");
    }
    // A developer superuser holds every permission without joining a demo role, so say that
    // instead of leaving the line blank.
    return userStore.loggedInUser?.is_superuser ? "Superuser" : "";
});

const models = [
    { title: "Inventory Records", model: "inventoryrecord", icon: faBoxesStacked },
    { title: "Promotions", model: "promotion", icon: faTag },
    { title: "Purchase Orders", model: "purchaseorder", icon: faFileImport },
    { title: "Suppliers", model: "supplier", icon: faHandshake },
    { title: "Warehouses", model: "warehouse", icon: faWarehouse },
    { title: "Widgets", model: "widget", icon: faCog },
    { title: "Widget Categories", model: "widgetcategory", icon: faLayerGroup },
    { title: "Widget Variants", model: "widgetvariant", icon: faCodeBranch },
].map(({ icon = null, ...m }) => ({
    ...m,
    icon,
    // Reading userStore.loggedIn synchronously makes this computedAsync react to
    // sign-in: it re-evaluates once authenticated and resolves the real route.
    // Returning early while logged out also avoids fetching model info before we
    // have a session; those 403s would otherwise poison storeModelInfo's error
    // cache (its self-DDoS guard), leaving the nav stuck on skeletons even after
    // login until a full page reload.
    to: computedAsync(async () => {
        if (!userStore.loggedIn) return undefined;
        // Model info reports only the actions the signed-in user is permitted, so a role
        // without list on this model resolves to null and the item is skipped. This is the
        // whole difference between the roles on screen: the same nav, built per user from
        // the server's own permission answer, rather than a hard-coded per-role menu.
        const info = await modelInfoStore.fetchModelInfo({ app: "catalog", model: m.model });
        if (!info.actions?.some((action) => action.name === "list")) return null;
        return getCRUDForTo({ app: "catalog", model: m.model, view: "list" });
    }),
}));

function isModelActive(modelName) {
    return route.params.app === "catalog" && route.params.model === modelName;
}
</script>

<template>
    <Sidebar collapsible="icon">
        <SidebarHeader>
            <div class="flex items-center justify-between gap-2">
                <NavLogo class="min-w-0 whitespace-nowrap" :animated="true" />
            </div>
        </SidebarHeader>
        <SidebarContent>
            <SidebarGroup v-if="userStore.loggedIn">
                <SidebarGroupLabel>Catalog</SidebarGroupLabel>
                <SidebarGroupContent>
                    <SidebarMenu>
                        <SidebarMenuItem v-for="model in models" :key="model.title">
                            <SidebarMenuSkeleton v-if="unref(model.to) === undefined" :show-icon="!!model.icon" />
                            <SidebarMenuButton
                                v-else-if="unref(model.to)"
                                as-child
                                :is-active="isModelActive(model.model)"
                                :tooltip="model.title"
                            >
                                <RouterLink :to="unref(model.to)">
                                    <FontAwesomeIcon v-if="model.icon" :icon="model.icon" />
                                    <span>{{ model.title }}</span>
                                </RouterLink>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
            <SidebarUserBlock
                v-if="userStore.loggedIn"
                :name="userName"
                :role="userRole"
                class="rounded-vueda-control p-2"
            />
            <SidebarMenu>
                <SidebarMenuItem v-if="!userStore.loggedIn">
                    <SidebarMenuButton as-child tooltip="Sign In">
                        <RouterLink to="/sign-in/">
                            <FontAwesomeIcon :icon="faRightToBracket" fixed-width />
                            <span>Sign In</span>
                        </RouterLink>
                    </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem v-else>
                    <SidebarMenuButton tooltip="Sign Out" @click="handleSignOut">
                        <FontAwesomeIcon :icon="faRightFromBracket" fixed-width />
                        <span>Sign Out</span>
                    </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                    <SidebarMenuButton variant="outline" tooltip="Toggle color mode" @click="darkModeStore.toggle()">
                        <FontAwesomeIcon v-if="darkModeStore.isDark" :icon="faSunBright" fixed-width />
                        <FontAwesomeIcon v-else :icon="faCloudMoon" fixed-width />
                        <span>Switch to {{ darkModeStore.isDark ? "light" : "dark" }} mode</span>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarFooter>
        <SidebarRail />
    </Sidebar>
</template>
