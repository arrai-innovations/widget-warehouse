<script setup>
import LinkModelView from "@vueda/components/LinkModelView.vue";

import DefaultViewList from "@/views/DefaultViewList.vue";

const relatedModelTargets = {
    category: { app: "catalog", model: "widgetcategory" },
    supplier: { app: "catalog", model: "supplier" },
};
const relatedModelFieldNames = Object.keys(relatedModelTargets);

function getRelatedModelTarget(fieldName, field = {}) {
    const fallback = relatedModelTargets[fieldName] || {};
    return {
        app: field.app_label ?? field.app ?? fallback.app,
        model: field.model ?? fallback.model,
    };
}

function getRelatedModelPk(value) {
    if (value && typeof value === "object") {
        return value.id ?? value.pk;
    }
    return value;
}

function hasRelatedModelPk(value) {
    const pk = getRelatedModelPk(value);
    return pk != null && pk !== "";
}

function getRelatedModelLabel({ formatted, value }) {
    if (formatted != null && formatted !== "") {
        return formatted;
    }
    if (value && typeof value === "object") {
        return value.formatted_name ?? value.name ?? value.id ?? value.pk ?? "";
    }
    return value ?? "";
}

// Model-specific list for catalog.widget. Wraps the app-wide DefaultViewList so
// it inherits the reusable per-row links, then adds a model-specific touch:
// the existing "name" column links to the widget's read view. This keeps the
// "link an existing column" alternative alongside the synthetic "update" (Edit)
// column that DefaultViewList adds for update-capable models.
defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
});
defineOptions({ inheritAttrs: false });
</script>

<template>
    <DefaultViewList v-bind="{ ...$props, ...$attrs }">
        <template #[`field(name)`]="{ pk, formatted }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="read">
                {{ formatted }}
            </LinkModelView>
        </template>
        <template v-for="fieldName in relatedModelFieldNames" :key="fieldName" #[`field(${fieldName})`]="slotProps">
            <LinkModelView
                v-if="hasRelatedModelPk(slotProps.value)"
                :app="getRelatedModelTarget(fieldName, slotProps.field).app"
                :model="getRelatedModelTarget(fieldName, slotProps.field).model"
                :pk="getRelatedModelPk(slotProps.value)"
                view="read"
            >
                {{ getRelatedModelLabel(slotProps) }}
            </LinkModelView>
            <span v-else>{{ getRelatedModelLabel(slotProps) }}</span>
        </template>
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </DefaultViewList>
</template>
