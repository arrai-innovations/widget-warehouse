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
});
defineOptions({ inheritAttrs: false });

const modelConfig = useModelConfig(toRef(props, "app"), toRef(props, "model"), "list");
const filteredActions = useFilteredActions({ modelConfigInstance: modelConfig });
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

    if (filteredActions.actions.includes("update")) {
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
    <ViewList :app="app" :model="model" v-bind="$attrs" :display-fields="displayFieldsWithUpdate">
        <!--
            Reusable per-row detail links. The default list prepends a synthetic
            "update" display field for update-capable models without adding it to
            fetch fields. The "read" slot remains available for explicit model
            list customizations.
        -->
        <template #[`field(update)`]="{ pk }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="update" label="Edit" />
        </template>
        <template #[`field(read)`]="{ pk }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="read" label="View" />
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
