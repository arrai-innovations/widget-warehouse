<script setup>
import LinkModelView from "@vueda/navigation/link-model-view/LinkModelView.vue";
import { useFilteredActions } from "@vueda/use/useFilteredActions.js";
import { useModelConfig } from "@vueda/use/useModelConfig.js";
import ViewList from "@vueda/views/ViewList.vue";
import { computed, toRef } from "vue";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    displayFields: { type: Array, default: undefined },
    fieldDetails: { type: Object, default: undefined },
    fetchFields: { type: Array, default: undefined },
});
defineOptions({ inheritAttrs: false });

const modelConfig = useModelConfig(toRef(props, "app"), toRef(props, "model"), "list");
const filteredActions = useFilteredActions({ modelConfigInstance: modelConfig });
const fetchFieldsWithActions = computed(() => [
    ...new Set([
        ...(props.fetchFields?.length ? props.fetchFields : modelConfig.config?.fetchFields || []),
        "available_actions",
    ]),
]);

function canPerform(obj, action) {
    return filteredActions.actions.includes(action) && obj?.available_actions?.includes(action);
}

// "update" is a synthetic column with no model info behind it, so its label comes from here.
const displayFieldsWithUpdate = computed(() => {
    const names = props.displayFields?.length ? props.displayFields : modelConfig.config?.displayFields || [];
    const showUpdate = filteredActions.actions.some((action) => ["update", "retrieve"].includes(action));
    return [...new Set([...(showUpdate ? ["update"] : []), ...names])];
});
const fieldDetailsWithUpdate = computed(() => ({
    ...props.fieldDetails,
    update: { label: "Actions", ...props.fieldDetails?.update },
}));
</script>

<template>
    <ViewList
        :app="app"
        :model="model"
        v-bind="$attrs"
        :display-fields="displayFieldsWithUpdate"
        :field-details="fieldDetailsWithUpdate"
        :fetch-fields="fetchFieldsWithActions"
    >
        <!--
            Reusable per-row detail links. The default list prepends a synthetic
            "update" display field for readable or update-capable models. The
            row's available_actions chooses the link; the server still enforces
            access. The "read" slot supports explicit model list customizations.
        -->
        <template #[`field(update)`]="{ pk, obj }">
            <LinkModelView
                v-if="canPerform(obj, 'update')"
                :app="app"
                :model="model"
                :pk="pk"
                view="update"
                label="Update"
            />
            <LinkModelView
                v-else-if="canPerform(obj, 'retrieve')"
                :app="app"
                :model="model"
                :pk="pk"
                view="read"
                label="Read"
            />
        </template>
        <template #[`field(read)`]="{ pk, obj }">
            <LinkModelView
                v-if="canPerform(obj, 'retrieve')"
                :app="app"
                :model="model"
                :pk="pk"
                view="read"
                label="Read"
            />
        </template>
        <!-- Synthetic columns have no server-provided header; label them in card layout. -->
        <template #[`header(update)`]="slotProps">
            <div v-if="slotProps.isCardLayout" :class="slotProps.class" data-card-header="update">Actions</div>
        </template>
        <template #[`header(read)`]="slotProps">
            <div v-if="slotProps.isCardLayout" :class="slotProps.class" data-card-header="read">Actions</div>
        </template>
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </ViewList>
</template>
