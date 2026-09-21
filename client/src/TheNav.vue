<script setup>
import {
    PhCloudMoon,
    PhFileArrowUp,
    PhGauge,
    PhGear,
    PhGitBranch,
    PhHandshake,
    PhSignIn,
    PhSignOut,
    PhSquaresFour,
    PhStack,
    PhSun,
    PhTag,
    PhWarehouse,
} from "@phosphor-icons/vue";
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
import { computed, markRaw, nextTick, unref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import NavLogo from "@/nav/NavLogo.vue";

const darkModeStore = storeDarkMode();
const modelInfoStore = storeModelInfo();
const userStore = storeUser();
const router = useRouter();
const route = useRoute();

async function handleSignOut() {
    try {
        // Leave the CRUD view before logout invalidates its permissions and metadata.
        // Otherwise it can redirect sign-in back to an edit the next role cannot use.
        await router.push({ name: "dashboard" });
        await nextTick();
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
    { title: "Inventory Records", model: "inventoryrecord", icon: PhStack },
    { title: "Promotions", model: "promotion", icon: PhTag },
    { title: "Purchase Orders", model: "purchaseorder", icon: PhFileArrowUp },
    { title: "Supplier Prices", model: "supplierprice", icon: PhTag },
    { title: "Suppliers", model: "supplier", icon: PhHandshake },
    { title: "Warehouses", model: "warehouse", icon: PhWarehouse },
    { title: "Widgets", model: "widget", icon: PhGear },
    { title: "Widget Categories", model: "widgetcategory", icon: PhSquaresFour },
    { title: "Widget Variants", model: "widgetvariant", icon: PhGitBranch },
].map(({ icon = null, ...m }) => ({
    ...m,
    // The icon is a component rather than a data object, so keep it out of the reactive
    // proxy the way VUEDA's own icon registry does.
    icon: icon && markRaw(icon),
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
        <SidebarHeader
            class="h-12 items-center justify-center"
            :theme-override="{
                SidebarHeader: {
                    root: {
                        class: { 'p-2': false, 'p-0': true },
                    },
                },
            }"
        >
            <NavLogo class="min-w-0 whitespace-nowrap" :animated="true" />
        </SidebarHeader>
        <SidebarContent>
            <SidebarGroup v-if="userStore.loggedIn">
                <SidebarGroupContent>
                    <SidebarMenu>
                        <!-- Above the catalog and outside its group: the dashboard is a
                             place rather than a model, and it takes no permission check
                             because every signed-in user may see the page. What they see
                             on it is decided tile by tile, by the same model info the
                             items below are resolved from. -->
                        <SidebarMenuItem>
                            <SidebarMenuButton as-child :is-active="route.name === 'dashboard'" tooltip="Dashboard">
                                <RouterLink :to="{ name: 'dashboard' }">
                                    <PhGauge weight="duotone" />
                                    <span>Dashboard</span>
                                </RouterLink>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
            <SidebarGroup v-if="userStore.loggedIn">
                <SidebarGroupLabel>Catalog</SidebarGroupLabel>
                <SidebarGroupContent>
                    <SidebarMenu>
                        <!-- Skip the whole item for a model the role cannot list. An empty item would
                             still take a slot in the menu's gap rhythm and leave a visible hole. -->
                        <template v-for="model in models" :key="model.title">
                            <SidebarMenuItem v-if="unref(model.to) !== null">
                                <SidebarMenuSkeleton v-if="unref(model.to) === undefined" :show-icon="!!model.icon" />
                                <SidebarMenuButton
                                    v-else
                                    as-child
                                    :is-active="isModelActive(model.model)"
                                    :tooltip="model.title"
                                >
                                    <RouterLink :to="unref(model.to)">
                                        <component :is="model.icon" v-if="model.icon" weight="duotone" />
                                        <span>{{ model.title }}</span>
                                    </RouterLink>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </template>
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
                            <PhSignIn weight="duotone" />
                            <span>Sign In</span>
                        </RouterLink>
                    </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem v-else>
                    <SidebarMenuButton tooltip="Sign Out" @click="handleSignOut">
                        <PhSignOut weight="duotone" />
                        <span>Sign Out</span>
                    </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                    <SidebarMenuButton tooltip="Toggle color mode" @click="darkModeStore.toggle()">
                        <PhSun v-if="darkModeStore.isDark" weight="duotone" />
                        <PhCloudMoon v-else weight="duotone" />
                        <span>Switch to {{ darkModeStore.isDark ? "light" : "dark" }} mode</span>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        </SidebarFooter>
        <SidebarRail />
    </Sidebar>
</template>
