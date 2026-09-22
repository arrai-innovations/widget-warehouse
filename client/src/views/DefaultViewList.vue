<script setup>
import LinkModelView from "@vueda/navigation/link-model-view/LinkModelView.vue";
import { useFilteredActions } from "@vueda/use/useFilteredActions.js";
import { useModelConfig } from "@vueda/use/useModelConfig.js";
import ViewList from "@vueda/views/ViewList.vue";
import { computed, toRef } from "vue";

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    displayFields: { type: Object, default: undefined },
    listFields: { type: Array, default: undefined },
});
defineOptions({ inheritAttrs: false });

const modelConfig = useModelConfig(toRef(props, "app"), toRef(props, "model"), "list");
const filteredActions = useFilteredActions({ modelConfigInstance: modelConfig });
const listFieldsWithActions = computed(() => [
    ...new Set([
        ...(props.listFields?.length ? props.listFields : modelConfig.config?.fetchFields || []),
        "available_actions",
    ]),
]);

function canPerform(obj, action) {
    return filteredActions.actions.includes(action) && obj?.available_actions?.includes(action);
}
const updateField = {
    name: "update",
    label: "Actions",
};

const displayFieldsWithUpdate = computed(() => {
    const fields = {};
    const configuredDisplayFields = Object.keys(props.displayFields || {}).length
        ? Object.values(props.displayFields)
        : (modelConfig.config?.displayFields || []).map((name) => ({
              name,
              ...modelConfig.config?.fieldDetails?.[name],
          }));

    if (filteredActions.actions.some((action) => ["update", "retrieve"].includes(action))) {
        fields.update = updateField;
    }
    for (const field of configuredDisplayFields) {
        if (field?.name === "update") {
            fields.update = { ...updateField, ...field };
        } else if (field?.name) {
            fields[field.name] = field;
        }
    }
    return fields;
});
</script>

<template>
    <ViewList
        :app="app"
        :model="model"
        v-bind="$attrs"
        :display-fields="displayFieldsWithUpdate"
        :list-fields="listFieldsWithActions"
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
