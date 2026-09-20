<script setup>
import Button from "@vueda/controls/button/Button.vue";
import { storeUser } from "@vueda/stores/storeUser.js";
import { useModelConfig } from "@vueda/use/useModelConfig.js";
import { FIELDS_PARAM, ORDERING_PARAM, PAGE_PARAM, PAGE_SIZE_PARAM } from "@vueda/utils/constants.js";
import { fetchHelper } from "@vueda/utils/fetchSupport.js";
import { getListUrl } from "@vueda/utils/urls.js";
import { computedAsync } from "@vueuse/core";
import { computed, toRef } from "vue";
import { useRoute, useRouter } from "vue-router";

import DefaultViewList from "@/views/DefaultViewList.vue";

const props = defineProps({ app: { type: String, required: true }, model: { type: String, required: true } });
defineOptions({ inheritAttrs: false });
const route = useRoute();
const router = useRouter();
const user = storeUser();
const config = useModelConfig(toRef(props, "app"), toRef(props, "model"), "list");
const canReplenish = computed(() => config.info?.actions?.some((action) => action.name === "replenish"));
const shortages = computedAsync(async () => {
    if (!user.loggedIn || route.params.action !== "list") return 0;
    const query = { ...route.query, below_reorder: "true", [PAGE_SIZE_PARAM]: 1, [FIELDS_PARAM]: "id" };
    delete query[PAGE_PARAM];
    delete query[ORDERING_PARAM];
    const page = await fetchHelper(getListUrl({ ...props, query: `?${new URLSearchParams(query)}` }));
    return page.totalRecords;
}, 0);
function reviewShortages() {
    const query = { ...route.query, below_reorder: "true", [ORDERING_PARAM]: "-shortfall" };
    delete query[PAGE_PARAM];
    router.push({ query });
}
</script>

<template>
    <DefaultViewList v-bind="{ ...props, ...$attrs }">
        <!-- Use the list's live click handler: the default link caches a route after
             the first selection and does not observe later mutations of its PK array. -->
        <template #bulk-action-button="action">
            <Button :class="action.class" :disabled="action.disabled" emphasis="ghost" @click="action.click">
                {{ action.label }}
            </Button>
        </template>
        <template #before-list>
            <div v-if="shortages" class="flex flex-wrap items-center justify-between gap-2 border-b px-4 py-2 text-sm">
                <span>{{ shortages }} inventory records below reorder threshold.</span>
                <Button v-if="route.query.below_reorder !== 'true'" emphasis="ghost" @click="reviewShortages">
                    Review shortages
                </Button>
                <span v-else-if="canReplenish" class="text-muted-foreground"
                    >Select records to review replenishment.</span
                >
            </div>
        </template>
    </DefaultViewList>
</template>
